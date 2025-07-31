"""
FastAPI + HTMX Web Application for Multi-Agent System
High-performance replacement for Streamlit GUI
"""
import os
import sys
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Setup logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import existing utilities
from gui.database.models import get_db_config, get_user, get_user_sessions
from gui.utils.redis_cache import RedisCache

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent System Web App",
    description="High-performance web interface for multi-agent system",
    version="2.0.0"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for user state
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
)

# Create templates and static directories
templates_dir = project_root / "web_templates"
static_dir = project_root / "web_static"

templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

# Setup templates
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize database and cache
db_config = get_db_config()
redis_cache = RedisCache(db_config.redis_client) if db_config.redis_client else None

# SocketIO server URL
SOCKETIO_URL = os.getenv("SOCKETIO_SERVER_URL", "http://localhost:8001")


# Password utilities
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"  # In production, use random salt per user
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from session."""
    return request.session.get("user")


def require_auth(request: Request) -> Dict[str, Any]:
    """Require authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to login or chat."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/chat", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "web_app"
    }


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/chat", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "socketio_url": SOCKETIO_URL
    })


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    # Validate username
    if not username or len(username) < 3:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Username must be at least 3 characters long",
            "socketio_url": SOCKETIO_URL
        })

    # Validate password
    if not password or len(password) < 6:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Password must be at least 6 characters long",
            "socketio_url": SOCKETIO_URL
        })

    # Authenticate user against database
    user_doc = db_config.users.find_one({"user_id": username})

    if not user_doc:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password",
            "socketio_url": SOCKETIO_URL
        })

    # Verify password
    if not verify_password(password, user_doc.get("password_hash", "")):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password",
            "socketio_url": SOCKETIO_URL
        })

    # Check if user is active
    if not user_doc.get("is_active", True):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Account is disabled. Please contact administrator.",
            "socketio_url": SOCKETIO_URL
        })

    # Update last login
    db_config.users.update_one(
        {"user_id": username},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    # Store user in session
    user_data = {
        "user_id": username,
        "display_name": user_doc.get("display_name") or username,
        "email": user_doc.get("email"),
        "authenticated": True,
        "login_time": datetime.now().isoformat()
    }

    request.session["user"] = user_data

    # Cache user data if Redis available
    if redis_cache:
        redis_cache.set_user_cache(username, user_data)

    return RedirectResponse(url="/chat", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    """Logout user."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Main chat interface."""
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": user,
        "socketio_url": SOCKETIO_URL
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Admin dashboard."""
    # Allow any authenticated user for demo purposes
    # In production, you can add proper role-based access control

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user
    })


@app.get("/api/admin/metrics")
async def get_admin_metrics(user: Dict[str, Any] = Depends(require_auth)):
    """Get admin dashboard metrics from real database."""
    try:
        # Get total users
        total_users = db_config.users.count_documents({})

        # Get active sessions (sessions updated in last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_sessions = db_config.sessions.count_documents({
            "updated_at": {"$gte": yesterday}
        })

        # Get total messages
        total_messages = db_config.messages.count_documents({})

        # Calculate system health (simple metric based on successful messages)
        successful_messages = db_config.messages.count_documents({"success": True})
        health_percentage = round((successful_messages / max(total_messages, 1)) * 100, 1) if total_messages > 0 else 100

        return {
            "total_users": total_users,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "system_health": f"{health_percentage}%"
        }
    except Exception as e:
        logger.error(f"Error getting admin metrics: {e}")
        return {
            "total_users": 0,
            "active_sessions": 0,
            "total_messages": 0,
            "system_health": "N/A"
        }


@app.get("/api/admin/users")
async def get_admin_users(user: Dict[str, Any] = Depends(require_auth)):
    """Get users list for admin dashboard."""
    try:
        users_cursor = db_config.users.find().sort("created_at", -1).limit(50)
        users = []
        for user_doc in users_cursor:
            # Handle created_at field safely
            created_at = user_doc.get("created_at")
            if created_at:
                if isinstance(created_at, datetime):
                    created_at_str = created_at.strftime("%Y-%m-%d")
                elif isinstance(created_at, str):
                    created_at_str = created_at[:10]  # Take first 10 chars if it's a string
                else:
                    created_at_str = str(created_at)
            else:
                created_at_str = "N/A"

            users.append({
                "user_id": user_doc.get("user_id"),
                "display_name": user_doc.get("display_name"),
                "email": user_doc.get("email"),
                "password": user_doc.get("password", "N/A"),  # Show plain password for admin
                "password_hash": user_doc.get("password_hash", "")[:20] + "..." if user_doc.get("password_hash") else "N/A",  # Show truncated hash
                "created_at": created_at_str,
                "is_active": user_doc.get("is_active", True)
            })
        return {"users": users}
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return {"users": []}


@app.post("/api/admin/users")
async def add_user(request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Add new user."""
    try:
        data = await request.json()

        user_id = data.get("user_id", "").strip()
        password = data.get("password", "").strip()
        display_name = data.get("display_name", "").strip()
        email = data.get("email", "").strip()
        is_active = data.get("is_active", True)

        # Validate user_id
        if not user_id or len(user_id) < 3:
            return {"success": False, "message": "User ID must be at least 3 characters long"}

        # Validate password
        if not password or len(password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters long"}

        # Check if user already exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if existing_user:
            return {"success": False, "message": f"User '{user_id}' already exists"}

        # Create new user
        from gui.database.models import User
        new_user = User(
            user_id=user_id,
            password_hash=hash_password(password),
            password=password,  # Store plain password for admin management
            display_name=display_name or user_id,
            email=email if email else None,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to database
        user_doc = new_user.to_dict()
        db_config.users.insert_one(user_doc)

        logger.info(f"✅ New user created by admin: {user_id}")

        return {
            "success": True,
            "message": f"User '{user_id}' created successfully",
            "user": {
                "user_id": user_id,
                "display_name": display_name or user_id,
                "email": email,
                "is_active": is_active
            }
        }

    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return {"success": False, "message": "Failed to add user"}


@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, user: Dict[str, Any] = Depends(require_auth)):
    """Delete user and all related data."""
    try:
        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            return {"success": False, "message": f"User '{user_id}' not found"}

        # Prevent deleting current admin user
        if user_id == user.get("user_id"):
            return {"success": False, "message": "Cannot delete your own account"}

        # Delete user's sessions
        sessions_deleted = db_config.sessions.delete_many({"user_id": user_id})

        # Delete user's messages
        messages_deleted = db_config.messages.delete_many({"user_id": user_id})

        # Delete user
        user_deleted = db_config.users.delete_one({"user_id": user_id})

        logger.info(f"🗑️ User deleted by admin: {user_id} (sessions: {sessions_deleted.deleted_count}, messages: {messages_deleted.deleted_count})")

        return {
            "success": True,
            "message": f"User '{user_id}' and all related data deleted successfully",
            "deleted": {
                "user": user_deleted.deleted_count,
                "sessions": sessions_deleted.deleted_count,
                "messages": messages_deleted.deleted_count
            }
        }

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return {"success": False, "message": "Failed to delete user"}


@app.put("/api/admin/users/{user_id}/password")
async def update_user_password(user_id: str, request: Request, user: Dict[str, Any] = Depends(require_auth)):
    """Update user password."""
    try:
        data = await request.json()
        new_password = data.get("password", "").strip()

        # Validate password
        if not new_password or len(new_password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters long"}

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            return {"success": False, "message": f"User '{user_id}' not found"}

        # Update password
        result = db_config.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "password": new_password,
                    "password_hash": hash_password(new_password),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"🔐 Password updated for user: {user_id}")
            return {
                "success": True,
                "message": f"Password updated successfully for '{user_id}'"
            }
        else:
            return {"success": False, "message": "Failed to update password"}

    except Exception as e:
        logger.error(f"Error updating password: {e}")
        return {"success": False, "message": "Failed to update password"}


@app.get("/api/chat/sessions")
async def get_user_sessions(user: Dict[str, Any] = Depends(require_auth)):
    """Get user's chat sessions."""
    try:
        user_id = user.get("user_id")
        logger.info(f"🔍 Getting sessions for user: {user_id}")

        # Get user's sessions, sorted by most recent
        sessions = list(db_config.sessions.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).limit(20))

        logger.info(f"📊 Found {len(sessions)} sessions for user {user_id}")

        session_list = []
        for session in sessions:
            # Get message count for this session
            message_count = db_config.messages.count_documents({"session_id": session.get("session_id")})

            # Get last message for preview
            last_message = db_config.messages.find_one(
                {"session_id": session.get("session_id")},
                sort=[("created_at", -1)]
            )

            # Format session data
            created_at = session.get("created_at")
            updated_at = session.get("updated_at")

            # Handle both datetime objects and strings
            if isinstance(created_at, str):
                created_at_str = created_at[:16] if len(created_at) >= 16 else created_at
            elif hasattr(created_at, 'strftime'):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                created_at_str = "Unknown"

            if isinstance(updated_at, str):
                updated_at_str = updated_at[:16] if len(updated_at) >= 16 else updated_at
            elif hasattr(updated_at, 'strftime'):
                updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M")
            else:
                updated_at_str = "Unknown"

            session_data = {
                "session_id": session.get("session_id"),
                "session_id_display": session.get("session_id", "")[:8] + "...",
                "created_at": created_at_str,
                "updated_at": updated_at_str,
                "message_count": message_count,
                "last_message_preview": last_message.get("user_input", "")[:50] + "..." if last_message and last_message.get("user_input") else "No messages",
                "is_active": session.get("is_active", True)
            }
            session_list.append(session_data)

        logger.info(f"✅ Returning {len(session_list)} sessions for user {user_id}")
        return {"sessions": session_list}

    except Exception as e:
        logger.error(f"❌ Error getting user sessions: {e}")
        return {"sessions": []}


@app.get("/api/admin/sessions")
async def get_admin_sessions(user: Dict[str, Any] = Depends(require_auth)):
    """Get sessions list for admin dashboard."""
    try:
        sessions_cursor = db_config.sessions.find().sort("updated_at", -1).limit(50)
        sessions = []
        for session_doc in sessions_cursor:
            # Handle created_at field safely
            created_at = session_doc.get("created_at")
            if created_at:
                if isinstance(created_at, datetime):
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
                elif isinstance(created_at, str):
                    created_at_str = created_at[:16]  # Take first 16 chars for datetime
                else:
                    created_at_str = str(created_at)
            else:
                created_at_str = "N/A"

            sessions.append({
                "session_id": session_doc.get("session_id", ""),
                "session_id_display": session_doc.get("session_id", "")[:12] + "...",
                "user_id": session_doc.get("user_id"),
                "total_messages": session_doc.get("total_messages", 0),
                "created_at": created_at_str,
                "is_active": session_doc.get("is_active", True)
            })
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return {"sessions": []}


@app.get("/api/admin/session/{session_id}")
async def get_session_details(session_id: str, user: Dict[str, Any] = Depends(require_auth)):
    """Get detailed session information."""
    try:
        # Get session details
        session_doc = db_config.sessions.find_one({"session_id": session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get session messages
        messages_cursor = db_config.messages.find({"session_id": session_id}).sort("created_at", 1)
        messages = []
        for msg_doc in messages_cursor:
            created_at = msg_doc.get("created_at")
            if created_at:
                if isinstance(created_at, datetime):
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
                else:
                    created_at_str = str(created_at)[:16]
            else:
                created_at_str = "N/A"

            messages.append({
                "message_id": msg_doc.get("message_id", ""),
                "user_input": msg_doc.get("user_input", ""),
                "agent_response": msg_doc.get("agent_response", ""),
                "processing_time": f"{msg_doc.get('processing_time', 0) / 1000:.1f}s" if msg_doc.get('processing_time') else "N/A",
                "success": msg_doc.get("success", False),
                "created_at": created_at_str
            })

        # Format session data
        created_at = session_doc.get("created_at")
        if created_at:
            if isinstance(created_at, datetime):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                created_at_str = str(created_at)[:16]
        else:
            created_at_str = "N/A"

        session_data = {
            "session_id": session_doc.get("session_id"),
            "user_id": session_doc.get("user_id"),
            "title": session_doc.get("title", ""),
            "created_at": created_at_str,
            "total_messages": session_doc.get("total_messages", 0),
            "is_active": session_doc.get("is_active", True),
            "messages": messages
        }

        return session_data
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session details")


@app.get("/api/admin/logs")
async def get_admin_logs(user: Dict[str, Any] = Depends(require_auth)):
    """Get system logs for admin dashboard."""
    try:
        logs = []

        # Read recent logs from log files
        log_files = ["logs/gui.log", "logs/socketio.log"]

        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 50 lines
                        recent_lines = lines[-50:] if len(lines) > 50 else lines

                        for line in recent_lines:
                            line = line.strip()
                            if line:
                                # Parse log level and message
                                if "INFO" in line:
                                    level = "INFO"
                                    icon = "ℹ️"
                                elif "ERROR" in line:
                                    level = "ERROR"
                                    icon = "❌"
                                elif "WARNING" in line:
                                    level = "WARNING"
                                    icon = "⚠️"
                                elif "DEBUG" in line:
                                    level = "DEBUG"
                                    icon = "🔍"
                                else:
                                    level = "INFO"
                                    icon = "📝"

                                # Extract timestamp if available
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                if line.startswith("2024"):
                                    timestamp = line[:19]

                                logs.append({
                                    "timestamp": timestamp,
                                    "level": level,
                                    "icon": icon,
                                    "message": line,
                                    "source": log_file.split("/")[-1]
                                })
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")

        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit to last 100 entries
        logs = logs[:100]

        return {"logs": logs}

    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return {"logs": []}


@app.post("/api/admin/logs/clear")
async def clear_admin_logs(user: Dict[str, Any] = Depends(require_auth)):
    """Clear system logs."""
    try:
        log_files = ["logs/gui.log", "logs/socketio.log"]
        cleared_files = []

        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    # Clear file content
                    with open(log_file, 'w') as f:
                        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Logs cleared by admin\n")
                    cleared_files.append(log_file)
            except Exception as e:
                logger.error(f"Error clearing log file {log_file}: {e}")

        return {
            "success": True,
            "message": f"Cleared {len(cleared_files)} log files",
            "files": cleared_files
        }

    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return {"success": False, "message": "Failed to clear logs"}


@app.get("/api/admin/messages")
async def get_admin_messages(user: Dict[str, Any] = Depends(require_auth)):
    """Get messages stats for admin dashboard."""
    try:
        # Get message statistics
        total_messages = db_config.messages.count_documents({})
        successful_messages = db_config.messages.count_documents({"success": True})
        failed_messages = total_messages - successful_messages

        # Get average response time (if available)
        pipeline = [
            {"$match": {"processing_time": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time"}}}
        ]
        avg_result = list(db_config.messages.aggregate(pipeline))
        avg_response_time = round(avg_result[0]["avg_time"] / 1000, 1) if avg_result else 0

        # Get recent messages
        messages_cursor = db_config.messages.find().sort("created_at", -1).limit(20)
        recent_messages = []
        for msg_doc in messages_cursor:
            # Handle created_at field safely
            created_at = msg_doc.get("created_at")
            if created_at:
                if isinstance(created_at, datetime):
                    created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
                elif isinstance(created_at, str):
                    created_at_str = created_at[:16]  # Take first 16 chars for datetime
                else:
                    created_at_str = str(created_at)
            else:
                created_at_str = "N/A"

            recent_messages.append({
                "message_id": msg_doc.get("message_id", "")[:8] + "...",
                "user_id": msg_doc.get("user_id"),
                "content": (msg_doc.get("user_input", ""))[:50] + "..." if len(msg_doc.get("user_input", "")) > 50 else msg_doc.get("user_input", ""),
                "processing_time": f"{msg_doc.get('processing_time', 0) / 1000:.1f}s" if msg_doc.get('processing_time') else "N/A",
                "success": msg_doc.get("success", False),
                "created_at": created_at_str
            })

        return {
            "stats": {
                "total_messages": total_messages,
                "successful_messages": successful_messages,
                "failed_messages": failed_messages,
                "avg_response_time": f"{avg_response_time}s"
            },
            "recent_messages": recent_messages
        }
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return {
            "stats": {
                "total_messages": 0,
                "successful_messages": 0,
                "failed_messages": 0,
                "avg_response_time": "N/A"
            },
            "recent_messages": []
        }


@app.get("/api/chat/history/{session_id}")
async def get_session_history(session_id: str, user: Dict[str, Any] = Depends(require_auth)):
    """Get messages for a specific session."""
    try:
        user_id = user.get("user_id")
        logger.info(f"🔍 Getting history for session: {session_id}, user: {user_id}")

        # Verify session belongs to user
        session = db_config.sessions.find_one({
            "session_id": session_id,
            "user_id": user_id
        })

        if not session:
            logger.warning(f"❌ Session {session_id} not found for user {user_id}")
            return {"messages": []}

        # Get messages for this session
        messages = list(db_config.messages.find(
            {"session_id": session_id}
        ).sort("created_at", 1))

        logger.info(f"📊 Found {len(messages)} messages for session {session_id}")

        message_list = []
        for msg in messages:
            # Handle datetime formatting
            created_at = msg.get("created_at")
            if isinstance(created_at, str):
                created_at_str = created_at
            elif hasattr(created_at, 'isoformat'):
                created_at_str = created_at.isoformat()
            else:
                created_at_str = str(created_at)

            message_data = {
                "message_id": str(msg.get("_id")),
                "user_input": msg.get("user_input"),
                "agent_response": msg.get("agent_response"),
                "agent_responses": msg.get("agent_responses", {}),
                "created_at": created_at_str,
                "processing_time": msg.get("processing_time")
            }
            message_list.append(message_data)

        logger.info(f"✅ Returning {len(message_list)} messages for session {session_id}")
        return {"messages": message_list}

    except Exception as e:
        logger.error(f"❌ Error getting session history: {e}")
        return {"messages": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8502,
        reload=True,
        log_level="info"
    )
