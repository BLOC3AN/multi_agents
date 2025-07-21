"""
Main chat interface for Multi-Agent System GUI.
"""
import streamlit as st
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from gui.utils.socketio_client import get_socketio_client
from gui.database.models import get_user_sessions, get_session_messages


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return timestamp


def display_message(message: Dict[str, Any], is_user: bool = True):
    """Display a chat message."""
    if is_user:
        with st.chat_message("user"):
            st.write(message.get("content", ""))
            if message.get("timestamp"):
                st.caption(f"⏰ {format_timestamp(message['timestamp'])}")
    else:
        with st.chat_message("assistant"):
            st.write(message.get("content", ""))
            
            # Show processing details if available
            if message.get("processing_info"):
                info = message["processing_info"]
                
                with st.expander("🔍 Processing Details", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Intent", info.get("primary_intent", "Unknown"))
                        st.metric("Mode", info.get("processing_mode", "Unknown"))
                    
                    with col2:
                        if info.get("processing_time"):
                            st.metric("Time", f"{info['processing_time']:.2f}s")
                        execution_summary = info.get("execution_summary") or {}
                        if execution_summary.get("total_agents"):
                            st.metric("Agents", execution_summary["total_agents"])
                    
                    with col3:
                        if info.get("detected_intents"):
                            st.write("**Detected Intents:**")
                            for intent in info["detected_intents"]:
                                st.write(f"• {intent['intent']} ({intent['confidence']:.2f})")
                    
                    execution_summary = info.get("execution_summary")
                    if execution_summary:
                        st.write("**Execution Summary:**")
                        st.json(execution_summary)
            
            if message.get("timestamp"):
                st.caption(f"⏰ {format_timestamp(message['timestamp'])}")


def show_session_sidebar():
    """Show session management in sidebar."""
    st.sidebar.header("💬 Chat Sessions")
    
    # Current session info
    if st.session_state.get("current_session_id"):
        st.sidebar.success(f"📝 Active: {st.session_state.current_session_id[:8]}...")
    
    # New session button
    if st.sidebar.button("➕ New Session", use_container_width=True):
        create_new_session()
    
    # Recent sessions
    if st.session_state.get("recent_sessions"):
        st.sidebar.subheader("📚 Recent Sessions")
        
        for session in st.session_state.recent_sessions[:10]:
            session_title = session.get("title", f"Session {session['session_id'][:8]}")
            
            col1, col2 = st.sidebar.columns([3, 1])
            
            with col1:
                if st.button(
                    f"📝 {session_title}",
                    key=f"session_{session['session_id']}",
                    help=f"Messages: {session.get('total_messages', 0)}"
                ):
                    load_session(session["session_id"])
            
            with col2:
                st.caption(f"{session.get('total_messages', 0)} msgs")
    
    # User info
    st.sidebar.divider()
    st.sidebar.subheader("👤 User Info")
    st.sidebar.write(f"**User ID:** {st.session_state.get('user_id', 'Unknown')}")
    st.sidebar.write(f"**Display Name:** {st.session_state.get('display_name', 'Unknown')}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()


def create_new_session():
    """Create a new chat session."""
    client = st.session_state.get("socketio_client")
    if not client:
        st.error("❌ Not connected to server")
        return

    # Check if client is still connected and authenticated
    if not client.connected or not client.authenticated:
        st.error("❌ Connection lost. Please login again.")
        # Clear session state to force re-login
        st.session_state.authenticated = False
        st.rerun()
        return

    with st.spinner("📝 Creating new session..."):
        result = client.create_session()
        
        if result["success"]:
            session_data = result["data"]
            st.session_state.current_session_id = session_data["session_id"]
            st.session_state.conversation_history = []
            st.success(f"✅ New session created: {session_data['session_id'][:8]}...")
            st.rerun()
        else:
            st.error(f"❌ Failed to create session: {result['error']}")


def load_session(session_id: str):
    """Load an existing chat session."""
    client = st.session_state.get("socketio_client")
    if not client:
        st.error("❌ Not connected to server")
        return

    # Check if client is still connected and authenticated
    if not client.connected or not client.authenticated:
        st.error("❌ Connection lost. Please login again.")
        # Clear session state to force re-login
        st.session_state.authenticated = False
        st.rerun()
        return

    with st.spinner(f"📚 Loading session {session_id[:8]}..."):
        result = client.join_session(session_id)
        
        if result["success"]:
            session_data = result["data"]
            st.session_state.current_session_id = session_id
            st.session_state.conversation_history = session_data.get("conversation_history", [])
            st.success(f"✅ Loaded session: {session_id[:8]}...")
            st.rerun()
        else:
            st.error(f"❌ Failed to load session: {result['error']}")


def logout():
    """Logout and disconnect."""
    client = st.session_state.get("socketio_client")
    if client:
        client.disconnect_from_server()
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()


def show_chat_page():
    """Display the main chat interface."""
    st.set_page_config(
        page_title="Multi-Agent System - Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check authentication
    if not st.session_state.get("authenticated"):
        st.error("❌ Please login first")
        st.stop()
    
    # Custom CSS
    st.markdown("""
    <style>
    .chat-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-connected {
        background-color: #4CAF50;
    }
    .status-disconnected {
        background-color: #f44336;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show session sidebar
    show_session_sidebar()
    
    # Main chat area
    st.markdown(f"""
    <div class="chat-header">
        <h1>🤖 Multi-Agent System Chat</h1>
        <p>Welcome, {st.session_state.get('display_name', 'User')}! 
        <span class="status-indicator status-connected"></span>Connected</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have an active session
    if not st.session_state.get("current_session_id"):
        st.info("💡 Create a new session or select an existing one from the sidebar to start chatting.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start New Session", use_container_width=True, type="primary"):
                create_new_session()
        return
    
    # Display conversation history
    conversation_history = st.session_state.get("conversation_history", [])
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        if conversation_history:
            for msg in conversation_history:
                # User message
                display_message({
                    "content": msg.get("user_input", ""),
                    "timestamp": msg.get("timestamp", "")
                }, is_user=True)
                
                # Agent response
                if msg.get("agent_response"):
                    display_message({
                        "content": msg.get("agent_response", ""),
                        "timestamp": msg.get("timestamp", ""),
                        "processing_info": {
                            "primary_intent": msg.get("primary_intent"),
                            "processing_mode": msg.get("processing_mode"),
                            "detected_intents": msg.get("detected_intents"),
                            "execution_summary": msg.get("execution_summary"),
                            "processing_time": msg.get("processing_time", 0) / 1000 if msg.get("processing_time") else None
                        }
                    }, is_user=False)
        else:
            st.info("👋 Start a conversation! Try asking about math, requesting a poem, or explaining a concept.")
    
    # Chat input
    with st.container():
        st.divider()
        
        # Example prompts
        with st.expander("💡 Example Prompts", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**🧮 Math Examples:**")
                if st.button("Solve 2x + 3 = 7", key="math1"):
                    st.session_state.example_input = "Solve 2x + 3 = 7"
                if st.button("Calculate area of circle r=5", key="math2"):
                    st.session_state.example_input = "Calculate the area of a circle with radius 5"
            
            with col2:
                st.write("**🎭 Creative Examples:**")
                if st.button("Write poem about AI", key="poem1"):
                    st.session_state.example_input = "Write a poem about artificial intelligence"
                if st.button("Create haiku about nature", key="poem2"):
                    st.session_state.example_input = "Create a haiku about nature"
            
            with col3:
                st.write("**🤖 Multi-Intent Examples:**")
                if st.button("Explain AI and solve 10+15", key="multi1"):
                    st.session_state.example_input = "Explain artificial intelligence and solve 10 + 15"
                if st.button("Write poem and calculate 5²", key="multi2"):
                    st.session_state.example_input = "Write a poem about mathematics and calculate 5 squared"
        
        # Chat input form
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_area(
                    "Your message:",
                    value=st.session_state.get("example_input", ""),
                    placeholder="Ask me anything! I can solve math, write poems, explain concepts, or handle multiple requests at once...",
                    height=100,
                    key="user_message_input"
                )
                
                # Clear example input after using it
                if "example_input" in st.session_state:
                    del st.session_state.example_input
            
            with col2:
                st.write("")  # Spacing
                send_button = st.form_submit_button("🚀 Send", use_container_width=True, type="primary")
                
                # Processing options
                st.write("**Options:**")
                force_parallel = st.checkbox("Force parallel mode", help="Force parallel processing even for single intents")
        
        # Handle message sending
        if send_button and user_input.strip():
            client = st.session_state.get("socketio_client")
            if not client:
                st.error("❌ Not connected to server")
                return
            
            # Add user message to conversation immediately
            user_msg = {
                "user_input": user_input,
                "timestamp": datetime.now().isoformat()
            }
            
            if "conversation_history" not in st.session_state:
                st.session_state.conversation_history = []
            
            st.session_state.conversation_history.append(user_msg)
            
            # Show processing indicator
            with st.spinner("🤖 Processing your request..."):
                result = client.send_message(user_input)
                
                if result["success"]:
                    response_data = result["data"]

                    # Update the last message with response data
                    st.session_state.conversation_history[-1].update({
                        "agent_response": response_data.get("response"),  # Map "response" to "agent_response"
                        "primary_intent": response_data.get("primary_intent"),
                        "processing_mode": response_data.get("processing_mode"),
                        "detected_intents": response_data.get("detected_intents"),
                        "execution_summary": response_data.get("execution_summary"),
                        "processing_time": response_data.get("processing_time"),
                        "success": response_data.get("status") == "success",
                        "errors": response_data.get("errors"),
                        "agent_responses": response_data.get("agent_responses"),
                        "metadata": response_data.get("metadata"),
                        "timestamp": response_data.get("timestamp")
                    })
                    
                    st.rerun()
                    
                else:
                    st.error(f"❌ Processing failed: {result['error']}")
                    # Remove the user message if processing failed
                    st.session_state.conversation_history.pop()


if __name__ == "__main__":
    show_chat_page()
