from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas
from app.models.db_models import CML, RiskLevel
import logging
from datetime import datetime
import json

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/metrics", response_model=schemas.DashboardMetrics)
async def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Get key metrics for dashboard"""
    cmls = db.query(CML).all()
    
    metrics = schemas.DashboardMetrics(
        total_cmls=len(cmls),
        active_cmls=sum(1 for c in cmls if not c.elimination_candidate),
        elimination_candidates=sum(1 for c in cmls if c.elimination_candidate),
        critical_risk=sum(1 for c in cmls if c.risk_level == RiskLevel.CRITICAL),
        high_risk=sum(1 for c in cmls if c.risk_level == RiskLevel.HIGH),
        medium_risk=sum(1 for c in cmls if c.risk_level == RiskLevel.MEDIUM),
        low_risk=sum(1 for c in cmls if c.risk_level == RiskLevel.LOW),
        avg_remaining_life=round(sum(c.remaining_life_years or 0 for c in cmls) / len(cmls), 1) if cmls else 0,
        facilities_count=len(set(c.facility for c in cmls if c.facility)),
        last_updated=datetime.now()
    )
    return metrics

@router.get("/risk-matrix")
async def get_risk_matrix(db: Session = Depends(get_db)):
    """Get risk matrix data for heatmap visualization"""
    cmls = db.query(CML).all()
    
    # Create matrix: corrosion rate vs remaining life
    matrix_data = []
    for cml in cmls:
        if cml.average_corrosion_rate and cml.remaining_life_years:
            matrix_data.append({
                'cml_id': cml.cml_id,
                'corrosion_rate': cml.average_corrosion_rate,
                'remaining_life': cml.remaining_life_years,
                'risk_level': cml.risk_level.value if cml.risk_level else 'Unknown',
                'facility': cml.facility,
                'commodity': cml.commodity
            })
    
    return JSONResponse(content={'data': matrix_data, 'count': len(matrix_data)})

@router.get("/corrosion-trends")
async def get_corrosion_trends(db: Session = Depends(get_db)):
    """Get corrosion rate trends by commodity and material"""
    cmls = db.query(CML).all()
    
    # Group by commodity
    commodity_trends = {}
    for cml in cmls:
        if cml.commodity and cml.average_corrosion_rate:
            if cml.commodity not in commodity_trends:
                commodity_trends[cml.commodity] = []
            commodity_trends[cml.commodity].append(cml.average_corrosion_rate)
    
    # Calculate averages
    trends = []
    for commodity, rates in commodity_trends.items():
        trends.append({
            'commodity': commodity,
            'avg_rate': round(sum(rates) / len(rates), 3),
            'min_rate': round(min(rates), 3),
            'max_rate': round(max(rates), 3),
            'count': len(rates)
        })
    
    trends.sort(key=lambda x: x['avg_rate'], reverse=True)
    
    return JSONResponse(content={'trends': trends})

@router.get("/elimination-summary")
async def get_elimination_summary(db: Session = Depends(get_db)):
    """Get summary of elimination candidates with reasoning"""
    candidates = db.query(CML).filter(CML.elimination_candidate == True).all()
    
    summary = []
    for cml in candidates:
        summary.append({
            'cml_id': cml.cml_id,
            'facility': cml.facility,
            'system': cml.system,
            'commodity': cml.commodity,
            'risk_level': cml.risk_level.value if cml.risk_level else 'Unknown',
            'remaining_life': cml.remaining_life_years,
            'ml_probability': cml.ml_elimination_probability,
            'ml_confidence': cml.ml_confidence,
            'sme_override': cml.sme_override,
            'sme_decision': cml.sme_decision,
            'reason': f"Low risk ({cml.risk_level.value}), {cml.remaining_life_years:.1f} years remaining" if cml.remaining_life_years else "Low risk"
        })
    
    return JSONResponse(content={
        'total_candidates': len(summary),
        'candidates': summary,
        'sme_overrides': sum(1 for c in candidates if c.sme_override)
    })

@router.get("/facility-breakdown")
async def get_facility_breakdown(db: Session = Depends(get_db)):
    """Get CML breakdown by facility"""
    cmls = db.query(CML).all()
    
    facility_data = {}
    for cml in cmls:
        facility = cml.facility or 'Unknown'
        if facility not in facility_data:
            facility_data[facility] = {
                'total': 0,
                'eliminations': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        
        facility_data[facility]['total'] += 1
        if cml.elimination_candidate:
            facility_data[facility]['eliminations'] += 1
        
        if cml.risk_level == RiskLevel.CRITICAL:
            facility_data[facility]['critical'] += 1
        elif cml.risk_level == RiskLevel.HIGH:
            facility_data[facility]['high'] += 1
        elif cml.risk_level == RiskLevel.MEDIUM:
            facility_data[facility]['medium'] += 1
        elif cml.risk_level == RiskLevel.LOW:
            facility_data[facility]['low'] += 1
    
    return JSONResponse(content={'facilities': facility_data})
