#!/usr/bin/env python3
"""
Test script to create friendships between users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, User, Friendship, FriendRequest

def create_test_friendships():
    db = SessionLocal()
    
    try:
        # Get users
        alice = db.query(User).filter(User.username == "alice").first()
        bob = db.query(User).filter(User.username == "bob").first()
        charlie = db.query(User).filter(User.username == "charlie").first()
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not all([alice, bob, charlie, admin]):
            print("Some users not found. Please run init_db.py first.")
            return
        
        print("Current users:")
        for user in [alice, bob, charlie, admin]:
            print(f"- {user.username} (ID: {user.id})")
        
        # Check existing friendships
        existing_friendships = db.query(Friendship).all()
        print(f"\nExisting friendships: {len(existing_friendships)}")
        for friendship in existing_friendships:
            user1 = db.query(User).filter(User.id == friendship.user1_id).first()
            user2 = db.query(User).filter(User.id == friendship.user2_id).first()
            print(f"- {user1.username} ↔ {user2.username}")
        
        # Create friendship between alice and charlie if it doesn't exist
        alice_charlie_friendship = db.query(Friendship).filter(
            ((Friendship.user1_id == alice.id) & (Friendship.user2_id == charlie.id)) |
            ((Friendship.user1_id == charlie.id) & (Friendship.user2_id == alice.id))
        ).first()
        
        if not alice_charlie_friendship:
            print(f"\nCreating friendship between {alice.username} and {charlie.username}")
            new_friendship = Friendship(
                user1_id=min(alice.id, charlie.id),
                user2_id=max(alice.id, charlie.id)
            )
            db.add(new_friendship)
            db.commit()
            print("✓ Friendship created!")
        else:
            print(f"\n{alice.username} and {charlie.username} are already friends")
        
        # Check friend requests
        pending_requests = db.query(FriendRequest).filter(FriendRequest.status == "pending").all()
        print(f"\nPending friend requests: {len(pending_requests)}")
        for req in pending_requests:
            sender = db.query(User).filter(User.id == req.sender_id).first()
            receiver = db.query(User).filter(User.id == req.receiver_id).first()
            print(f"- {sender.username} → {receiver.username}")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_friendships()
