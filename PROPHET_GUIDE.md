# Prophet AI Integration & Advanced KPI Guide

## 🤖 What is Prophet?

**Facebook Prophet** is an advanced time series forecasting tool that:
- ✅ Detects seasonal patterns (weekly, yearly)
- ✅ Identifies trend changes
- ✅ Provides confidence intervals (95% by default)
- ✅ Handles gaps in data gracefully
- ✅ Works with relatively short time series (>10 data points)

---

## 📊 New Features

### 1. Prophet Demand Forecasting

**Purpose**: Predict future demand using historical data patterns

**How it works**:
1. Extracts historical Real (actual) sales data
2. Trains Prophet model to identify trends and seasonality
3. Forecasts future periods with confidence bounds
4. Evaluates forecast accuracy (MAPE, MAE, RMSE, R²)

**Access**: UI button "🚀 Prophet Forecast" after processing files

**Parameters**:
- **Product**: (optional) Forecast for specific product or all
- **Periods**: Number of days to forecast (default 30, range 7-90)

---

### 2. Advanced Analytics

**Purpose**: Deep dive analysis of forecast accuracy and performance

**Metrics included**:
- **Overall Accuracy**: % of time forecast matches reality
- **Best Products**: Top 5 most accurately forecasted items
- **Worst Products**: Bottom 5 with accuracy issues (anomalies)
- **Volatile Products**: Items with unpredictable demand
- **Recommendations**: AI-generated suggestions for improvement

**Access**: UI button "📊 Analytics"

---

## 📈 Enhanced KPI Metrics

### Traditional KPIs (Unchanged)
```
Fiabilité (Reliability)    = 100 - Error%
Écart (Deviation)          = Sum(Real - Forecast)
Erreur (Error %)           = |Écart| / Forecast × 100
```

### New AI KPIs (Prophet Forecast Tab)

| Metric | Range | Meaning |
|--------|-------|---------|
| **R²** | 0-1 | Model fit quality (1 = perfect) |
| **MAPE** | 0-100% | Mean Absolute % Error |
| **MAE** | ≥ 0 | Mean Absolute Error (units) |
| **RMSE** | ≥ 0 | Root Mean Squared Error |
| **Accuracy** | 0-100% | Forecast reliability score |

### Advanced Analytics Metrics

| Metric | Purpose |
|--------|---------|
| **Bias** | Systematic over/under forecasting |
| **Under-forecast Rate** | % times forecast < actual |
| **Over-forecast Rate** | % times forecast > actual |
| **Samples Analyzed** | Data points used for evaluation |

---

## 🔮 Prophet Forecast Endpoints

### `GET /forecast/prophet`

**Parameters**:
```
?product=PROD001&periods=30
```

**Response**:
```json
{
    "forecast": [
        {
            "ds": "2024-04-15",
            "yhat": 150.5,
            "yhat_upper": 175.2,
            "yhat_lower": 125.8
        }
    ],
    "trend": {
        "trend_direction": "increasing",
        "trend_strength": 0.25,
        "forecast_mean": 150.0,
        "forecast_std": 12.5,
        "upper_bound": 200.0,
        "lower_bound": 100.0
    },
    "metrics": {
        "mape": 12.5,
        "mae": 15.2,
        "rmse": 18.7,
        "r2": 0.87,
        "accuracy": 87.5
    },
    "insights": [
        "✅ Stable forecast - low volatility expected",
        "📈 Upward trend detected - demand increasing",
        "🔄 Seasonal patterns detected in forecast"
    ],
    "periods": 30,
    "product": "All Products",
    "data_points_used": 52
}
```

---

### `GET /analytics/advanced`

**Response**:
```json
{
    "overall_accuracy": 82.5,
    "total_products": 12,
    "products_with_good_accuracy": 10,
    "products_with_poor_accuracy": 2,
    "best_performing_products": [
        {
            "product": "PROD001",
            "forecast_total": 1200,
            "real_total": 1215,
            "accuracy": 98.75,
            "ecart": 15,
            "ecart_pct": 1.25
        }
    ],
    "worst_performing_products": [
        {
            "product": "PROD012",
            "accuracy": 45.2,
            "ecart": 450
        }
    ],
    "most_volatile_products": [
        {
            "product": "PROD005",
            "real_std": 25.3,
            "consistency": 0.62
        }
    ],
    "recommendations": [
        {
            "type": "success",
            "message": "✅ Forecast accuracy is good"
        },
        {
            "type": "info",
            "message": "Products with high volatility detected"
        }
    ]
}
```

---

## 💡 How to Use Prophet

### Step 1: Upload & Process Files
1. Upload forecast and real data files
2. Click "Analyser" to upload
3. Click "Générer KPI" to process

### Step 2: View Base Metrics
- Check Fiabilité, Écart, Erreur in KPI cards

### Step 3: Run Prophet Forecast
1. (Optional) Select specific product or keep "Tous"
2. (Optional) Adjust forecast periods (default 30)
3. Click "🚀 Prophet Forecast"
4. Wait for computation (a few seconds)
5. View:
   - 💡 AI Insights (trend, volatility, seasonality)
   - 📊 Forecast Metrics (R², MAPE, etc.)
   - 🔮 Chart with confidence bounds

### Step 4: Advanced Analytics
1. Click "📊 Analytics"
2. Review:
   - Product accuracy rankings
   - Volatile products list
   - AI-generated recommendations

---

## 🎯 Interpreting Results

### Trend Direction
- **📈 Increasing**: Demand is growing - increase inventory
- **📉 Decreasing**: Demand is falling - reduce stock
- **➡️ Stable**: Steady demand - maintain current levels

### Volatility Indicators
- **Low Volatility** ✅ → Predictable demand, standard safety stock
- **High Volatility** ⚠️ → Unpredictable demand, increase safety stock

### Accuracy Interpretation
| Accuracy | Rating | Action |
|----------|--------|--------|
| 90%+ | Excellent ⭐⭐⭐⭐⭐ | Keep current method |
| 80-90% | Good ⭐⭐⭐⭐ | Minor adjustments |
| 70-80% | Fair ⭐⭐⭐ | Review methodology |
| 60-70% | Poor ⭐⭐ | Major adjustments needed |
| <60% | Very Poor ⭐ | Complete overhaul needed |

### Bias Detection
- **Positive Bias** (+): Systematically under-forecasting
  - Action: Increase forecast values
  
- **Negative Bias** (-): Systematically over-forecasting
  - Action: Decrease forecast values

---

## 🔧 Technical Details

### Prophet Model Configuration

```python
model = Prophet(
    yearly_seasonality=True,      # Detect yearly patterns
    weekly_seasonality=True,       # Detect weekly patterns
    daily_seasonality=False,       # No daily patterns
    interval_width=0.95,          # 95% confidence interval
    changepoint_prior_scale=0.05, # Sensitivity to trend changes
    seasonality_prior_scale=10    # Strength of seasonal effect
)
```

### Minimum Data Requirements
- **Minimum**: 10 data points
- **Recommended**: 50+ data points for reliable seasonality detection
- **Optimal**: 100+ data points for full pattern recognition

### Computation Time
- Small dataset (10-50 points): < 1 second
- Medium dataset (50-200 points): 1-3 seconds
- Large dataset (200+ points): 3-10 seconds

---

## 📋 Evaluation Metrics Explained

### MAPE (Mean Absolute Percentage Error)
```
MAPE = Mean(|Actual - Forecast| / |Actual|) × 100
```
- **Lower is better** (0% = perfect)
- Measures percentage error
- Good for comparing across different scales

### MAE (Mean Absolute Error)
```
MAE = Mean(|Actual - Forecast|)
```
- **Lower is better**
- Same units as your data (e.g., units, kg)
- Easy to interpret

### RMSE (Root Mean Squared Error)
```
RMSE = √(Mean((Actual - Forecast)²))
```
- **Lower is better**
- Penalizes large errors more heavily
- More sensitive to outliers

### R² (Coefficient of Determination)
```
R² = 1 - (SS_res / SS_tot)
```
- Range: 0 to 1 (can be negative if model is worse than average)
- **Higher is better** (1 = perfect fit)
- Proportion of variance explained by model

---

## ⚠️ Limitations & Best Practices

### Limitations
- Works best with stationary data (no major permanent shifts)
- Needs at least 2 complete cycles for seasonality detection
- May overfit with very limited data
- Not suitable for extreme anomalies without preprocessing

### Best Practices
1. **Data Quality**: Ensure accurate input data
2. **Regular Updates**: Retrain model with new data periodically
3. **Product-Level**: Forecast by product for better accuracy
4. **Monitor Performance**: Track actual vs forecast weekly
5. **Adjust Parameters**: If accuracy is low, review configurations

---

## 🚀 Advanced Usage

### Segment Forecasting
Use the product filter to forecast individual products:
1. Select specific product in dropdown
2. Run Prophet Forecast
3. Compare accuracy across products
4. Identify which products need strategy adjustment

### Trend Analysis
Monitor trend direction over time:
- Track weekly trends to spot seasonal patterns
- Use trend insights for inventory planning
- Adjust safety stock based on volatility

### Confidence Intervals
The 95% confidence bounds show:
- **Upper Bound**: Optimistic scenario (95% confident actual ≤ this)
- **Point Forecast**: Best estimate
- **Lower Bound**: Pessimistic scenario (95% confident actual ≥ this)

Use bounds for:
- Safety stock dimensioning
- Reserve capacity planning
- Risk assessment

---

## 📞 Troubleshooting

### "Insufficient data for forecasting"
**Solution**: Ensure you have at least 10 data points (preferably 50+)

### Forecast looks too smooth/unrealistic
**Solution**: 
- May have limited data
- Try product-level forecasting instead of all combined
- Prophet works better with seasonal products

### Accuracy is low (< 60%)
**Solutions**:
1. Check data quality and outliers
2. Forecast by product instead of aggregate
3. Try different forecast periods
4. Review for permanent demand shifts

### "No processed data available"
**Solution**: Upload files and click "Générer KPI" first

---

## 📚 Further Reading

- [Facebook Prophet Documentation](https://facebook.github.io/prophet/)
- [Time Series Forecasting Best Practices](https://www.forecast.app)
- [Seasonality & Trend Analysis](https://otexts.com/fpp2/)

---

**Status**: ✅ Prophet AI integration complete and ready for use
