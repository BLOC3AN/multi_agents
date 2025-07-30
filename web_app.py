"""
FastAPI + HTMX Web Application for Multi-Agent System
High-performance replacement for Streamlit GUI
"""
import os
import sys
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8502,
        reload=True,
        log_level="info"
    )
