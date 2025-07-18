"""
Working SocketIO Server - Simple and Clean
"""
import socketio
import eventlet
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SocketIO server
sio = socketio.Server(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Global variables
connected_clients = {}

@sio.event
def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"🔌 Client connected: {sid}")
    connected_clients[sid] = {
        "connected_at": datetime.utcnow(),
        "user_id": None,
        "session_id": None
    }

@sio.event
def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"🔌 Client disconnected: {sid}")
    if sid in connected_clients:
        del connected_clients[sid]

@sio.event
def user_login(sid, data):
    """Handle user login."""
    try:
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        if sid in connected_clients:
            connected_clients[sid]['user_id'] = user_id
            connected_clients[sid]['session_id'] = session_id
        
        logger.info(f"✅ User logged in: {user_id} (session: {session_id})")
        return {"status": "success", "message": "Login successful"}
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return {"status": "error", "message": str(e)}

@sio.event
def process_message(sid, data):
    """Process user message."""
    try:
        message = data.get('message', '')
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        logger.info(f"📨 Processing message from {user_id}: {message[:50]}...")
        
        # Simple echo response for testing
        response = {
            "status": "success",
            "response": f"Echo: {message}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
    except Exception as e:
        logger.error(f"❌ Message processing error: {e}")
        return {"status": "error", "message": str(e)}

@sio.event
def health_check(sid):
    """Health check via SocketIO."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "connected_clients": len(connected_clients)
    }

# Create WSGI app
app = socketio.WSGIApp(sio)

if __name__ == "__main__":
    logger.info("🚀 Starting SocketIO server on port 8001...")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8001)), app)
