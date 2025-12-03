from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas
from app.models.db_models import CML, UploadHistory, RiskLevel
import pandas as pd
import logging
from datetime import datetime
from typing import List, Optional
import time
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=schemas.UploadResponse)
async def upload_cml_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and parse CML data from Excel file"""
    start_time = time.time()
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    try:
        # Read Excel file
        df = pd.read_excel(file.file, sheet_name='CML_Master_Data')
        total_rows = len(df)
        successful = 0
        failed = 0
        errors = []
        
        # Column mapping
        column_map = {
            'CML_ID': 'cml_id',
            'Line_ID': 'line_id',
            'Equipment_ID': 'equipment_id',
            'Facility': 'facility',
            'System': 'system',
            'Commodity': 'commodity',
            'Material_Type': 'material_type',
            'Feature_Type': 'feature_type',
            'CML_Shape': 'cml_shape',
            'Design_Thickness_mm': 'design_thickness_mm',
            'Min_Allowable_Thickness_mm': 'min_allowable_thickness_mm',
            'Corrosion_Allowance_mm': 'corrosion_allowance_mm',
            'Current_Thickness_mm': 'current_thickness_mm',
            'Average_Corrosion_Rate_mm_per_year': 'average_corrosion_rate',
            'Years_In_Service': 'years_in_service',
            'Number_of_Inspections': 'number_of_inspections',
            'Last_Inspection_Date': 'last_inspection_date',
            'First_Inspection_Date': 'first_inspection_date',
            'Remaining_Life_Years': 'remaining_life_years',
            'Risk_Level': 'risk_level',
            'Isometric_ID': 'isometric_id',
            'Inspection_Technique': 'inspection_technique',
            'Data_Quality_Score': 'data_quality_score',
            'Elimination_Candidate': 'elimination_candidate',
            'Requires_Engineering_Review': 'requires_engineering_review',
            'Inspection_History_Dates': 'inspection_history_dates',
            'Inspection_History_Measurements': 'inspection_history_measurements',
            'Notes': 'notes'
        }
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Check if CML already exists
                existing = db.query(CML).filter(CML.cml_id == row['CML_ID']).first()
                if existing:
                    # Update existing
                    for excel_col, db_col in column_map.items():
                        if excel_col in row and pd.notna(row[excel_col]):
                            value = row[excel_col]
                            if db_col == 'risk_level':
                                value = RiskLevel[value.upper().replace(' ', '_')]
                            setattr(existing, db_col, value)
                else:
                    # Create new CML
                    cml_data = {}
                    for excel_col, db_col in column_map.items():
                        if excel_col in row and pd.notna(row[excel_col]):
                            value = row[excel_col]
                            if db_col == 'risk_level':
                                value = RiskLevel[value.upper().replace(' ', '_')]
                            cml_data[db_col] = value
                    
                    cml = CML(**cml_data)
                    db.add(cml)
                
                successful += 1
            except Exception as e:
                failed += 1
                errors.append(f"Row {idx}: {str(e)}")
                logger.error(f"Error processing row {idx}: {e}")
        
        db.commit()
        
        # Log upload history
        upload_record = UploadHistory(
            filename=file.filename,
            total_rows=total_rows,
            successful_rows=successful,
            failed_rows=failed,
            user="system",
            status="success" if failed == 0 else "partial",
            error_log="\n".join(errors[:100]) if errors else None,
            processing_time_seconds=time.time() - start_time
        )
        db.add(upload_record)
        db.commit()
        
        return schemas.UploadResponse(
            message=f"Successfully processed {successful} of {total_rows} CMLs",
            total_rows=total_rows,
            successful_rows=successful,
            failed_rows=failed,
            processing_time=time.time() - start_time,
            errors=errors[:10] if errors else None
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/summary", response_model=schemas.CMLSummary)
async def get_summary(db: Session = Depends(get_db)):
    """Get summary statistics of all CMLs"""
    cmls = db.query(CML).all()
    
    risk_dist = {
        'Critical': sum(1 for c in cmls if c.risk_level == RiskLevel.CRITICAL),
        'High': sum(1 for c in cmls if c.risk_level == RiskLevel.HIGH),
        'Medium': sum(1 for c in cmls if c.risk_level == RiskLevel.MEDIUM),
        'Low': sum(1 for c in cmls if c.risk_level == RiskLevel.LOW)
    }
    
    avg_rate = sum(c.average_corrosion_rate or 0 for c in cmls) / len(cmls) if cmls else 0
    
    return schemas.CMLSummary(
        total_cmls=len(cmls),
        elimination_candidates=sum(1 for c in cmls if c.elimination_candidate),
        requires_review=sum(1 for c in cmls if c.requires_engineering_review),
        risk_distribution=risk_dist,
        average_corrosion_rate=round(avg_rate, 3),
        facilities=list(set(c.facility for c in cmls if c.facility)),
        systems=list(set(c.system for c in cmls if c.system))
    )

@router.get("/list", response_model=List[schemas.CMLResponse])
async def list_cmls(
    facility: Optional[str] = None,
    risk_level: Optional[str] = None,
    elimination_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List CMLs with optional filtering"""
    query = db.query(CML)
    
    if facility:
        query = query.filter(CML.facility == facility)
    if risk_level:
        query = query.filter(CML.risk_level == RiskLevel[risk_level.upper().replace(' ', '_')])
    if elimination_only:
        query = query.filter(CML.elimination_candidate == True)
    
    cmls = query.offset(skip).limit(limit).all()
    return cmls

@router.get("/{cml_id}", response_model=schemas.CMLResponse)
async def get_cml(cml_id: str, db: Session = Depends(get_db)):
    """Get details of a specific CML"""
    cml = db.query(CML).filter(CML.cml_id == cml_id).first()
    if not cml:
        raise HTTPException(status_code=404, detail="CML not found")
    return cml

@router.post("/analyze", response_model=schemas.AnalysisResponse)
async def analyze_cmls(
    request: schemas.AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run ML analysis on CMLs to identify elimination candidates"""
    from app.ml.model_elimination import CMLEliminationModel
    
    # Query CMls based on filters
    query = db.query(CML)
    if request.facility:
        query = query.filter(CML.facility == request.facility)
    if request.system:
        query = query.filter(CML.system == request.system)
    
    cmls = query.all()
    
    if not cmls:
        raise HTTPException(status_code=404, detail="No CMLs found matching criteria")
    
    # Initialize and run model
    model = CMLEliminationModel()
    
    if request.retrain or not os.path.exists(model.model_path):
        model.train(cmls)
    
    predictions = model.predict(cmls, threshold=request.threshold)
    
    # Update database with predictions
    high_confidence = 0
    for cml_id, pred in predictions.items():
        cml = db.query(CML).filter(CML.cml_id == cml_id).first()
        if cml:
            cml.ml_elimination_probability = pred['probability']
            cml.ml_confidence = pred['confidence']
            cml.ml_prediction_date = datetime.now()
            cml.shap_values = pred.get('shap_values')
            cml.elimination_candidate = pred['recommendation'] == 'eliminate'
            if pred['confidence'] > 0.85:
                high_confidence += 1
    
    db.commit()
    
    # Refresh to get updated data
    results = query.all()
    
    return schemas.AnalysisResponse(
        total_analyzed=len(cmls),
        eliminations_recommended=sum(1 for r in results if r.elimination_candidate),
        high_confidence_count=high_confidence,
        analysis_timestamp=datetime.now(),
        results=results[:50],  # Return first 50
        model_metrics=model.get_metrics() if hasattr(model, 'get_metrics') else None
    )

@router.post("/sme-override")
async def sme_override(
    override: schemas.SMEOverride,
    db: Session = Depends(get_db)
):
    """SME override for ML recommendations"""
    cml = db.query(CML).filter(CML.cml_id == override.cml_id).first()
    if not cml:
        raise HTTPException(status_code=404, detail="CML not found")
    
    cml.sme_override = True
    cml.sme_decision = override.decision
    cml.sme_reason = override.reason
    cml.sme_user = override.user
    cml.sme_timestamp = datetime.now()
    
    # Update elimination candidate based on SME decision
    cml.elimination_candidate = (override.decision == 'eliminate')
    
    db.commit()
    
    return {"message": "SME override recorded successfully", "cml_id": cml.cml_id}
