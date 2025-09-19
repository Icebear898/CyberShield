from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.database import get_db, User, Message, Friendship
from app.auth import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/messages", tags=["messages"])

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    is_abusive: bool
    abuse_score: float
    abuse_type: str = None

class MessageCreate(BaseModel):
    receiver_id: int
    content: str

@router.get("/conversation/{user_id}", response_model=List[MessageResponse])
async def get_conversation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history between current user and specified user"""
    
    # Check if users are friends (or if current user is admin)
    if not current_user.is_admin:
        friendship = db.query(Friendship).filter(
            or_(
                and_(Friendship.user1_id == current_user.id, Friendship.user2_id == user_id),
                and_(Friendship.user1_id == user_id, Friendship.user2_id == current_user.id)
            )
        ).first()
        
        if not friendship:
            raise HTTPException(status_code=403, detail="Can only view conversations with friends")
    
    # Get messages between the two users
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    return [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            content=msg.content,
            created_at=msg.created_at,
            is_abusive=msg.is_abusive,
            abuse_score=msg.abuse_score,
            abuse_type=msg.abuse_type
        )
        for msg in messages
    ]

@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to another user (friends only)"""
    
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    # Check if users are friends (or if current user is admin)
    if not current_user.is_admin:
        friendship = db.query(Friendship).filter(
            or_(
                and_(Friendship.user1_id == current_user.id, Friendship.user2_id == message.receiver_id),
                and_(Friendship.user1_id == message.receiver_id, Friendship.user2_id == current_user.id)
            )
        ).first()
        
        if not friendship:
            raise HTTPException(status_code=403, detail="Can only send messages to friends")
    
    # Create message (abuse detection would happen in WebSocket handler)
    db_message = Message(
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_abusive=False,  # Will be updated by abuse detection
        abuse_score=0.0    # Will be updated by abuse detection
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return MessageResponse(
        id=db_message.id,
        sender_id=db_message.sender_id,
        receiver_id=db_message.receiver_id,
        content=db_message.content,
        created_at=db_message.created_at,
        is_abusive=db_message.is_abusive,
        abuse_score=db_message.abuse_score,
        abuse_type=db_message.abuse_type
    )
