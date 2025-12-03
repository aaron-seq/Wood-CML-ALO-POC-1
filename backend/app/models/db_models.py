from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class RiskLevel(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class CML(Base):
    """Condition Monitoring Location model"""
    __tablename__ = "cmls"
    
    id = Column(Integer, primary_key=True, index=True)
    cml_id = Column(String, unique=True, index=True, nullable=False)
    line_id = Column(String, index=True)
    equipment_id = Column(String)
    facility = Column(String, index=True)
    system = Column(String, index=True)
    commodity = Column(String, index=True)
    material_type = Column(String)
    feature_type = Column(String)
    cml_shape = Column(String)
    design_thickness_mm = Column(Float)
    min_allowable_thickness_mm = Column(Float)
    corrosion_allowance_mm = Column(Float)
    current_thickness_mm = Column(Float)
    average_corrosion_rate = Column(Float)
    years_in_service = Column(Integer)
    number_of_inspections = Column(Integer)
    last_inspection_date = Column(Date)
    first_inspection_date = Column(Date)
    remaining_life_years = Column(Float)
    risk_level = Column(Enum(RiskLevel))
    isometric_id = Column(String)
    inspection_technique = Column(String)
    data_quality_score = Column(Float)
    elimination_candidate = Column(Boolean, default=False)
    requires_engineering_review = Column(Boolean, default=False)
    notes = Column(Text)
    ml_elimination_probability = Column(Float)
    ml_confidence = Column(Float)
    ml_prediction_date = Column(DateTime)
    shap_values = Column(JSON)
    feature_importance = Column(JSON)
    sme_override = Column(Boolean, nullable=True)
    sme_decision = Column(String)
    sme_reason = Column(Text)
    sme_user = Column(String)
    sme_timestamp = Column(DateTime)
    inspection_history_dates = Column(Text)
    inspection_history_measurements = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    measurements = relationship("Measurement", back_populates="cml", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="cml", cascade="all, delete-orphan")

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    cml_id = Column(Integer, ForeignKey("cmls.id"), nullable=False)
    inspection_date = Column(Date, nullable=False)
    measured_thickness_mm = Column(Float, nullable=False)
    technique = Column(String)
    inspector = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    cml = relationship("CML", back_populates="measurements")

class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True, index=True)
    cml_id = Column(Integer, ForeignKey("cmls.id"), nullable=False)
    forecast_date = Column(Date, nullable=False)
    predicted_thickness_mm = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    confidence_level = Column(Float)
    model_used = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    cml = relationship("CML", back_populates="forecasts")

class UploadHistory(Base):
    __tablename__ = "upload_history"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, server_default=func.now())
    total_rows = Column(Integer)
    successful_rows = Column(Integer)
    failed_rows = Column(Integer)
    user = Column(String)
    status = Column(String)
    error_log = Column(Text)
    processing_time_seconds = Column(Float)

class ModelTrainingRun(Base):
    __tablename__ = "model_training_runs"
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String)
    training_date = Column(DateTime, server_default=func.now())
    training_samples = Column(Integer)
    validation_accuracy = Column(Float)
    test_accuracy = Column(Float)
    model_path = Column(String)
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    status = Column(String)
