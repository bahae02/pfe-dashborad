from flask_cors import CORS
from flask import Flask, request, jsonify
import pandas as pd
from flask import render_template
import os
import math
from datetime import datetime
import logging
from werkzeug.utils import secure_filename
from config import Config
from utils import cleanup_old_files, get_folder_size
from prophet_utils import (
    prepare_prophet_data, train_prophet_model, evaluate_forecast,
    analyze_trend, forecast_by_segment, calculate_advanced_kpis,
    get_forecast_insights
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
config = Config()
app.config.from_object(config)
CORS(app)

# Helper function to validate file upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def get_file_error(file):
    """Validate uploaded file and return error message or None"""
    if file is None:
        return "No file provided"
    if file.filename == '':
        return "Empty filename"
    if not allowed_file(file.filename):
        return f"File type not allowed. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
    
    # Check file size (max 50MB per file)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    max_file_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_file_size:
        return f"File too large. Max size: 50MB, got: {file_size / (1024*1024):.1f}MB"
    
    return None

# Store file paths instead of dataframes in memory
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

forecast_files = []
real_files = []
last_merged_data = None

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload/forecast", methods=["POST"])
def upload_forecast():
    try:
        if "file" not in request.files:
            logger.warning("Upload forecast: No file in request")
            return {"error": "No file part"}, 400
        
        file = request.files["file"]
        file_error = get_file_error(file)
        if file_error:
            logger.warning(f"Upload forecast: {file_error}")
            return {"error": file_error}, 400
        
        safe_filename = secure_filename(file.filename)
        filename = os.path.join(config.UPLOAD_FOLDER, f"forecast_{safe_filename}")
        file.save(filename)
        forecast_files.append(filename)
        logger.info(f"Forecast file uploaded: {safe_filename}")
        return {"message": "Forecast ajouté"}, 200
    except Exception as e:
        logger.error(f"Error uploading forecast: {str(e)}")
        return {"error": "Upload failed"}, 500

@app.route("/upload/real", methods=["POST"])
def upload_real():
    try:
        if "file" not in request.files:
            logger.warning("Upload real: No file in request")
            return {"error": "No file part"}, 400
        
        file = request.files["file"]
        file_error = get_file_error(file)
        if file_error:
            logger.warning(f"Upload real: {file_error}")
            return {"error": file_error}, 400
        
        safe_filename = secure_filename(file.filename)
        filename = os.path.join(config.UPLOAD_FOLDER, f"real_{safe_filename}")
        file.save(filename)
        real_files.append(filename)
        logger.info(f"Real file uploaded: {safe_filename}")
        return {"message": "Real ajouté"}, 200
    except Exception as e:
        logger.error(f"Error uploading real: {str(e)}")
        return {"error": "Upload failed"}, 500

@app.route("/clear", methods=["POST"])
def clear_uploads():
    """Clear all uploaded files"""
    global forecast_files, real_files
    for f in forecast_files + real_files:
        try:
            os.remove(f)
        except:
            pass
    forecast_files = []
    real_files = []
    logger.info("Cleared all uploaded files")
    return {"message": "Cleared"}, 200


@app.route("/health", methods=["GET"])
def health_check():
    """System health check"""
    try:
        folder_size = get_folder_size(config.UPLOAD_FOLDER)
        
        # Warn if folder is getting large
        warning = None
        if folder_size > 500:  # 500MB
            warning = f"Upload folder is {folder_size:.1f}MB - consider cleanup"
            cleanup_count = cleanup_old_files(config.UPLOAD_FOLDER, hours=24)
            logger.warning(f"Auto cleanup: removed {cleanup_count} old files")
        
        return jsonify({
            "status": "healthy",
            "folder_size_mb": round(folder_size, 2),
            "warning": warning,
            "files_count": len(forecast_files) + len(real_files)
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/process", methods=["GET"])
def process():

    try:
        global forecast_files, real_files, last_merged_data

        logger.info(f"Processing: forecast_files={forecast_files}, real_files={real_files}")

        if len(forecast_files) == 0 or len(real_files) == 0:
            return jsonify({"error": "Upload forecast et real"}), 400

        # -----------------------
        # 1. FORECAST - Read from files
        # -----------------------
        forecast_dfs = []
        for file_path in forecast_files:
            logger.info(f"Reading forecast from: {file_path}")
            df = pd.read_excel(file_path, skiprows=1)
            df.columns = df.columns.str.strip()
            forecast_dfs.append(df)
        
        forecast_df = pd.concat(forecast_dfs, ignore_index=True)

        logger.info(f"Forecast columns BEFORE clean: {forecast_df.columns.tolist()}")
        
        # Drop columns with NaN names and empty columns
        forecast_df = forecast_df.loc[:, forecast_df.columns.notna()]
        forecast_df = forecast_df.dropna(axis=1, how='all')
        
        logger.info(f"Forecast columns AFTER clean: {forecast_df.columns.tolist()}")
        logger.info(f"Forecast shape: {forecast_df.shape}")

        if "Fournisseur" not in forecast_df.columns or "Réf. STC" not in forecast_df.columns:
            return jsonify({"error": "Forecast data missing 'Fournisseur' or 'Réf. STC' column"}), 400

        # Get only Semaine columns (weeks)
        id_vars = ["Fournisseur", "Réf. STC"]
        week_cols = [col for col in forecast_df.columns if "Semaine" in str(col).lower() or "semaine" in str(col).lower()]
        
        logger.info(f"Week columns found: {week_cols}")
        
        if not week_cols:
            return jsonify({"error": "No 'Semaine' columns found in forecast data. Columns: " + str(forecast_df.columns.tolist())}), 400

        forecast_melt = forecast_df[id_vars + week_cols].melt(
            id_vars=id_vars,
            var_name="Periode",
            value_name="Forecast"
        )

        # Convert Forecast to numeric, coercing errors to NaN
        forecast_melt["Forecast"] = pd.to_numeric(forecast_melt["Forecast"], errors="coerce")
        
        forecast_melt = forecast_melt.dropna(subset=["Forecast"])
        
        # Aggregate by Réf. STC and Periode
        forecast_agg = forecast_melt.groupby(["Réf. STC", "Periode"])["Forecast"].sum().reset_index()
        forecast_agg["Forecast"] = pd.to_numeric(forecast_agg["Forecast"], errors="coerce")
        logger.info(f"Forecast aggregated: {len(forecast_agg)} rows")

        # -----------------------
        # 2. REAL - Read from files
        # -----------------------
        logger.info(f"Real files count: {len(real_files)}")
        
        real_dfs = []
        for file_path in real_files:
            logger.info(f"Reading real from: {file_path}")
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            real_dfs.append(df)
        
        real_df = pd.concat(real_dfs, ignore_index=True)

        logger.info(f"Real columns: {real_df.columns.tolist()}")
        logger.info(f"Real shape: {real_df.shape}")

        # Check if required columns exist - handle different possible column names
        date_col = None
        qty_col = None
        article_col = None
        
        for col in real_df.columns:
            col_lower = str(col).lower()
            if "date" in col_lower and date_col is None:
                date_col = col
            if "quantité" in col_lower or "qty" in col_lower or "quantity" in col_lower:
                qty_col = col
        
        # Prioritize "Article" over "Référence"
        for col in real_df.columns:
            col_lower = str(col).lower()
            if col_lower == "article":
                article_col = col
                break
        
        # If no Article, try Référence
        if article_col is None:
            for col in real_df.columns:
                col_lower = str(col).lower()
                if "réf" in col_lower or "ref" in col_lower:
                    article_col = col
                    break
        
        if date_col is None:
            return jsonify({"error": f"Real data missing date column. Available: {real_df.columns.tolist()}"})
        if qty_col is None:
            return jsonify({"error": f"Real data missing quantity column. Available: {real_df.columns.tolist()}"})
        if article_col is None:
            return jsonify({"error": f"Real data missing article/reference column. Available: {real_df.columns.tolist()}"})

        logger.info(f"Using columns - Date: {date_col}, Qty: {qty_col}, Article: {article_col}")

        # convertir date
        real_df["Date_temp"] = pd.to_datetime(real_df[date_col], errors="coerce")
        
        # Drop rows with invalid dates
        initial_row_count = len(real_df)
        real_df = real_df.dropna(subset=["Date_temp"])
        logger.info(f"Date conversion: {initial_row_count} -> {len(real_df)} rows (dropped {initial_row_count - len(real_df)} invalid dates)")

        # créer période (année-semaine format to match forecast)
        # Python %W: 0-53 (Monday is first day), so we add 1 to match "Semaine 01-53" format
        try:
            real_df["week_num"] = real_df["Date_temp"].dt.strftime("%W").astype(int)
            real_df["Periode"] = real_df["week_num"].add(1).apply(lambda x: f"Semaine {x:02d}")
            logger.info(f"Real periode created successfully. Sample: {real_df['Periode'].head().tolist()}")
        except Exception as e:
            logger.error(f"ERROR creating Periode: {e}")
            logger.error(f"Date_temp sample: {real_df['Date_temp'].head()}")
            raise

        # agréger quantité
        real_df[qty_col] = pd.to_numeric(real_df[qty_col], errors="coerce")
        
        # Remove rows with NaN quantities
        qty_before = len(real_df)
        real_df = real_df.dropna(subset=[qty_col])
        logger.info(f"Quantity conversion: {qty_before} -> {len(real_df)} rows (dropped {qty_before - len(real_df)} invalid quantities)")
        
        real_grouped = real_df.groupby([article_col, "Periode"])[qty_col].sum().reset_index()
        real_grouped = real_grouped.rename(columns={article_col: "Réf. STC", qty_col: "Real"})
        real_grouped["Real"] = pd.to_numeric(real_grouped["Real"], errors="coerce")
        
        # Clean up
        real_grouped = real_grouped.dropna(subset=["Real"])

        # -----------------------
        # 3. MERGE
        # -----------------------
        # Ensure 'Réf. STC' is string in both dataframes
        forecast_agg["Réf. STC"] = forecast_agg["Réf. STC"].astype(str).str.strip()
        real_grouped["Réf. STC"] = real_grouped["Réf. STC"].astype(str).str.strip()

        # Debug: print available data
        logger.debug(f"Forecast periodes: {sorted(forecast_agg['Periode'].unique())}")
        logger.debug(f"Real periodes: {sorted(real_grouped['Periode'].unique())}")
        logger.debug(f"Forecast Réf. STC (first 5): {forecast_agg['Réf. STC'].unique()[:5]}")
        logger.debug(f"Real Réf. STC (first 5): {real_grouped['Réf. STC'].unique()[:5]}")

        merged = pd.merge(forecast_agg, real_grouped, on=["Réf. STC", "Periode"], how="inner")
        logger.info(f"Merged rows: {len(merged)}")
        
        if merged.empty:
            # Try outer join to see what's available
            outer_merge = pd.merge(forecast_agg, real_grouped, on=["Réf. STC", "Periode"], how="outer")
            return jsonify({"error": f"No matching data. Forecast has {len(forecast_agg)} rows, Real has {len(real_grouped)} rows, but 0 matched on (Réf. STC, Periode)"})

        # -----------------------
        # 4. KPI
        # -----------------------
        if merged.empty:
            return jsonify({"error": "Aucune donnée correspondante trouvée"})

        merged["Ecart"] = merged["Real"] - merged["Forecast"]
        
        # Total quantities
        total_forecast = merged["Forecast"].sum()
        total_real = merged["Real"].sum()
        total_ecart = merged["Ecart"].sum()
        
        # Overall error percentage
        if total_forecast != 0:
            erreur_percentage = (abs(total_ecart) / total_forecast) * 100
        else:
            erreur_percentage = 0
        
        # Reliability: how close forecast was to reality
        # 100% = perfect, 0% = completely wrong
        fiabilite = max(0, 100 - erreur_percentage)

        logger.info(f"Total Forecast: {total_forecast}, Total Real: {total_real}, Total Écart: {total_ecart}")
        logger.info(f"Error %: {erreur_percentage}, Fiabilité: {fiabilite}")

        # Handle NaN or inf values
        if math.isnan(erreur_percentage) or math.isinf(erreur_percentage):
            erreur_percentage = 0.0
        if math.isnan(total_ecart) or math.isinf(total_ecart):
            total_ecart = 0.0
        if math.isnan(fiabilite) or math.isinf(fiabilite):
            fiabilite = 100.0

        # Store data for charts
        last_merged_data = merged

        return jsonify({
            "fiabilite": round(fiabilite, 2),
            "ecart": round(total_ecart, 2),
            "erreur": round(erreur_percentage, 2)
        })
    except Exception as e:
        logger.error(f"Error in process: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Store last merged data for charts
last_merged_data = None

@app.route("/chart-data", methods=["GET"])
def get_chart_data():
    """Return data for charts with optional filtering"""
    global last_merged_data
    if last_merged_data is None:
        return jsonify({"error": "No data available"}), 400
    
    try:
        df = last_merged_data.copy()
        
        # Apply filters
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")
        product = request.args.get("product", "")
        
        # Product filter
        if product and product != "":
            df = df[df["Réf. STC"].astype(str).str.strip() == str(product).strip()]
        
        # Date filter - convert calendar dates to week numbers
        if start_date or end_date:
            # Extract week number from Periode (e.g., "Semaine 01" -> 1)
            df["week_num"] = df["Periode"].str.extract(r'(\d+)').astype(int)
            
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    # Python %W returns 0-53, so add 1 to match "Semaine 01-53" format
                    start_week = int(start_dt.strftime("%W")) + 1
                    df = df[df["week_num"] >= start_week]
                    logger.debug(f"Start date {start_date} converted to week {start_week}")
                except Exception as e:
                    logger.warning(f"Error parsing start_date: {e}")
            
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    # Python %W returns 0-53, so add 1 to match "Semaine 01-53" format
                    end_week = int(end_dt.strftime("%W")) + 1
                    df = df[df["week_num"] <= end_week]
                    logger.debug(f"End date {end_date} converted to week {end_week}")
                except Exception as e:
                    logger.warning(f"Error parsing end_date: {e}")
            
            df = df.drop("week_num", axis=1)
        
        # By Week - sort properly
        week_data = df.groupby("Periode").agg({
            "Forecast": "sum",
            "Real": "sum"
        }).reset_index()
        
        # Sort weeks naturally (Semaine 01, 02, 03, etc.)
        week_data["week_num"] = week_data["Periode"].str.extract(r'(\d+)').astype(int)
        week_data = week_data.sort_values("week_num").drop("week_num", axis=1).reset_index(drop=True)
        
        # Validate data
        if len(week_data) == 0:
            logger.warning(f"Warning: No week data after filtering")
            return jsonify({
                "by_week": [],
                "by_product": [],
                "heatmap": [],
                "trend": []
            })
        
        # By Product (top 10)
        product_data = df.groupby("Réf. STC").agg({
            "Forecast": "sum",
            "Real": "sum",
            "Ecart": "sum"
        }).reset_index().nlargest(10, "Real")
        
        # Heatmap data (all detail rows for error calculation)
        heatmap_data = df[["Réf. STC", "Periode", "Forecast", "Real", "Ecart"]].copy()
        heatmap_data["error_pct"] = (heatmap_data["Ecart"].abs() / (heatmap_data["Forecast"] + 1) * 100).round(2)
        # Cap error_pct to maximum 10000% to avoid extremely large values
        heatmap_data["error_pct"] = heatmap_data["error_pct"].clip(upper=10000)
        heatmap_data = heatmap_data.to_dict(orient="records")
        
        # Trend data (cumulative by week in correct order)
        trend_data = week_data.copy()
        trend_data["cumulative_ecart"] = (trend_data["Real"] - trend_data["Forecast"]).cumsum()
        
        logger.info(f"Chart data filtered: {len(df)} rows, product={product}, start={start_date}, end={end_date}")
        logger.info(f"Week data shape: {len(week_data)}, Product data shape: {len(product_data)}")
        
        return jsonify({
            "by_week": week_data.to_dict(orient="records"),
            "by_product": product_data.to_dict(orient="records"),
            "heatmap": heatmap_data,
            "trend": trend_data[["Periode", "Forecast", "Real", "cumulative_ecart"]].to_dict(orient="records")
        })
    except Exception as e:
        logger.error(f"Error in chart-data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["GET"])
def get_products():
    """Return list of all products"""
    global last_merged_data
    if last_merged_data is None:
        return jsonify({"products": []}), 200
    
    try:
        products = sorted(last_merged_data["Réf. STC"].unique().tolist())
        return jsonify({"products": products})
    except Exception as e:
        return jsonify({"products": []}), 200


@app.route("/forecast/prophet", methods=["GET"])
def prophet_forecast():
    """
    Generate Prophet AI forecast for daily demand
    
    Query parameters:
        - product: (optional) Filter by specific product
        - periods: (optional) Number of days to forecast (default 30)
    """
    global last_merged_data
    
    if last_merged_data is None:
        return jsonify({"error": "No processed data available. Please upload and process files first."}), 400
    
    try:
        product = request.args.get("product", "")
        periods = int(request.args.get("periods", 30))
        
        logger.info(f"Prophet forecast requested: product={product}, periods={periods}")
        
        # Filter by product if specified
        df = last_merged_data.copy()
        if product and product != "":
            df = df[df["Réf. STC"].astype(str).str.strip() == str(product).strip()]
            if df.empty:
                return jsonify({"error": f"Product '{product}' not found"}), 404
        
        # Convert Periode to date for Prophet - use Monday as reference day
        # Assuming weekly data: "Semaine 01" = first week of year
        periodo_num = "1-" + df["Periode"].str.extract(r'(\d+)', expand=False).astype(str) + "-2024"
        df["date"] = pd.to_datetime(periodo_num, format='%w-%W-%Y', errors='coerce')
        if df["date"].isna().all():
            # Fallback: just use sequential dates
            df["date"] = pd.date_range(start='2024-01-01', periods=len(df))
        
        df = df.dropna(subset=["date"])
        
        if len(df) < 10:
            return jsonify({
                "error": f"Insufficient data for forecasting. Need at least 10 data points, have {len(df)}"
            }), 400
        
        # Prepare and train Prophet model
        prophet_data = prepare_prophet_data(df, "date", "Real")
        logger.info(f"Prophet data prepared: {len(prophet_data)} rows")
        logger.debug(f"Prophet data sample:\n{prophet_data.head()}")
        
        model, forecast = train_prophet_model(prophet_data, periods=periods, interval_width=0.95)
        logger.info(f"Prophet model trained with forecast for {periods} periods")
        
        # Evaluate against actual data - ensure proper alignment
        if "Real" in df.columns and len(df) > 0:
            # Use the original df with correct dates for evaluation
            actual_data = df[["date", "Real"]].drop_duplicates().reset_index(drop=True)
            actual_data['date'] = pd.to_datetime(actual_data['date'])
            actual_data = actual_data.dropna(subset=['Real'])
            
            logger.info(f"Actual data for evaluation: {len(actual_data)} rows")
            logger.debug(f"Actual data range: {actual_data['date'].min()} to {actual_data['date'].max()}")
            
            metrics = calculate_advanced_kpis(
                actual_data,
                forecast,
                "date",
                "Real"
            )
            logger.info(f"Metrics: {metrics}")
        else:
            metrics = None
        
        # Get trend analysis
        trend = analyze_trend(forecast)
        
        # Get insights
        insights = get_forecast_insights(forecast)
        
        # Prepare response with proper JSON-serializable format
        forecast_future = forecast.tail(periods)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        forecast_records = []
        for _, row in forecast_future.iterrows():
            record = {
                "ds": str(row['ds'].date()),
                "yhat": float(row['yhat']) if not pd.isna(row['yhat']) else None,
                "yhat_lower": float(row['yhat_lower']) if not pd.isna(row['yhat_lower']) else None,
                "yhat_upper": float(row['yhat_upper']) if not pd.isna(row['yhat_upper']) else None
            }
            forecast_records.append(record)
        
        response = {
            "forecast": forecast_records,
            "trend": trend,
            "metrics": metrics,
            "insights": insights,
            "periods": periods,
            "product": product if product else "All Products",
            "data_points_used": len(prophet_data)
        }
        
        logger.info(f"Prophet forecast generated successfully")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in prophet_forecast: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/analytics/advanced", methods=["GET"])
def advanced_analytics():
    """
    Get advanced analytics and AI insights about forecast accuracy
    
    Returns:
        - Accuracy metrics by product
        - Forecast improvement suggestions
        - Anomaly detection
        - Seasonality insights
    """
    global last_merged_data
    
    if last_merged_data is None:
        return jsonify({"error": "No processed data available"}), 400
    
    try:
        df = last_merged_data.copy()
        
        logger.info("Generating advanced analytics...")
        
        # 1. Accuracy by product
        product_accuracy = df.groupby("Réf. STC").apply(
            lambda x: {
                "product": x.name,
                "forecast_total": float(x["Forecast"].sum()),
                "real_total": float(x["Real"].sum()),
                "accuracy": float(max(0, 100 - abs((x["Real"].sum() - x["Forecast"].sum()) / max(1, x["Forecast"].sum()) * 100))),
                "ecart": float((x["Real"] - x["Forecast"]).sum()),
                "ecart_pct": float(abs((x["Real"] - x["Forecast"]).sum()) / max(1, x["Forecast"].sum()) * 100)
            }
        ).tolist()
        
        # Sanitize NaN and inf values
        for p in product_accuracy:
            for key in list(p.keys()):
                if isinstance(p[key], float):
                    if math.isnan(p[key]) or math.isinf(p[key]):
                        p[key] = 0.0 if key == "accuracy" else None
        
        # 2. Worst performing products (anomalies) - filter None accuracy values
        valid_products = [p for p in product_accuracy if p["accuracy"] is not None]
        anomalies = sorted(valid_products, key=lambda x: x["accuracy"])[:5]
        
        # 3. Best performing products
        best_products = sorted(valid_products, key=lambda x: x["accuracy"], reverse=True)[:5]
        
        # 4. Overall insights
        total_accuracy = max(0, 100 - abs(df["Ecart"].sum()) / max(1, df["Forecast"].sum()) * 100)
        
        # 5. Volatility analysis
        volatility = df.groupby("Réf. STC").apply(
            lambda x: {
                "product": x.name,
                "forecast_std": float(x["Forecast"].std()),
                "real_std": float(x["Real"].std()),
                "consistency": float(1 - (x["Real"].std() / max(1, x["Forecast"].std()) if x["Forecast"].std() > 0 else 1))
            }
        ).tolist()
        
        # Sanitize NaN and inf values from volatility
        for v in volatility:
            for key in list(v.keys()):
                if isinstance(v[key], float):
                    if math.isnan(v[key]) or math.isinf(v[key]):
                        v[key] = None
        
        # Most volatile products - filter None values
        valid_volatility = [v for v in volatility if v["real_std"] is not None]
        volatile_products = sorted(valid_volatility, key=lambda x: x["real_std"], reverse=True)[:3]
        
        response = {
            "overall_accuracy": round(total_accuracy, 2),
            "total_products": len(product_accuracy),
            "products_with_good_accuracy": len([p for p in product_accuracy if p["accuracy"] >= 80]),
            "products_with_poor_accuracy": len([p for p in product_accuracy if p["accuracy"] < 60]),
            "best_performing_products": best_products,
            "worst_performing_products": anomalies,
            "most_volatile_products": volatile_products,
            "recommendations": generate_recommendations(product_accuracy, volatile_products)
        }
        
        logger.info("Advanced analytics generated")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in advanced_analytics: {str(e)}")
        return jsonify({"error": str(e)}), 500


def generate_recommendations(products, volatile):
    """Generate actionable recommendations based on analytics"""
    recommendations = []
    
    # Overall accuracy recommendation
    avg_accuracy = sum(p["accuracy"] for p in products) / len(products) if products else 0
    if avg_accuracy < 70:
        recommendations.append({
            "type": "warning",
            "message": "Overall forecast accuracy is low. Review forecast methodology."
        })
    
    # volatile products
    if volatile:
        recommendations.append({
            "type": "info",
            "message": f"Products with high volatility detected: {', '.join([p['product'] for p in volatile])}. Consider safety stock increase."
        })
    
    # Bias detection
    if products:
        total_bias = sum(p["ecart"] for p in products)
        if total_bias > 0:
            recommendations.append({
                "type": "warning",
                "message": f"Systematic under-forecasting detected (+{total_bias:.0f}). Forecast is consistently below actual."
            })
        elif total_bias < 0:
            recommendations.append({
                "type": "warning",
                "message": f"Systematic over-forecasting detected ({total_bias:.0f}). Forecast is consistently above actual."
            })
    
    if not recommendations:
        recommendations.append({
            "type": "success",
            "message": "✅ Forecast accuracy is good. Keep current methodology."
        })
    
    return recommendations


if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )