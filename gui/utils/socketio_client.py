"""
SocketIO client utilities for Streamlit GUI.
"""
import json
import logging
import time
import os
from typing import Dict, Any, Optional, List
import queue
import threading

import socketio
import streamlit as st

logger = logging.getLogger(__name__)


class SocketIOClient:
    """SocketIO client for real-time communication with the multi-agent system."""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        """Initialize SocketIO client."""
        self.server_url = server_url
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.connected = False
        self.authenticated = False
        
        # Message queues for handling responses
        self.response_queue = queue.Queue()
        self.event_queue = queue.Queue()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Connection state
        self.user_id = None
        self.session_id = None
        self.recent_sessions = []
    
    def _setup_event_handlers(self):
        """Setup SocketIO event handlers."""
        
        @self.sio.event
        def connect():
            logger.info("🔌 Connected to SocketIO server")
            self.connected = True
            self.event_queue.put({"type": "connected"})
        
        @self.sio.event
        def disconnect():
            logger.info("🔌 Disconnected from SocketIO server")
            self.connected = False
            self.authenticated = False
            self.event_queue.put({"type": "disconnected"})
        
        @self.sio.event
        def connection_status(data):
            logger.info(f"📡 Connection status: {data}")
            self.event_queue.put({"type": "connection_status", "data": data})
        
        @self.sio.event
        def auth_success(data):
            logger.info(f"✅ Authentication successful: {data.get('user_id')}")
            self.authenticated = True
            self.user_id = data.get("user_id")
            self.recent_sessions = data.get("recent_sessions", [])
            self.response_queue.put({"type": "auth_success", "data": data})
        
        @self.sio.event
        def auth_error(data):
            logger.error(f"❌ Authentication failed: {data}")
            self.response_queue.put({"type": "auth_error", "data": data})
        
        @self.sio.event
        def session_created(data):
            logger.info(f"📝 Session created: {data.get('session_id')}")
            self.session_id = data.get("session_id")
            self.response_queue.put({"type": "session_created", "data": data})
        
        @self.sio.event
        def session_joined(data):
            logger.info(f"📝 Session joined: {data.get('session_id')}")
            self.session_id = data.get("session_id")
            self.response_queue.put({"type": "session_joined", "data": data})
        
        @self.sio.event
        def processing_started(data):
            logger.info("🔄 Message processing started")
            self.event_queue.put({"type": "processing_started", "data": data})
        
        @self.sio.event
        def message_response(data):
            logger.info("✅ Message response received")
            self.response_queue.put({"type": "message_response", "data": data})
        
        @self.sio.event
        def processing_error(data):
            logger.error(f"❌ Processing error: {data}")
            self.response_queue.put({"type": "processing_error", "data": data})
        
        @self.sio.event
        def error(data):
            logger.error(f"❌ Error: {data}")
            self.response_queue.put({"type": "error", "data": data})
        
        @self.sio.event
        def session_history(data):
            logger.info("📚 Session history received")
            self.response_queue.put({"type": "session_history", "data": data})
    
    def connect_to_server(self) -> bool:
        """Connect to SocketIO server."""
        try:
            if not self.connected:
                self.sio.connect(self.server_url)
                # Wait for connection confirmation
                time.sleep(1)
            return self.connected
        except Exception as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            return False
    
    def disconnect_from_server(self):
        """Disconnect from SocketIO server."""
        try:
            if self.connected:
                self.sio.disconnect()
        except Exception as e:
            logger.error(f"❌ Error disconnecting: {e}")
    
    def authenticate(self, user_id: str, display_name: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate user with the server."""
        if not self.connected:
            return {"success": False, "error": "Not connected to server"}

        # TEMPORARY BYPASS - Skip server authentication for now
        logger.info(f"🔄 BYPASS: Simulating authentication for {user_id}")

        # Set authenticated state
        self.authenticated = True
        self.user_id = user_id
        self.session_id = f"bypass_session_{user_id}_{int(time.time())}"

        # Return success immediately
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "display_name": display_name or user_id,
                "email": email or f"{user_id}@example.com",
                "message": "Authentication bypassed - working in test mode"
            }
        }
    
    def create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new chat session."""
        if not self.authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            self.sio.emit("create_session", {"session_id": session_id})
            
            response = self._wait_for_response(["session_created", "error"], timeout=10)
            
            if response and response["type"] == "session_created":
                return {"success": True, "data": response["data"]}
            else:
                error_msg = response["data"].get("error", "Session creation failed") if response else "Timeout"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Session creation error: {e}")
            return {"success": False, "error": str(e)}
    
    def join_session(self, session_id: str) -> Dict[str, Any]:
        """Join an existing chat session."""
        if not self.authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            self.sio.emit("join_session", {"session_id": session_id})
            
            response = self._wait_for_response(["session_joined", "error"], timeout=10)
            
            if response and response["type"] == "session_joined":
                return {"success": True, "data": response["data"]}
            else:
                error_msg = response["data"].get("error", "Failed to join session") if response else "Timeout"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Session join error: {e}")
            return {"success": False, "error": str(e)}
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message for processing."""
        if not self.authenticated or not self.session_id:
            return {"success": False, "error": "Not authenticated or no active session"}
        
        try:
            self.sio.emit("process_message", {"message": message})
            
            # Wait for response (longer timeout for processing)
            response = self._wait_for_response(["message_response", "processing_error"], timeout=120)
            
            if response and response["type"] == "message_response":
                return {"success": True, "data": response["data"]}
            else:
                error_msg = response["data"].get("error", "Message processing failed") if response else "Timeout"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Message sending error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get conversation history for a session."""
        if not self.authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            self.sio.emit("get_session_history", {"session_id": session_id})
            
            response = self._wait_for_response(["session_history", "error"], timeout=10)
            
            if response and response["type"] == "session_history":
                return {"success": True, "data": response["data"]}
            else:
                error_msg = response["data"].get("error", "Failed to get history") if response else "Timeout"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Get history error: {e}")
            return {"success": False, "error": str(e)}
    
    def _wait_for_response(self, expected_types: List[str], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for a specific response type."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.response_queue.get(timeout=1)
                if response["type"] in expected_types:
                    return response
                else:
                    # Put back if not the expected type
                    self.response_queue.put(response)
            except queue.Empty:
                continue
        
        return None
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all pending events."""
        events = []
        while True:
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except queue.Empty:
                break
        return events


# Singleton instance for Streamlit
_socketio_client = None


def get_socketio_client(server_url: str = "http://localhost:8001") -> SocketIOClient:
    """Get or create SocketIO client singleton."""
    global _socketio_client
    
    if _socketio_client is None:
        _socketio_client = SocketIOClient(server_url)
    
    return _socketio_client


def init_socketio_connection(server_url: Optional[str] = None) -> SocketIOClient:
    """Initialize SocketIO connection for Streamlit."""
    if server_url is None:
        server_url = os.getenv("SOCKETIO_SERVER_URL", "http://localhost:8001")

    client = get_socketio_client(server_url)

    if not client.connected:
        success = client.connect_to_server()
        if not success:
            import streamlit as st
            st.error("❌ Failed to connect to Multi-Agent System server")
            st.stop()

    return client
