from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas
from app.models.db_models import CML, Forecast
import logging
from datetime import datetime, timedelta
import pandas as pd

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/predict", response_model=schemas.ForecastResponse)
async def predict_forecast(
    request: schemas.ForecastRequest,
    db: Session = Depends(get_db)
):
    """Generate thickness forecast for a CML"""
    from app.ml.model_forecast import CMLForecastModel
    
    # Get CML
    cml = db.query(CML).filter(CML.cml_id == request.cml_id).first()
    if not cml:
        raise HTTPException(status_code=404, detail="CML not found")
    
    # Parse historical data
    if not cml.inspection_history_dates or not cml.inspection_history_measurements:
        raise HTTPException(status_code=400, detail="Insufficient historical data for forecasting")
    
    try:
        dates_str = cml.inspection_history_dates.split('|')
        measurements_str = cml.inspection_history_measurements.split('|')
        
        dates = [datetime.strptime(d.strip(), '%Y-%m-%d').date() for d in dates_str]
        measurements = [float(m.strip()) for m in measurements_str]
        
        if len(dates) < 3:
            raise HTTPException(status_code=400, detail="Need at least 3 historical measurements")
        
        # Create DataFrame for model
        df = pd.DataFrame({
            'ds': dates,
            'y': measurements
        })
        
        # Initialize and run forecast model
        forecast_model = CMLForecastModel(model_type=request.model_type)
        forecast_df = forecast_model.predict(df, periods=request.periods)
        
        # Convert to forecast points
        forecast_points = []
        for _, row in forecast_df.iterrows():
            forecast_points.append(schemas.ForecastPoint(
                date=row['ds'],
                predicted_thickness=round(row['yhat'], 2),
                lower_bound=round(row.get('yhat_lower', row['yhat'] - 0.5), 2),
                upper_bound=round(row.get('yhat_upper', row['yhat'] + 0.5), 2)
            ))
        
        # Estimate failure date (when thickness hits min allowable)
        estimated_failure = None
        for point in forecast_points:
            if point.predicted_thickness <= cml.min_allowable_thickness_mm:
                estimated_failure = point.date
                break
        
        # Save forecasts to database
        for point in forecast_points:
            forecast_record = Forecast(
                cml_id=cml.id,
                forecast_date=point.date,
                predicted_thickness_mm=point.predicted_thickness,
                lower_bound=point.lower_bound,
                upper_bound=point.upper_bound,
                confidence_level=0.95,
                model_used=request.model_type
            )
            db.add(forecast_record)
        
        db.commit()
        
        return schemas.ForecastResponse(
            cml_id=cml.cml_id,
            current_thickness=cml.current_thickness_mm,
            min_allowable=cml.min_allowable_thickness_mm,
            forecast_points=forecast_points,
            estimated_failure_date=estimated_failure,
            confidence=0.95
        )
        
    except Exception as e:
        logger.error(f"Forecast error for CML {request.cml_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")

@router.get("/{cml_id}/history", response_model=schemas.ForecastResponse)
async def get_forecast_history(
    cml_id: str,
    db: Session = Depends(get_db)
):
    """Get existing forecast history for a CML"""
    cml = db.query(CML).filter(CML.cml_id == cml_id).first()
    if not cml:
        raise HTTPException(status_code=404, detail="CML not found")
    
    # Get latest forecasts
    forecasts = db.query(Forecast).filter(
        Forecast.cml_id == cml.id
    ).order_by(Forecast.forecast_date).all()
    
    if not forecasts:
        raise HTTPException(status_code=404, detail="No forecasts available for this CML")
    
    forecast_points = [
        schemas.ForecastPoint(
            date=f.forecast_date,
            predicted_thickness=f.predicted_thickness_mm,
            lower_bound=f.lower_bound or f.predicted_thickness_mm - 0.5,
            upper_bound=f.upper_bound or f.predicted_thickness_mm + 0.5
        )
        for f in forecasts
    ]
    
    estimated_failure = None
    for point in forecast_points:
        if point.predicted_thickness <= cml.min_allowable_thickness_mm:
            estimated_failure = point.date
            break
    
    return schemas.ForecastResponse(
        cml_id=cml.cml_id,
        current_thickness=cml.current_thickness_mm,
        min_allowable=cml.min_allowable_thickness_mm,
        forecast_points=forecast_points,
        estimated_failure_date=estimated_failure,
        confidence=forecasts[0].confidence_level if forecasts else 0.95
    )
