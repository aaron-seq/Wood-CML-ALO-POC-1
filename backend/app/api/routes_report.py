from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas
from app.models.db_models import CML, RiskLevel
import logging
from datetime import datetime
import io
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate")
async def generate_report(
    request: schemas.ReportRequest,
    db: Session = Depends(get_db)
):
    """Generate PDF report for CML analysis"""
    from app.services.report_service import ReportService
    
    # Query CMLs based on filters
    query = db.query(CML)
    
    if request.facility:
        query = query.filter(CML.facility == request.facility)
    
    if request.start_date:
        query = query.filter(CML.last_inspection_date >= request.start_date)
    
    if request.end_date:
        query = query.filter(CML.last_inspection_date <= request.end_date)
    
    cmls = query.all()
    
    if not cmls:
        raise HTTPException(status_code=404, detail="No CMLs found matching criteria")
    
    # Generate report
    report_service = ReportService()
    pdf_buffer = report_service.generate_pdf_report(
        cmls=cmls,
        include_forecasts=request.include_forecasts,
        include_shap=request.include_shap
    )
    
    # Generate filename
    filename = f"CML_Report_{request.facility or 'All'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.getvalue()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export-excel")
async def export_to_excel(
    facility: str = None,
    db: Session = Depends(get_db)
):
    """Export CML data to Excel"""
    import pandas as pd
    
    query = db.query(CML)
    if facility:
        query = query.filter(CML.facility == facility)
    
    cmls = query.all()
    
    if not cmls:
        raise HTTPException(status_code=404, detail="No CMLs found")
    
    # Convert to DataFrame
    data = []
    for cml in cmls:
        data.append({
            'CML ID': cml.cml_id,
            'Facility': cml.facility,
            'System': cml.system,
            'Commodity': cml.commodity,
            'Material': cml.material_type,
            'Feature Type': cml.feature_type,
            'Current Thickness (mm)': cml.current_thickness_mm,
            'Min Allowable (mm)': cml.min_allowable_thickness_mm,
            'Corrosion Rate (mm/yr)': cml.average_corrosion_rate,
            'Remaining Life (years)': cml.remaining_life_years,
            'Risk Level': cml.risk_level.value if cml.risk_level else None,
            'Elimination Candidate': 'Yes' if cml.elimination_candidate else 'No',
            'ML Probability': cml.ml_elimination_probability,
            'ML Confidence': cml.ml_confidence,
            'SME Override': 'Yes' if cml.sme_override else 'No',
            'SME Decision': cml.sme_decision,
            'Last Inspection': cml.last_inspection_date
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='CML Data', index=False)
    
    output.seek(0)
    
    filename = f"CML_Export_{facility or 'All'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/summary-stats")
async def get_summary_statistics(db: Session = Depends(get_db)):
    """Get statistical summary for reports"""
    cmls = db.query(CML).all()
    
    if not cmls:
        return {"message": "No CML data available"}
    
    import numpy as np
    
    corrosion_rates = [c.average_corrosion_rate for c in cmls if c.average_corrosion_rate]
    remaining_lives = [c.remaining_life_years for c in cmls if c.remaining_life_years]
    
    stats = {
        'total_cmls': len(cmls),
        'corrosion_rate_stats': {
            'mean': round(np.mean(corrosion_rates), 3) if corrosion_rates else 0,
            'median': round(np.median(corrosion_rates), 3) if corrosion_rates else 0,
            'std': round(np.std(corrosion_rates), 3) if corrosion_rates else 0,
            'min': round(min(corrosion_rates), 3) if corrosion_rates else 0,
            'max': round(max(corrosion_rates), 3) if corrosion_rates else 0
        },
        'remaining_life_stats': {
            'mean': round(np.mean(remaining_lives), 1) if remaining_lives else 0,
            'median': round(np.median(remaining_lives), 1) if remaining_lives else 0,
            'std': round(np.std(remaining_lives), 1) if remaining_lives else 0,
            'min': round(min(remaining_lives), 1) if remaining_lives else 0,
            'max': round(max(remaining_lives), 1) if remaining_lives else 0
        },
        'risk_distribution': {
            'Critical': sum(1 for c in cmls if c.risk_level == RiskLevel.CRITICAL),
            'High': sum(1 for c in cmls if c.risk_level == RiskLevel.HIGH),
            'Medium': sum(1 for c in cmls if c.risk_level == RiskLevel.MEDIUM),
            'Low': sum(1 for c in cmls if c.risk_level == RiskLevel.LOW)
        },
        'elimination_stats': {
            'total_candidates': sum(1 for c in cmls if c.elimination_candidate),
            'sme_overrides': sum(1 for c in cmls if c.sme_override),
            'high_confidence': sum(1 for c in cmls if c.ml_confidence and c.ml_confidence > 0.85)
        }
    }
    
    return stats
