import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "cml_optimization")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "cml_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    
    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    # ML Models
    MODEL_PATH: str = os.getenv("MODEL_PATH", "data/models/cml_elimination_model.pkl")
    FORECAST_MODEL_PATH: str = os.getenv("FORECAST_MODEL_PATH", "data/models/forecast_model.pkl")
    MIN_TRAINING_SAMPLES: int = int(os.getenv("MIN_TRAINING_SAMPLES", "50"))
    ELIMINATION_THRESHOLD: float = float(os.getenv("ELIMINATION_THRESHOLD", "0.70"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
    
    # Feature Engineering
    MAX_CORROSION_RATE: float = float(os.getenv("MAX_CORROSION_RATE", "5.0"))
    MIN_REMAINING_LIFE: float = float(os.getenv("MIN_REMAINING_LIFE", "0.0"))
    MAX_REMAINING_LIFE: float = float(os.getenv("MAX_REMAINING_LIFE", "100.0"))
    
    # Reports
    REPORT_OUTPUT_DIR: str = os.getenv("REPORT_OUTPUT_DIR", "reports/")
    REPORT_COMPANY_NAME: str = os.getenv("REPORT_COMPANY_NAME", "Wood Engineering")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        case_sensitive = True

settings = Settings()
