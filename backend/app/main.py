from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import os
import json
from typing import List, Dict

from app.models.database import get_db, create_tables
from app.routes import auth, users, messages, reports, dashboard, friends
from app.services.websocket_manager import ConnectionManager
from app.services.abuse_detector import AbuseDetector

# Initialize FastAPI app
app = FastAPI(title="CyberShield API", description="API for cyberbullying detection and auto-response system")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
create_tables()

# Initialize WebSocket connection manager
manager = ConnectionManager()

# Initialize AI abuse detector
abuse_detector = AbuseDetector()

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(friends.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CyberShield API - Protecting users from cyberbullying"}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Check message for abusive content
            is_abusive, abuse_score, analysis = abuse_detector.analyze_text(message_data["content"])
            message_data["is_abusive"] = is_abusive
            message_data["abuse_score"] = abuse_score
            message_data["abuse_type"] = analysis.get("classification") if is_abusive else None
            
            # Store message in database (handled by the manager)
            await manager.store_message(message_data)
            
            # If abusive, handle according to threshold logic
            if is_abusive:
                await manager.handle_abusive_message(message_data, analysis)
            
            # Send message to intended recipient
            await manager.send_personal_message(message_data, message_data["receiver_id"])
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)