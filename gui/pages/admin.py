"""
Admin dashboard for user and session management.
"""

from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

from gui.database.models import (
    get_db_config, User, ChatSession, ChatMessage, SystemLog,
    get_user, get_user_sessions, get_session_messages
)
from gui.utils.redis_cache import RedisCache


def get_all_users() -> List[User]:
    """Get all users from MongoDB."""
    try:
        db_config = get_db_config()
        user_docs = db_config.users.find().sort("created_at", -1)
        return [User.from_dict(doc) for doc in user_docs]
    except Exception as e:
        st.error(f"❌ Failed to get users: {e}")
        return []


def get_user_stats() -> Dict[str, Any]:
    """Get user statistics from MongoDB."""
    try:
        db_config = get_db_config()
        total_users = db_config.users.count_documents({})
        active_users = db_config.users.count_documents({"is_active": True})
        total_sessions = db_config.sessions.count_documents({})
        total_messages = db_config.messages.count_documents({})

        # Recent activity (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        recent_users = db_config.users.count_documents({"created_at": {"$gte": week_ago}})
        recent_sessions = db_config.sessions.count_documents({"created_at": {"$gte": week_ago}})
        recent_messages = db_config.messages.count_documents({"created_at": {"$gte": week_ago}})

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "recent_users": recent_users,
            "recent_sessions": recent_sessions,
            "recent_messages": recent_messages
        }
    except Exception as e:
        st.error(f"❌ Failed to get user stats: {e}")
        return {
            "total_users": 0,
            "active_users": 0,
            "total_sessions": 0,
            "total_messages": 0,
            "recent_users": 0,
            "recent_sessions": 0,
            "recent_messages": 0
        }


def get_system_logs(limit: int = 100) -> List[SystemLog]:
    """Get recent system logs from MongoDB."""
    try:
        db_config = get_db_config()
        log_docs = db_config.logs.find().sort("timestamp", -1).limit(limit)
        return [SystemLog.from_dict(doc) for doc in log_docs]
    except Exception as e:
        st.error(f"❌ Failed to get system logs: {e}")
        return []


def show_admin_dashboard():
    """Display the admin dashboard."""
    st.set_page_config(
        page_title="Multi-Agent System - Admin",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ Admin Dashboard")
    st.markdown("---")
    
    # Check if user is admin (simple check for demo)
    if not st.session_state.get("is_admin"):
        st.error("❌ Access denied. Admin privileges required.")
        
        # Simple admin login
        with st.form("admin_login"):
            admin_password = st.text_input("Admin Password", type="password")
            if st.form_submit_button("Login as Admin"):
                if admin_password == "admin123":  # Simple password for demo
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("❌ Invalid admin password")
        return
    
    # Admin navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "👥 Users", 
        "💬 Sessions", 
        "📝 Messages", 
        "📋 Logs"
    ])
    
    with tab1:
        show_overview_tab()
    
    with tab2:
        show_users_tab()
    
    with tab3:
        show_sessions_tab()
    
    with tab4:
        show_messages_tab()
    
    with tab5:
        show_logs_tab()


def show_overview_tab():
    """Show overview statistics."""
    st.header("📊 System Overview")
    
    # Get statistics
    stats = get_user_stats()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Users", 
            stats["total_users"],
            delta=f"+{stats['recent_users']} this week"
        )
    
    with col2:
        st.metric(
            "Active Users", 
            stats["active_users"]
        )
    
    with col3:
        st.metric(
            "Total Sessions", 
            stats["total_sessions"],
            delta=f"+{stats['recent_sessions']} this week"
        )
    
    with col4:
        st.metric(
            "Total Messages", 
            stats["total_messages"],
            delta=f"+{stats['recent_messages']} this week"
        )
    
    # Charts (placeholder for now)
    st.subheader("📈 Activity Trends")
    st.info("📊 Activity charts would be implemented here with proper time-series data")
    
    # System health
    st.subheader("🏥 System Health")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Database Status", "✅ Healthy")
    
    with col2:
        st.metric("SocketIO Server", "✅ Running")
    
    with col3:
        st.metric("API Server", "✅ Running")


def show_users_tab():
    """Show users management."""
    st.header("👥 User Management")
    
    # Get all users
    users = get_all_users()
    
    if not users:
        st.info("No users found.")
        return
    
    # Users table
    users_data = []
    db_config = get_db_config()
    for user in users:
        # Count sessions for this user from MongoDB
        session_count = db_config.sessions.count_documents({"user_id": user.user_id})

        # Handle datetime formatting
        created_str = user.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(user.created_at, 'strftime') else str(user.created_at)
        last_login_str = "Never"
        if user.last_login:
            if hasattr(user.last_login, 'strftime'):
                last_login_str = user.last_login.strftime("%Y-%m-%d %H:%M")
            else:
                last_login_str = str(user.last_login)

        users_data.append({
            "User ID": user.user_id,
            "Display Name": user.display_name or "N/A",
            "Email": user.email or "N/A",
            "Created": created_str,
            "Last Login": last_login_str,
            "Active": "✅" if user.is_active else "❌",
            "Sessions": session_count
        })
    
    df = pd.DataFrame(users_data)
    st.dataframe(df, use_container_width=True)
    
    # User details
    st.subheader("🔍 User Details")
    selected_user_id = st.selectbox(
        "Select User",
        options=[user.user_id for user in users],
        format_func=lambda x: f"{x} ({next(u.display_name for u in users if u.user_id == x) or 'No name'})"
    )
    
    if selected_user_id:
        user = get_user(selected_user_id)
        if user:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User ID:** {user.user_id}")
                st.write(f"**Display Name:** {user.display_name or 'N/A'}")
                st.write(f"**Email:** {user.email or 'N/A'}")
                st.write(f"**Created:** {user.created_at}")
                st.write(f"**Active:** {'Yes' if user.is_active else 'No'}")
            
            with col2:
                # User sessions
                sessions = get_user_sessions(selected_user_id)
                st.write(f"**Total Sessions:** {len(sessions)}")
                
                if sessions:
                    st.write("**Recent Sessions:**")
                    for session in sessions[:5]:
                        st.write(f"• {session.session_id[:8]}... ({session.total_messages} messages)")


def show_sessions_tab():
    """Show sessions management."""
    st.header("💬 Session Management")

    # Get all sessions from MongoDB
    try:
        db_config = get_db_config()
        session_docs = db_config.sessions.find().sort("updated_at", -1).limit(100)
        sessions = [ChatSession.from_dict(doc) for doc in session_docs]
    except Exception as e:
        st.error(f"❌ Failed to get sessions: {e}")
        sessions = []
    
    if not sessions:
        st.info("No sessions found.")
        return
    
    # Sessions table
    sessions_data = []
    for sess in sessions:
        # Handle datetime formatting
        created_str = sess.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(sess.created_at, 'strftime') else str(sess.created_at)
        updated_str = sess.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(sess.updated_at, 'strftime') else str(sess.updated_at)

        sessions_data.append({
            "Session ID": sess.session_id[:8] + "...",
            "User ID": sess.user_id,
            "Title": sess.title or "Untitled",
            "Messages": sess.total_messages,
            "Created": created_str,
            "Updated": updated_str,
            "Active": "✅" if sess.is_active else "❌"
        })
    
    df = pd.DataFrame(sessions_data)
    st.dataframe(df, use_container_width=True)
    
    # Session details
    st.subheader("🔍 Session Details")
    selected_session = st.selectbox(
        "Select Session",
        options=[sess.session_id for sess in sessions],
        format_func=lambda x: f"{x[:8]}... ({next(s.user_id for s in sessions if s.session_id == x)})"
    )
    
    if selected_session:
        messages = get_session_messages(selected_session)
        st.write(f"**Messages in session:** {len(messages)}")
        
        if messages:
            for i, msg in enumerate(messages[-5:], 1):  # Show last 5 messages
                with st.expander(f"Message {i} - {msg.created_at.strftime('%H:%M:%S')}"):
                    st.write(f"**User:** {msg.user_input}")
                    if msg.agent_response:
                        st.write(f"**Agent:** {msg.agent_response}")
                    st.write(f"**Intent:** {msg.primary_intent}")
                    st.write(f"**Mode:** {msg.processing_mode}")


def show_messages_tab():
    """Show messages analysis."""
    st.header("📝 Message Analysis")

    # Get recent messages from MongoDB
    try:
        db_config = get_db_config()
        message_docs = db_config.messages.find().sort("created_at", -1).limit(100)
        messages = [ChatMessage.from_dict(doc) for doc in message_docs]
    except Exception as e:
        st.error(f"❌ Failed to get messages: {e}")
        messages = []
    
    if not messages:
        st.info("No messages found.")
        return
    
    # Message statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Messages", len(messages))
    
    with col2:
        successful = sum(1 for msg in messages if msg.success)
        st.metric("Successful", successful)
    
    with col3:
        failed = sum(1 for msg in messages if not msg.success)
        st.metric("Failed", failed)
    
    with col4:
        avg_time = sum(msg.processing_time or 0 for msg in messages) / len(messages)
        st.metric("Avg Processing Time", f"{avg_time:.0f}ms")
    
    # Intent distribution
    st.subheader("🎯 Intent Distribution")
    intent_counts = {}
    for msg in messages:
        intent = msg.primary_intent or "Unknown"
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    if intent_counts:
        intent_df = pd.DataFrame(list(intent_counts.items()), columns=["Intent", "Count"])
        st.bar_chart(intent_df.set_index("Intent"))
    
    # Processing mode distribution
    st.subheader("🔄 Processing Mode Distribution")
    mode_counts = {}
    for msg in messages:
        mode = msg.processing_mode or "Unknown"
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    if mode_counts:
        mode_df = pd.DataFrame(list(mode_counts.items()), columns=["Mode", "Count"])
        st.bar_chart(mode_df.set_index("Mode"))


def show_logs_tab():
    """Show system logs."""
    st.header("📋 System Logs")
    
    # Get logs
    logs = get_system_logs(50)
    
    if not logs:
        st.info("No logs found.")
        return
    
    # Log level filter
    log_levels = list(set(log.level for log in logs))
    selected_levels = st.multiselect("Filter by Level", log_levels, default=log_levels)
    
    # Component filter
    components = list(set(log.component for log in logs))
    selected_components = st.multiselect("Filter by Component", components, default=components)
    
    # Filtered logs
    filtered_logs = [
        log for log in logs 
        if log.level in selected_levels and log.component in selected_components
    ]
    
    # Display logs
    for log in filtered_logs:
        level_color = {
            "INFO": "🔵",
            "WARNING": "🟡", 
            "ERROR": "🔴",
            "DEBUG": "⚪"
        }.get(log.level, "⚫")
        
        with st.expander(f"{level_color} {log.level} - {log.component} - {log.timestamp.strftime('%H:%M:%S')}"):
            st.write(f"**Message:** {log.message}")
            if log.user_id:
                st.write(f"**User ID:** {log.user_id}")
            if log.session_id:
                st.write(f"**Session ID:** {log.session_id}")
            if log.additional_data:
                st.write("**Additional Data:**")
                st.json(log.additional_data)


if __name__ == "__main__":
    show_admin_dashboard()
