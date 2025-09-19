from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.models.database import get_db, User, BlockedUser
from app.routers.auth import get_current_user

router = APIRouter()

# Models
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True

class BlockedUserResponse(BaseModel):
    id: int
    blocked_user_id: int
    blocked_username: str
    reason: str

    class Config:
        from_attributes = True

# Routes
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/blocked", response_model=List[BlockedUserResponse])
async def get_blocked_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    blocked = db.query(BlockedUser).filter(BlockedUser.user_id == current_user.id).all()
    
    # Enrich with username information
    result = []
    for block in blocked:
        blocked_user = db.query(User).filter(User.id == block.blocked_user_id).first()
        if blocked_user:
            result.append({
                "id": block.id,
                "blocked_user_id": block.blocked_user_id,
                "blocked_username": blocked_user.username,
                "reason": block.reason or "No reason provided"
            })
    
    return result

@router.post("/block/{user_id}", response_model=BlockedUserResponse)
async def block_user(user_id: int, reason: str = None, db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_user)):
    # Check if user exists
    user_to_block = db.query(User).filter(User.id == user_id).first()
    if not user_to_block:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already blocked
    existing_block = db.query(BlockedUser).filter(
        BlockedUser.user_id == current_user.id,
        BlockedUser.blocked_user_id == user_id
    ).first()
    
    if existing_block:
        raise HTTPException(status_code=400, detail="User is already blocked")
    
    # Create block
    new_block = BlockedUser(
        user_id=current_user.id,
        blocked_user_id=user_id,
        reason=reason
    )
    
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    
    return {
        "id": new_block.id,
        "blocked_user_id": new_block.blocked_user_id,
        "blocked_username": user_to_block.username,
        "reason": new_block.reason or "No reason provided"
    }

@router.delete("/unblock/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(user_id: int, db: Session = Depends(get_db), 
                      current_user: User = Depends(get_current_user)):
    # Find block
    block = db.query(BlockedUser).filter(
        BlockedUser.user_id == current_user.id,
        BlockedUser.blocked_user_id == user_id
    ).first()
    
    if not block:
        raise HTTPException(status_code=404, detail="User is not blocked")
    
    # Remove block
    db.delete(block)
    db.commit()
    
    return None