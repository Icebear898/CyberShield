#!/usr/bin/env python3
"""
Script to test new abuse types and create ZIP reports
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, Message, Report, User
from app.services.abuse_detector import AbuseDetector
from app.services.websocket_manager import ConnectionManager
import datetime
import asyncio

async def create_test_abuse_messages():
    db = SessionLocal()
    abuse_detector = AbuseDetector()
    manager = ConnectionManager()
    
    try:
        # Get test users
        alice = db.query(User).filter(User.username == "alice").first()
        bob = db.query(User).filter(User.username == "bob").first()
        charlie = db.query(User).filter(User.username == "charlie").first()
        
        if not all([alice, bob, charlie]):
            print("Test users not found. Please run init_db.py first.")
            return
        
        # Test messages for each abuse type
        test_messages = [
            # CYBERBULLYING
            {"content": "You are so ugly and stupid", "expected_type": "CYBERBULLYING"},
            {"content": "Nobody likes you, you worthless loser", "expected_type": "CYBERBULLYING"},
            
            # SEXUAL_HARASSMENT  
            {"content": "Send me your nude pics baby", "expected_type": "SEXUAL_HARASSMENT"},
            {"content": "Show me your sexy body", "expected_type": "SEXUAL_HARASSMENT"},
            
            # EXPLOITATION
            {"content": "Give me your money or I will scam you", "expected_type": "EXPLOITATION"},
            {"content": "Pay me $100 or I will trick your friends", "expected_type": "EXPLOITATION"},
            
            # BLACKMAIL
            {"content": "I will expose your secrets unless you do what I say", "expected_type": "BLACKMAIL"},
            {"content": "Send me money or else I will share your photos with everyone", "expected_type": "BLACKMAIL"},
            
            # MENTAL_HARASSMENT
            {"content": "Kill yourself, nobody cares about you", "expected_type": "MENTAL_HARASSMENT"},
            {"content": "You should hurt yourself, you are worthless", "expected_type": "MENTAL_HARASSMENT"},
            
            # THREAT
            {"content": "I will kill you and destroy your life", "expected_type": "THREAT"},
            {"content": "I will find you and hurt you badly", "expected_type": "THREAT"},
        ]
        
        print("Creating test messages with new abuse types...")
        
        for i, msg_data in enumerate(test_messages):
            content = msg_data["content"]
            expected_type = msg_data["expected_type"]
            
            # Analyze message
            is_abusive, abuse_score, analysis = abuse_detector.analyze_text(content)
            detected_type = analysis.get("classification", "UNKNOWN")
            
            print(f"\nMessage {i+1}: '{content}'")
            print(f"Expected: {expected_type} | Detected: {detected_type} | Score: {abuse_score}")
            print(f"Match: {'✓' if detected_type == expected_type else '✗'}")
            
            # Create message in database
            message = Message(
                sender_id=bob.id,
                receiver_id=alice.id,
                content=content,
                is_abusive=is_abusive,
                abuse_score=abuse_score,
                abuse_type=detected_type
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # Create report
            if is_abusive:
                # Prepare message data for report generation
                message_data = {
                    "id": message.id,
                    "content": content,
                    "abuse_score": abuse_score,
                    "abuse_type": detected_type,
                    "timestamp": message.created_at.isoformat()
                }
                
                # Generate evidence report (ZIP file)
                try:
                    evidence_path = await manager.generate_evidence_report(
                        bob.id, alice.id, [message_data]
                    )
                    
                    # Create report entry
                    report = Report(
                        user_id=alice.id,
                        reported_user_id=bob.id,
                        message_id=message.id,
                        evidence_file_path=evidence_path,
                        status="pending"
                    )
                    db.add(report)
                    db.commit()
                    
                    print(f"✓ Created ZIP report: {os.path.basename(evidence_path)}")
                    
                except Exception as e:
                    print(f"✗ Error creating report: {e}")
        
        print(f"\n🎉 Test completed! Created {len(test_messages)} messages with reports.")
        print("Each report is now a ZIP file containing:")
        print("  - JSON data with incident details")
        print("  - Screenshot of abusive messages")
        print("  - README file with summary")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

async def main():
    await create_test_abuse_messages()

if __name__ == "__main__":
    asyncio.run(main())
