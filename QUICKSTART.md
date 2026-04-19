# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd c:\Users\asus\Desktop\pfe-dashboard
pip install -r requirements.txt
```

### Step 2: Run the App
```bash
python app.py
```

### Step 3: Open in Browser
Navigate to: `http://127.0.0.1:5000`

---

## 📋 Basic Usage

### 1. Prepare Your Data Files

**Forecast File** (.xlsx):
```
Fournisseur | Réf. STC | Semaine 01 | Semaine 02 | ...
-----------+----------+----------+----------+
Supplier A | PROD001  | 100      | 150      | ...
Supplier B | PROD002  | 200      | 250      | ...
```

**Real Data File** (.xlsx):
```
Date       | Quantité | Article/Référence
----------+-----------+---------------
2024-01-01| 95        | PROD001
2024-01-02| 210       | PROD002
```

### 2. Upload Files
1. Click "Upload Forecast" and select your forecast file
2. Click "Upload Réel" and select your real data file
3. Click "Analyser" button

### 3. Generate KPIs
- Click "Générer KPI" to calculate metrics
- View results in the cards at the top:
  - 📈 **Fiabilité** - Forecast reliability percentage
  - 📊 **Écart** - Total difference (Real - Forecast)
  - ⚠️ **Erreur** - Error percentage

### 4. Analyze Charts
Four charts automatically appear:
- **Week Chart** - Forecast vs Real by week
- **Top 10 Products** - Best/worst performing products
- **Performance Heatmap** - Error % by week
- **Trend Chart** - Cumulative deviation over time

### 5. Filter Results
Use the filter section to:
- 📅 Select date range (start/end date)
- 🏷️ Filter by specific product
- Click "Appliquer" to update charts

---

## 🎯 Key Features

### File Management
| Action | Button | Result |
|--------|--------|--------|
| Upload & Process | "Analyser" | Files uploaded to server |
| Clear Files | Clear (in route) | Removes all files |
| Check System | `/health` endpoint | Folder size, file count |

### Analysis Metrics

**Fiabilité (Reliability)**
- 100% = Perfect forecast
- 0% = Completely wrong
- Formula: `100 - error_percentage`

**Écart (Difference)**
- Sum of (Real - Forecast) across all items
- Positive = Forecast underestimated
- Negative = Forecast overestimated

**Erreur (Error %)**
- Percentage error of forecast
- Formula: `(|Total Écart| / Total Forecast) × 100`

---

## 🔧 Configuration

Edit `.env` file for custom settings:

```env
# Server
DEBUG=False
HOST=127.0.0.1
PORT=5000

# Files
UPLOAD_FOLDER=uploads
MAX_UPLOAD_SIZE=52428800  # 50MB

# API
API_BASE_URL=http://127.0.0.1:5000
FRONTEND_URL=http://localhost:3000

# Environment
FLASK_ENV=development
```

---

## 📊 API Endpoints Quick Reference

```bash
# Upload files
POST /upload/forecast          # Upload forecast file
POST /upload/real              # Upload real data file

# Analysis
GET  /process                  # Calculate KPIs
GET  /chart-data?start_date=2024-01-01&end_date=2024-01-31&product=PROD001

# Management
POST /clear                    # Delete all files
GET  /health                   # Check system status
GET  /products                 # List all products

# Frontend
GET  /                         # Dashboard
```

**Example:**
```bash
curl "http://127.0.0.1:5000/chart-data?product=PROD001&start_date=2024-01-01"
```

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Upload forecast et real" error | Make sure both files are uploaded |
| "No matching data" error | Check column names in your files match requirements |
| File not uploading | Verify file size < 50MB and format is .xlsx/.xls/.csv |
| Charts not loading | Check browser console (F12) for errors, review API response |
| 404 on favicon | Harmless warning, can be ignored |

---

## 📝 File Requirements Checklist

### Forecast File
- [ ] File format: .xlsx, .xls, or .csv
- [ ] Contains "Fournisseur" column
- [ ] Contains "Réf. STC" column
- [ ] Contains "Semaine XX" columns (weeks)
- [ ] File size < 50MB

### Real Data File
- [ ] File format: .xlsx, .xls, or .csv
- [ ] Contains "Date" column
- [ ] Contains "Quantité" or "Qty" column
- [ ] Contains "Article" or "Référence" column
- [ ] File size < 50MB

---

## 🚀 Tips & Tricks

**Tip 1: Filter by Date**
```
Start: 2024-01-15 (what week does this fall in?)
Week 1 = Jan 1-7, Week 2 = Jan 8-14, Week 3 = Jan 15-21
```

**Tip 2: Compare Products**
1. Filter by product
2. Look at heatmap - identifies problem products
3. Check trend chart - see if recurring pattern

**Tip 3: Weekly Analysis**
- Top 10 products chart shows best sellers
- Heatmap shows consistency (red = inconsistent)
- Trend chart shows overall accuracy improving/declining

---

## 📞 Need Help?

1. **Check logs** - Application logs appear in terminal
2. **Read README.md** - Comprehensive documentation
3. **Review IMPROVEMENTS.md** - Recent changes and enhancements
4. **Browser console** - F12 → Console tab for JS errors

---

## 🎓 Next Steps

After basic usage:
1. Explore filtering with date ranges
2. Compare multiple products
3. Check the health endpoint: `http://127.0.0.1:5000/health`
4. Review trend patterns for forecasting improvements

---

**Happy analyzing! 📊**
