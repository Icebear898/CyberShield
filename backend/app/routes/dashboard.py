from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.database import get_db, User, Message, Report, BlockedUser
from app.auth import get_current_user
from datetime import datetime, timedelta
from typing import Dict, List

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Basic counts
    total_users = db.query(User).count()
    total_messages = db.query(Message).count()
    total_reports = db.query(Report).count()
    total_blocked_users = db.query(BlockedUser).count()
    
    # Abusive message stats
    abusive_messages = db.query(Message).filter(Message.is_abusive == True).count()
    abusive_percentage = (abusive_messages / total_messages * 100) if total_messages > 0 else 0
    
    # Recent activity (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    recent_messages = db.query(Message).filter(Message.created_at >= yesterday).count()
    recent_reports = db.query(Report).filter(Report.created_at >= yesterday).count()
    recent_blocks = db.query(BlockedUser).filter(BlockedUser.created_at >= yesterday).count()
    
    # Alert levels
    high_severity_reports = db.query(Report).join(Message).filter(
        Message.abuse_score > 8,
        Message.is_abusive == True
    ).count()
    
    # Top abusers (users with most abusive messages)
    top_abusers = db.query(
        User.username,
        User.full_name,
        func.count(Message.id).label('abuse_count')
    ).join(Message, User.id == Message.sender_id).filter(
        Message.is_abusive == True
    ).group_by(User.id).order_by(desc('abuse_count')).limit(5).all()
    
    # Recent activity timeline
    recent_activity = []
    
    # Get recent reports
    recent_report_items = db.query(Report).order_by(desc(Report.created_at)).limit(5).all()
    for report in recent_report_items:
        reporter = db.query(User).filter(User.id == report.user_id).first()
        reported = db.query(User).filter(User.id == report.reported_user_id).first()
        recent_activity.append({
            "type": "report",
            "timestamp": report.created_at.isoformat(),
            "description": f"Report generated: {reporter.username} reported {reported.username}",
            "severity": "high" if any(msg.abuse_score > 8 for msg in db.query(Message).filter(
                Message.sender_id == report.reported_user_id,
                Message.receiver_id == report.user_id,
                Message.is_abusive == True
            ).all()) else "medium"
        })
    
    # Get recent blocks
    recent_block_items = db.query(BlockedUser).order_by(desc(BlockedUser.created_at)).limit(3).all()
    for block in recent_block_items:
        blocker = db.query(User).filter(User.id == block.user_id).first()
        blocked = db.query(User).filter(User.id == block.blocked_user_id).first()
        recent_activity.append({
            "type": "block",
            "timestamp": block.created_at.isoformat(),
            "description": f"User blocked: {blocker.username} blocked {blocked.username}",
            "severity": "medium"
        })
    
    # Sort activity by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        "overview": {
            "total_users": total_users,
            "total_messages": total_messages,
            "total_reports": total_reports,
            "total_blocked_users": total_blocked_users,
            "abusive_messages": abusive_messages,
            "abusive_percentage": round(abusive_percentage, 2)
        },
        "recent_activity": {
            "messages_24h": recent_messages,
            "reports_24h": recent_reports,
            "blocks_24h": recent_blocks
        },
        "alerts": {
            "high_severity_reports": high_severity_reports,
            "pending_reports": db.query(Report).filter(Report.status == "pending").count(),
            "escalated_reports": db.query(Report).filter(Report.status == "escalated").count()
        },
        "top_abusers": [
            {
                "username": abuser.username,
                "full_name": abuser.full_name,
                "abuse_count": abuser.abuse_count
            }
            for abuser in top_abusers
        ],
        "activity_timeline": recent_activity[:10]
    }

@router.get("/charts/messages")
async def get_message_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get message statistics for charts (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Messages over time (last 7 days)
    daily_stats = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        total = db.query(Message).filter(
            Message.created_at >= start_of_day,
            Message.created_at < end_of_day
        ).count()
        
        abusive = db.query(Message).filter(
            Message.created_at >= start_of_day,
            Message.created_at < end_of_day,
            Message.is_abusive == True
        ).count()
        
        daily_stats.append({
            "date": start_of_day.strftime("%Y-%m-%d"),
            "total_messages": total,
            "abusive_messages": abusive,
            "clean_messages": total - abusive
        })
    
    # Reverse to show chronological order
    daily_stats.reverse()
    
    # Abuse score distribution
    abuse_distribution = {
        "low": db.query(Message).filter(
            Message.is_abusive == True,
            Message.abuse_score <= 5
        ).count(),
        "medium": db.query(Message).filter(
            Message.is_abusive == True,
            Message.abuse_score > 5,
            Message.abuse_score <= 8
        ).count(),
        "high": db.query(Message).filter(
            Message.is_abusive == True,
            Message.abuse_score > 8
        ).count()
    }
    
    return {
        "daily_stats": daily_stats,
        "abuse_distribution": abuse_distribution
    }

@router.get("/users/activity")
async def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity statistics (admin only)"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Active users (sent messages in last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    active_users = db.query(func.count(func.distinct(Message.sender_id))).filter(
        Message.created_at >= week_ago
    ).scalar()
    
    # New users (registered in last 7 days)
    new_users = db.query(User).filter(User.created_at >= week_ago).count()
    
    # User engagement stats
    user_stats = db.query(
        User.username,
        User.full_name,
        func.count(Message.id).label('message_count'),
        func.sum(func.cast(Message.is_abusive, db.Integer)).label('abusive_count')
    ).outerjoin(Message, User.id == Message.sender_id).group_by(User.id).order_by(
        desc('message_count')
    ).limit(10).all()
    
    return {
        "active_users_week": active_users,
        "new_users_week": new_users,
        "total_users": db.query(User).count(),
        "top_users": [
            {
                "username": user.username,
                "full_name": user.full_name,
                "message_count": user.message_count or 0,
                "abusive_count": user.abusive_count or 0,
                "clean_percentage": round(
                    ((user.message_count or 0) - (user.abusive_count or 0)) / max(user.message_count or 1, 1) * 100, 2
                )
            }
            for user in user_stats
        ]
    }
