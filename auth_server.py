"""
Authentication API Server for Multi-Agent System - Optimized Version
Provides REST API endpoints for user authentication with MongoDB
Optimized with lazy loading, caching, and connection pooling
"""
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import io
import asyncio
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Global cache for lazy loading
_cache: Dict[str, Any] = {}

class LazyLoader:
    """Lazy loader for modules and connections."""
    
    @staticmethod
    def get_loggers():
        """Lazy load optimized loggers."""
        if 'loggers' not in _cache:
            try:
                from src.utils.optimized_logger import get_api_logger, get_system_logger
                _cache['loggers'] = (get_api_logger(), get_system_logger())
            except ImportError:
                # Fallback to original loggers
                from src.utils.logger import api_logger, system_logger
                _cache['loggers'] = (api_logger, system_logger)
        return _cache['loggers']

    @staticmethod
    def get_database_models():
        """Lazy load database models."""
        if 'db_models' not in _cache:
            try:
                from src.database.models import get_db_config, User
                _cache['db_models'] = (get_db_config, User)
                _cache['db_available'] = True
                api_logger, system_logger = LazyLoader.get_loggers()
                system_logger.info("✅ Database models loaded successfully")
            except ImportError as e:
                _cache['db_models'] = None
                _cache['db_available'] = False
                api_logger, system_logger = LazyLoader.get_loggers()
                system_logger.warning(f"⚠️ Database models not available: {e}")
        return _cache['db_models'], _cache['db_available']

    @staticmethod
    def get_db_connection():
        """Lazy load database connection with connection pooling."""
        if 'db_connection' not in _cache:
            db_models, db_available = LazyLoader.get_database_models()
            if db_available and db_models:
                try:
                    get_db_config, _ = db_models
                    _cache['db_connection'] = get_db_config()
                    api_logger, system_logger = LazyLoader.get_loggers()
                    system_logger.info("✅ Database connection initialized")
                except Exception as e:
                    _cache['db_connection'] = None
                    api_logger, system_logger = LazyLoader.get_loggers()
                    system_logger.error(f"❌ Failed to initialize database: {e}")
            else:
                _cache['db_connection'] = None
        return _cache['db_connection']

    @staticmethod
    def get_s3_manager():
        """Lazy load S3 manager."""
        if 's3_manager' not in _cache:
            try:
                from src.database.model_s3 import get_s3_manager as _get_s3_manager
                _cache['s3_manager'] = _get_s3_manager
                _cache['s3_available'] = True
                api_logger, system_logger = LazyLoader.get_loggers()
                system_logger.info("✅ S3 manager loaded successfully")
            except ImportError as e:
                _cache['s3_manager'] = None
                _cache['s3_available'] = False
                api_logger, system_logger = LazyLoader.get_loggers()
                system_logger.warning(f"⚠️ S3 manager not available: {e}")
        return _cache['s3_manager'], _cache['s3_available']

    @staticmethod
    def get_file_manager():
        """Lazy load file manager."""
        if 'file_manager' not in _cache:
            try:
                from src.services.file_manager import get_file_manager as _get_file_manager
                _cache['file_manager'] = _get_file_manager
                _cache['file_manager_available'] = True
                api_logger, system_logger = LazyLoader.get_loggers()
                system_logger.info("✅ File manager loaded successfully")
            except ImportError as e:
                _cache['file_manager'] = None
                _cache['file_manager_available'] = False
                api_logger, system_logger = LazyLoader.get_loggers()
                system_logger.warning(f"⚠️ File manager not available: {e}")
        return _cache['file_manager'], _cache['file_manager_available']

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System Authentication API - Optimized",
    description="Authentication service for the Multi-Agent System with performance optimizations",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Utility functions with caching
@lru_cache(maxsize=1000)
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt. Cached for performance."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash

@lru_cache(maxsize=100)
def is_admin_user(user_id: str) -> bool:
    """Check if a user has editor role. Cached for performance."""
    db_models, db_available = LazyLoader.get_database_models()
    db_config = LazyLoader.get_db_connection()
    
    if not db_available or not db_config:
        return False

    user_doc = db_config.users.find_one({"user_id": user_id})
    if not user_doc:
        return False

    return user_doc.get("role") == "editor"

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_models, db_available = LazyLoader.get_database_models()
    return {
        "status": "healthy",
        "service": "authentication-optimized",
        "database": "connected" if db_available else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

# Login endpoint with optimizations
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with user_id and password. Optimized version."""
    api_logger, system_logger = LazyLoader.get_loggers()
    api_logger.info(f"🌐 POST /auth/login - User: {request.user_id}")
    
    start_time = datetime.now(timezone.utc)
    
    try:
        db_models, db_available = LazyLoader.get_database_models()
        db_config = LazyLoader.get_db_connection()
        
        if not db_available or not db_config:
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            api_logger.log_response(503, processing_time)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
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
                    "display_name": admin_doc.get("display_name", admin_doc.get("admin_id")),
                    "email": admin_doc.get("email"),
                    "password_hash": admin_doc.get("password_hash"),
                    "role": "editor",  # Admins have editor role
                    "is_active": admin_doc.get("is_active", True),
                    "created_at": admin_doc.get("created_at"),
                    "updated_at": admin_doc.get("updated_at"),
                    "last_login": admin_doc.get("last_login"),
                    "number_upload_files": admin_doc.get("number_upload_files", 10)  # Admins get more files
                }
                is_admin_user = True

        if not user_doc:
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            api_logger.log_response(401, processing_time)
            return LoginResponse(
                success=False,
                error="Invalid user ID or password"
            )

        # Verify password
        if not verify_password(request.password, user_doc.get("password_hash", "")):
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            api_logger.log_response(401, processing_time)
            return LoginResponse(
                success=False,
                error="Invalid user ID or password"
            )

        # Check if user is active
        if not user_doc.get("is_active", True):
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            api_logger.log_response(403, processing_time)
            return LoginResponse(
                success=False,
                error="Account is deactivated"
            )

        # Update last login in appropriate collection
        if is_admin_user:
            db_config.admins.update_one(
                {"admin_id": request.user_id},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
        else:
            db_config.users.update_one(
                {"user_id": request.user_id},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )

        # Prepare user data for response (exclude sensitive information)
        user_data = {
            "user_id": user_doc["user_id"],
            "display_name": user_doc.get("display_name", user_doc["user_id"]),
            "email": user_doc.get("email"),
            "role": user_doc.get("role", "user"),
            "is_active": user_doc.get("is_active", True),
            "created_at": user_doc.get("created_at"),
            "last_login": user_doc.get("last_login"),
            "number_upload_files": user_doc.get("number_upload_files", 3)
        }

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        api_logger.log_response(200, processing_time)
        system_logger.info(f"✅ User {request.user_id} logged in successfully")

        return LoginResponse(
            success=True,
            user=user_data,
            message="Login successful"
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        api_logger.log_response(500, processing_time)
        api_logger.error(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

if __name__ == "__main__":
    api_logger, system_logger = LazyLoader.get_loggers()
    system_logger.info("🚀 Starting Optimized Authentication API server on port 8000...")
    uvicorn.run(
        "auth_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
