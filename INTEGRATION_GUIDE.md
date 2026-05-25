# Frontend-Backend Integration Guide

## Overview

This guide explains how to connect the Next.js frontend with the existing Python ML backend.

## Architecture

```
┌─────────────────┐                  ┌──────────────────┐
│  Next.js        │  HTTP/REST       │   FastAPI/       │
│  Frontend       │◄────────────────►│   Flask Backend  │
│  (Port 3000)    │                  │   (Port 8000)    │
└─────────────────┘                  └──────────────────┘
```

## Backend Setup (Python)

### 1. Create FastAPI Server

Add to your `backend.py` or create new `api_server.py`:

```python
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import json
from ml.train import RecoveryModelTrainer
from ml.predictor import RecoveryPredictor

app = FastAPI(title="Healthcare Recovery Forecast API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models globally
models = None
predictor = None

@app.on_event("startup")
async def startup_event():
    global models, predictor
    try:
        trainer = RecoveryModelTrainer()
        models = trainer.load_models()
        predictor = RecoveryPredictor(models)
    except Exception as e:
        print(f"Warning: Could not load models: {e}")

# ==================== Auth Endpoints ====================

@app.post("/api/auth/login")
async def login(data: dict):
    """Mock authentication endpoint"""
    hospital_id = data.get("hospitalId")
    password = data.get("password")
    
    if hospital_id and password:
        return {
            "success": True,
            "token": f"token_{hospital_id}",
            "user": {
                "id": "1",
                "hospitalId": hospital_id,
                "name": "Dr. Sarah Johnson",
                "role": "admin"
            }
        }
    return {"success": False, "error": "Invalid credentials"}

# ==================== Upload Endpoints ====================

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...), hospital_id: str = ""):
    """Upload and process patient dataset"""
    try:
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        
        # Validate required columns
        required_cols = ['Patient_ID', 'Age', 'Gender', 'Severity', 'Ward']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return {
                "success": False,
                "error": f"Missing columns: {missing_cols}"
            }
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "preview": df.head().to_dict(orient='records'),
            "stats": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== Prediction Endpoints ====================

@app.post("/api/predict/batch")
async def predict_batch(data: dict):
    """Batch predict for multiple patients"""
    try:
        patients = data.get("patients", [])
        
        if not predictor:
            return {"success": False, "error": "Models not loaded"}
        
        predictions = predictor.predict_batch([
            {k: v for k, v in p.items() if k in predictor.required_features}
            for p in patients
        ])
        
        return {
            "success": True,
            "predictions": predictions.to_dict(orient='records')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/predict/single")
async def predict_single(patient_data: dict):
    """Predict for single patient"""
    try:
        if not predictor:
            return {"success": False, "error": "Models not loaded"}
        
        result = predictor.predict_single_patient(patient_data)
        
        return {
            "success": True,
            "prediction": {
                "predicted_los": result["predicted_los"],
                "confidence_interval": {
                    "lower": result["confidence_interval"][0],
                    "upper": result["confidence_interval"][1]
                },
                "severity": result["severity_level"],
                "discharge_date": result["discharge_date"].isoformat()
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/predict/explain/{patient_id}")
async def explain_prediction(patient_id: str):
    """Get SHAP explanation for patient prediction"""
    try:
        if not predictor:
            return {"success": False, "error": "Models not loaded"}
        
        explanation = predictor.explain_prediction({"patient_id": patient_id})
        
        return {
            "success": True,
            "explanation": {
                "features": explanation["features"],
                "shap_values": explanation["shap_values"].tolist()
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== Dashboard Endpoints ====================

@app.get("/api/dashboard/bed-occupancy")
async def get_bed_occupancy():
    """Get 14-day bed occupancy forecast"""
    return {
        "success": True,
        "data": [
            {
                "day": i + 1,
                "current": 45 + (i % 10),
                "predicted": 48 + (i % 8),
                "available": 100 - (45 + (i % 10))
            }
            for i in range(14)
        ]
    }

@app.get("/api/dashboard/severity")
async def get_severity_distribution():
    """Get severity level distribution"""
    return {
        "success": True,
        "data": {
            "1": 180,
            "2": 245,
            "3": 312,
            "4": 189,
            "5": 74
        }
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get aggregate dashboard statistics"""
    return {
        "success": True,
        "stats": {
            "total_admitted": 847,
            "avg_los": 6.2,
            "critical_cases": 124,
            "bed_utilization": 78,
            "recovery_rate": 94.2
        }
    }

# ==================== Reports Endpoints ====================

@app.post("/api/reports/generate")
async def generate_report(data: dict):
    """Generate PDF report"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        
        # Add content
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "Healthcare Recovery Forecast Report")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Hospital: {data.get('hospitalName', 'Central Medical')}")
        c.drawString(50, 700, f"Date: {data.get('reportDate', '')}")
        
        c.showPage()
        c.save()
        
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer,
            media_type="application/pdf",
            filename=f"report_{data.get('reportDate')}.pdf"
        )
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "models_loaded": predictor is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Install FastAPI

```bash
pip install fastapi uvicorn python-multipart reportlab
```

### 3. Run Backend

```bash
python api_server.py
# or
uvicorn api_server:app --reload --port 8000
```

## Frontend Configuration

### 1. Set Environment Variables

Create `.env.local` in `/frontend`:

```env
# Use the backend URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Healthcare Recovery Forecast
```

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:3000
```

## API Endpoints Reference

### Authentication
```
POST /api/auth/login
Body: { hospitalId: string, password: string }
Response: { success: bool, token: string, user: User }
```

### Data Upload
```
POST /api/upload (multipart/form-data)
Fields: file, hospital_id
Response: { success: bool, preview: [], stats: {} }
```

### Predictions
```
POST /api/predict/batch
Body: { patients: [PatientData] }
Response: { success: bool, predictions: [] }

POST /api/predict/single
Body: PatientData
Response: { success: bool, prediction: PredictionResult }

GET /api/predict/explain/{patient_id}
Response: { success: bool, explanation: {} }
```

### Dashboard
```
GET /api/dashboard/bed-occupancy
Response: { success: bool, data: [] }

GET /api/dashboard/severity
Response: { success: bool, data: {} }

GET /api/dashboard/stats
Response: { success: bool, stats: {} }
```

### Reports
```
POST /api/reports/generate
Body: { hospitalName: string, reportDate: string, ... }
Response: Binary PDF file
```

## CORS Configuration

If frontend and backend are on different domains, ensure CORS is configured:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Data Format Expectations

### Patient Record (CSV Upload)
```csv
Patient_ID,Age,Gender,Admission_Date,Severity,Ward,SBP,DBP,HR,RR,Temp,WBC,Hgb,Glucose,Creatinine,Platelets,Comorbidities
P001,65,M,2026-03-29,3,ICU,140,90,85,18,37.2,8.5,12.0,120,1.2,250,HTN|Diabetes
```

### Prediction Request (JSON)
```json
{
  "patient_id": "P001",
  "age": 65,
  "gender": "M",
  "severity": 3,
  "vital_signs": {
    "sbp": 140,
    "dbp": 90,
    "hr": 85,
    "rr": 18,
    "temp": 37.2
  },
  "lab_values": {
    "wbc": 8.5,
    "hemoglobin": 12.0,
    "glucose": 120,
    "creatinine": 1.2,
    "platelets": 250
  }
}
```

### Prediction Response
```json
{
  "patient_id": "P001",
  "predicted_los": 7,
  "confidence_interval": [5, 9],
  "severity_level": 3,
  "discharge_date": "2026-04-05",
  "confidence_score": 0.92,
  "key_factors": ["Age 65+", "HTN", "Abnormal vitals"]
}
```

## Running Both Together

### Option 1: Two Terminal Windows

Terminal 1 (Backend):
```bash
cd ~
python api_server.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

### Option 2: Docker Compose

Create `docker-compose.yml` in root:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./ml:/app/ml

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
```

Run:
```bash
docker-compose up
```

Visit:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs

## Testing the Connection

### Test Backend Health
```bash
curl http://localhost:8000/api/health
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"hospitalId":"demo","password":"demo"}'
```

### Test Prediction
```bash
curl -X POST http://localhost:8000/api/predict/single \
  -H "Content-Type: application/json" \
  -d '{"age":65,"severity":3,"vital_signs":{"sbp":140}}'
```

## Next Steps

1. ✅ Backend API service running
2. ✅ Frontend connected to backend
3. **Integrate real ML models** - Replace mock predictions
4. **Setup authentication** - Implement JWT tokens
5. **Add data validation** - Comprehensive input checking
6. **Deploy to production** - Configure for handling live data
7. **Setup monitoring** - Track API performance
8. **Create admin dashboard** - For system monitoring

## Troubleshooting

### "Cannot reach backend" error
- Verify backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- Ensure no CORS issues
- Check firewall settings

### API methods returning 500 errors
- Check backend console for errors
- Verify data format matches expectations
- Ensure ML models are loaded
- Check file paths for model artifacts

### PDF generation fails
- Verify `html2canvas` and `jspdf` are installed
- Check browser console for canvas errors
- Ensure reportlab is installed on backend

### Authentication not working
- Verify login endpoint returns correct token format
- Check token is being stored in localStorage
- Verify API interceptor is adding token to requests

## Production Deployment

### Environment Variables
```env
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NODE_ENV=production
```

### Backend (Docker)
```bash
docker build -t hrf-backend .
docker run -p 8000:8000 \
  -e DB_URL=your_db_url \
  -e ENVIRONMENT=production \
  hrf-backend
```

### Frontend (Vercel)
```bash
vercel deploy --prod
```

Or with Docker:
```bash
docker build -f frontend/Dockerfile -t hrf-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com \
  hrf-frontend
```
