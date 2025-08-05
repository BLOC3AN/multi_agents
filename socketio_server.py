"""
Working SocketIO Server - Simple and Reliable
"""
import socketio
import eventlet
import logging
import time
import uuid
import sys
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced logging
from src.utils.logger import socketio_logger, system_logger

# Import database models for saving messages
try:
    from src.database.models import get_db_config, ChatMessage, ChatSession, User
    DATABASE_AVAILABLE = True
    system_logger.info("✅ Database models imported successfully")
except ImportError as e:
    DATABASE_AVAILABLE = False
    system_logger.warning(f"⚠️ Database models not available: {e}")

# Try to import multiagents system
try:
    from graph import create_agent_graph, create_initial_state
    MULTIAGENTS_AVAILABLE = True
    system_logger.info("✅ Multiagents system available")
except ImportError as e:
    MULTIAGENTS_AVAILABLE = False
    system_logger.warning(f"⚠️ Multiagents system not available: {e}")

# Initialize agent graph if available
agent_graph = None
if MULTIAGENTS_AVAILABLE:
    try:
        agent_graph = create_agent_graph()
        system_logger.info("✅ Agent graph initialized successfully")
    except Exception as e:
        system_logger.error(f"❌ Failed to initialize agent graph: {e}")
        MULTIAGENTS_AVAILABLE = False

# Create SocketIO server
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)

# Store connected clients
connected_clients: Dict[str, Dict[str, Any]] = {}

# Initialize database connection
db_config = None
if DATABASE_AVAILABLE:
    try:
        db_config = get_db_config()
        system_logger.info("✅ Database connection initialized")
    except Exception as e:
        system_logger.error(f"❌ Failed to initialize database: {e}")
        DATABASE_AVAILABLE = False


def save_message_to_db(user_id: str, session_id: str, user_input: str, agent_response: str,
                      processing_time: float = 0, success: bool = True, metadata: Dict = None):
    """Save chat message to MongoDB."""
    if not DATABASE_AVAILABLE or not db_config:
        return

    try:
        # Create message document
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            user_input=user_input,
            agent_response=agent_response,
            processing_time=processing_time,
            success=success,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        # Save to MongoDB
        message_doc = message.to_dict()
        db_config.messages.insert_one(message_doc)

        # Update session message count
        db_config.sessions.update_one(
            {"session_id": session_id},
            {
                "$inc": {"total_messages": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        system_logger.info(f"✅ Message saved to database: {message.message_id}")

    except Exception as e:
        system_logger.error(f"❌ Failed to save message to database: {e}")


def ensure_user_exists(user_id: str, display_name: str = None, email: str = None):
    """Ensure user exists in database."""
    if not DATABASE_AVAILABLE or not db_config:
        return

    try:
        # Check if user exists in users collection
        existing_user = db_config.users.find_one({"user_id": user_id})

        # Also check if user exists in admins collection (to avoid duplicates)
        existing_admin = db_config.admins.find_one({"admin_id": user_id})

        if not existing_user and not existing_admin:
            # Create new user only if not exists in both collections
            user = User(
                user_id=user_id,
                display_name=display_name or user_id,
                email=email,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            user_doc = user.to_dict()
            db_config.users.insert_one(user_doc)
            system_logger.info(f"✅ New user created: {user_id}")
        elif existing_user:
            # Update last login for regular user
            db_config.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        elif existing_admin:
            # Update last login for admin user
            db_config.admins.update_one(
                {"admin_id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            system_logger.info(f"✅ Admin user login updated: {user_id}")

    except Exception as e:
        system_logger.error(f"❌ Failed to ensure user exists: {e}")


def ensure_session_exists(session_id: str, user_id: str):
    """Ensure session exists in database."""
    if not DATABASE_AVAILABLE or not db_config:
        return

    try:
        # Check if session exists
        existing_session = db_config.sessions.find_one({"session_id": session_id})

        if not existing_session:
            # Create new session
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=f"Session {session_id[:8]}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                total_messages=0,
                is_active=True
            )

            session_doc = session.to_dict()
            db_config.sessions.insert_one(session_doc)
            system_logger.info(f"✅ New session created: {session_id}")

    except Exception as e:
        system_logger.error(f"❌ Failed to ensure session exists: {e}")


def ensure_session_exists_with_name(session_id: str, user_id: str, session_name: str):
    """Ensure session exists in database with custom name."""
    if not DATABASE_AVAILABLE or not db_config:
        return

    try:
        # Check if session exists
        existing_session = db_config.sessions.find_one({"session_id": session_id})

        if not existing_session:
            # Create new session with custom name
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=session_name,  # Use custom session name
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                total_messages=0,
                is_active=True
            )

            session_doc = session.to_dict()
            db_config.sessions.insert_one(session_doc)
            system_logger.info(f"✅ New session created: {session_id} with name: '{session_name}'")
        else:
            # Update existing session name if different
            if existing_session.get('title') != session_name:
                db_config.sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {"title": session_name, "updated_at": datetime.utcnow()}}
                )
                system_logger.info(f"✅ Session name updated: {session_id} -> '{session_name}'")

    except Exception as e:
        system_logger.error(f"❌ Failed to ensure session exists with name: {e}")

@sio.event
def connect(sid, environ):
    """Handle client connection."""
    socketio_logger.log_socket_event("connect", data={"sid": sid})
    connected_clients[sid] = {
        'connected_at': datetime.now(),
        'user_id': None,
        'session_id': None,
        'authenticated': False
    }

@sio.event
def disconnect(sid):
    """Handle client disconnection."""
    user_id = connected_clients.get(sid, {}).get('user_id')
    socketio_logger.log_socket_event("disconnect", user_id=user_id, data={"sid": sid})
    if sid in connected_clients:
        del connected_clients[sid]

@sio.event
def authenticate(sid, data):
    """Handle user authentication."""
    print(f"🔐 AUTH: {sid} -> {data}")
    system_logger.info(f"🔐 AUTH: {sid} -> {data}")
    
    try:
        user_id = data.get('user_id', 'anonymous')
        display_name = data.get('display_name', user_id)
        email = data.get('email', f'{user_id}@example.com')
        
        # Ensure user exists in database
        ensure_user_exists(user_id, display_name, email)

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
        system_logger.info(f"✅ AUTH SUCCESS: {user_id}")
        
    except Exception as e:
        print(f"❌ AUTH ERROR: {e}")
        system_logger.error(f"❌ AUTH ERROR: {e}")
        sio.emit('auth_error', {"error": str(e)}, room=sid)

@sio.event
def process_message(sid, data):
    """Process user message through multi-agent system."""
    print(f"📨 MESSAGE: {sid} -> {data}")
    system_logger.info(f"📨 MESSAGE: {sid} -> {data}")

    try:
        message = data.get('message', '')
        client_info = connected_clients.get(sid, {})
        user_id = client_info.get('user_id', 'anonymous')

        # Get session_id from message data first, fallback to client_info
        session_id = data.get('session_id') or client_info.get('session_id')

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

        # Update client_info with current session_id if it's different
        if client_info.get('session_id') != session_id:
            connected_clients[sid]['session_id'] = session_id
            print(f"🔄 Updated session for client {sid}: {session_id}")

        print(f"🔍 Processing message for user: {user_id}, session: {session_id}")

        # Ensure session exists in database
        ensure_session_exists(session_id, user_id)

        # Send processing started notification
        sio.emit('processing_started', {
            "message": "Processing your request...",
            "timestamp": datetime.now().isoformat()
        }, room=sid)

        # Track processing time
        start_time = time.time()

        if MULTIAGENTS_AVAILABLE and agent_graph:
            # Use simple conversation system
            print(f"🤖 Using conversation agent for: {message[:50]}...")

            try:
                # Use the simple conversation system
                from src.core.simple_graph import process_user_input
                result = process_user_input(message, user_id=user_id, session_id=session_id)

                # Extract response
                response_text = result.get('result', 'No response generated')

                response = {
                    "status": "success",
                    "response": response_text,
                    "user_input": message,  # Include original user input
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "session_id": session_id,
                    "agent_responses": {"conversation": {"result": response_text}},
                    "metadata": result.get('metadata', {}),
                    "processing_mode": "single_agent"
                }
            except Exception as e:
                print(f"❌ Error in conversation agent: {e}")
                response = {
                    "status": "error",
                    "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                    "user_input": message,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "session_id": session_id,
                    "processing_mode": "error"
                }

        else:
            # Fallback to simple echo response
            print(f"⚠️ Using fallback echo response")
            response_text = f"Hello {user_id}! You said: {message}"

            response = {
                "status": "success",
                "response": response_text,
                "user_input": message,  # Include original user input
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "processing_mode": "fallback",
                "note": "Multiagents system not available - using echo response"
            }

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Save message to database
        save_message_to_db(
            user_id=user_id,
            session_id=session_id,
            user_input=message,
            agent_response=response.get('response', ''),
            processing_time=processing_time,
            success=response.get('status') == 'success',
            metadata={
                'agent_responses': response.get('agent_responses', {}),
                'metadata': response.get('metadata', {}),
                'processing_mode': response.get('processing_mode', 'unknown')
            }
        )

        print(f"📤 Sending response: {response['response'][:100]}...")

        # Send response
        sio.emit('message_response', response, room=sid)
        print(f"✅ RESPONSE SENT to {user_id}")
        system_logger.info(f"✅ RESPONSE SENT to {user_id}")

    except Exception as e:
        print(f"❌ MESSAGE ERROR: {e}")
        system_logger.error(f"❌ MESSAGE ERROR: {e}")
        sio.emit('processing_error', {"error": str(e)}, room=sid)

@sio.event
def create_session(sid, data):
    """Create a new chat session."""
    print(f"📝 CREATE SESSION: {sid} -> {data}")
    system_logger.info(f"📝 CREATE SESSION: {sid} -> {data}")

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

        # Get session name from data, fallback to default
        session_name = data.get("session_name")
        if not session_name or not session_name.strip():
            session_name = f"Session {session_id[:8]}"
        else:
            session_name = session_name.strip()

        print(f"📝 Creating session with name: '{session_name}'")

        # Ensure session exists in database with custom name
        ensure_session_exists_with_name(session_id, user_id, session_name)

        # Update client info with new session
        connected_clients[sid]["session_id"] = session_id

        # Create session response
        session_data = {
            "session_id": session_id,
            "session_name": session_name,  # Use session_name instead of title
            "title": session_name,  # Keep title for backward compatibility
            "created_at": datetime.now().isoformat()
        }

        print(f"✅ Session created: {session_id} with name: '{session_name}'")

        # Send success response
        sio.emit('session_created', session_data, room=sid)
        system_logger.info(f"✅ Session created: {session_id} with name '{session_name}' for user {user_id}")

    except Exception as e:
        print(f"❌ SESSION CREATION ERROR: {e}")
        system_logger.error(f"❌ SESSION CREATION ERROR: {e}")
        sio.emit('error', {"error": str(e)}, room=sid)

@sio.event
def join_session(sid, data):
    """Join an existing chat session."""
    print(f"🔗 JOIN SESSION: {sid} -> {data}")
    system_logger.info(f"🔗 JOIN SESSION: {sid} -> {data}")

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

        # Try to get session name from database
        session_name = f"Session {session_id[:8]}"  # Default fallback
        if DATABASE_AVAILABLE and db_config:
            try:
                existing_session = db_config.sessions.find_one({"session_id": session_id})
                if existing_session and existing_session.get('title'):
                    session_name = existing_session['title']
            except Exception as e:
                print(f"⚠️ Could not fetch session name from DB: {e}")

        # Create join response
        session_data = {
            "session_id": session_id,
            "session_name": session_name,  # Use actual session name
            "title": session_name,  # Keep title for backward compatibility
            "joined_at": datetime.now().isoformat()
        }

        print(f"✅ Joined session: {session_id} with name: '{session_name}'")

        # Send success response
        sio.emit('session_joined', session_data, room=sid)
        system_logger.info(f"✅ User {user_id} joined session: {session_id}")

    except Exception as e:
        print(f"❌ SESSION JOIN ERROR: {e}")
        system_logger.error(f"❌ SESSION JOIN ERROR: {e}")
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
    system_logger.info("🚀 Starting SocketIO server on port 8001...")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8001)), app)
