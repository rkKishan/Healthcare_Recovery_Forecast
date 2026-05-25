"""
FastAPI Backend for Healthcare Recovery Forecast
Serves API endpoints including PDF report generation with database integration
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
from pathlib import Path
import tempfile
from datetime import datetime, timedelta
import json
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add ml module to path
ml_path = os.path.join(os.path.dirname(__file__), 'ml')
sys.path.insert(0, ml_path)

# Database and Auth imports
from database import User, PatientData, Analysis, SessionLocal, create_tables, get_db
from auth import create_access_token, verify_password, hash_password, get_current_user
from pdf_report_generator import generate_pdf_report

# Create database tables on startup
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Recovery Forecast API",
    description="API for healthcare recovery predictions and reporting",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:9000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class LoginRequest(BaseModel):
    hospital_id: str
    password: str


class RegisterRequest(BaseModel):
    hospital_id: str
    email: str
    full_name: str
    hospital_name: str
    password: str
    role: str = "doctor"  # admin, doctor, analyst


class UserResponse(BaseModel):
    id: int
    hospital_id: str
    email: str
    full_name: str
    role: str
    hospital_name: str


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/register")
async def register(request: RegisterRequest, db = Depends(get_db)):
    """Register new hospital user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.hospital_id == request.hospital_id) | 
        (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital ID or email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(request.password)
    new_user = User(
        hospital_id=request.hospital_id,
        email=request.email,
        full_name=request.full_name,
        hospital_name=request.hospital_name,
        hashed_password=hashed_password,
        role=request.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": new_user.hospital_id, "user_id": new_user.id}
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "hospital_id": new_user.hospital_id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "hospital_name": new_user.hospital_name
        }
    }


@app.post("/api/auth/login")
async def login(request: LoginRequest, db = Depends(get_db)):
    """Authenticate user and return access token"""
    # Find user by hospital_id
    user = db.query(User).filter(User.hospital_id == request.hospital_id).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid hospital ID or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.hospital_id, "user_id": user.id}
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "hospital_id": user.hospital_id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "hospital_name": user.hospital_name
        }
    }


@app.post("/api/auth/logout")
async def logout():
    """Logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}


# ==================== Upload Endpoints ====================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    """Handle file uploads and save patient data to database"""
    try:
        contents = await file.read()
        file_hash = hashlib.md5(contents).hexdigest()
        
        # Check for duplicate uploads
        existing = db.query(PatientData).filter(PatientData.file_hash == file_hash).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This file has already been uploaded"
            )
        
        # Parse CSV/JSON data (simplified)
        user_id = current_user.get("user_id")
        
        # Save patient data record
        patient_data = PatientData(
            user_id=user_id,
            patient_id=f"PAT_{datetime.utcnow().timestamp()}",
            patient_name="Patient",
            file_name=file.filename,
            file_hash=file_hash,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(patient_data)
        db.commit()
        db.refresh(patient_data)
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(contents),
            "patient_data_id": patient_data.id,
            "message": "File uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Prediction Endpoints ====================

@app.post("/api/predict/batch")
async def batch_predict(data: dict):
    """Batch prediction endpoint"""
    try:
        patients = data.get("patients", [])
        
        # Mock predictions
        predictions = []
        for patient in patients:
            predictions.append({
                "patientId": patient.get("id"),
                "predictedLOS": 7,
                "confidence": 0.92,
                "severity": patient.get("severity", 3),
                "factors": ["Age", "Comorbidity", "Vital Signs"]
            })
        
        return {
            "success": True,
            "predictions": predictions,
            "totalProcessed": len(patients)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/predict/single")
async def single_predict(patient_data: dict):
    """Single patient prediction"""
    return {
        "success": True,
        "prediction": {
            "patientId": patient_data.get("id"),
            "predictedLOS": 7,
            "confidence": 0.92,
            "severity": patient_data.get("severity", 3),
            "factors": ["Age", "Comorbidity", "Vital Signs"]
        }
    }


@app.get("/api/predict/explain/{patient_id}")
async def explain_prediction(patient_id: str):
    """Get prediction explanation for a patient"""
    return {
        "success": True,
        "patientId": patient_id,
        "explanation": {
            "features": ["Age", "Severity Level", "Comorbidities", "Vital Signs", "Lab Results"],
            "importance": [0.28, 0.24, 0.18, 0.15, 0.12]
        }
    }


# ==================== Dashboard Endpoints ====================

@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard statistics and data"""
    return {
        "success": True,
        "statistics": {
            "totalPatients": 464,
            "averageLOS": 6.2,
            "criticalCases": 24,
            "bedUtilization": 0.78
        },
        "bedOccupancy": {
            "days": list(range(1, 15)),
            "occupancy": [75, 78, 80, 77, 79, 81, 78, 76, 80, 82, 79, 77, 81, 78]
        },
        "severityDistribution": {
            "level1": 45,
            "level2": 120,
            "level3": 180,
            "level4": 95,
            "level5": 24
        }
    }


# ==================== Report Endpoints ====================

@app.get("/api/reports/pdf")
async def generate_report(hospital_name: str = "Central Medical Center"):
    """Generate and download comprehensive PDF report"""
    try:
        # Create temporary directory for PDF
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(temp_dir, f"Recovery_Forecast_Report_{timestamp}.pdf")
        
        # Generate PDF
        generate_pdf_report(hospital_name=hospital_name, output_path=output_path)
        
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"PDF generation failed")
        
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"Recovery_Forecast_Report_{timestamp}.pdf"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


@app.post("/api/reports/patient")
async def generate_patient_report(patient_data: dict):
    """Generate patient-specific report (mock)"""
    return {
        "success": True,
        "reportId": "RPT001",
        "patientName": patient_data.get("name"),
        "generatedAt": datetime.now().isoformat(),
        "message": "Patient report generated successfully"
    }


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Healthcare Recovery Forecast API",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Healthcare Recovery Forecast API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": {
                "login": "POST /api/auth/login",
                "logout": "POST /api/auth/logout"
            },
            "predictions": {
                "batch": "POST /api/predict/batch",
                "single": "POST /api/predict/single",
                "explain": "GET /api/predict/explain/{patient_id}"
            },
            "dashboard": "GET /api/dashboard",
            "reports": {
                "pdf": "GET /api/reports/pdf?hospital_name=Hospital%20Name",
                "patient": "POST /api/reports/patient"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
