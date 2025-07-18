"""
Working SocketIO Server - Simple and Reliable
"""
import socketio
import eventlet
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SocketIO server
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)

# Store connected clients
connected_clients: Dict[str, Dict[str, Any]] = {}

@sio.event
def connect(sid, environ):
    """Handle client connection."""
    print(f"🔌 Client connected: {sid}")
    logger.info(f"🔌 Client connected: {sid}")
    connected_clients[sid] = {
        'connected_at': datetime.now(),
        'user_id': None,
        'session_id': None,
        'authenticated': False
    }

@sio.event
def disconnect(sid):
    """Handle client disconnection."""
    print(f"🔌 Client disconnected: {sid}")
    logger.info(f"🔌 Client disconnected: {sid}")
    if sid in connected_clients:
        del connected_clients[sid]

@sio.event
def authenticate(sid, data):
    """Handle user authentication."""
    print(f"🔐 AUTH: {sid} -> {data}")
    logger.info(f"🔐 AUTH: {sid} -> {data}")
    
    try:
        user_id = data.get('user_id', 'anonymous')
        display_name = data.get('display_name', user_id)
        email = data.get('email', f'{user_id}@example.com')
        
        # Update client info
        if sid in connected_clients:
            connected_clients[sid].update({
                'user_id': user_id,
                'display_name': display_name,
                'email': email,
                'authenticated': True,
                'session_id': f"session_{user_id}_{int(time.time())}"
            })
            print(f"✅ Updated client: {connected_clients[sid]}")
        
        # Send success response
        response = {
            "user_id": user_id,
            "display_name": display_name,
            "email": email,
            "message": "Authentication successful"
        }
        
        sio.emit('auth_success', response, room=sid)
        print(f"✅ AUTH SUCCESS: {user_id}")
        logger.info(f"✅ AUTH SUCCESS: {user_id}")
        
    except Exception as e:
        print(f"❌ AUTH ERROR: {e}")
        logger.error(f"❌ AUTH ERROR: {e}")
        sio.emit('auth_error', {"error": str(e)}, room=sid)

@sio.event
def process_message(sid, data):
    """Process user message."""
    print(f"📨 MESSAGE: {sid} -> {data}")
    logger.info(f"📨 MESSAGE: {sid} -> {data}")
    
    try:
        message = data.get('message', '')
        client_info = connected_clients.get(sid, {})
        user_id = client_info.get('user_id', 'anonymous')
        
        print(f"🔍 Processing for user: {user_id}")
        
        # Simple echo response
        response_text = f"Hello {user_id}! You said: {message}"
        
        response = {
            "status": "success",
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        print(f"📤 Sending response: {response}")
        
        # Send response
        sio.emit('message_response', response, room=sid)
        print(f"✅ RESPONSE SENT: {response_text}")
        logger.info(f"✅ RESPONSE SENT: {response_text}")
        
    except Exception as e:
        print(f"❌ MESSAGE ERROR: {e}")
        logger.error(f"❌ MESSAGE ERROR: {e}")
        sio.emit('processing_error', {"error": str(e)}, room=sid)

@sio.event
def health_check(sid):
    """Health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(connected_clients)
    }

if __name__ == "__main__":
    print("🚀 Starting Working SocketIO server on port 8002...")
    logger.info("🚀 Starting Working SocketIO server on port 8002...")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8002)), app)
