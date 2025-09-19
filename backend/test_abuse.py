#!/usr/bin/env python3
"""
Script to test abuse detection and create sample reports
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, Message, Report, User
from app.services.abuse_detector import AbuseDetector
import datetime

def create_test_abusive_messages():
    db = SessionLocal()
    abuse_detector = AbuseDetector()
    
    try:
        # Get test users (assuming they exist)
        alice = db.query(User).filter(User.username == "alice").first()
        bob = db.query(User).filter(User.username == "bob").first()
        
        if not alice:
            print("Alice user not found. Creating...")
            alice = User(
                username="alice",
                email="alice@test.com",
                hashed_password="$2b$12$dummy_hash",
                full_name="Alice Johnson",
                is_admin=False,
                is_active=True
            )
            db.add(alice)
            db.commit()
            db.refresh(alice)
        
        if not bob:
            print("Bob user not found. Creating...")
            bob = User(
                username="bob",
                email="bob@test.com", 
                hashed_password="$2b$12$dummy_hash",
                full_name="Bob Smith",
                is_admin=False,
                is_active=True
            )
            db.add(bob)
            db.commit()
            db.refresh(bob)
        
        # Create some abusive messages for testing
        test_messages = [
            "Hey you bitch",
            "You are so stupid",
            "I hate you",
            "Go kill yourself",
            "Hello there"  # Non-abusive
        ]
        
        for content in test_messages:
            is_abusive, abuse_score, analysis = abuse_detector.analyze_text(content)
            
            # Create message
            message = Message(
                sender_id=bob.id,
                receiver_id=alice.id,
                content=content,
                is_abusive=is_abusive,
                abuse_score=abuse_score,
                abuse_type=analysis.get("classification", "GENERAL_ABUSE") if is_abusive else None
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            print(f"Created message: '{content}' - Abusive: {is_abusive}, Score: {abuse_score}")
            
            # Create report if abusive
            if is_abusive:
                report = Report(
                    user_id=alice.id,
                    reported_user_id=bob.id,
                    message_id=message.id,
                    evidence_file_path=f"reports/test_report_{message.id}.txt",
                    status="pending"
                )
                db.add(report)
                db.commit()
                print(f"Created report for message ID: {message.id}")
        
        print("\nTest data created successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_abusive_messages()
