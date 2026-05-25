"""
Database models and configuration for Healthcare Recovery Forecast
Uses SQLite for development, easily upgradeable to PostgreSQL
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Use SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare_forecast.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== Database Models ====================

class User(Base):
    """Hospital user accounts"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)  # admin, doctor, analyst
    hospital_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient_data = relationship("PatientData", back_populates="user")
    analyses = relationship("Analysis", back_populates="user")


class PatientData(Base):
    """Uploaded patient data"""
    __tablename__ = "patient_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(String, index=True)
    patient_name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    admission_date = Column(DateTime)
    primary_diagnosis = Column(String)
    severity_level = Column(Integer)  # 1-5
    comorbidities = Column(Text)  # JSON string
    vital_signs = Column(Text)  # JSON string
    lab_results = Column(Text)  # JSON string
    file_name = Column(String)
    file_hash = Column(String, unique=True)  # To detect duplicate uploads
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="patient_data")
    analyses = relationship("Analysis", back_populates="patient_data")


class Analysis(Base):
    """Patient analysis and predictions"""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_data_id = Column(Integer, ForeignKey("patient_data.id"))
    predicted_los = Column(Float)  # Length of stay prediction
    confidence = Column(Float)  # Confidence score 0-1
    key_factors = Column(Text)  # JSON string of important factors
    risk_factors = Column(Text)  # JSON string
    recommendations = Column(Text)  # JSON string
    model_version = Column(String)
    analysis_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="analyses")
    patient_data = relationship("PatientData", back_populates="analyses")


# ==================== Database Initialization ====================

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    print("✅ Database tables created successfully!")
