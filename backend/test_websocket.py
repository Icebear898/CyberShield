#!/usr/bin/env python3
"""
Simple WebSocket test script to verify WebSocket functionality
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/1"  # Test with user ID 1
    
    try:
        print(f"Attempting to connect to {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established!")
            
            # Send a test message
            test_message = {
                "sender_id": 1,
                "receiver_id": 2,
                "content": "Hello, this is a test message!"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test message sent")
            
            # Wait for response (optional)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Received: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received (this is normal)")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print("🔍 Possible issues:")
        print("   - Backend server not running")
        print("   - WebSocket endpoint not properly configured")
        print("   - Port 8000 not accessible")

if __name__ == "__main__":
    asyncio.run(test_websocket())
