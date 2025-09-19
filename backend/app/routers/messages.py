from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.models.database import get_db, Message, User, BlockedUser
from app.routers.auth import get_current_user
from app.ai.abuse_detector import AbuseDetector

router = APIRouter()
abuse_detector = AbuseDetector()

# Models
class MessageCreate(BaseModel):
    receiver_id: int
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    is_abusive: bool
    abuse_score: int

    class Config:
        from_attributes = True

# Routes
@router.post("/", response_model=MessageResponse)
async def create_message(message: MessageCreate, db: Session = Depends(get_db), 
                        current_user: User = Depends(get_current_user)):
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    # Check if user is blocked by receiver
    block = db.query(BlockedUser).filter(
        BlockedUser.user_id == message.receiver_id,
        BlockedUser.blocked_user_id == current_user.id
    ).first()
    
    if block:
        raise HTTPException(status_code=403, detail="You have been blocked by this user")
    
    # Check if message is abusive
    is_abusive, abuse_score, analysis = abuse_detector.analyze_text(message.content)
    
    # Create message
    db_message = Message(
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_abusive=is_abusive,
        abuse_score=abuse_score
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@router.get("/", response_model=List[MessageResponse])
async def get_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get all messages sent to or by the current user
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.desc()).all()
    
    return messages

@router.get("/conversation/{user_id}", response_model=List[MessageResponse])
async def get_conversation(user_id: int, db: Session = Depends(get_db), 
                          current_user: User = Depends(get_current_user)):
    # Check if other user exists
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get conversation between current user and other user
    messages = db.query(Message).filter(
        (
            (Message.sender_id == current_user.id) & (Message.receiver_id == user_id) |
            (Message.sender_id == user_id) & (Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    return messages

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: int, db: Session = Depends(get_db), 
                        current_user: User = Depends(get_current_user)):
    # Find message
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is the sender
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    # Delete message
    db.delete(message)
    db.commit()
    
    return None