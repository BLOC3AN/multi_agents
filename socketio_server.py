"""
Working SocketIO Server - Simple and Reliable
"""
import socketio
import eventlet
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import multiagents system
try:
    from graph import create_agent_graph, create_initial_state
    MULTIAGENTS_AVAILABLE = True
    logger.info("✅ Multiagents system available")
except ImportError as e:
    MULTIAGENTS_AVAILABLE = False
    logger.warning(f"⚠️ Multiagents system not available: {e}")

# Initialize agent graph if available
agent_graph = None
if MULTIAGENTS_AVAILABLE:
    try:
        agent_graph = create_agent_graph()
        logger.info("✅ Agent graph initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent graph: {e}")
        MULTIAGENTS_AVAILABLE = False

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
    """Process user message through multi-agent system."""
    print(f"📨 MESSAGE: {sid} -> {data}")
    logger.info(f"📨 MESSAGE: {sid} -> {data}")

    try:
        message = data.get('message', '')
        client_info = connected_clients.get(sid, {})
        user_id = client_info.get('user_id', 'anonymous')
        session_id = client_info.get('session_id')

        if not user_id or not client_info.get('authenticated'):
            print(f"❌ User not authenticated: {user_id}")
            sio.emit('processing_error', {
                "error": "User not authenticated"
            }, room=sid)
            return

        if not session_id:
            print(f"❌ No active session for user: {user_id}")
            sio.emit('processing_error', {
                "error": "No active session. Please create a session first."
            }, room=sid)
            return

        print(f"🔍 Processing message for user: {user_id}, session: {session_id}")

        # Send processing started notification
        sio.emit('processing_started', {
            "message": "Processing your request...",
            "timestamp": datetime.now().isoformat()
        }, room=sid)

        if MULTIAGENTS_AVAILABLE and agent_graph:
            # Use multiagents system
            print(f"🤖 Using multiagents system for: {message[:50]}...")

            # Create initial state
            initial_state = create_initial_state(message)

            # Process through agent graph
            result = agent_graph.invoke(initial_state)

            # Extract response
            response_text = result.get('final_result', 'No response generated')

            # Convert agent results to JSON-serializable format
            agent_results = result.get('agent_results', {})
            serializable_agent_results = {}

            for key, value in agent_results.items():
                if hasattr(value, 'to_dict'):
                    serializable_agent_results[key] = value.to_dict()
                elif hasattr(value, '__dict__'):
                    serializable_agent_results[key] = str(value)
                else:
                    serializable_agent_results[key] = value

            response = {
                "status": "success",
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "agent_responses": serializable_agent_results,
                "metadata": result.get('metadata', {})
            }

        else:
            # Fallback to simple echo response
            print(f"⚠️ Using fallback echo response")
            response_text = f"Hello {user_id}! You said: {message}"

            response = {
                "status": "success",
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "note": "Multiagents system not available - using echo response"
            }

        print(f"📤 Sending response: {response['response'][:100]}...")

        # Send response
        sio.emit('message_response', response, room=sid)
        print(f"✅ RESPONSE SENT to {user_id}")
        logger.info(f"✅ RESPONSE SENT to {user_id}")

    except Exception as e:
        print(f"❌ MESSAGE ERROR: {e}")
        logger.error(f"❌ MESSAGE ERROR: {e}")
        sio.emit('processing_error', {"error": str(e)}, room=sid)

@sio.event
def create_session(sid, data):
    """Create a new chat session."""
    print(f"📝 CREATE SESSION: {sid} -> {data}")
    logger.info(f"📝 CREATE SESSION: {sid} -> {data}")

    try:
        client_info = connected_clients.get(sid, {})
        user_id = client_info.get('user_id')

        if not user_id or not client_info.get('authenticated'):
            print(f"❌ User not authenticated: {user_id}")
            sio.emit('error', {
                "error": "User not authenticated"
            }, room=sid)
            return

        session_id = data.get("session_id") or str(uuid.uuid4())

        # Update client info with new session
        connected_clients[sid]["session_id"] = session_id

        # Create session response
        session_data = {
            "session_id": session_id,
            "title": f"Session {session_id[:8]}",
            "created_at": datetime.now().isoformat()
        }

        print(f"✅ Session created: {session_id}")

        # Send success response
        sio.emit('session_created', session_data, room=sid)
        logger.info(f"✅ Session created: {session_id} for user {user_id}")

    except Exception as e:
        print(f"❌ SESSION CREATION ERROR: {e}")
        logger.error(f"❌ SESSION CREATION ERROR: {e}")
        sio.emit('error', {"error": str(e)}, room=sid)

@sio.event
def join_session(sid, data):
    """Join an existing chat session."""
    print(f"🔗 JOIN SESSION: {sid} -> {data}")
    logger.info(f"🔗 JOIN SESSION: {sid} -> {data}")

    try:
        client_info = connected_clients.get(sid, {})
        user_id = client_info.get('user_id')

        if not user_id or not client_info.get('authenticated'):
            print(f"❌ User not authenticated: {user_id}")
            sio.emit('error', {
                "error": "User not authenticated"
            }, room=sid)
            return

        session_id = data.get("session_id")
        if not session_id:
            sio.emit('error', {
                "error": "Session ID is required"
            }, room=sid)
            return

        # Update client info with session
        connected_clients[sid]["session_id"] = session_id

        # Create join response
        session_data = {
            "session_id": session_id,
            "title": f"Session {session_id[:8]}",
            "joined_at": datetime.now().isoformat()
        }

        print(f"✅ Joined session: {session_id}")

        # Send success response
        sio.emit('session_joined', session_data, room=sid)
        logger.info(f"✅ User {user_id} joined session: {session_id}")

    except Exception as e:
        print(f"❌ SESSION JOIN ERROR: {e}")
        logger.error(f"❌ SESSION JOIN ERROR: {e}")
        sio.emit('error', {"error": str(e)}, room=sid)

@sio.event
def health_check(sid):
    """Health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(connected_clients)
    }

if __name__ == "__main__":
    print("🚀 Starting SocketIO server on port 8001...")
    logger.info("🚀 Starting SocketIO server on port 8001...")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8001)), app)
