# Quick Start: Comprehensive PDF Report System

## 🚀 30-Second Setup

### 1. Install Backend Requirements (1 minute)
```bash
cd /Users/kishanbhumi/Downloads/healthcare-recovery-forecast
pip install -r requirements.txt
```

### 2. Start Backend Server (Terminal 1)
```bash
python api_server.py
```

You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

Access at: **http://localhost:9000**

---

## 📊 Generate Your First Report

1. **Navigate** to http://localhost:9000
2. **Login** with any Hospital ID and Password (mock auth)
3. **Click** "Analysis" in the sidebar
4. **Scroll down** and click **"📄 Download Comprehensive Report"**
5. **Wait** 2-5 seconds for PDF generation
6. **Open** the downloaded PDF in your default viewer

---

## 📄 What's in the Report?

### Page 1: Executive Summary
- Hospital header and vital statistics
- 4 key metrics in color-coded boxes
- Severity distribution donut chart

### Page 2: Bed Management
- 14-day bed occupancy forecast chart
- Table of upcoming bed availability
- Day-by-day predictions

### Page 3: Recovery Analytics
- Length of stay distribution histogram
- Feature importance analysis
- Median recovery time highlighted

### Page 4: Patient Data
- Table of 20 sample patients
- Severity levels, predicted LOS, discharge dates
- Print-optimized formatting

---

## 🎨 Design Features

✅ **Clinical Modernist Theme**
- Deep Navy (#1A2B3C) primary color
- Soft Teal (#20B2AA) accent color
- Severity color coding (Green→Red)

✅ **Professional Layout**
- 300 DPI print quality
- Print-optimized tables
- Embedded Matplotlib charts

✅ **Comprehensive Data**
- Charts rendered on backend (not screenshots)
- Real statistical distributions
- Mock data that mimics real scenarios

---

## 🛠️ Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# If needed, kill the process
kill -9 <PID>

# Or use different port
python api_server.py --port 8001
```

### PDF Download Fails
1. Check browser console: Press **F12 → Console**
2. Look for error messages
3. Verify backend is running: http://localhost:8000/health
4. Should return: `{"status": "healthy", ...}`

### Missing Dependencies
```bash
# Install missing packages
pip install fastapi uvicorn reportlab matplotlib seaborn Pillow

# Or reinstall everything
pip install -r requirements.txt --upgrade
```

---

## 📁 File Structure

```
Healthcare Recovery Forecast/
├── api_server.py ★ NEW - FastAPI backend
├── requirements.txt ✓ UPDATED - Added new packages
├── ml/
│   └── pdf_report_generator.py ★ NEW - PDF generation module
├── frontend/
│   ├── components/
│   │   └── Reports.tsx ✓ UPDATED - Calls backend API
│   ├── .env.local.template ★ NEW - Environment template
│   └── app/
└── PDF_REPORT_SETUP.md ★ NEW - Detailed setup guide
```

---

## 🔄 How It Works Architecture

```
1. User clicks "Download Report" button
   ↓
2. Frontend sends request to http://localhost:8000/api/reports/pdf
   ↓
3. Backend (Python) receives request
   ├─ Creates charts using Matplotlib
   ├─ Renders PDF layout using ReportLab
   └─ Returns PDF file as blob
   ↓
4. Browser saves PDF to Downloads folder
```

---

## 📚 Advanced Usage

### Custom Hospital Name
```javascript
// In the Analysis page
const reportData = {
  hospitalName: 'Your Hospital Name', // Change this
  reportDate: new Date().toISOString().split('T')[0],
  datasetStats: { ... }
}
```

### API Endpoint Direct Access
#### Generate PDF via curl:
```bash
curl -G http://localhost:8000/api/reports/pdf \
  --data-urlencode 'hospital_name=My Hospital'
```

#### Check backend health:
```bash
curl http://localhost:8000/health
```

#### Get dashboard data:
```bash
curl http://localhost:8000/api/dashboard
```

---

## 📞 Need Help?

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Connection refused" | Start backend: `python api_server.py` |
| "No module named fastapi" | Run: `pip install -r requirements.txt` |
| PDF button disabled | Check `.env.local` has correct API URL |
| Charts missing | Verify matplotlib installed: `pip list \| grep matplotlib` |
| Slow generation | Normal - takes 2-5 seconds on first run |

---

## ✨ Next Steps

- [ ] Test report generation 5+ times to ensure stability
- [ ] Customize the hospital name in your environment
- [ ] Share reports with team members
- [ ] Integrate real patient data
- [ ] Deploy to production when ready

---

## 📊 Creating Real Reports

To use with actual hospital data:

1. **Upload CSV** in Data Upload page
2. **Run predictions** on uploaded data
3. **Generate report** - it uses your actual data

Example CSV format:
```csv
Patient_ID,Age,Gender,Admission,Severity,Ward
P001,65,M,2026-03-29,3,ICU
P002,42,F,2026-03-29,2,General Ward
```

---

**Happy reporting! 🎉**

For detailed setup instructions, see: [PDF_REPORT_SETUP.md](./PDF_REPORT_SETUP.md)
