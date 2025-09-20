from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.models.database import get_db, Report, User, Message, BlockedUser
from app.auth import get_current_user
from typing import List, Optional
import json
import os
from datetime import datetime

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/")
async def get_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for the current user or all reports if admin"""
    
    if current_user.is_admin:
        # Admin can see all reports
        reports = db.query(Report).all()
    else:
        # Regular users can only see their own reports
        reports = db.query(Report).filter(Report.user_id == current_user.id).all()
    
    result = []
    for report in reports:
        # Get user details
        reported_user = db.query(User).filter(User.id == report.reported_user_id).first()
        reporter_user = db.query(User).filter(User.id == report.user_id).first()
        
        # Get abusive messages for this report
        abusive_messages = db.query(Message).filter(
            Message.sender_id == report.reported_user_id,
            Message.receiver_id == report.user_id,
            Message.is_abusive == True
        ).all()
        
        report_data = {
            "id": report.id,
            "reporter": {
                "id": reporter_user.id,
                "username": reporter_user.username,
                "full_name": reporter_user.full_name
            },
            "reported_user": {
                "id": reported_user.id,
                "username": reported_user.username,
                "full_name": reported_user.full_name
            },
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "evidence_file_path": report.evidence_file_path,
            "abusive_messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "abuse_score": msg.abuse_score,
                    "created_at": msg.created_at.isoformat(),
                    "sender_ip": "192.168.1.100"  # Mock IP for now
                }
                for msg in abusive_messages
            ],
            "total_abusive_messages": len(abusive_messages),
            "severity": "HIGH" if any(msg.abuse_score > 7 for msg in abusive_messages) else "MEDIUM" if any(msg.abuse_score > 5 for msg in abusive_messages) else "LOW"
        }
        result.append(report_data)
    
    return result

@router.get("/{report_id}")
async def get_report_details(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific report"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions
    if not current_user.is_admin and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user details
    reported_user = db.query(User).filter(User.id == report.reported_user_id).first()
    reporter_user = db.query(User).filter(User.id == report.user_id).first()
    
    # Get all abusive messages between these users
    abusive_messages = db.query(Message).filter(
        Message.sender_id == report.reported_user_id,
        Message.receiver_id == report.user_id,
        Message.is_abusive == True
    ).order_by(Message.created_at.desc()).all()
    
    # Get blocking status
    is_blocked = db.query(BlockedUser).filter(
        BlockedUser.user_id == report.user_id,
        BlockedUser.blocked_user_id == report.reported_user_id
    ).first() is not None
    
    return {
        "id": report.id,
        "reporter": {
            "id": reporter_user.id,
            "username": reporter_user.username,
            "full_name": reporter_user.full_name,
            "email": reporter_user.email
        },
        "reported_user": {
            "id": reported_user.id,
            "username": reported_user.username,
            "full_name": reported_user.full_name,
            "email": reported_user.email
        },
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "evidence_file_path": report.evidence_file_path,
        "is_blocked": is_blocked,
        "abusive_messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "abuse_score": msg.abuse_score,
                "created_at": msg.created_at.isoformat(),
                "sender_ip": "192.168.1.100",  # Mock IP
                "abuse_type": classify_abuse_type(msg.content, msg.abuse_score)
            }
            for msg in abusive_messages
        ],
        "summary": {
            "total_messages": len(abusive_messages),
            "highest_abuse_score": max([msg.abuse_score for msg in abusive_messages], default=0),
            "abuse_types": list(set([classify_abuse_type(msg.content, msg.abuse_score) for msg in abusive_messages])),
            "first_incident": abusive_messages[-1].created_at.isoformat() if abusive_messages else None,
            "last_incident": abusive_messages[0].created_at.isoformat() if abusive_messages else None
        }
    }


def classify_abuse_type(content: str, score: float) -> str:
    """Classify the type of abuse based on content and score"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['hate', 'kill', 'die', 'death']):
        return "HATE_SPEECH"
    elif any(word in content_lower for word in ['bitch', 'fuck', 'shit', 'damn']):
        return "PROFANITY"
    elif any(word in content_lower for word in ['stupid', 'idiot', 'loser', 'ugly']):
        return "HARASSMENT"
    elif score > 8:
        return "SEVERE_ABUSE"
    elif score > 6:
        return "MODERATE_ABUSE"
    else:
        return "MILD_ABUSE"

def generate_comprehensive_report(report_data: dict) -> str:
    """Generate a comprehensive text report"""
    
    content = f"""
CYBERSHIELD ABUSE REPORT
========================
Report ID: {report_data['id']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {report_data['status']}

INCIDENT SUMMARY
================
Reporter: {report_data['reporter']['full_name']} ({report_data['reporter']['username']})
Reporter ID: {report_data['reporter']['id']}
Reporter Email: {report_data['reporter']['email']}

Reported User: {report_data['reported_user']['full_name']} ({report_data['reported_user']['username']})
Reported User ID: {report_data['reported_user']['id']}
Reported User Email: {report_data['reported_user']['email']}

Report Created: {report_data['created_at']}
User Blocked: {'Yes' if report_data['is_blocked'] else 'No'}

ABUSE STATISTICS
================
Total Abusive Messages: {report_data['summary']['total_messages']}
Highest Abuse Score: {report_data['summary']['highest_abuse_score']}/10
Abuse Types Detected: {', '.join(report_data['summary']['abuse_types'])}
First Incident: {report_data['summary']['first_incident']}
Last Incident: {report_data['summary']['last_incident']}

DETAILED MESSAGE LOG
====================
"""
    
    for i, msg in enumerate(report_data['abusive_messages'], 1):
        content += f"""
Message {i}:
-----------
Timestamp: {msg['created_at']}
Sender IP: {msg['sender_ip']}
Abuse Score: {msg['abuse_score']}/10
Abuse Type: {msg['abuse_type']}
Content: "{msg['content']}"

"""
    
    content += f"""
EVIDENCE FILES
==============
Evidence File Path: {report_data.get('evidence_file_path', 'N/A')}

SYSTEM INFORMATION
==================
Platform: CyberShield v2.0
Detection Algorithm: AI-based content analysis
Report Format: Comprehensive incident report

This report was automatically generated by CyberShield's abuse detection system.
For questions or concerns, please contact the system administrator.

END OF REPORT
=============
"""
    
    return content

@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a report as a ZIP file (new format) or text file (legacy format)"""
    
    # Get the report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions
    if not current_user.is_admin and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if evidence file exists
    if not report.evidence_file_path or not os.path.exists(report.evidence_file_path):
        # For old reports without evidence files, generate a text report
        report_data = await get_report_details(report_id, current_user, db)
        report_content = generate_comprehensive_report(report_data)
        
        filename = f"cybershield_report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return Response(
            content=report_content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    # Determine file type and serve accordingly
    filename = os.path.basename(report.evidence_file_path)
    
    if filename.endswith('.zip'):
        # New ZIP format with JSON + screenshots
        return FileResponse(
            path=report.evidence_file_path,
            filename=filename,
            media_type='application/zip',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        # Legacy text format
        return FileResponse(
            path=report.evidence_file_path,
            filename=filename,
            media_type='text/plain',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
