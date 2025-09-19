from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.database import get_db, User, FriendRequest, Friendship
from app.auth import get_current_user
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/friends", tags=["friends"])

class FriendRequestCreate(BaseModel):
    receiver_id: int

class FriendRequestResponse(BaseModel):
    action: str  # accept, reject

@router.post("/request")
async def send_friend_request(
    request: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a friend request to another user"""
    
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == request.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't send request to yourself
    if current_user.id == request.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    # Check if already friends
    existing_friendship = db.query(Friendship).filter(
        or_(
            and_(Friendship.user1_id == current_user.id, Friendship.user2_id == request.receiver_id),
            and_(Friendship.user1_id == request.receiver_id, Friendship.user2_id == current_user.id)
        )
    ).first()
    
    if existing_friendship:
        raise HTTPException(status_code=400, detail="Already friends with this user")
    
    # Check if request already exists
    existing_request = db.query(FriendRequest).filter(
        or_(
            and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == request.receiver_id),
            and_(FriendRequest.sender_id == request.receiver_id, FriendRequest.receiver_id == current_user.id)
        ),
        FriendRequest.status == "pending"
    ).first()
    
    if existing_request:
        if existing_request.sender_id == current_user.id:
            raise HTTPException(status_code=400, detail="Friend request already sent")
        else:
            raise HTTPException(status_code=400, detail="This user has already sent you a friend request")
    
    # Create friend request
    friend_request = FriendRequest(
        sender_id=current_user.id,
        receiver_id=request.receiver_id,
        status="pending"
    )
    
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    
    return {
        "message": f"Friend request sent to {receiver.full_name}",
        "request_id": friend_request.id
    }

@router.get("/requests/received")
async def get_received_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending friend requests received by current user"""
    
    requests = db.query(FriendRequest).filter(
        FriendRequest.receiver_id == current_user.id,
        FriendRequest.status == "pending"
    ).all()
    
    result = []
    for req in requests:
        sender = db.query(User).filter(User.id == req.sender_id).first()
        result.append({
            "id": req.id,
            "sender": {
                "id": sender.id,
                "username": sender.username,
                "full_name": sender.full_name
            },
            "created_at": req.created_at.isoformat()
        })
    
    return result

@router.get("/requests/sent")
async def get_sent_friend_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all friend requests sent by current user"""
    
    requests = db.query(FriendRequest).filter(
        FriendRequest.sender_id == current_user.id,
        FriendRequest.status == "pending"
    ).all()
    
    result = []
    for req in requests:
        receiver = db.query(User).filter(User.id == req.receiver_id).first()
        result.append({
            "id": req.id,
            "receiver": {
                "id": receiver.id,
                "username": receiver.username,
                "full_name": receiver.full_name
            },
            "created_at": req.created_at.isoformat(),
            "status": req.status
        })
    
    return result

@router.post("/requests/{request_id}/respond")
async def respond_to_friend_request(
    request_id: int,
    response: FriendRequestResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept or reject a friend request"""
    
    # Get the friend request
    friend_request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.receiver_id == current_user.id,
        FriendRequest.status == "pending"
    ).first()
    
    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    if response.action not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")
    
    # Update request status
    friend_request.status = "accepted" if response.action == "accept" else "rejected"
    
    # If accepted, create friendship
    if response.action == "accept":
        # Ensure user1_id is always smaller for consistency
        user1_id = min(current_user.id, friend_request.sender_id)
        user2_id = max(current_user.id, friend_request.sender_id)
        
        friendship = Friendship(
            user1_id=user1_id,
            user2_id=user2_id
        )
        
        db.add(friendship)
    
    db.commit()
    
    sender = db.query(User).filter(User.id == friend_request.sender_id).first()
    
    return {
        "message": f"Friend request from {sender.full_name} {response.action}ed",
        "action": response.action
    }

@router.get("/list")
async def get_friends_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of current user's friends"""
    
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user1_id == current_user.id,
            Friendship.user2_id == current_user.id
        )
    ).all()
    
    friends = []
    for friendship in friendships:
        friend_id = friendship.user2_id if friendship.user1_id == current_user.id else friendship.user1_id
        friend = db.query(User).filter(User.id == friend_id).first()
        
        friends.append({
            "id": friend.id,
            "username": friend.username,
            "full_name": friend.full_name,
            "friendship_since": friendship.created_at.isoformat()
        })
    
    return friends

@router.get("/search")
async def search_users_for_friends(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for users to send friend requests to"""
    
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    # Get current friends
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user1_id == current_user.id,
            Friendship.user2_id == current_user.id
        )
    ).all()
    
    friend_ids = set()
    for friendship in friendships:
        friend_ids.add(friendship.user1_id if friendship.user2_id == current_user.id else friendship.user2_id)
    
    # Get pending requests
    pending_requests = db.query(FriendRequest).filter(
        or_(
            FriendRequest.sender_id == current_user.id,
            FriendRequest.receiver_id == current_user.id
        ),
        FriendRequest.status == "pending"
    ).all()
    
    pending_user_ids = set()
    for req in pending_requests:
        pending_user_ids.add(req.sender_id if req.receiver_id == current_user.id else req.receiver_id)
    
    # Search users
    users = db.query(User).filter(
        or_(
            User.username.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%")
        ),
        User.id != current_user.id,  # Exclude current user
        ~User.id.in_(friend_ids),     # Exclude existing friends
        ~User.id.in_(pending_user_ids)  # Exclude pending requests
    ).limit(10).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "can_send_request": True
        })
    
    return result

@router.delete("/remove/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a friend"""
    
    friendship = db.query(Friendship).filter(
        or_(
            and_(Friendship.user1_id == current_user.id, Friendship.user2_id == friend_id),
            and_(Friendship.user1_id == friend_id, Friendship.user2_id == current_user.id)
        )
    ).first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    friend = db.query(User).filter(User.id == friend_id).first()
    
    db.delete(friendship)
    db.commit()
    
    return {
        "message": f"Removed {friend.full_name} from friends list"
    }

@router.get("/status/{user_id}")
async def get_friendship_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get friendship status with a specific user"""
    
    if user_id == current_user.id:
        return {"status": "self"}
    
    # Check if friends
    friendship = db.query(Friendship).filter(
        or_(
            and_(Friendship.user1_id == current_user.id, Friendship.user2_id == user_id),
            and_(Friendship.user1_id == user_id, Friendship.user2_id == current_user.id)
        )
    ).first()
    
    if friendship:
        return {"status": "friends", "since": friendship.created_at.isoformat()}
    
    # Check for pending requests
    pending_request = db.query(FriendRequest).filter(
        or_(
            and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == user_id),
            and_(FriendRequest.sender_id == user_id, FriendRequest.receiver_id == current_user.id)
        ),
        FriendRequest.status == "pending"
    ).first()
    
    if pending_request:
        if pending_request.sender_id == current_user.id:
            return {"status": "request_sent", "request_id": pending_request.id}
        else:
            return {"status": "request_received", "request_id": pending_request.id}
    
    return {"status": "not_friends"}
