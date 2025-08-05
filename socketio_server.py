"""
Working SocketIO Server - Optimized Version
Simple, reliable, and high-performance with async/await, caching, and connection pooling
"""
import socketio
import eventlet
import time
import uuid
import sys
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Global cache for lazy loading and performance
_cache: Dict[str, Any] = {}
connected_clients: Dict[str, Dict[str, Any]] = {}

class OptimizedSocketIOServer:
    """Optimized SocketIO server with lazy loading and caching."""
    
    def __init__(self):
        self.sio = socketio.AsyncServer(cors_allowed_origins="*")
        self.app = socketio.ASGIApp(self.sio)
        self._setup_event_handlers()
    
    @lru_cache(maxsize=1)
    def get_loggers(self):
        """Lazy load optimized loggers with caching."""
        try:
            from src.utils.optimized_logger import get_socketio_logger, get_system_logger
            return get_socketio_logger(), get_system_logger()
        except ImportError:
            # Fallback to original loggers
            try:
                from src.utils.logger import socketio_logger, system_logger
                return socketio_logger, system_logger
            except ImportError as e:
                print(f"⚠️ Logger not available: {e}")
                return None, None
    
    @lru_cache(maxsize=1)
    def get_database_connection(self):
        """Get optimized database connection."""
        try:
            from src.database.connection_pool import get_pooled_db_connection
            return get_pooled_db_connection()
        except ImportError:
            try:
                from src.database.models import get_db_config
                return get_db_config()
            except ImportError as e:
                print(f"⚠️ Database not available: {e}")
                return None
    
    @lru_cache(maxsize=1)
    def get_agent_graph(self):
        """Get cached agent graph."""
        try:
            from src.core.agent_cache import get_cached_agent_graph
            graph = get_cached_agent_graph()
            if graph:
                socketio_logger, system_logger = self.get_loggers()
                if system_logger:
                    system_logger.info("✅ Cached agent graph loaded successfully")
                return graph
        except ImportError:
            pass
        
        try:
            from src.core.simple_graph import create_simple_agent_graph
            graph = create_simple_agent_graph()
            socketio_logger, system_logger = self.get_loggers()
            if system_logger:
                system_logger.info("✅ Agent graph created successfully")
            return graph
        except ImportError as e:
            print(f"⚠️ Agent system not available: {e}")
            return None
    
    async def ensure_user_exists_async(self, user_id: str, display_name: str = None, email: str = None):
        """Async version of ensure_user_exists."""
        try:
            from src.database.connection_pool import ensure_user_exists_optimized
            await asyncio.get_event_loop().run_in_executor(
                None, ensure_user_exists_optimized, user_id, display_name, email
            )
        except ImportError:
            # Fallback to sync version
            db_config = self.get_database_connection()
            if not db_config:
                return
            
            await asyncio.get_event_loop().run_in_executor(
                None, self._ensure_user_exists_fallback, user_id, display_name, email, db_config
            )
    
    def _ensure_user_exists_fallback(self, user_id: str, display_name: str, email: str, db_config):
        """Fallback sync version of ensure_user_exists."""
        try:
            from src.database.models import User
            
            existing_user = db_config.users.find_one({"user_id": user_id})
            existing_admin = db_config.admins.find_one({"admin_id": user_id})
            
            if not existing_user and not existing_admin:
                user = User(
                    user_id=user_id,
                    display_name=display_name or user_id,
                    email=email,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                user_doc = user.to_dict()
                db_config.users.insert_one(user_doc)
                print(f"✅ New user created: {user_id}")
            elif existing_user:
                db_config.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_login": datetime.now(timezone.utc)}}
                )
            elif existing_admin:
                db_config.admins.update_one(
                    {"admin_id": user_id},
                    {"$set": {"last_login": datetime.now(timezone.utc)}}
                )
        except Exception as e:
            print(f"❌ Failed to ensure user exists: {e}")
    
    async def ensure_session_exists_async(self, session_id: str, user_id: str):
        """Async version of ensure_session_exists."""
        try:
            from src.database.connection_pool import ensure_session_exists_optimized
            await asyncio.get_event_loop().run_in_executor(
                None, ensure_session_exists_optimized, session_id, user_id
            )
        except ImportError:
            # Fallback to sync version
            db_config = self.get_database_connection()
            if not db_config:
                return
            
            await asyncio.get_event_loop().run_in_executor(
                None, self._ensure_session_exists_fallback, session_id, user_id, db_config
            )
    
    def _ensure_session_exists_fallback(self, session_id: str, user_id: str, db_config):
        """Fallback sync version of ensure_session_exists."""
        try:
            from src.database.models import ChatSession
            
            existing_session = db_config.sessions.find_one({"session_id": session_id})
            if not existing_session:
                session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    title=f"Session {session_id[:8]}",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    total_messages=0,
                    is_active=True
                )
                session_doc = session.to_dict()
                db_config.sessions.insert_one(session_doc)
                print(f"✅ New session created: {session_id}")
        except Exception as e:
            print(f"❌ Failed to ensure session exists: {e}")
    
    async def save_message_to_db_async(self, user_id: str, session_id: str, user_input: str, 
                                     agent_response: str, processing_time: float = 0, 
                                     success: bool = True, metadata: Dict = None):
        """Async version of save_message_to_db."""
        db_config = self.get_database_connection()
        if not db_config:
            return
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._save_message_to_db_sync, 
            user_id, session_id, user_input, agent_response, 
            processing_time, success, metadata, db_config
        )
    
    def _save_message_to_db_sync(self, user_id: str, session_id: str, user_input: str,
                               agent_response: str, processing_time: float, success: bool,
                               metadata: Dict, db_config):
        """Sync version of save_message_to_db."""
        try:
            from src.database.models import ChatMessage
            
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                user_input=user_input,
                agent_response=agent_response,
                processing_time=processing_time,
                success=success,
                metadata=metadata or {},
                created_at=datetime.now(timezone.utc)
            )
            
            message_doc = message.to_dict()
            db_config.messages.insert_one(message_doc)
            
            db_config.sessions.update_one(
                {"session_id": session_id},
                {
                    "$inc": {"total_messages": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            
            socketio_logger, system_logger = self.get_loggers()
            if system_logger:
                system_logger.info(f"✅ Message saved to database: {message.message_id}")
        except Exception as e:
            print(f"❌ Failed to save message to database: {e}")
    
    def _setup_event_handlers(self):
        """Setup all event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            socketio_logger, _ = self.get_loggers()
            if socketio_logger:
                socketio_logger.log_socket_event("connect", data={"sid": sid})
            
            connected_clients[sid] = {
                'connected_at': datetime.now(timezone.utc),
                'user_id': None,
                'session_id': None,
                'authenticated': False
            }
            print(f"🔗 Client connected: {sid}")
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            user_id = connected_clients.get(sid, {}).get('user_id')
            socketio_logger, _ = self.get_loggers()
            if socketio_logger:
                socketio_logger.log_socket_event("disconnect", user_id=user_id, data={"sid": sid})
            
            if sid in connected_clients:
                del connected_clients[sid]
            print(f"🔌 Client disconnected: {sid}")
        
        @self.sio.event
        async def authenticate(sid, data):
            """Handle user authentication."""
            socketio_logger, system_logger = self.get_loggers()
            print(f"🔐 AUTH: {sid} -> {data}")
            if system_logger:
                system_logger.info(f"🔐 AUTH: {sid} -> {data}")
            
            try:
                user_id = data.get('user_id', 'anonymous')
                display_name = data.get('display_name', user_id)
                email = data.get('email', f'{user_id}@example.com')
                
                # Ensure user exists in database (async)
                await self.ensure_user_exists_async(user_id, display_name, email)
                
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
                
                await self.sio.emit('auth_success', response, room=sid)
                print(f"✅ AUTH SUCCESS: {user_id}")
                if system_logger:
                    system_logger.info(f"✅ AUTH SUCCESS: {user_id}")
                
            except Exception as e:
                print(f"❌ AUTH ERROR: {e}")
                if system_logger:
                    system_logger.error(f"❌ AUTH ERROR: {e}")
                await self.sio.emit('auth_error', {"error": str(e)}, room=sid)

        @self.sio.event
        async def process_message(sid, data):
            """Process user message through multi-agent system with async/await."""
            socketio_logger, system_logger = self.get_loggers()
            print(f"📨 MESSAGE: {sid} -> {data}")
            if system_logger:
                system_logger.info(f"📨 MESSAGE: {sid} -> {data}")

            try:
                message = data.get('message', '').strip()
                if not message:
                    print(f"❌ Empty message from {sid}")
                    await self.sio.emit('processing_error', {
                        "error": "Message cannot be empty"
                    }, room=sid)
                    return

                # Get client info
                client_info = connected_clients.get(sid, {})
                user_id = client_info.get('user_id', 'anonymous')
                session_id = data.get('session_id') or client_info.get('session_id')

                if not user_id or not client_info.get('authenticated'):
                    print(f"❌ User not authenticated: {user_id}")
                    await self.sio.emit('processing_error', {
                        "error": "User not authenticated"
                    }, room=sid)
                    return

                if not session_id:
                    print(f"❌ No active session for user: {user_id}")
                    await self.sio.emit('processing_error', {
                        "error": "No active session. Please create a session first."
                    }, room=sid)
                    return

                # Update client_info with current session_id if different
                if client_info.get('session_id') != session_id:
                    connected_clients[sid]['session_id'] = session_id
                    print(f"🔄 Updated session for client {sid}: {session_id}")

                print(f"🔍 Processing message for user: {user_id}, session: {session_id}")

                # Ensure session exists in database (async)
                await self.ensure_session_exists_async(session_id, user_id)

                # Send processing started notification
                await self.sio.emit('processing_started', {
                    "message": "Processing your request...",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, room=sid)

                # Track processing time
                start_time = time.time()

                # Get agent graph
                agent_graph = self.get_agent_graph()

                if agent_graph:
                    print(f"🤖 Using conversation agent for: {message[:50]}...")

                    try:
                        # Process with agent system (async)
                        from src.core.simple_graph import process_user_input
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, process_user_input, message, user_id, session_id
                        )

                        response_text = result.get('result', 'No response generated')

                        response = {
                            "status": "success",
                            "response": response_text,
                            "user_input": message,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "user_id": user_id,
                            "session_id": session_id,
                            "agent_responses": {"conversation": {"result": response_text}},
                            "metadata": result.get('metadata', {}),
                            "processing_mode": "single_agent_optimized"
                        }
                    except Exception as e:
                        print(f"❌ Error in conversation agent: {e}")
                        response = {
                            "status": "error",
                            "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                            "user_input": message,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
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
                        "user_input": message,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "user_id": user_id,
                        "session_id": session_id,
                        "processing_mode": "fallback",
                        "note": "Agent system not available - using echo response"
                    }

                # Calculate processing time
                processing_time = (time.time() - start_time) * 1000

                # Save message to database (async)
                await self.save_message_to_db_async(
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
                await self.sio.emit('message_response', response, room=sid)
                print(f"✅ RESPONSE SENT to {user_id}")
                if system_logger:
                    system_logger.info(f"✅ RESPONSE SENT to {user_id}")

            except Exception as e:
                print(f"❌ MESSAGE PROCESSING ERROR: {e}")
                if system_logger:
                    system_logger.error(f"❌ MESSAGE PROCESSING ERROR: {e}")
                await self.sio.emit('processing_error', {
                    "error": f"Processing failed: {str(e)}"
                }, room=sid)

        @self.sio.event
        async def health_check(sid):
            """Health check with cache statistics."""
            try:
                from src.core.agent_cache import get_agent_cache_manager
                cache_stats = get_agent_cache_manager().get_cache_stats()
            except ImportError:
                cache_stats = {}

            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connected_clients": len(connected_clients),
                "version": "optimized-2.0.0",
                "cache_stats": cache_stats
            }

# Create optimized server instance
optimized_server = OptimizedSocketIOServer()
sio = optimized_server.sio
app = optimized_server.app

if __name__ == "__main__":
    print("🚀 Starting Optimized SocketIO server on port 8001...")
    socketio_logger, system_logger = optimized_server.get_loggers()
    if system_logger:
        system_logger.info("🚀 Starting Optimized SocketIO server on port 8001...")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8001)), app)
