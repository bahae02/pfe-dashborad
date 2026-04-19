# PFE Dashboard - Forecast vs Reality Analysis

A Flask-based dashboard for comparing forecast data against real-world outcomes with **AI-powered Prophet forecasting**, KPI analysis and visualization.

## ✨ Key Features

- 📤 **File Upload** - Support for Excel (.xlsx, .xls, .csv) files
- 📊 **Multi-dimensional Analysis** - Forecast vs Real by week, product, and trends
- 🎯 **KPI Metrics** - Reliability %, Error %, and Ecart calculation
- 📈 **Interactive Charts** - Week comparison, top products, heatmap, trend analysis
- 🔍 **Filtering** - Filter by date range and product
- **🤖 AI Forecasting** - Facebook Prophet time series forecasting with confidence intervals
- **📊 Advanced Analytics** - Product accuracy analysis, anomaly detection, volatility assessment
- 🛡️ **Input Validation** - File type, size, and data structure validation
- 📝 **Logging** - Comprehensive logging for debugging and monitoring
- 💾 **Auto Cleanup** - Automatic cleanup of old uploaded files

## Installation

### 1. Clone/Setup Project
```bash
cd c:\Users\asus\Desktop\pfe-dashboard
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env` and adjust as needed:
```bash
cp .env.example .env
```

### 5. Run Application
```bash
python app.py
```

Access the dashboard at `http://127.0.0.1:5000`

## Configuration

Edit `.env` file to customize:
- `DEBUG` - Enable/disable debug mode
- `HOST` - Server host
- `PORT` - Server port (default 5000)
- `MAX_UPLOAD_SIZE` - Maximum file upload size in bytes
- `API_BASE_URL` - API endpoint URL
- `FLASK_ENV` - Environment (development/production)

## API Endpoints

### Upload Files
- **POST** `/upload/forecast` - Upload forecast Excel file
- **POST** `/upload/real` - Upload actual/real data Excel file
- **POST** `/clear` - Clear all uploaded files

### Analysis
- **GET** `/process` - Process uploaded files and calculate KPIs
- **GET** `/chart-data` - Get filtered chart data
  - Query params: `start_date`, `end_date`, `product`
- **GET** `/products` - Get list of all products

### 🤖 AI Prophet Forecasting
- **GET** `/forecast/prophet` - Generate AI demand forecast
  - Query params: `product` (optional), `periods` (7-90, default 30)
  - Returns: Forecast values, trend analysis, metrics (MAPE, MAE, RMSE, R²)

### 📊 Advanced Analytics
- **GET** `/analytics/advanced` - Deep dive analysis
  - Returns: Product accuracy ranking, anomalies, volatility assessment, recommendations

### System
- **GET** `/health` - System health check

### Frontend
- **GET** `/` - Dashboard HTML

## Advanced Features

### 🤖 Prophet AI Forecasting

Integrated with Facebook Prophet for intelligent demand forecasting:
- Automatically detects seasonal patterns and trends
- Generates 1-90 day forecasts with 95% confidence intervals
- Evaluates forecast accuracy (MAPE, MAE, RMSE, R²)
- Works at product level or aggregate level
- Provides AI-driven insights and recommendations

**Usage**:
1. Upload and process your files
2. Click "🚀 Prophet Forecast" button
3. (Optional) Select specific product and forecast periods
4. View forecast with:
   - 🔮 Chart with confidence bounds
   - 💡 Automatic insights (trend, seasonality, volatility)
   - 📊 Accuracy metrics

### 📊 Advanced Analytics

Comprehensive analysis of forecast performance:
- **Product Rankings** - Identify best/worst performing products
- **Anomaly Detection** - Flag products with accuracy issues
- **Volatility Analysis** - Identify unpredictable demand items
- **AI Recommendations** - Actionable suggestions for improvement
- **Bias Analysis** - Detect systematic over/under-forecasting

**Usage**:
1. After processing files, click "📊 Analytics"
2. Review accuracy rankings and insights
3. Follow recommendations to improve forecasts

### Enhanced KPI Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| **Fiabilité (Reliability)** | Basic | Forecast reliability percentage |
| **Écart (Deviation)** | Basic | Total difference vs forecast |
| **Erreur (Error %)** | Basic | Percentage error rate |
| **R²** | AI | Model fit quality (0-1) |
| **MAPE** | AI | Mean Absolute % Error |
| **MAE** | AI | Mean Absolute Error (units) |
| **RMSE** | AI | Root Mean Squared Error |
| **Accuracy** | AI | Forecast reliability score |
| **Bias** | Advanced | Systematic over/under-forecasting |
| **Volatility** | Advanced | Demand unpredictability measure |

---
Required columns:
- `Fournisseur` (Supplier)
- `Réf. STC` (Reference/Product ID)
- `Semaine XX` (Weekly columns)

### Real Data File
Required columns:
- `Date` - Transaction date
- `Quantité` or `Qty` - Quantity
- `Article` or `Référence` - Product reference

## Anomalies Fixed

### Code Quality
✅ All `print()` statements replaced with proper logging  
✅ Added HTTP status codes to all error responses  
✅ File size validation (max 50MB per file)  
✅ Input data structure validation  
✅ Added python-dotenv to dependencies  

### New Enhancements
✅ Auto cleanup of old files (24h threshold)  
✅ Folder size monitoring  
✅ Health check endpoint  
✅ Better error messages with structured JSON responses  
✅ Debug vs Info logging levels  
✅ Utility functions for common tasks  

## Project Structure

```
pfe-dashboard/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git exclusions
├── .instructions.md       # Development instructions (optional)
├── templates/
│   └── index.html        # Dashboard frontend
└── uploads/              # Uploaded files directory
    └── .gitkeep
```

## Logging

Logs include:
- INFO - General application flow
- WARNING - Potential issues
- ERROR - Error conditions
- DEBUG - Detailed debugging info

Check console output or configure file logging in `app.py`:
```python
# Add file handler for persistent logs
file_handler = logging.FileHandler('app.log')
logger.addHandler(file_handler)
```

## Performance Considerations

- **Memory**: Dataframes are loaded entirely in-memory. For large files (>100MB), consider chunking
- **Storage**: Files are kept in `uploads/` folder. Configure auto-cleanup interval in `/health` endpoint
- **Concurrency**: Flask development server is single-threaded. Use Gunicorn for production:
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 127.0.0.1:5000 app:app
  ```

## Future Enhancements

- [ ] Database persistence (SQLite/PostgreSQL)
- [ ] User authentication & multi-tenant support
- [ ] Real-time forecasting updates
- [ ] Email alerts for accuracy thresholds
- [ ] Historical forecast comparison
- [ ] Ensemble forecasting (Prophet + ML models)
- [ ] Export to PDF/Excel reports with insights
- [ ] API rate limiting & caching
- [ ] Forecast model A/B testing
- [ ] Integration with ERP/WMS systems

## Troubleshooting

**Issue**: "Module 'config' not found"
- Ensure you're running from the project directory
- Check that `config.py` exists

**Issue**: Files not uploading
- Check file size (max 50MB)
- Verify file type is .xlsx, .xls, or .csv
- Check `uploads/` folder permissions

**Issue**: "No matching data" error
- Verify column names match requirements
- Check data format and dates
- Review logs for details

## License

Internal use only

## Support

For issues or questions, check the application logs and ensure:
1. Dependencies are properly installed
2. Configuration is correct
3. File formats match requirements
