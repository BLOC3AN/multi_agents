"""
SocketIO Server for real-time communication between Streamlit GUI and Multi-Agent System.
"""
import socketio
import eventlet
import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import only what we need for basic functionality
try:
    from graph import create_agent_graph, create_initial_state
    from gui.database.models import (
        init_database, save_chat_message, get_conversation_context,
        create_user, get_user, create_chat_session, get_user_sessions, get_db_config
    )
    from gui.utils.redis_cache import RedisCache
    FULL_FEATURES = True
except ImportError as e:
    logger.warning(f"Some features disabled due to import error: {e}")
    FULL_FEATURES = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and cache if available
if FULL_FEATURES:
    try:
        db_config = get_db_config()
        init_database()
        redis_cache = RedisCache(db_config.redis_client)
        logger.info("✅ Database and cache initialized")
    except Exception as e:
        logger.warning(f"Database/cache initialization failed: {e}")
        FULL_FEATURES = False

# Create SocketIO server
sio = socketio.Server(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Global variables
agent_graph = None
connected_clients: Dict[str, Dict[str, Any]] = {}
startup_time = time.time()


def initialize_agent_graph():
    """Initialize the agent graph."""
    global agent_graph
    if FULL_FEATURES:
        try:
            agent_graph = create_agent_graph()
            logger.info("✅ Agent graph initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent graph: {e}")
    else:
        logger.warning("⚠️ Agent graph disabled - limited features")


# Initialize agent graph
initialize_agent_graph()

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
    """Process user message through the multi-agent system."""
    try:
        message = data.get('message', '')
        user_id = data.get('user_id')
        session_id = data.get('session_id')

        if not agent_graph:
            return {"status": "error", "message": "Agent graph not initialized"}

        logger.info(f"📨 Processing message from {user_id}: {message[:50]}...")

        # Create initial state
        initial_state = create_initial_state(message)

        # Process through agent graph
        result = agent_graph.invoke(initial_state)

        # Extract response
        response_text = result.get('final_response', 'No response generated')

        # Save message to database
        save_chat_message(
            session_id=session_id,
            user_input=message,
            agent_response=response_text,
            processing_data={
                'agent_responses': result.get('agent_responses', {}),
                'metadata': result.get('metadata', {})
            }
        )

        response = {
            "status": "success",
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_responses": result.get('agent_responses', {}),
            "metadata": result.get('metadata', {})
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
