"""
Prophet AI Model Integration for Time Series Forecasting
Provides advanced forecasting and trend analysis capabilities
"""

import logging
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error, mean_squared_error
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


def interpolate_daily_from_weekly(df, date_col, value_col):
    """
    Interpolate weekly data to daily data for better Prophet forecasting
    
    Args:
        df: DataFrame with weekly data
        date_col: Date column name
        value_col: Value column name
        
    Returns:
        DataFrame with daily interpolated data
    """
    try:
        # Copy and prepare data
        interp_df = df[[date_col, value_col]].copy()
        interp_df.columns = ['ds', 'y']
        interp_df['ds'] = pd.to_datetime(interp_df['ds'])
        interp_df = interp_df.sort_values('ds').drop_duplicates('ds')
        
        # Create daily range
        date_range = pd.date_range(start=interp_df['ds'].min(), end=interp_df['ds'].max(), freq='D')
        daily_df = pd.DataFrame({'ds': date_range})
        
        # Merge and interpolate
        daily_df = daily_df.merge(interp_df, on='ds', how='left')
        daily_df['y'] = daily_df['y'].interpolate(method='linear')
        
        # Fill any remaining NaN at start/end with forward/backward fill
        daily_df['y'] = daily_df['y'].fillna(method='bfill').fillna(method='ffill')
        
        logger.info(f"Interpolated {len(interp_df)} weekly points to {len(daily_df)} daily points")
        return daily_df
        
    except Exception as e:
        logger.warning(f"Interpolation failed: {e}. Using original weekly data.")
        return df



def prepare_prophet_data(df, date_col, value_col):
    """
    Prepare data for Prophet model with daily interpolation for better accuracy
    
    Args:
        df: DataFrame with timeseries data
        date_col: Column name with dates
        value_col: Column name with values to forecast
        
    Returns:
        DataFrame with 'ds' and 'y' columns (Prophet format)
    """
    try:
        # First interpolate to daily if we have few data points
        if len(df) < 20:
            logger.info(f"Interpolating {len(df)} weekly data points to daily data...")
            prophet_df = interpolate_daily_from_weekly(df, date_col, value_col)
        else:
            prophet_df = df[[date_col, value_col]].copy()
            prophet_df.columns = ['ds', 'y']
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
            prophet_df = prophet_df.sort_values('ds')
            
            # Remove duplicates, keeping the sum
            prophet_df = prophet_df.groupby('ds')['y'].sum().reset_index()
        
        # Remove nulls
        prophet_df = prophet_df.dropna(subset=['y'])
        
        logger.info(f"Prepared Prophet data: {len(prophet_df)} rows, date range: {prophet_df['ds'].min()} to {prophet_df['ds'].max()}")
        return prophet_df
        
    except Exception as e:
        logger.error(f"Error preparing Prophet data: {e}")
        raise


def train_prophet_model(df, periods=12, interval_width=0.95):
    """
    Train Prophet model on timeseries data
    
    Args:
        df: DataFrame with 'ds' and 'y' columns
        periods: Number of periods to forecast
        interval_width: Prediction interval width (0-1)
        
    Returns:
        Tuple: (model, forecast_df)
    """
    try:
        if len(df) < 10:
            logger.warning(f"Warning: Only {len(df)} rows for forecasting. Prophet works better with more data (50+)")
        
        # Initialize and train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=interval_width,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10
        )
        
        logger.info("Training Prophet model...")
        model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=periods, freq='D')
        forecast = model.predict(future)
        
        logger.info(f"Prophet model trained. Forecast: {periods} periods ahead")
        
        return model, forecast
        
    except Exception as e:
        logger.error(f"Error training Prophet model: {e}")
        raise


def evaluate_forecast(actual, predicted):
    """
    Calculate forecast accuracy metrics
    
    Args:
        actual: Actual values
        predicted: Predicted values
        
    Returns:
        Dict with metrics: MAPE, MAE, RMSE, R²
    """
    try:
        # Ensure same length
        min_len = min(len(actual), len(predicted))
        actual = actual[:min_len]
        predicted = predicted[:min_len]
        
        # Handle zeros for MAPE
        mask = actual != 0
        if mask.sum() == 0:
            mape = 0
        else:
            mape = mean_absolute_percentage_error(actual[mask], predicted[mask])
        
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        
        # R² calculation
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            "mape": round(mape * 100, 2),  # Convert to percentage
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4),
            "accuracy": round(max(0, (100 - mape * 100)), 2)
        }
        
    except Exception as e:
        logger.error(f"Error evaluating forecast: {e}")
        return {
            "mape": 0,
            "mae": 0,
            "rmse": 0,
            "r2": 0,
            "accuracy": 0
        }


def analyze_trend(forecast_df):
    """
    Analyze trend from forecast
    
    Args:
        forecast_df: Prophet forecast dataframe
        
    Returns:
        Dict with trend analysis
    """
    try:
        if 'trend' not in forecast_df.columns:
            return None
        
        trend = forecast_df['trend'].values
        
        # Calculate trend direction
        if len(trend) >= 2:
            trend_slope = (trend[-1] - trend[0]) / len(trend)
            trend_direction = "increasing" if trend_slope > 0 else "decreasing" if trend_slope < 0 else "stable"
        else:
            trend_direction = "stable"
        
        return {
            "trend_direction": trend_direction,
            "trend_strength": abs(trend_slope) if len(trend) >= 2 else 0,
            "forecast_mean": float(forecast_df['yhat'].mean()),
            "forecast_std": float(forecast_df['yhat'].std()),
            "upper_bound": float(forecast_df['yhat_upper'].max()),
            "lower_bound": float(forecast_df['yhat_lower'].min())
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trend: {e}")
        return None


def forecast_by_segment(df, group_col, date_col, value_col, periods=12):
    """
    Train separate Prophet models for each segment (product)
    
    Args:
        df: DataFrame with data
        group_col: Column to group by (e.g., product)
        date_col: Date column
        value_col: Value column
        periods: Number of periods to forecast
        
    Returns:
        Dict with forecasts by segment
    """
    results = {}
    
    try:
        for group in df[group_col].unique():
            group_data = df[df[group_col] == group]
            
            try:
                prophet_data = prepare_prophet_data(group_data, date_col, value_col)
                
                if len(prophet_data) >= 5:
                    model, forecast = train_prophet_model(prophet_data, periods=periods)
                    
                    results[str(group)] = {
                        "forecast": forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_dict(orient='records'),
                        "trend": analyze_trend(forecast),
                        "success": True
                    }
                else:
                    logger.warning(f"Insufficient data for {group}: {len(prophet_data)} rows")
                    results[str(group)] = {"success": False, "error": "Insufficient data"}
                    
            except Exception as e:
                logger.error(f"Error forecasting {group}: {e}")
                results[str(group)] = {"success": False, "error": str(e)}
        
        return results
        
    except Exception as e:
        logger.error(f"Error in forecast_by_segment: {e}")
        return {}


def calculate_advanced_kpis(actual_df, forecast_df, date_col, value_col):
    """
    Calculate advanced KPI metrics using actual vs forecasted data
    
    Args:
        actual_df: Actual data with date and value columns
        forecast_df: Prophet forecast dataframe with 'ds' and 'yhat' columns
        date_col: Date column name in actual_df
        value_col: Value column name in actual_df
        
    Returns:
        Dict with advanced metrics
    """
    try:
        # Ensure we have the right data
        if actual_df is None or forecast_df is None:
            logger.warning("Actual or forecast dataframe is None")
            return None
            
        # Prepare actual data
        actual_prep = actual_df[[date_col, value_col]].copy()
        actual_prep['ds'] = pd.to_datetime(actual_prep[date_col])
        actual_prep = actual_prep[['ds', value_col]].sort_values('ds').drop_duplicates('ds')
        
        # Remove rows with NaN or invalid values
        actual_prep = actual_prep.dropna(subset=[value_col])
        actual_prep = actual_prep[actual_prep[value_col] != 0]  # Remove zero values
        
        if len(actual_prep) == 0:
            logger.warning("No valid actual data after cleaning")
            return None
        
        # Prepare forecast data
        forecast_prep = forecast_df[['ds', 'yhat']].copy()
        forecast_prep['ds'] = pd.to_datetime(forecast_prep['ds'])
        forecast_prep = forecast_prep.dropna(subset=['yhat'])
        
        # Merge on date - only matching dates
        merged = pd.merge(
            actual_prep,
            forecast_prep,
            on='ds',
            how='inner'  # Only dates that appear in both
        )
        
        if len(merged) == 0:
            logger.warning("No overlapping dates between actual and forecast")
            return None
        
        logger.info(f"Calculating KPIs on {len(merged)} aligned data points")
        logger.debug(f"Sample: {merged.head()}")
        
        y_true = merged[value_col].values.astype(float)
        y_pred = merged['yhat'].values.astype(float)
        
        # Remove any negative predictions for realistic metrics
        mask = y_pred > 0
        if mask.sum() > 0:
            y_true = y_true[mask]
            y_pred = y_pred[mask]
        
        if len(y_true) < 2:
            logger.warning(f"Insufficient data for metrics: {len(y_true)} points")
            return None
        
        # Calculate MAPE safely
        mape = np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-6)).mean() * 100
        mape = min(mape, 500)  # Cap at 500% to avoid unrealistic values
        
        # Calculate other metrics
        mae = np.abs(y_true - y_pred).mean()
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        
        # Calculate R² safely
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        # Cap R² to realistic range (-1 to 1)
        r2 = max(-1, min(1, r2))
        
        # Calculate accuracy
        accuracy = max(0, min(100, 100 - mape))
        
        # Bias and forecast directions
        bias = np.mean(y_true - y_pred)
        under_forecast_rate = (y_true > y_pred).sum() / len(y_true) * 100
        over_forecast_rate = (y_true < y_pred).sum() / len(y_true) * 100
        
        metrics = {
            "mape": round(mape, 2),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4),
            "accuracy": round(accuracy, 2),
            "bias": round(bias, 2),
            "under_forecast_rate": round(under_forecast_rate, 2),
            "over_forecast_rate": round(over_forecast_rate, 2),
            "samples_analyzed": len(y_true)
        }
        
        logger.info(f"Advanced KPIs calculated: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating advanced KPIs: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_forecast_insights(forecast_df):
    """
    Extract key insights from Prophet forecast
    
    Args:
        forecast_df: Prophet forecast dataframe
        
    Returns:
        List of insight strings
    """
    insights = []
    
    try:
        # Volatility insight
        if 'yhat' in forecast_df.columns:
            forecast_std = forecast_df['yhat'].std()
            if forecast_std > forecast_df['yhat'].mean() * 0.3:
                insights.append("⚠️ High volatility expected - consider safety stock")
            else:
                insights.append("✅ Stable forecast - low volatility expected")
        
        # Trend insight
        if 'trend' in forecast_df.columns:
            trend_values = forecast_df['trend'].tail(30).values
            if len(trend_values) > 1:
                if trend_values[-1] > trend_values[0]:
                    insights.append("📈 Upward trend detected - demand increasing")
                elif trend_values[-1] < trend_values[0]:
                    insights.append("📉 Downward trend detected - demand decreasing")
                else:
                    insights.append("➡️ Stable trend - no major changes expected")
        
        # Seasonality insight
        if 'yearly' in forecast_df.columns or 'weekly' in forecast_df.columns:
            insights.append("🔄 Seasonal patterns detected in forecast")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return []
