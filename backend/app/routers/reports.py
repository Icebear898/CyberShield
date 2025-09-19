from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.models.database import get_db, User, Report
from app.routers.auth import get_current_user

router = APIRouter()

# Models
class ReportResponse(BaseModel):
    id: int
    user_id: int
    reported_user_id: int
    created_at: datetime
    status: str
    evidence_file_path: str = None

    class Config:
        from_attributes = True

# Routes
@router.get("/", response_model=List[ReportResponse])
async def get_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get all reports created by the current user
    reports = db.query(Report).filter(Report.user_id == current_user.id).all()
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_user)):
    # Find report
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if user is authorized to view this report
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this report")
    
    return report

@router.post("/{user_id}", response_model=ReportResponse)
async def create_report(user_id: int, db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)):
    # Check if reported user exists
    reported_user = db.query(User).filter(User.id == user_id).first()
    if not reported_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create report
    new_report = Report(
        user_id=current_user.id,
        reported_user_id=user_id,
        status="pending"
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return new_report

@router.put("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(report_id: int, status: str, db: Session = Depends(get_db), 
                              current_user: User = Depends(get_current_user)):
    # Find report
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if user is authorized to update this report
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this report")
    
    # Validate status
    valid_statuses = ["pending", "reviewed", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Update status
    report.status = status
    db.commit()
    db.refresh(report)
    
    return report