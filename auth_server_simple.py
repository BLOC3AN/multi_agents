"""
Simple Authentication API Server for testing
"""
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System Authentication API - Simple",
    description="Simple authentication service for testing",
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

# Pydantic models
class LoginRequest(BaseModel):
    user_id: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "authentication-simple",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# Login endpoint
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Simple login endpoint for testing."""
    print(f"🔐 Login request: {request.user_id}")
    
    # Simple test credentials
    test_users = {
        "admin": "admin123",
        "user": "user123",
        "test": "test123"
    }
    
    if request.user_id in test_users and request.password == test_users[request.user_id]:
        user_data = {
            "user_id": request.user_id,
            "display_name": request.user_id.title(),
            "email": f"{request.user_id}@example.com",
            "role": "editor" if request.user_id == "admin" else "user",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat(),
            "number_upload_files": 10 if request.user_id == "admin" else 3
        }
        
        print(f"✅ Login successful: {request.user_id}")
        return LoginResponse(
            success=True,
            user=user_data,
            message="Login successful"
        )
    else:
        print(f"❌ Login failed: {request.user_id}")
        return LoginResponse(
            success=False,
            error="Invalid user ID or password"
        )

# Logout endpoint
@app.post("/auth/logout")
async def logout():
    """Simple logout endpoint."""
    return {"success": True, "message": "Logout successful"}

# Get user info endpoint
@app.get("/auth/user/{user_id}")
async def get_user(user_id: str):
    """Get user information."""
    test_users = ["admin", "user", "test"]
    
    if user_id in test_users:
        return {
            "success": True,
            "user": {
                "user_id": user_id,
                "display_name": user_id.title(),
                "email": f"{user_id}@example.com",
                "role": "editor" if user_id == "admin" else "user",
                "is_active": True,
                "number_upload_files": 10 if user_id == "admin" else 3
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

if __name__ == "__main__":
    print("🚀 Starting Simple Authentication API server on port 8000...")
    uvicorn.run(
        "auth_server_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
