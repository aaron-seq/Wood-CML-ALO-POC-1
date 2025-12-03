from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

class RiskLevelEnum(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class CMLBase(BaseModel):
    cml_id: str
    line_id: Optional[str] = None
    equipment_id: Optional[str] = None
    facility: Optional[str] = None
    system: Optional[str] = None
    commodity: Optional[str] = None
    material_type: Optional[str] = None
    feature_type: Optional[str] = None
    cml_shape: Optional[str] = None
    design_thickness_mm: Optional[float] = None
    min_allowable_thickness_mm: Optional[float] = None
    current_thickness_mm: Optional[float] = None
    average_corrosion_rate: Optional[float] = None
    remaining_life_years: Optional[float] = None
    risk_level: Optional[RiskLevelEnum] = None

class CMLCreate(CMLBase):
    pass

class CMLResponse(CMLBase):
    id: int
    elimination_candidate: bool
    ml_elimination_probability: Optional[float] = None
    ml_confidence: Optional[float] = None
    sme_override: Optional[bool] = None
    sme_decision: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CMLSummary(BaseModel):
    total_cmls: int
    elimination_candidates: int
    requires_review: int
    risk_distribution: Dict[str, int]
    average_corrosion_rate: float
    facilities: List[str]
    systems: List[str]

class AnalysisRequest(BaseModel):
    facility: Optional[str] = None
    system: Optional[str] = None
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    retrain: bool = False
    
class AnalysisResponse(BaseModel):
    total_analyzed: int
    eliminations_recommended: int
    high_confidence_count: int
    analysis_timestamp: datetime
    results: List[CMLResponse]
    model_metrics: Optional[Dict[str, Any]] = None

class ForecastRequest(BaseModel):
    cml_id: str
    periods: int = Field(default=24, ge=1, le=120, description="Months to forecast")
    model_type: str = Field(default="prophet", pattern="^(prophet|linear|arima)$")
    
class ForecastPoint(BaseModel):
    date: date
    predicted_thickness: float
    lower_bound: float
    upper_bound: float
    
class ForecastResponse(BaseModel):
    cml_id: str
    current_thickness: float
    min_allowable: float
    forecast_points: List[ForecastPoint]
    estimated_failure_date: Optional[date] = None
    confidence: float
    
class SMEOverride(BaseModel):
    cml_id: str
    decision: str = Field(..., pattern="^(keep|eliminate)$")
    reason: str
    user: str

class ReportRequest(BaseModel):
    facility: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_forecasts: bool = True
    include_shap: bool = True

class UploadResponse(BaseModel):
    message: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    processing_time: float
    errors: Optional[List[str]] = None

class DashboardMetrics(BaseModel):
    total_cmls: int
    active_cmls: int
    elimination_candidates: int
    critical_risk: int
    high_risk: int
    medium_risk: int
    low_risk: int
    avg_remaining_life: float
    facilities_count: int
    last_updated: datetime
