"""
Complete Authentication API Server for Multi-Agent System
Provides all necessary endpoints with optimized performance
"""
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

import uvicorn
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System Authentication API - Complete",
    description="Complete authentication service with all endpoints",
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

class UserCreateRequest(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    password: str
    is_active: bool = True
    role: str = "user"
    number_upload_files: int = 3

class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    number_upload_files: Optional[int] = None

# Mock data for testing
MOCK_USERS = {
    "admin": {
        "user_id": "admin",
        "display_name": "Administrator",
        "email": "admin@example.com",
        "password_hash": hashlib.sha256("admin123multi_agent_salt_2024".encode()).hexdigest(),
        "role": "editor",
        "is_active": True,
        "number_upload_files": 10,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat()
    },
    "user": {
        "user_id": "user",
        "display_name": "Regular User",
        "email": "user@example.com",
        "password_hash": hashlib.sha256("user123multi_agent_salt_2024".encode()).hexdigest(),
        "role": "user",
        "is_active": True,
        "number_upload_files": 3,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat()
    },
    "test": {
        "user_id": "test",
        "display_name": "Test User",
        "email": "test@example.com",
        "password_hash": hashlib.sha256("test123multi_agent_salt_2024".encode()).hexdigest(),
        "role": "user",
        "is_active": True,
        "number_upload_files": 3,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat()
    }
}

MOCK_SESSIONS = [
    {
        "session_id": "session_admin_1733404800",
        "user_id": "admin",
        "title": "Hỏi về Python Programming",
        "created_at": "2025-08-05T10:00:00.000000+00:00",
        "updated_at": "2025-08-05T10:30:00.000000+00:00",
        "total_messages": 4,
        "is_active": True
    },
    {
        "session_id": "session_admin_1733404900",
        "user_id": "admin",
        "title": "Tối ưu hóa hệ thống",
        "created_at": "2025-08-05T11:00:00.000000+00:00",
        "updated_at": "2025-08-05T11:45:00.000000+00:00",
        "total_messages": 6,
        "is_active": True
    },
    {
        "session_id": "session_admin_1733405000",
        "user_id": "admin",
        "title": "Debugging API Issues",
        "created_at": "2025-08-05T12:00:00.000000+00:00",
        "updated_at": "2025-08-05T12:20:00.000000+00:00",
        "total_messages": 3,
        "is_active": True
    }
]

MOCK_MESSAGES = [
    {
        "message_id": "msg_001",
        "session_id": "session_admin_1733404800",
        "user_id": "admin",
        "user_input": "Làm thế nào để tối ưu hóa code Python?",
        "agent_response": "Có nhiều cách để tối ưu hóa code Python:\n\n1. **Sử dụng list comprehensions** thay vì loops\n2. **Tránh global variables** \n3. **Sử dụng built-in functions** như map(), filter()\n4. **Profile code** để tìm bottlenecks\n5. **Sử dụng generators** cho large datasets\n\nBạn có muốn tôi giải thích chi tiết về một phương pháp nào không?",
        "processing_time": 1250.5,
        "success": True,
        "created_at": "2025-08-05T10:05:00.000000+00:00",
        "metadata": {"processing_mode": "single_agent"}
    },
    {
        "message_id": "msg_002",
        "session_id": "session_admin_1733404800",
        "user_id": "admin",
        "user_input": "Giải thích về list comprehensions",
        "agent_response": "**List Comprehensions** là cách viết ngắn gọn để tạo lists:\n\n```python\n# Thay vì:\nresult = []\nfor i in range(10):\n    if i % 2 == 0:\n        result.append(i * 2)\n\n# Dùng list comprehension:\nresult = [i * 2 for i in range(10) if i % 2 == 0]\n```\n\n**Ưu điểm:**\n- Nhanh hơn 20-30%\n- Code ngắn gọn hơn\n- Dễ đọc khi quen\n\n**Khi nào dùng:**\n- Transformations đơn giản\n- Filtering data\n- Tạo lists từ iterables",
        "processing_time": 890.2,
        "success": True,
        "created_at": "2025-08-05T10:10:00.000000+00:00",
        "metadata": {"processing_mode": "single_agent"}
    },
    {
        "message_id": "msg_003",
        "session_id": "session_admin_1733404900",
        "user_id": "admin",
        "user_input": "Hệ thống đang chạy chậm, làm sao tối ưu?",
        "agent_response": "Để tối ưu hệ thống chạy chậm, tôi khuyên bạn:\n\n**1. Profiling & Monitoring:**\n- Dùng tools như `htop`, `iostat`\n- Monitor memory usage\n- Check database queries\n\n**2. Database Optimization:**\n- Add indexes cho queries thường dùng\n- Connection pooling\n- Query optimization\n\n**3. Caching:**\n- Redis cho session data\n- Application-level caching\n- CDN cho static files\n\n**4. Code Optimization:**\n- Lazy loading\n- Async/await cho I/O operations\n- Remove redundant operations\n\nBạn muốn tôi focus vào phần nào trước?",
        "processing_time": 1456.8,
        "success": True,
        "created_at": "2025-08-05T11:15:00.000000+00:00",
        "metadata": {"processing_mode": "single_agent"}
    },
    {
        "message_id": "msg_004",
        "session_id": "session_admin_1733405000",
        "user_id": "admin",
        "user_input": "API trả về 404 error, debug như thế nào?",
        "agent_response": "Để debug 404 API errors:\n\n**1. Check Routes:**\n```bash\n# Kiểm tra endpoint có tồn tại\ncurl -X GET http://localhost:8000/your-endpoint\n```\n\n**2. Verify HTTP Method:**\n- GET vs POST vs PUT\n- Check request headers\n\n**3. Check Logs:**\n```bash\ntail -f logs/api.log\n```\n\n**4. Common Issues:**\n- Trailing slashes: `/api/users/` vs `/api/users`\n- Case sensitivity\n- Missing route registration\n- Middleware blocking requests\n\n**5. Testing Tools:**\n- Postman/Insomnia\n- curl commands\n- Browser dev tools\n\nBạn có thể share endpoint cụ thể đang lỗi không?",
        "processing_time": 1123.4,
        "success": True,
        "created_at": "2025-08-05T12:05:00.000000+00:00",
        "metadata": {"processing_mode": "single_agent"}
    }
]

MOCK_FILES = [
    {
        "file_id": "file_001",
        "user_id": "admin",
        "key": "documents/python_optimization_guide.pdf",
        "filename": "python_optimization_guide.pdf",
        "size": 2048576,
        "content_type": "application/pdf",
        "created_at": "2025-08-05T09:00:00.000000+00:00",
        "updated_at": "2025-08-05T09:00:00.000000+00:00"
    },
    {
        "file_id": "file_002",
        "user_id": "admin",
        "key": "images/system_architecture.png",
        "filename": "system_architecture.png",
        "size": 1024768,
        "content_type": "image/png",
        "created_at": "2025-08-05T10:30:00.000000+00:00",
        "updated_at": "2025-08-05T10:30:00.000000+00:00"
    }
]

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
        "service": "authentication-complete",
        "database": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user with user_id and password."""
    print(f"🔐 Login request: {request.user_id}")
    
    if request.user_id in MOCK_USERS:
        user = MOCK_USERS[request.user_id]
        if verify_password(request.password, user["password_hash"]):
            # Update last login
            user["last_login"] = datetime.now(timezone.utc).isoformat()
            
            # Prepare user data for response (exclude password)
            user_data = {k: v for k, v in user.items() if k != "password_hash"}
            
            print(f"✅ Login successful: {request.user_id}")
            return LoginResponse(
                success=True,
                user=user_data,
                message="Login successful"
            )
    
    print(f"❌ Login failed: {request.user_id}")
    return LoginResponse(
        success=False,
        error="Invalid user ID or password"
    )

@app.post("/auth/logout")
async def logout():
    """Logout endpoint."""
    return {"success": True, "message": "Logout successful"}

# Admin endpoints
@app.get("/admin/stats")
async def get_admin_stats():
    """Get admin statistics."""
    return {
        "success": True,
        "stats": {
            "total_users": len(MOCK_USERS),
            "total_sessions": len(MOCK_SESSIONS),
            "total_messages": len(MOCK_MESSAGES),
            "total_files": len(MOCK_FILES),
            "active_users": len([u for u in MOCK_USERS.values() if u["is_active"]]),
            "admin_users": len([u for u in MOCK_USERS.values() if u["role"] == "editor"]),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    }

@app.get("/admin/users")
async def get_admin_users(collection: str = Query("users")):
    """Get users for admin panel."""
    if collection == "admins":
        users = [u for u in MOCK_USERS.values() if u["role"] == "editor"]
    else:
        users = list(MOCK_USERS.values())
    
    # Remove password hashes from response
    clean_users = []
    for user in users:
        clean_user = {k: v for k, v in user.items() if k != "password_hash"}
        clean_users.append(clean_user)
    
    return {
        "success": True,
        "users": clean_users,
        "total": len(clean_users)
    }

@app.get("/admin/sessions")
async def get_admin_sessions():
    """Get sessions for admin panel."""
    return {
        "success": True,
        "sessions": MOCK_SESSIONS,
        "total": len(MOCK_SESSIONS)
    }

@app.get("/admin/messages")
async def get_admin_messages():
    """Get messages for admin panel."""
    return {
        "success": True,
        "messages": MOCK_MESSAGES,
        "total": len(MOCK_MESSAGES)
    }

@app.get("/admin/files")
async def get_admin_files():
    """Get files for admin panel."""
    return {
        "success": True,
        "files": MOCK_FILES,
        "total": len(MOCK_FILES)
    }

# User management endpoints
@app.post("/admin/users")
async def create_user(user_data: UserCreateRequest):
    """Create a new user."""
    if user_data.user_id in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    new_user = {
        "user_id": user_data.user_id,
        "display_name": user_data.display_name or user_data.user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "is_active": user_data.is_active,
        "number_upload_files": user_data.number_upload_files,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None
    }
    
    MOCK_USERS[user_data.user_id] = new_user
    
    # Return user data without password hash
    response_user = {k: v for k, v in new_user.items() if k != "password_hash"}
    
    return {
        "success": True,
        "user": response_user,
        "message": "User created successfully"
    }

@app.put("/admin/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdateRequest):
    """Update user information."""
    if user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = MOCK_USERS[user_id]
    
    # Update fields if provided
    if user_data.display_name is not None:
        user["display_name"] = user_data.display_name
    if user_data.email is not None:
        user["email"] = user_data.email
    if user_data.is_active is not None:
        user["is_active"] = user_data.is_active
    if user_data.role is not None:
        user["role"] = user_data.role
    if user_data.number_upload_files is not None:
        user["number_upload_files"] = user_data.number_upload_files
    
    user["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Return user data without password hash
    response_user = {k: v for k, v in user.items() if k != "password_hash"}
    
    return {
        "success": True,
        "user": response_user,
        "message": "User updated successfully"
    }

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user."""
    if user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    del MOCK_USERS[user_id]
    
    return {
        "success": True,
        "message": "User deleted successfully"
    }

# File management endpoints
@app.get("/api/s3/files")
async def list_files(user_id: str = Query(...)):
    """List files for a user."""
    user_files = [f for f in MOCK_FILES if f.get("user_id") == user_id]
    
    return {
        "success": True,
        "files": user_files,
        "total": len(user_files)
    }

@app.get("/api/s3/files/{file_key}")
async def get_file_info(file_key: str):
    """Get file information."""
    file_info = next((f for f in MOCK_FILES if f.get("key") == file_key), None)

    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return {
        "success": True,
        "file": file_info
    }

# Session management endpoints
@app.get("/api/sessions")
async def get_user_sessions(user_id: str = Query(...)):
    """Get sessions for a user."""
    user_sessions = [s for s in MOCK_SESSIONS if s.get("user_id") == user_id]

    return {
        "success": True,
        "sessions": user_sessions,
        "total": len(user_sessions)
    }

@app.post("/api/sessions")
async def create_session(session_data: dict):
    """Create a new session."""
    session_id = session_data.get("session_id", f"session_{session_data.get('user_id')}_{int(datetime.now().timestamp())}")

    new_session = {
        "session_id": session_id,
        "user_id": session_data.get("user_id"),
        "title": session_data.get("title", "New Chat Session"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_messages": 0,
        "is_active": True
    }

    MOCK_SESSIONS.append(new_session)

    return {
        "success": True,
        "session": new_session,
        "message": "Session created successfully"
    }

@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, session_data: dict):
    """Update session information."""
    session = next((s for s in MOCK_SESSIONS if s.get("session_id") == session_id), None)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Update fields if provided
    if "title" in session_data:
        session["title"] = session_data["title"]
    if "is_active" in session_data:
        session["is_active"] = session_data["is_active"]

    session["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "session": session,
        "message": "Session updated successfully"
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    session_index = next((i for i, s in enumerate(MOCK_SESSIONS) if s.get("session_id") == session_id), None)

    if session_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    del MOCK_SESSIONS[session_index]

    return {
        "success": True,
        "message": "Session deleted successfully"
    }

# Session title update endpoint (specific for frontend compatibility)
@app.put("/session/{session_id}/title")
async def update_session_title(session_id: str, title_data: dict):
    """Update session title - frontend compatible endpoint."""
    print(f"📝 Updating session title: {session_id} -> {title_data}")

    session = next((s for s in MOCK_SESSIONS if s.get("session_id") == session_id), None)

    if not session:
        # Create session if it doesn't exist
        new_session = {
            "session_id": session_id,
            "user_id": "admin",  # Default to admin for now
            "title": title_data.get("title", "New Chat Session"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_messages": 0,
            "is_active": True
        }
        MOCK_SESSIONS.append(new_session)
        session = new_session
        print(f"✅ Created new session: {session_id}")
    else:
        # Update existing session
        session["title"] = title_data.get("title", session["title"])
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        print(f"✅ Updated session title: {session_id}")

    return {
        "success": True,
        "session": session,
        "message": "Session title updated successfully"
    }

# Additional session endpoints for frontend compatibility
@app.delete("/session/{session_id}")
async def delete_session_frontend(session_id: str):
    """Delete session - frontend compatible endpoint."""
    print(f"🗑️ Deleting session: {session_id}")

    session_index = next((i for i, s in enumerate(MOCK_SESSIONS) if s.get("session_id") == session_id), None)

    if session_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    del MOCK_SESSIONS[session_index]
    print(f"✅ Deleted session: {session_id}")

    return {
        "success": True,
        "message": "Session deleted successfully"
    }

@app.get("/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages for a session."""
    session_messages = [m for m in MOCK_MESSAGES if m.get("session_id") == session_id]

    return {
        "success": True,
        "messages": session_messages,
        "total": len(session_messages)
    }

@app.get("/user/{user_id}/sessions")
async def get_user_sessions_frontend(user_id: str):
    """Get sessions for a user - frontend compatible."""
    user_sessions = [s for s in MOCK_SESSIONS if s.get("user_id") == user_id]

    return {
        "success": True,
        "sessions": user_sessions,
        "total": len(user_sessions)
    }

# User management endpoints with PATCH support
@app.patch("/admin/users/{user_id}")
async def patch_user(user_id: str, user_data: UserUpdateRequest):
    """Update user information using PATCH."""
    return await update_user(user_id, user_data)

@app.patch("/admin/users/{user_id}/password")
async def change_user_password(user_id: str, password_data: dict):
    """Change user password."""
    if user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = MOCK_USERS[user_id]

    # In a real system, you'd verify the current password
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")

    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password is required"
        )

    user["password_hash"] = hash_password(new_password)
    user["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Password changed successfully"
    }

@app.patch("/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, password_data: dict):
    """Reset user password (admin only)."""
    if user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = MOCK_USERS[user_id]
    new_password = password_data.get("new_password")

    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password is required"
        )

    user["password_hash"] = hash_password(new_password)
    user["updated_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Password reset successfully"
    }

@app.get("/admin/users/{user_id}/sessions")
async def get_user_sessions_admin(user_id: str, limit: int = Query(50), offset: int = Query(0)):
    """Get user sessions for admin panel."""
    user_sessions = [s for s in MOCK_SESSIONS if s.get("user_id") == user_id]

    # Apply pagination
    paginated_sessions = user_sessions[offset:offset + limit]

    return {
        "success": True,
        "sessions": paginated_sessions,
        "total": len(user_sessions),
        "limit": limit,
        "offset": offset
    }

@app.get("/admin/users/{user_id}/messages")
async def get_user_messages_admin(user_id: str, limit: int = Query(50), offset: int = Query(0), session_id: str = Query(None)):
    """Get user messages for admin panel."""
    user_messages = [m for m in MOCK_MESSAGES if m.get("user_id") == user_id]

    if session_id:
        user_messages = [m for m in user_messages if m.get("session_id") == session_id]

    # Apply pagination
    paginated_messages = user_messages[offset:offset + limit]

    return {
        "success": True,
        "messages": paginated_messages,
        "total": len(user_messages),
        "limit": limit,
        "offset": offset
    }

@app.get("/admin/users/{user_id}/current-password")
async def get_user_current_password(user_id: str):
    """Get user current password info (for admin)."""
    if user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = MOCK_USERS[user_id]

    return {
        "success": True,
        "has_password": bool(user.get("password_hash")),
        "current_password": "****",  # Never return actual password
        "message": "Password info retrieved"
    }

# File management endpoints
@app.delete("/admin/files/{file_key}")
async def delete_admin_file(file_key: str, user_id: str = Query(...)):
    """Delete file (admin)."""
    file_index = next((i for i, f in enumerate(MOCK_FILES) if f.get("key") == file_key and f.get("user_id") == user_id), None)

    if file_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    del MOCK_FILES[file_index]

    return {
        "success": True,
        "message": "File deleted successfully"
    }

# Message management endpoints
@app.delete("/admin/messages/{message_id}")
async def delete_admin_message(message_id: str):
    """Delete message (admin)."""
    message_index = next((i for i, m in enumerate(MOCK_MESSAGES) if m.get("message_id") == message_id), None)

    if message_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    del MOCK_MESSAGES[message_index]

    return {
        "success": True,
        "message": "Message deleted successfully"
    }

if __name__ == "__main__":
    print("🚀 Starting Complete Authentication API server on port 8000...")
    uvicorn.run(
        "auth_server_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
