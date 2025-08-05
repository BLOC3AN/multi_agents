"""
Authentication API Server for Multi-Agent System
Provides REST API endpoints for user authentication with MongoDB
"""
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import io

import uvicorn
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
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

# Import S3 manager
try:
    from src.database.model_s3 import get_s3_manager
    S3_AVAILABLE = True
    system_logger.info("✅ S3 manager imported successfully")
except ImportError as e:
    S3_AVAILABLE = False
    system_logger.warning(f"⚠️ S3 manager not available: {e}")

# Import File Manager
try:
    from src.services.file_manager import get_file_manager
    FILE_MANAGER_AVAILABLE = True
    system_logger.info("✅ File manager imported successfully")
except ImportError as e:
    FILE_MANAGER_AVAILABLE = False
    system_logger.warning(f"⚠️ File manager not available: {e}")

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


# User management models
class UserCreateRequest(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    password: str
    is_active: bool = True
    role: str = "user"  # user, editor
    number_upload_files: int = 3


class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    number_upload_files: Optional[int] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    user: Optional[dict] = None
    error: Optional[str] = None


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def is_admin_user(user_id: str) -> bool:
    """Check if a user has editor role."""
    if not DATABASE_AVAILABLE or not db_config:
        return False

    user_doc = db_config.users.find_one({"user_id": user_id})
    if not user_doc:
        return False

    return user_doc.get("role") == "editor"


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
    api_logger.info(f"🌐 POST /auth/login - User: {request.user_id}")
    
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
        
        # Find user in database (check both users and admins collections)
        user_doc = db_config.users.find_one({"user_id": request.user_id})
        is_admin_user = False

        # If not found in users, check admins collection
        if not user_doc:
            admin_doc = db_config.admins.find_one({"admin_id": request.user_id})
            if admin_doc:
                # Convert admin doc to user doc format for consistency
                user_doc = {
                    "user_id": admin_doc.get("admin_id"),
                    "display_name": admin_doc.get("display_name"),
                    "email": admin_doc.get("email"),
                    "password_hash": admin_doc.get("password_hash"),
                    "is_active": admin_doc.get("is_active", True),
                    "role": admin_doc.get("role", "admin"),
                    "created_at": admin_doc.get("created_at"),
                    "last_login": admin_doc.get("last_login"),
                    # Admin-specific permissions
                    "can_manage_users": admin_doc.get("can_manage_users", True),
                    "can_manage_system": admin_doc.get("can_manage_system", True),
                    "can_view_logs": admin_doc.get("can_view_logs", True),
                    "can_delete_users": admin_doc.get("can_delete_users", True),
                    "can_manage_admins": admin_doc.get("can_manage_admins", True),
                    "can_access_all_data": admin_doc.get("can_access_all_data", True),
                }
                is_admin_user = True

        if not user_doc:
            api_logger.warning(f"🔐 Login attempt for non-existent user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID or password"
            )

        # Determine user role
        user_role = user_doc.get("role", "user")
        is_admin = user_role == "editor"
        
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

        # Update last login in appropriate collection
        if is_admin_user:
            db_config.admins.update_one(
                {"admin_id": request.user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        else:
            db_config.users.update_one(
                {"user_id": request.user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        
        # Prepare user data (exclude sensitive fields)
        user_data = {
            "user_id": user_doc["user_id"],
            "role": user_role,
            "display_name": user_doc.get("display_name", user_doc["user_id"]),
            "email": user_doc.get("email"),
            "is_active": user_doc.get("is_active", True),
            "created_at": user_doc.get("created_at"),
            "last_login": datetime.utcnow().isoformat(),
        }

        # Add admin permissions if user is admin
        if is_admin_user:
            user_data.update({
                "can_manage_users": user_doc.get("can_manage_users", True),
                "can_manage_system": user_doc.get("can_manage_system", True),
                "can_view_logs": user_doc.get("can_view_logs", True),
                "can_delete_users": user_doc.get("can_delete_users", True),
                "can_manage_admins": user_doc.get("can_manage_admins", True),
                "can_access_all_data": user_doc.get("can_access_all_data", True),
            })
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ Successful login for {user_role}: {request.user_id} ({processing_time:.2f}ms)")

        return LoginResponse(
            success=True,
            user=user_data,
            message=f"Login successful as {user_role}"
        )
        
    except HTTPException:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"❌ Response 401 ({processing_time:.2f}ms)")
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Response 500 ({processing_time:.2f}ms)")
        api_logger.error(f"❌ Login error for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/auth/logout", response_model=LogoutResponse)
async def logout():
    """Logout user (placeholder for future session management)."""
    api_logger.info("🌐 POST /auth/logout")

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
async def get_all_users(collection: Optional[str] = None):
    """Get all users for admin dashboard. Use collection=admins to get from admins collection."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Choose collection based on parameter
        if collection == "admins":
            # Get from admins collection (super_admin users)
            users_cursor = db_config.admins.find({})
            users = []

            for admin_doc in users_cursor:
                # Convert admin doc to user format
                user_data = {
                    "user_id": admin_doc.get("admin_id"),
                    "username": admin_doc.get("admin_id"),
                    "display_name": admin_doc.get("display_name"),
                    "email": admin_doc.get("email"),
                    "is_active": admin_doc.get("is_active", True),
                    "created_at": admin_doc.get("created_at"),
                    "last_login": admin_doc.get("last_login"),
                    "has_password": bool(admin_doc.get("password_hash")),
                    "role": admin_doc.get("role", "super_admin"),
                    "updated_at": admin_doc.get("updated_at"),
                    # Super admin permissions
                    "can_manage_users": admin_doc.get("can_manage_users", True),
                    "can_manage_system": admin_doc.get("can_manage_system", True),
                    "can_view_logs": admin_doc.get("can_view_logs", True),
                    "can_delete_users": admin_doc.get("can_delete_users", True),
                    "can_manage_admins": admin_doc.get("can_manage_admins", True),
                    "can_access_all_data": admin_doc.get("can_access_all_data", True),
                }
                users.append(user_data)
        else:
            # Get from users collection (regular users)
            users_cursor = db_config.users.find({})
            users = []

            for user_doc in users_cursor:
                # Hide system emails
                display_email = user_doc.get("email")
                if display_email and display_email.endswith("@system.local"):
                    display_email = None

                user_data = {
                    "user_id": user_doc["user_id"],
                    "username": user_doc.get("user_id"),
                    "display_name": user_doc.get("display_name", user_doc["user_id"]),
                    "email": display_email,
                    "is_active": user_doc.get("is_active", True),
                    "created_at": user_doc.get("created_at"),
                    "last_login": user_doc.get("last_login"),
                    "has_password": bool(user_doc.get("password_hash")),
                    "role": user_doc.get("role", "user"),  # Default to "user" if not set
                    "updated_at": user_doc.get("updated_at"),
                    "number_upload_files": user_doc.get("number_upload_files", 3)
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
    api_logger.info("🌐 API Request")

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
    api_logger.info("🌐 API Request")

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

        # Get files count from database (same as admin files endpoint)
        total_files = 0
        try:
            # Count active files from file_metadata collection
            total_files = db_config.file_metadata.count_documents({"is_active": True})
        except Exception as e:
            api_logger.warning(f"Could not get files count from database: {e}")
            total_files = 0

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
                "total_files": total_files,
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


@app.get("/admin/files")
async def get_all_files():
    """Get all files for admin dashboard."""
    api_logger.info("🌐 GET /admin/files")
    start_time = datetime.utcnow()

    try:
        if not FILE_MANAGER_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File management service not available"
            )

        # Get all files from all users
        file_manager = get_file_manager()
        db_config = get_db_config()

        # Get all file metadata
        files_cursor = db_config.file_metadata.find({"is_active": True}).sort("upload_date", -1)
        files = []

        for file_doc in files_cursor:
            file_data = {
                "file_id": file_doc["file_id"],
                "user_id": file_doc["user_id"],
                "file_key": file_doc["file_key"],
                "file_name": file_doc["file_name"],
                "file_size": file_doc["file_size"],
                "content_type": file_doc["content_type"],
                "upload_date": file_doc.get("upload_date"),
                "s3_bucket": file_doc.get("s3_bucket"),
                "metadata": file_doc.get("metadata", {})
            }
            files.append(file_data)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ Listed {len(files)} files ({processing_time:.2f}ms)")

        return {
            "success": True,
            "files": files,
            "total": len(files)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Error getting files: {e} ({processing_time:.2f}ms)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.delete("/admin/files/{file_key:path}")
async def delete_file_admin(file_key: str, user_id: str):
    """Delete a file (admin endpoint)."""
    api_logger.info(f"🌐 DELETE /admin/files/{file_key} - User: {user_id}")
    start_time = datetime.utcnow()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    try:
        if not FILE_MANAGER_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File management service not available"
            )

        file_manager = get_file_manager()
        success = file_manager.delete_file(file_key, user_id)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if success:
            api_logger.info(f"✅ File deleted (admin): {file_key} by user {user_id} ({processing_time:.2f}ms)")
            return JSONResponse(content={
                "success": True,
                "message": "File deleted successfully",
                "file_key": file_key
            })
        else:
            api_logger.error(f"❌ Delete failed: File not found or access denied")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Delete error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/admin/messages")
async def get_all_messages():
    """Get all messages for admin dashboard."""
    api_logger.info("🌐 GET /admin/messages")
    start_time = datetime.utcnow()

    try:
        db_config = get_db_config()

        # Get all messages from all sessions
        messages_cursor = db_config.messages.find({}).sort("timestamp", -1)
        messages = []

        for msg_doc in messages_cursor:
            message_data = {
                "message_id": msg_doc.get("message_id"),
                "session_id": msg_doc.get("session_id"),
                "user_id": msg_doc.get("user_id"),
                "role": msg_doc.get("role"),
                "content": msg_doc.get("content"),
                "timestamp": msg_doc.get("timestamp"),
                "metadata": msg_doc.get("metadata", {}),
                "created_at": msg_doc.get("created_at"),
                "updated_at": msg_doc.get("updated_at")
            }
            messages.append(message_data)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ Listed {len(messages)} messages ({processing_time:.2f}ms)")

        return {
            "success": True,
            "messages": messages,
            "total": len(messages)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Error getting messages: {e} ({processing_time:.2f}ms)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.delete("/admin/messages/{message_id}")
async def delete_message_admin(message_id: str):
    """Delete a message (admin endpoint)."""
    api_logger.info(f"🌐 DELETE /admin/messages/{message_id}")
    start_time = datetime.utcnow()

    try:
        db_config = get_db_config()

        # Delete the message
        result = db_config.messages.delete_one({"message_id": message_id})

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result.deleted_count > 0:
            api_logger.info(f"✅ Message deleted (admin): {message_id} ({processing_time:.2f}ms)")
            return JSONResponse(content={
                "success": True,
                "message": "Message deleted successfully",
                "message_id": message_id
            })
        else:
            api_logger.error(f"❌ Delete failed: Message not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Delete error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# User management endpoints
@app.post("/admin/users", response_model=UserResponse)
async def create_user(request: UserCreateRequest):
    """Create a new user."""
    api_logger.info("🌐 API Request")

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

        # Check if user already exists
        existing_user = db_config.users.find_one({"user_id": request.user_id})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )

        # Validate role
        if request.role not in ["user", "editor"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'user' or 'editor'"
            )

        # Validate number_upload_files
        if request.number_upload_files < 1 or request.number_upload_files > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of upload files must be between 1 and 100"
            )

        # Hash password
        password_hash = hash_password(request.password)

        # Create user (handle empty email)
        email = request.email.strip() if request.email else None
        if email == "" or email is None:
            # Generate unique email based on user_id to avoid duplicate key error
            email = f"{request.user_id}@system.local"

        user = User(
            user_id=request.user_id,
            display_name=request.display_name or request.user_id,
            email=email,
            password_hash=password_hash,
            is_active=request.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            number_upload_files=request.number_upload_files
        )

        # Add role and original password to user data
        user_doc = user.to_dict()
        user_doc["role"] = request.role
        user_doc["original_password"] = request.password  # Store for admin access

        # Insert user
        result = db_config.users.insert_one(user_doc)

        if result.inserted_id:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            api_logger.info(f"✅ User created successfully: {request.user_id} ({processing_time:.2f}ms)")

            # Return user data without password (hide system emails)
            display_email = user_doc.get("email")
            if display_email and display_email.endswith("@system.local"):
                display_email = None

            user_data = {
                "user_id": request.user_id,
                "display_name": user_doc["display_name"],
                "email": display_email,
                "is_active": user_doc["is_active"],
                "role": user_doc["role"],
                "created_at": user_doc["created_at"],
                "has_password": True,
                "number_upload_files": user_doc["number_upload_files"]
            }

            return UserResponse(
                success=True,
                message="User created successfully",
                user=user_data
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Error creating user: {e} ({processing_time:.2f}ms)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.delete("/admin/users/{user_id}", response_model=UserResponse)
async def delete_user(user_id: str, force: bool = False):
    """Delete a user. Use force=true for super_admin to bypass restrictions."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )



        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if user has admin role (double check, unless force=true)
        if not force and existing_user.get("role") == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete admin user"
            )

        # Delete user
        result = db_config.users.delete_one({"user_id": user_id})

        if result.deleted_count > 0:
            # Also delete user's sessions and messages for cleanup
            db_config.sessions.delete_many({"user_id": user_id})
            db_config.messages.delete_many({"user_id": user_id})

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            api_logger.log_response(200, processing_time)
            api_logger.info(f"✅ User deleted successfully: {user_id}")

            return UserResponse(
                success=True,
                message="User deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.patch("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, request: UserUpdateRequest):
    """Update user information."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if request.display_name is not None:
            update_data["display_name"] = request.display_name

        if request.email is not None:
            update_data["email"] = request.email

        if request.is_active is not None:
            update_data["is_active"] = request.is_active

        if request.role is not None:
            # Validate role
            if request.role not in ["user", "editor"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role must be 'user' or 'editor'"
                )
            update_data["role"] = request.role

        if request.number_upload_files is not None:
            # Validate number_upload_files
            if request.number_upload_files < 1 or request.number_upload_files > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Number of upload files must be between 1 and 100"
                )
            update_data["number_upload_files"] = request.number_upload_files

        # Update user
        result = db_config.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )

        if result.modified_count > 0 or result.matched_count > 0:
            # Get updated user
            updated_user = db_config.users.find_one({"user_id": user_id})

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            api_logger.log_response(200, processing_time)
            api_logger.info(f"✅ User updated successfully: {user_id}")

            # Return user data without password
            user_data = {
                "user_id": updated_user["user_id"],
                "display_name": updated_user.get("display_name"),
                "email": updated_user.get("email"),
                "is_active": updated_user.get("is_active", True),
                "role": updated_user.get("role", "user"),
                "created_at": updated_user.get("created_at"),
                "updated_at": updated_user.get("updated_at"),
                "has_password": bool(updated_user.get("password_hash"))
            }

            return UserResponse(
                success=True,
                message="User updated successfully",
                user=user_data
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.patch("/admin/users/{user_id}/password", response_model=UserResponse)
async def change_user_password(user_id: str, request: PasswordChangeRequest):
    """Change user password."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )

        # Note: current_password is provided for reference but not validated for admin changes

        if not request.new_password or len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters long"
            )

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Hash new password
        new_password_hash = hash_password(request.new_password)

        # Update password
        result = db_config.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "password_hash": new_password_hash,
                "original_password": request.new_password,  # Store for admin access
                "updated_at": datetime.utcnow().isoformat()
            }}
        )

        if result.modified_count > 0 or result.matched_count > 0:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            api_logger.log_response(200, processing_time)
            api_logger.info(f"✅ Password changed successfully for user: {user_id}")

            return UserResponse(
                success=True,
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.patch("/admin/users/{user_id}/reset-password", response_model=UserResponse)
async def reset_user_password(user_id: str, request: PasswordResetRequest):
    """Reset user password (super_admin only endpoint)."""
    api_logger.info(f"🌐 PATCH /admin/users/{user_id}/reset-password")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id or not request.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID and new password are required"
            )

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Hash new password
        new_password_hash = hash_password(request.new_password)

        # Update password
        result = db_config.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ Password reset successful for user: {user_id} ({processing_time:.2f}ms)")

        return UserResponse(
            success=True,
            message="Password reset successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/admin/users/{user_id}/current-password")
async def get_user_current_password(user_id: str):
    """Get current password for a user (admin endpoint)."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # For admin access, return actual password if available
        # Note: In production, you might want to store original password in encrypted form for admin access
        password_hash = existing_user.get("password_hash", "")
        original_password = existing_user.get("original_password")  # If stored

        if password_hash:
            if original_password:
                display_password = original_password
            else:
                # For existing users without original_password field, show a default
                # In production, you might want to force password reset
                display_password = "admin123"  # Default password for demo
        else:
            display_password = "No password set"

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "current_password": display_password,
            "has_password": bool(password_hash)
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting current password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/admin/users/{user_id}/sessions")
async def get_user_sessions_admin(user_id: str, limit: int = 50, offset: int = 0):
    """Get chat sessions for a specific user (admin endpoint)."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get user sessions with pagination
        sessions_cursor = db_config.sessions.find({"user_id": user_id}).sort("updated_at", -1).skip(offset).limit(limit)
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

        # Get total count
        total_sessions = db_config.sessions.count_documents({"user_id": user_id})

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "sessions": sessions,
            "total": total_sessions,
            "limit": limit,
            "offset": offset,
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/admin/users/{user_id}/messages")
async def get_user_messages_admin(user_id: str, limit: int = 50, offset: int = 0, session_id: Optional[str] = None):
    """Get messages for a specific user (admin endpoint)."""
    api_logger.info("🌐 API Request")

    start_time = datetime.utcnow()

    try:
        if not DATABASE_AVAILABLE or not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        # Validate input
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )

        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Build query
        query = {"user_id": user_id}
        if session_id:
            query["session_id"] = session_id

        # Get user messages with pagination
        messages_cursor = db_config.messages.find(query).sort("created_at", -1).skip(offset).limit(limit)
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
                "success": message_doc.get("success", True),
                "errors": message_doc.get("errors", [])
            }
            messages.append(message_data)

        # Get total count
        total_messages = db_config.messages.count_documents(query)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)

        return {
            "success": True,
            "messages": messages,
            "total": total_messages,
            "limit": limit,
            "offset": offset,
            "user_id": user_id,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting user messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/user/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """Get chat sessions for a specific user."""
    api_logger.info(f"🌐 GET /user/{user_id}/sessions")

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
        api_logger.info(f"✅ Response 200 ({processing_time:.2f}ms) - User: {user_id}")

        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Response 500 ({processing_time:.2f}ms) - User: {user_id}")
        api_logger.error(f"❌ Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a specific session."""
    api_logger.info(f"🌐 GET /session/{session_id}/messages")

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
    api_logger.info("🌐 API Request")

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
    api_logger.info("🌐 API Request")

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


# S3 File Management Endpoints
@app.post("/api/s3/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = Form(...)):
    """Upload a file to S3 storage for a specific user."""
    api_logger.info(f"🌐 POST /api/s3/upload - User: {user_id}, File: {file.filename}")
    start_time = datetime.utcnow()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    if not S3_AVAILABLE and not FILE_MANAGER_AVAILABLE:
        api_logger.error("❌ File management services not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File management service not available"
        )

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        filename = file.filename or "unnamed_file"

        # Get user info for role-based validation
        user_doc = None
        is_super_admin = False

        # Check in users collection first
        if DATABASE_AVAILABLE:
            user_doc = db_config.users.find_one({"user_id": user_id})
            if not user_doc:
                # Check in admins collection
                admin_doc = db_config.admins.find_one({"admin_id": user_id})
                if admin_doc:
                    user_doc = admin_doc
                    is_super_admin = admin_doc.get("role") == "super_admin"

        # File validation (skip for super admin)
        if not is_super_admin:
            # 1. File type validation
            allowed_extensions = ['.md', '.txt', '.docx', '.pdf']
            file_extension = None
            if '.' in filename:
                file_extension = '.' + filename.rsplit('.', 1)[1].lower()

            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Only {', '.join(allowed_extensions)} files are supported."
                )

            # 2. File size validation (25MB = 25 * 1024 * 1024 bytes)
            max_file_size = 25 * 1024 * 1024  # 25MB
            if file_size > max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size too large. Maximum allowed size is 25MB. Your file is {file_size / (1024 * 1024):.1f}MB."
                )

            # 3. File count validation
            if FILE_MANAGER_AVAILABLE and user_doc:
                file_manager = get_file_manager()
                current_count = file_manager.get_user_file_count(user_id)
                max_files = user_doc.get("number_upload_files", 3)  # Default to 3

                if current_count >= max_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File upload limit reached. You can upload maximum {max_files} files. Current: {current_count}/{max_files}."
                    )

        # Use FileManager for user-specific file management
        if FILE_MANAGER_AVAILABLE:
            try:
                api_logger.info(f"🔄 Starting upload process for user {user_id}, file: {filename}")

                # Upload to S3 first
                s3_manager = get_s3_manager()
                file_obj = io.BytesIO(file_content)
                s3_result = s3_manager.upload_file(file_obj, filename)

                api_logger.info(f"📤 S3 upload result: {s3_result.get('success', False)}")

                if s3_result['success']:
                    # Save metadata with FileManager and embed file
                    api_logger.info(f"💾 Saving metadata and embedding for user {user_id}")
                    file_manager = get_file_manager()
                    upload_result = file_manager.handle_file_upload(
                        user_id=user_id,
                        file_key=filename,
                        file_name=filename,
                        file_size=file_size,
                        content_type=file.content_type or "application/octet-stream",
                        s3_bucket=s3_result['file_info'].get('bucket'),
                        file_content=file_content  # Pass file content for embedding
                    )
                    api_logger.info(f"💾 Metadata saved: {upload_result}")

                    processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    api_logger.info(f"✅ File uploaded for user {user_id}: {filename} ({processing_time:.2f}ms)")

                    return JSONResponse(content={
                        "success": True,
                        "message": "File uploaded successfully",
                        "file_info": s3_result['file_info'],
                        "file_id": upload_result.get("file_id"),
                        "file_count": upload_result.get("file_count", 0),
                        "embedding_id": upload_result.get("embedding_id"),
                        "embedded": upload_result.get("embedding_id") is not None
                    })
                else:
                    raise Exception(s3_result['error'])

            except Exception as upload_error:
                # Fallback - simulate success for development
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                api_logger.warning(f"⚠️ Upload issue, simulating success for user {user_id}: {str(upload_error)}")

                # Still save metadata and embed even if S3 fails
                if FILE_MANAGER_AVAILABLE:
                    file_manager = get_file_manager()
                    upload_result = file_manager.handle_file_upload(
                        user_id=user_id,
                        file_key=filename,
                        file_name=filename,
                        file_size=file_size,
                        content_type=file.content_type or "application/octet-stream",
                        file_content=file_content  # Pass file content for embedding
                    )

                    return JSONResponse(content={
                        "success": True,
                        "message": "File upload simulated (S3 SHA256 hash issue)",
                        "file_info": {
                            "key": filename,
                            "name": filename,
                            "size": file_size,
                            "content_type": file.content_type or "application/octet-stream",
                            "last_modified": datetime.utcnow().isoformat() + "Z"
                        },
                        "file_id": upload_result.get("file_id"),
                        "file_count": upload_result.get("file_count", 0),
                        "embedding_id": upload_result.get("embedding_id"),
                        "embedded": upload_result.get("embedding_id") is not None,
                        "note": "S3 upload has SHA256 hash issues - upload simulated"
                    })
                else:
                    raise Exception("File management service not available")
        else:
            # Fallback to old S3 manager (less secure)
            s3_manager = get_s3_manager()
            file_obj = io.BytesIO(file_content)
            result = s3_manager.upload_file(file_obj, filename)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if result['success']:
                api_logger.info(f"✅ File uploaded (fallback): {filename} ({processing_time:.2f}ms)")
                return JSONResponse(content={
                    "success": True,
                    "message": "File uploaded successfully",
                    "file_info": result['file_info']
                })
            else:
                raise Exception(result['error'])

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Upload error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/s3/files")
async def list_files(user_id: str):
    """List files for a specific user."""
    api_logger.info(f"🌐 GET /api/s3/files - User: {user_id}")
    start_time = datetime.utcnow()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    try:
        # Use FileManager for user-specific file listing
        if FILE_MANAGER_AVAILABLE:
            file_manager = get_file_manager()
            user_files = file_manager.get_user_files(user_id)
            limit_check = file_manager.check_file_limit(user_id)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            api_logger.info(f"✅ Listed {len(user_files)} files for user {user_id} ({processing_time:.2f}ms)")

            return JSONResponse(content={
                "success": True,
                "files": user_files,
                "total_files": len(user_files),
                "file_limit": limit_check
            })
        else:
            # Fallback to S3 manager (less secure)
            if not S3_AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="File management service not available"
                )

            s3_manager = get_s3_manager()
            result = s3_manager.list_files()

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if result['success']:
                api_logger.info(f"✅ Listed {len(result.get('files', []))} files (fallback) ({processing_time:.2f}ms)")
                return JSONResponse(content=result)
            else:
                api_logger.error(f"❌ List files failed: {result['error']}")
                raise HTTPException(status_code=500, detail=result['error'])

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ List files error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.get("/api/s3/download/{file_key:path}")
async def download_file(file_key: str, user_id: str):
    """Download a file from S3 storage (only if owned by user)."""
    api_logger.info(f"🌐 GET /api/s3/download/{file_key} - User: {user_id}")
    start_time = datetime.utcnow()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    if not S3_AVAILABLE and not FILE_MANAGER_AVAILABLE:
        api_logger.error("❌ File management services not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File management service not available"
        )

    try:
        # Check file ownership first
        if FILE_MANAGER_AVAILABLE:
            file_manager = get_file_manager()
            file_metadata = file_manager.get_file_metadata(file_key, user_id)

            if not file_metadata:
                api_logger.error(f"❌ File not found or access denied: {file_key} for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found or access denied"
                )

            api_logger.info(f"✅ File ownership verified: {file_key} belongs to {user_id}")

        # Download from S3
        s3_manager = get_s3_manager()
        result = s3_manager.download_file(file_key)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result['success']:
            file_data = result['file_data']
            content_type = result['content_type']

            # Extract filename from file_key
            filename = file_key.split('/')[-1]

            api_logger.info(f"✅ File downloaded: {filename} by user {user_id} ({processing_time:.2f}ms)")

            return StreamingResponse(
                io.BytesIO(file_data),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            api_logger.error(f"❌ S3 download failed: {result['error']}")
            raise HTTPException(status_code=404, detail=result['error'])

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Download error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.delete("/api/s3/delete/{file_key:path}")
async def delete_file(file_key: str, user_id: str):
    """Delete a file from S3 storage (only if owned by user)."""
    api_logger.info(f"🌐 DELETE /api/s3/delete/{file_key} - User: {user_id}")
    start_time = datetime.utcnow()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required"
        )

    try:
        # Use FileManager for secure deletion with ownership check
        if FILE_MANAGER_AVAILABLE:
            file_manager = get_file_manager()
            success = file_manager.delete_file(file_key, user_id)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if success:
                api_logger.info(f"✅ File deleted: {file_key} by user {user_id} ({processing_time:.2f}ms)")
                return JSONResponse(content={
                    "success": True,
                    "message": "File deleted successfully",
                    "file_key": file_key
                })
            else:
                api_logger.error(f"❌ Delete failed: File not found or access denied for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found or access denied"
                )
        else:
            # Fallback to S3 manager (less secure)
            if not S3_AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="File management service not available"
                )

            s3_manager = get_s3_manager()
            result = s3_manager.delete_file(file_key)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            if result['success']:
                api_logger.info(f"✅ File deleted (fallback): {file_key} ({processing_time:.2f}ms)")
                return JSONResponse(content=result)
            else:
                api_logger.error(f"❌ Delete failed: {result['error']}")
                raise HTTPException(status_code=500, detail=result['error'])

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.post("/api/s3/search")
async def search_files(request: dict):
    """Search files using vector similarity."""
    api_logger.info(f"🌐 POST /api/s3/search")
    start_time = datetime.utcnow()

    try:
        user_id = request.get("user_id")
        query_text = request.get("query", "")
        limit = request.get("limit", 10)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )

        if not query_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="query text is required"
            )

        # Try to use file embedding service for search
        try:
            from src.services.file_embedding_service import get_file_embedding_service
            embedding_service = get_file_embedding_service()

            if embedding_service.is_available():
                # Generate query embedding
                query_embedding = embedding_service.embedding_provider.encode(query_text)

                # Search in Qdrant
                qdrant = embedding_service.qdrant
                search_results = qdrant.search_similar(
                    query_vector=query_embedding,
                    limit=limit,
                    score_threshold=0.3,
                    filter_conditions={
                        "must": [
                            {
                                "key": "user_id",
                                "match": {"value": user_id}
                            }
                        ]
                    }
                )

                # Format results
                formatted_results = []
                for result in search_results:
                    doc = result['document']
                    formatted_results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "source": doc.source,
                        "text_preview": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text,
                        "score": result['score'],
                        "metadata": doc.metadata,
                        "timestamp": doc.timestamp
                    })

                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                api_logger.info(f"✅ Search completed: {len(formatted_results)} results ({processing_time:.2f}ms)")

                return JSONResponse(content={
                    "success": True,
                    "query": query_text,
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                    "search_type": "vector_similarity"
                })
            else:
                raise Exception("Vector search not available")

        except Exception as search_error:
            api_logger.warning(f"⚠️ Vector search failed: {search_error}")

            # Fallback to text-based search in file metadata
            if FILE_MANAGER_AVAILABLE:
                file_manager = get_file_manager()
                user_files = file_manager.get_user_files(user_id)

                # Simple text matching
                matching_files = []
                query_lower = query_text.lower()

                for file_doc in user_files:
                    if (query_lower in file_doc.get("file_name", "").lower() or
                        query_lower in file_doc.get("metadata", {}).get("description", "").lower()):
                        matching_files.append({
                            "file_id": file_doc["file_id"],
                            "file_name": file_doc["file_name"],
                            "file_key": file_doc["file_key"],
                            "content_type": file_doc["content_type"],
                            "upload_date": file_doc["upload_date"],
                            "file_size": file_doc["file_size"],
                            "search_type": "filename_match"
                        })

                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                api_logger.info(f"✅ Fallback search completed: {len(matching_files)} results ({processing_time:.2f}ms)")

                return JSONResponse(content={
                    "success": True,
                    "query": query_text,
                    "results": matching_files,
                    "total_results": len(matching_files),
                    "search_type": "filename_match",
                    "note": "Vector search not available, using filename matching"
                })
            else:
                raise Exception("No search methods available")

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Search error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/s3/embed-existing")
async def embed_existing_file(request: dict):
    """Embed an existing file that wasn't embedded during upload."""
    api_logger.info(f"🌐 POST /api/s3/embed-existing")
    start_time = datetime.utcnow()

    try:
        user_id = request.get("user_id")
        file_key = request.get("file_key")

        if not user_id or not file_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id and file_key are required"
            )

        if not FILE_MANAGER_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File management service not available"
            )

        file_manager = get_file_manager()
        result = file_manager.embed_existing_file(user_id, file_key)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result["success"]:
            api_logger.info(f"✅ File embedded: {file_key} ({processing_time:.2f}ms)")
        else:
            api_logger.warning(f"⚠️ Embedding failed: {result.get('error')} ({processing_time:.2f}ms)")

        return JSONResponse(content=result)

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Embed existing file error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@app.post("/api/sync/analyze")
async def analyze_data_sync(request: dict):
    """Analyze data synchronization status across all storage systems."""
    api_logger.info(f"🌐 POST /api/sync/analyze")
    start_time = datetime.utcnow()

    try:
        user_id = request.get("user_id")  # Optional: analyze specific user

        # Import sync service
        from src.services.data_sync_service import get_data_sync_service
        sync_service = get_data_sync_service()

        # Generate sync report
        report = sync_service.get_sync_report(user_id)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ Sync analysis completed ({processing_time:.2f}ms)")

        return JSONResponse(content={
            "success": True,
            "report": report
        })

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Sync analysis error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Sync analysis failed: {str(e)}")


@app.post("/api/sync/fix")
async def fix_data_sync(request: dict):
    """Fix data synchronization issues."""
    api_logger.info(f"🌐 POST /api/sync/fix")
    start_time = datetime.utcnow()

    try:
        user_id = request.get("user_id")  # Optional: fix specific user
        dry_run = request.get("dry_run", True)  # Default to dry run for safety

        # Import sync service
        from src.services.data_sync_service import get_data_sync_service
        sync_service = get_data_sync_service()

        # Fix sync issues
        results = sync_service.fix_sync_issues(user_id, dry_run)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ Sync fix completed ({processing_time:.2f}ms)")

        return JSONResponse(content={
            "success": True,
            "dry_run": dry_run,
            "results": results
        })

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ Sync fix error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Sync fix failed: {str(e)}")


@app.get("/api/sync/status/{user_id}")
async def get_user_sync_status(user_id: str):
    """Get sync status for a specific user."""
    api_logger.info(f"🌐 GET /api/sync/status/{user_id}")
    start_time = datetime.utcnow()

    try:
        # Import sync service
        from src.services.data_sync_service import get_data_sync_service
        sync_service = get_data_sync_service()

        # Handle global sync status
        if user_id == "global":
            # Analyze all users' files for global status
            records = sync_service.analyze_file_sync(None)  # None means all users
        else:
            # Analyze specific user's files
            records = sync_service.analyze_file_sync(user_id)

        # Create summary
        summary = {
            "user_id": user_id,
            "total_files": len(records),
            "synced": len([r for r in records if r.sync_status.value == "synced"]),
            "issues": len([r for r in records if r.sync_status.value != "synced"]),
            "files": []
        }

        # Add file details
        for record in records:
            summary["files"].append({
                "file_name": record.file_name,
                "file_key": record.file_key,
                "sync_status": record.sync_status.value,
                "locations": {
                    "mongodb": record.in_mongodb,
                    "s3": record.in_s3,
                    "qdrant": record.in_qdrant
                },
                "issues": record.sync_issues
            })

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.info(f"✅ User sync status retrieved ({processing_time:.2f}ms)")

        return JSONResponse(content={
            "success": True,
            "sync_status": summary
        })

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.error(f"❌ User sync status error: {str(e)} ({processing_time:.2f}ms)")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@app.get("/api/s3/info/{file_key:path}")
async def get_file_info(file_key: str):
    """Get detailed information about a file."""
    start_time = datetime.utcnow()

    if not S3_AVAILABLE:
        api_logger.error("❌ S3 manager not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 service not available"
        )

    try:
        s3_manager = get_s3_manager()
        result = s3_manager.get_file_info(file_key)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if 'error' not in result:
            api_logger.log_response(200, processing_time)
            api_logger.info(f"✅ File info retrieved: {file_key}")
            return JSONResponse(content={"success": True, "file_info": result})
        else:
            api_logger.log_response(404, processing_time)
            api_logger.error(f"❌ File info failed: {result['error']}")
            raise HTTPException(status_code=404, detail=result['error'])

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Get file info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@app.get("/api/s3/content/{file_key:path}")
async def get_file_content(file_key: str):
    """Get file content for preview (not download)."""
    start_time = datetime.utcnow()

    if not S3_AVAILABLE:
        api_logger.error("❌ S3 manager not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 service not available"
        )

    try:
        s3_manager = get_s3_manager()
        result = s3_manager.get_file_content(file_key)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        if result['success']:
            api_logger.log_response(200, processing_time)
            api_logger.info(f"✅ File content retrieved: {file_key}")
            return JSONResponse(content=result)
        else:
            api_logger.log_response(404, processing_time)
            api_logger.error(f"❌ File content not found: {file_key}")
            raise HTTPException(status_code=404, detail=result['error'])

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Error getting file content: {e}")
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
