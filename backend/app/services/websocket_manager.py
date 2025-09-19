from fastapi import WebSocket
from typing import Dict, List
import json
from sqlalchemy.orm import Session
import os
import datetime
import zipfile
import shutil

from app.models.database import get_db, Message, User, Report, BlockedUser
from app.services.screenshot_generator import ScreenshotGenerator

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.abuse_counters: Dict[str, Dict] = {}  # Track abuse counts between users
        
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))
            
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))
            
    async def store_message(self, message_data: dict):
        # Get DB session
        db = next(get_db())
        
        # Create new message
        new_message = Message(
            sender_id=message_data["sender_id"],
            receiver_id=message_data["receiver_id"],
            content=message_data["content"],
            is_abusive=message_data.get("is_abusive", False),
            abuse_score=message_data.get("abuse_score", 0.0),
            abuse_type=message_data.get("abuse_type", None)
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Update message_data with the new ID
        message_data["id"] = new_message.id
        
        return new_message
    
    async def handle_abusive_message(self, message_data: dict, analysis: dict):
        sender_id = message_data["sender_id"]
        receiver_id = message_data["receiver_id"]
        
        # Create a unique key for this sender-receiver pair
        pair_key = f"{sender_id}_{receiver_id}"
        
        # Initialize counter if not exists
        if pair_key not in self.abuse_counters:
            self.abuse_counters[pair_key] = {
                "count": 0,
                "messages": [],
                "last_reset": datetime.datetime.now()
            }
        
        # Add to counter
        self.abuse_counters[pair_key]["count"] += 1
        self.abuse_counters[pair_key]["messages"].append({
            "id": message_data["id"],
            "content": message_data["content"],
            "abuse_score": message_data["abuse_score"],
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Get DB session
        db = next(get_db())
        
        # Create a report for every abusive message for dashboard tracking
        evidence_path = await self.generate_evidence_report(sender_id, receiver_id, [self.abuse_counters[pair_key]["messages"][-1]])
        
        new_report = Report(
            user_id=receiver_id,
            reported_user_id=sender_id,
            message_id=message_data["id"],
            evidence_file_path=evidence_path,
            status="pending"
        )
        db.add(new_report)
        db.commit()
        
        # Check thresholds and take action
        if self.abuse_counters[pair_key]["count"] == 1:
            # First abusive message - send alert
            alert_message = {
                "type": "alert",
                "message": "We've detected potentially abusive content in a recent message. Please be respectful in your communications.",
                "severity": "warning"
            }
            if receiver_id in self.active_connections:
                await self.active_connections[receiver_id].send_text(json.dumps(alert_message))
                
        elif self.abuse_counters[pair_key]["count"] >= 3:
            # Multiple abusive messages - block user
            
            # Block user
            new_block = BlockedUser(
                user_id=receiver_id,
                blocked_user_id=sender_id,
                reason="Multiple instances of abusive messages detected"
            )
            db.add(new_block)
            db.commit()
            
            # Notify receiver
            block_message = {
                "type": "alert",
                "message": f"User has been automatically blocked due to multiple abusive messages. Reports have been generated.",
                "severity": "critical"
            }
            if receiver_id in self.active_connections:
                await self.active_connections[receiver_id].send_text(json.dumps(block_message))
            
            # Reset counter after taking action
            self.abuse_counters[pair_key] = {
                "count": 0,
                "messages": [],
                "last_reset": datetime.datetime.now()
            }
    
    async def generate_evidence_report(self, sender_id: int, receiver_id: int, messages: List[dict]) -> str:
        """Generate a comprehensive evidence report with JSON data and screenshots in a ZIP file"""
        db = next(get_db())
        
        # Get user information
        sender = db.query(User).filter(User.id == sender_id).first()
        receiver = db.query(User).filter(User.id == receiver_id).first()
        
        # Create report directory if it doesn't exist
        reports_dir = os.path.join(os.getcwd(), "reports")
        temp_dir = os.path.join(reports_dir, "temp")
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Create JSON report data
        report_data = {
            "report_info": {
                "generated_at": datetime.datetime.now().isoformat(),
                "report_id": f"CR_{sender_id}_{receiver_id}_{timestamp}",
                "system": "CyberShield v1.0"
            },
            "incident_details": {
                "reporter": {
                    "id": receiver_id,
                    "username": receiver.username,
                    "full_name": receiver.full_name,
                    "email": receiver.email
                },
                "reported_user": {
                    "id": sender_id,
                    "username": sender.username,
                    "full_name": sender.full_name,
                    "email": sender.email
                },
                "incident_type": "Abusive Messaging",
                "severity": "HIGH" if any(msg.get('abuse_score', 0) > 8 for msg in messages) else "MEDIUM"
            },
            "evidence": {
                "total_abusive_messages": len(messages),
                "messages": []
            },
            "analysis": {
                "abuse_types_detected": [],
                "average_abuse_score": 0,
                "highest_abuse_score": 0,
                "keywords_detected": [],
                "patterns_detected": []
            }
        }
        
        # Process messages for JSON report
        total_score = 0
        abuse_types = set()
        all_keywords = set()
        
        for msg in messages:
            abuse_score = msg.get('abuse_score', 0)
            abuse_type = msg.get('abuse_type', 'CYBERBULLYING')
            
            total_score += abuse_score
            abuse_types.add(abuse_type)
            
            message_data = {
                "id": msg.get('id'),
                "timestamp": msg.get('timestamp'),
                "content": msg.get('content'),
                "abuse_score": abuse_score,
                "abuse_type": abuse_type,
                "sender_ip": "192.168.1.100",  # Mock IP for demo
                "evidence_level": "HIGH" if abuse_score > 8 else "MEDIUM" if abuse_score > 6 else "LOW"
            }
            report_data["evidence"]["messages"].append(message_data)
        
        # Calculate analysis data
        if messages:
            report_data["analysis"]["average_abuse_score"] = round(total_score / len(messages), 2)
            report_data["analysis"]["highest_abuse_score"] = max(msg.get('abuse_score', 0) for msg in messages)
            report_data["analysis"]["abuse_types_detected"] = list(abuse_types)
        
        # Save JSON report
        json_filename = f"report_data_{timestamp}.json"
        json_path = os.path.join(temp_dir, json_filename)
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        # 2. Generate screenshot
        screenshot_generator = ScreenshotGenerator()
        screenshot_messages = []
        
        for msg in messages:
            screenshot_messages.append({
                'sender_name': sender.full_name,
                'content': msg.get('content', ''),
                'created_at': msg.get('timestamp', datetime.datetime.now().isoformat()),
                'is_abusive': True,
                'abuse_type': msg.get('abuse_type', 'CYBERBULLYING'),
                'abuse_score': msg.get('abuse_score', 0)
            })
        
        screenshot_path = screenshot_generator.generate_evidence_screenshot(
            screenshot_messages, sender.full_name, receiver.full_name
        )
        
        # Copy screenshot to temp directory
        if screenshot_path and os.path.exists(screenshot_path):
            screenshot_filename = f"chat_evidence_{timestamp}.png"
            temp_screenshot_path = os.path.join(temp_dir, screenshot_filename)
            shutil.copy2(screenshot_path, temp_screenshot_path)
        
        # 3. Create README file
        readme_content = f"""CYBERSHIELD EVIDENCE REPORT
============================

Report ID: CR_{sender_id}_{receiver_id}_{timestamp}
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CONTENTS:
---------
1. report_data_{timestamp}.json - Complete incident data in JSON format
2. chat_evidence_{timestamp}.png - Screenshot of abusive messages
3. README.txt - This file

INCIDENT SUMMARY:
----------------
Reporter: {receiver.full_name} ({receiver.username})
Reported User: {sender.full_name} ({sender.username})
Total Abusive Messages: {len(messages)}
Severity Level: {report_data["incident_details"]["severity"]}

ABUSE TYPES DETECTED:
--------------------
{chr(10).join(f"- {abuse_type}" for abuse_type in abuse_types)}

LEGAL NOTICE:
------------
This report contains evidence of potentially harmful online behavior.
The content has been automatically analyzed by CyberShield's AI system.
This report can be used for educational, safety, or legal purposes.

For questions about this report, contact: support@cybershield.com
"""
        
        readme_path = os.path.join(temp_dir, "README.txt")
        with open(readme_path, "w") as f:
            f.write(readme_content)
        
        # 4. Create ZIP file
        zip_filename = f"cybershield_report_{timestamp}.zip"
        zip_path = os.path.join(reports_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON file
            zipf.write(json_path, json_filename)
            
            # Add screenshot if it exists
            if os.path.exists(temp_screenshot_path):
                zipf.write(temp_screenshot_path, screenshot_filename)
            
            # Add README
            zipf.write(readme_path, "README.txt")
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        return zip_path