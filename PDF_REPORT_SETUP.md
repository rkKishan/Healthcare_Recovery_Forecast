# Healthcare Recovery Forecast - PDF Report System Setup

## Overview

The system now includes a comprehensive multi-page PDF report generator that creates professional reports with embedded charts using ReportLab and Matplotlib on the backend.

## Architecture

```
Frontend (Next.js)
    ↓
API Request to /api/reports/pdf
    ↓
FastAPI Backend (Port 8000)
    ↓
PDF Report Generator (Python)
    ├─ ReportLab (PDF layout)
    ├─ Matplotlib (charts)
    └─ Generates 4-page professional report
    ↓
PDF File → Download
```

## Setup Instructions

### 1. Install Backend Dependencies

```bash
cd /Users/kishanbhumi/Downloads/healthcare-recovery-forecast
pip install -r requirements.txt
```

**Key packages added:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload support
- `reportlab` - PDF generation (already present)
- `matplotlib` - Chart rendering
- `seaborn` - Enhanced visualizations
- `Pillow` - Image processing

### 2. Start the Backend Server

```bash
python api_server.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

The server will:
- Run on `http://localhost:8000`
- Accept requests from the frontend (port 9000)
- Generate PDFs on demand
- Serve as central API hub

### 3. Frontend Configuration

The frontend is already configured to call the backend. Verify in `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

If not present, create `.env.local` in the `frontend` directory:

```bash
cd frontend
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
```

### 4. Run Both Services

**Terminal 1 - Backend:**
```bash
cd /Users/kishanbhumi/Downloads/healthcare-recovery-forecast
python api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/kishanbhumi/Downloads/healthcare-recovery-forecast/frontend
npm run dev
```

Then access the application at: **http://localhost:9000**

## Report Structure

### Page 1: Executive Summary & Overview
- **Hospital Logo & Title**: "PredictMed Healthcare Recovery Forecast"
- **Vital Signs Section**: 
  - Total Patients: 464
  - Average Length of Stay: 6.2 days
  - Critical Cases: 24
  - Bed Utilization: 78%
- **Visual 1**: Severity Distribution (Donut Chart)
  - Deep Navy and Soft Teal color scheme
  - Breakdown of Level 1-5 severity categories

### Page 2: Hospital Resource Insights (Bed Management)
- **Visual 2**: 14-Day Bed Occupancy Forecast
  - Bar chart showing predicted net gain/loss of available beds
  - Bars color-coded (Teal for gains, Navy for losses)
- **Data Table**: "Beds Opening Soon"
  - Date | Ward | Available Beds | Expected Patients
  - Sorted chronologically
  - 5 upcoming bed availability records

### Page 3: Recovery Analytics
- **Visual 3**: Length of Stay Distribution
  - Histogram showing LOS across all patients
  - Median line highlighted
  - Severity-based clustering visible
- **Feature Importance Chart**:
  - Horizontal bar chart
  - Top 5 factors: Age, Severity Level, Comorbidities, Vital Signs, Lab Results
  - Shows relative importance percentages

### Page 4: Detailed Patient Data
- **Structured Table**: First 20 patient records
- **Columns**: 
  - Patient ID (e.g., P001)
  - Severity Level (Level 1-5)
  - Predicted Stay (Days)
  - Estimated Discharge Date
- **Print-optimized** formatting with alternating row colors

## Design Theme

All charts use the Clinical Modernist theme:
- **Primary Color**: Deep Navy (#1A2B3C)
- **Accent Color**: Soft Teal (#20B2AA)
- **Severity Levels**: 
  - Level 1: Green (#2ca02c)
  - Level 2: Yellow (#90ee90)
  - Level 3: Gold (#ffd700)
  - Level 4: Orange (#ff8c00)
  - Level 5: Red (#dc143c)

## API Endpoints

### Generate Comprehensive PDF Report
```
GET /api/reports/pdf?hospital_name=Central%20Medical%20Center
```

**Response**: Binary PDF file
**Content-Type**: application/pdf
**Filename**: Recovery_Forecast_Report_YYYYMMDD.pdf

### Other Available Endpoints

```
POST /api/auth/login
POST /api/auth/logout
POST /api/upload
POST /api/predict/batch
POST /api/predict/single
GET /api/predict/explain/{patient_id}
GET /api/dashboard
POST /api/reports/patient
GET /health
```

## Troubleshooting

### Issue: "Failed to generate PDF: Connection refused"
**Solution**: Make sure backend server is running
```bash
python api_server.py
```

### Issue: "ModuleNotFoundError: No module named 'reportlab'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: PDF generated but download doesn't start
**Solution**: 
1. Check browser console for errors (F12)
2. Verify CORS is properly configured (should allow port 9000)
3. Check backend logs for generation errors

### Issue: Charts look wrong or are missing
**Solution**: 
1. Ensure matplotlib and seaborn are installed
2. Check matplotlib backend is set to 'Agg' for server environments

## Performance Notes

- PDF generation typically takes 2-5 seconds
- Temporary files are created in the system temp directory
- Large datasets may increase generation time
- Charts are rendered at 300 DPI for print quality

## File Locations

```
/app/
    └── api_server.py (FastAPI backend - NEW)

/ml/
    ├── pdf_report_generator.py (PDF generation module - NEW)
    ├── predictor.py
    ├── train.py
    ├── visualizer.py
    └── data_generator.py

/frontend/
    ├── components/
    │   └── Reports.tsx (Updated to use backend API)
    ├── .env.local (Create with API_BASE_URL)
    └── app/
        └── analysis.tsx (PDF button component)

requirements.txt (Updated with new packages)
```

## Next Steps

1. **Backend Integration**: Connect to actual ML models for real predictions
2. **Database**: Integrate with hospital data sources
3. **Authentication**: Implement JWT-based authentication
4. **Caching**: Add Redis caching for repeated PDF requests
5. **Scheduling**: Add scheduled report generation
6. **Customization**: Allow hospital-specific branding and colors

## Production Deployment

### Docker
```bash
# Build containers
docker-compose build

# Run
docker-compose up
```

### Manual Deployment
1. Install dependencies: `pip install -r requirements.txt`
2. Run backend on production server: `uvicorn api_server:app --host 0.0.0.0 --port 8000`
3. Deploy frontend to hosting service (Vercel, Netlify, etc.)
4. Update `NEXT_PUBLIC_API_BASE_URL` to production backend URL

## Support

For issues or questions:
1. Check browser console for frontend errors
2. Check backend logs for server errors
3. Verify both services are running on correct ports
4. Ensure network connectivity between frontend and backend
