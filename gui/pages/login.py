"""
Login page for Multi-Agent System GUI.
"""
import streamlit as st
from typing import Optional
import re

from gui.utils.socketio_client import init_socketio_connection


def validate_user_id(user_id: str) -> tuple:
    """Validate user ID format."""
    if not user_id:
        return False, "User ID cannot be empty"
    
    if len(user_id) < 3:
        return False, "User ID must be at least 3 characters long"
    
    if len(user_id) > 50:
        return False, "User ID must be less than 50 characters"
    
    # Allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r'^[a-zA-Z0-9._-]+$', user_id):
        return False, "User ID can only contain letters, numbers, dots, underscores, and hyphens"
    
    return True, None


def validate_email(email: str) -> tuple:
    """Validate email format."""
    if not email:
        return True, None  # Email is optional
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address"
    
    return True, None


def show_login_page():
    """Display the login page."""
    st.set_page_config(
        page_title="Multi-Agent System - Login",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: #f8f9fa;
    }
    .feature-list {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Multi-Agent System</h1>', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("### Welcome to the Intelligent Multi-Agent System")
    st.markdown("Experience the power of parallel AI processing with our advanced multi-agent platform.")
    
    # Features showcase
    with st.expander("🚀 System Features", expanded=False):
        st.markdown("""
        <div class="feature-list">
        <h4>🧠 Intelligent Features:</h4>
        <ul>
            <li><strong>Multi-Intent Detection:</strong> AI automatically detects multiple intents in your input</li>
            <li><strong>Parallel Processing:</strong> Multiple agents work simultaneously for faster responses</li>
            <li><strong>Smart Aggregation:</strong> AI combines results from different agents intelligently</li>
            <li><strong>Conversation Memory:</strong> Agents remember your conversation context</li>
            <li><strong>Real-time Communication:</strong> Instant responses via WebSocket connection</li>
        </ul>
        
        <h4>🎯 Specialized Agents:</h4>
        <ul>
            <li><strong>Math Agent:</strong> Solves equations and mathematical problems</li>
            <li><strong>English Agent:</strong> Explains concepts and answers questions</li>
            <li><strong>Poem Agent:</strong> Creates poetry and creative writing</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Login form
    st.markdown("### 🔐 Login to Continue")
    
    with st.form("login_form", clear_on_submit=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_id = st.text_input(
                "User ID *",
                placeholder="Enter your unique user ID",
                help="Your unique identifier (3-50 characters, alphanumeric, dots, underscores, hyphens allowed)"
            )
            
            display_name = st.text_input(
                "Display Name",
                placeholder="Your display name (optional)",
                help="How you want to be addressed in the system"
            )
            
            email = st.text_input(
                "Email",
                placeholder="your.email@example.com (optional)",
                help="Optional email for account recovery"
            )
        
        with col2:
            st.markdown("### 💡 Tips")
            st.markdown("""
            - Use a memorable User ID
            - Display name is optional
            - Email helps with account recovery
            - Your conversations are saved per User ID
            """)
        
        # Submit button
        submitted = st.form_submit_button("🚀 Login & Start Chatting", use_container_width=True)
        
        if submitted:
            # Validate inputs
            user_id_valid, user_id_error = validate_user_id(user_id)
            email_valid, email_error = validate_email(email)
            
            if not user_id_valid:
                st.error(f"❌ {user_id_error}")
                return
            
            if not email_valid:
                st.error(f"❌ {email_error}")
                return
            
            # Show loading
            with st.spinner("🔌 Connecting to Multi-Agent System..."):
                try:
                    # Initialize SocketIO connection
                    client = init_socketio_connection()
                    
                    # Authenticate user
                    auth_result = client.authenticate(
                        user_id=user_id,
                        display_name=display_name if display_name else None,
                        email=email if email else None
                    )
                    
                    if auth_result["success"]:
                        # Store user info in session state
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_id
                        st.session_state.display_name = display_name or user_id
                        st.session_state.email = email
                        st.session_state.socketio_client = client
                        st.session_state.recent_sessions = auth_result["data"].get("recent_sessions", [])
                        
                        st.success(f"✅ Welcome, {display_name or user_id}!")
                        st.balloons()
                        
                        # Redirect to chat page
                        st.rerun()
                        
                    else:
                        st.error(f"❌ Authentication failed: {auth_result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    st.info("💡 Make sure the Multi-Agent System server is running on port 8001")
    
    # Footer
    st.markdown("</div>", unsafe_allow_html=True)
    
    # System status
    with st.expander("🔧 System Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("SocketIO Server", "Port 8001")
        
        with col2:
            st.metric("API Server", "Port 8000")
        
        with col3:
            st.metric("Database", "SQLite")
        
        st.info("💡 If you can't connect, ensure all services are running with: `./deployment/scripts/deploy.sh dev`")
    
    # Quick start guide
    with st.expander("📚 Quick Start Guide", expanded=False):
        st.markdown("""
        ### Getting Started:
        
        1. **Enter your User ID** - This will be your unique identifier
        2. **Add display name** (optional) - How you want to be called
        3. **Click Login** - Connect to the system
        4. **Start chatting** - Try these examples:
           - "Solve 2x + 3 = 7"
           - "Write a poem about AI"
           - "Explain machine learning and calculate 10 + 15"
        
        ### Pro Tips:
        - Use the same User ID to access your conversation history
        - Try multi-intent queries to see parallel processing in action
        - Your conversations are automatically saved and can be resumed
        - Each session has a unique ID for organization
        """)


if __name__ == "__main__":
    show_login_page()
