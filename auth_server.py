"""
Authentication API Server for Multi-Agent System
Provides REST API endpoints for user authentication with MongoDB
"""
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced logging and database
from src.utils.logger import api_logger, system_logger

# Import database models
try:
    from src.database.models import get_db_config, User
    DATABASE_AVAILABLE = True
    system_logger.info("✅ Database models imported successfully")
except ImportError as e:
    DATABASE_AVAILABLE = False
    system_logger.warning(f"⚠️ Database models not available: {e}")

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System Authentication API",
    description="Authentication service for the Multi-Agent System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection
db_config = None
if DATABASE_AVAILABLE:
    try:
        db_config = get_db_config()
        system_logger.info("✅ Database connection initialized")
    except Exception as e:
        system_logger.error(f"❌ Failed to initialize database: {e}")
        DATABASE_AVAILABLE = False


# Pydantic models
class LoginRequest(BaseModel):
    user_id: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool
    message: str


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "authentication",
        "database": "connected" if DATABASE_AVAILABLE else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with user_id and password."""
    api_logger.log_request("POST", "/auth/login", request_id=f"login_{request.user_id}")
    
    start_time = datetime.utcnow()
    
    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Validate input
        if not request.user_id or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID and password are required"
            )
        
        # Find user in database
        user_doc = db_config.users.find_one({"user_id": request.user_id})
        
        if not user_doc:
            api_logger.warning(f"🔐 Login attempt for non-existent user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID or password"
            )
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            api_logger.warning(f"🔐 Login attempt for inactive user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Verify password
        stored_password_hash = user_doc.get("password_hash")
        if not stored_password_hash:
            api_logger.error(f"🔐 User {request.user_id} has no password hash")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User account configuration error"
            )
        
        if not verify_password(request.password, stored_password_hash):
            api_logger.warning(f"🔐 Invalid password for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID or password"
            )
        
        # Update last login
        db_config.users.update_one(
            {"user_id": request.user_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Prepare user data (exclude sensitive fields)
        user_data = {
            "user_id": user_doc["user_id"],
            "display_name": user_doc.get("display_name", user_doc["user_id"]),
            "email": user_doc.get("email"),
            "is_active": user_doc.get("is_active", True),
            "created_at": user_doc.get("created_at"),
            "last_login": datetime.utcnow().isoformat(),
        }
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time, user_id=request.user_id, request_id=f"login_{request.user_id}")
        api_logger.info(f"✅ Successful login for user: {request.user_id}")
        
        return LoginResponse(
            success=True,
            user=user_data,
            message="Login successful"
        )
        
    except HTTPException:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(401, processing_time, user_id=request.user_id, request_id=f"login_{request.user_id}")
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time, user_id=request.user_id, request_id=f"login_{request.user_id}")
        api_logger.error(f"❌ Login error for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/auth/logout", response_model=LogoutResponse)
async def logout():
    """Logout user (placeholder for future session management)."""
    api_logger.log_request("POST", "/auth/logout")
    
    # For now, just return success
    # In the future, this could invalidate tokens/sessions
    
    api_logger.info("✅ User logout")
    return LogoutResponse(
        success=True,
        message="Logout successful"
    )


@app.get("/auth/me")
async def get_current_user():
    """Get current user info (placeholder for future token-based auth)."""
    # This would validate JWT token and return user info
    # For now, return placeholder
    return {"message": "Token-based authentication not implemented yet"}


# Admin endpoints
@app.get("/admin/users")
async def get_all_users():
    """Get all users for admin dashboard."""
    api_logger.log_request("GET", "/admin/users")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Get all users
        users_cursor = db_config.users.find({})
        users = []

        for user_doc in users_cursor:
            user_data = {
                "user_id": user_doc["user_id"],
                "display_name": user_doc.get("display_name", user_doc["user_id"]),
                "email": user_doc.get("email"),
                "is_active": user_doc.get("is_active", True),
                "created_at": user_doc.get("created_at"),
                "last_login": user_doc.get("last_login"),
                "has_password": bool(user_doc.get("password_hash"))
            }
            users.append(user_data)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "users": users,
            "total": len(users)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/admin/sessions")
async def get_all_sessions():
    """Get all chat sessions for admin dashboard."""
    api_logger.log_request("GET", "/admin/sessions")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Get all sessions with user info
        sessions_cursor = db_config.sessions.find({}).sort("updated_at", -1)
        sessions = []

        for session_doc in sessions_cursor:
            session_data = {
                "session_id": session_doc["session_id"],
                "user_id": session_doc["user_id"],
                "title": session_doc.get("title", f"Session {session_doc['session_id'][:8]}"),
                "created_at": session_doc.get("created_at"),
                "updated_at": session_doc.get("updated_at"),
                "total_messages": session_doc.get("total_messages", 0),
                "is_active": session_doc.get("is_active", True)
            }
            sessions.append(session_data)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/admin/stats")
async def get_admin_stats():
    """Get admin dashboard statistics."""
    api_logger.log_request("GET", "/admin/stats")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Get statistics
        total_users = db_config.users.count_documents({})
        active_users = db_config.users.count_documents({"is_active": True})
        total_sessions = db_config.sessions.count_documents({})
        active_sessions = db_config.sessions.count_documents({"is_active": True})
        total_messages = db_config.messages.count_documents({})

        # Get recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_sessions = db_config.sessions.count_documents({
            "created_at": {"$gte": yesterday.isoformat()}
        })
        recent_messages = db_config.messages.count_documents({
            "created_at": {"$gte": yesterday.isoformat()}
        })

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "active_users": active_users,
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "recent_sessions_24h": recent_sessions,
                "recent_messages_24h": recent_messages
            }
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/user/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """Get chat sessions for a specific user."""
    api_logger.log_request("GET", f"/user/{user_id}/sessions")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Get user sessions
        sessions_cursor = db_config.sessions.find({"user_id": user_id}).sort("updated_at", -1)
        sessions = []

        for session_doc in sessions_cursor:
            session_data = {
                "session_id": session_doc["session_id"],
                "session_name": session_doc.get("title", f"Session {session_doc['session_id'][:8]}"),
                "user_id": session_doc["user_id"],
                "created_at": session_doc.get("created_at"),
                "updated_at": session_doc.get("updated_at"),
                "is_active": session_doc.get("is_active", True),
                "message_count": session_doc.get("total_messages", 0),
                "last_message_preview": ""  # TODO: Get from last message
            }
            sessions.append(session_data)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time, user_id=user_id)

        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time, user_id=user_id)
        api_logger.error(f"❌ Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a specific session."""
    api_logger.log_request("GET", f"/session/{session_id}/messages")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Get session messages
        messages_cursor = db_config.messages.find({"session_id": session_id}).sort("created_at", 1)
        messages = []

        for message_doc in messages_cursor:
            message_data = {
                "message_id": message_doc["message_id"],
                "session_id": message_doc["session_id"],
                "user_id": message_doc["user_id"],
                "user_input": message_doc["user_input"],
                "agent_response": message_doc.get("agent_response"),
                "created_at": message_doc.get("created_at"),
                "processing_time": message_doc.get("processing_time"),
                "primary_intent": message_doc.get("primary_intent"),
                "processing_mode": message_doc.get("processing_mode"),
                "success": message_doc.get("success", True)
            }
            messages.append(message_data)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "messages": messages,
            "total": len(messages)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting session messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.put("/session/{session_id}/title")
async def update_session_title(session_id: str, title_data: dict):
    """Update session title."""
    api_logger.log_request("PUT", f"/session/{session_id}/title")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        new_title = title_data.get("title", "").strip()
        if not new_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty"
            )

        # Update session title
        result = db_config.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "title": new_title,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "message": "Session title updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error updating session title: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    api_logger.log_request("DELETE", f"/session/{session_id}")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Delete session messages first
        messages_result = db_config.messages.delete_many({"session_id": session_id})

        # Delete session
        session_result = db_config.sessions.delete_one({"session_id": session_id})

        if session_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "message": f"Session deleted successfully. Removed {messages_result.deleted_count} messages."
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


if __name__ == "__main__":
    system_logger.info("🚀 Starting Authentication API server on port 8000...")
    uvicorn.run(
        "auth_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
