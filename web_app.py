"""
FastAPI + HTMX Web Application for Multi-Agent System
High-performance replacement for Streamlit GUI
"""
import os
import sys
import logging
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
    user_id: str = Form(...),
    display_name: str = Form(""),
    email: str = Form("")
):
    """Handle login form submission."""
    # Validate user_id
    if not user_id or len(user_id) < 3:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "User ID must be at least 3 characters long",
            "socketio_url": SOCKETIO_URL
        })
    
    # Store user in session
    user_data = {
        "user_id": user_id,
        "display_name": display_name or user_id,
        "email": email,
        "authenticated": True,
        "login_time": datetime.now().isoformat()
    }
    
    request.session["user"] = user_data
    
    # Cache user data if Redis available
    if redis_cache:
        redis_cache.set_user_cache(user_id, user_data)
    
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
                "created_at": created_at_str,
                "is_active": user_doc.get("is_active", True)
            })
        return {"users": users}
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return {"users": []}


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
                "session_id": session_doc.get("session_id", "")[:12] + "...",
                "user_id": session_doc.get("user_id"),
                "total_messages": session_doc.get("total_messages", 0),
                "created_at": created_at_str,
                "is_active": session_doc.get("is_active", True)
            })
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return {"sessions": []}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8502,
        reload=True,
        log_level="info"
    )
