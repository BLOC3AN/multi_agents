"""
Database models and connection management for Multi-Agent System.
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class User:
    """User model for authentication and profile management."""
    user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class ChatSession:
    """Chat session model."""
    session_id: str
    user_id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    total_messages: int = 0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class ChatMessage:
    """Chat message model."""
    message_id: str
    session_id: str
    user_id: str
    user_input: str
    agent_response: Optional[str] = None
    detected_intents: Optional[list] = None
    primary_intent: Optional[str] = None
    processing_mode: Optional[str] = None
    agent_results: Optional[Dict[str, Any]] = None
    execution_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    success: bool = True
    errors: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class SystemLog:
    """System log model."""
    log_id: str
    timestamp: datetime
    level: str
    component: str
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class FileMetadata:
    """File metadata model for user file management."""
    file_id: str
    user_id: str
    file_key: str  # S3 key/path
    file_name: str
    file_size: int
    content_type: str
    upload_date: Optional[datetime] = None
    s3_bucket: Optional[str] = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self, mongodb_uri: str = None, database_name: str = None):
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE", "multi_agent_system")
        
        # Initialize MongoDB client and database
        self.client: MongoClient = MongoClient(self.mongodb_uri)
        self.database: Database = self.client[self.database_name]
        
        # Collections
        self.users: Collection = self.database.users
        self.sessions: Collection = self.database.chat_sessions
        self.messages: Collection = self.database.chat_messages
        self.logs: Collection = self.database.system_logs
        self.file_metadata: Collection = self.database.file_metadata
        
        # Test connection
        try:
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {self.database_name}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()

    def create_indexes(self):
        """Create database indexes for better performance."""
        try:
            # Users collection indexes
            self.users.create_index("user_id", unique=True)
            self.users.create_index("email", unique=True, sparse=True)
            self.users.create_index("created_at")
            self.users.create_index("is_active")
            
            # Chat sessions collection indexes
            self.sessions.create_index("session_id", unique=True)
            self.sessions.create_index("user_id")
            self.sessions.create_index([("user_id", 1), ("updated_at", -1)])
            self.sessions.create_index("created_at")
            self.sessions.create_index("is_active")
            
            # Chat messages collection indexes
            self.messages.create_index("message_id", unique=True)
            self.messages.create_index("session_id")
            self.messages.create_index("user_id")
            self.messages.create_index([("session_id", 1), ("created_at", 1)])
            self.messages.create_index("created_at")
            self.messages.create_index("primary_intent")
            
            # System logs collection indexes
            self.logs.create_index("log_id", unique=True)
            self.logs.create_index([("timestamp", -1)])
            self.logs.create_index("level")
            self.logs.create_index("component")
            self.logs.create_index("user_id", sparse=True)
            self.logs.create_index("session_id", sparse=True)

            # File metadata collection indexes
            self.file_metadata.create_index("file_id", unique=True)
            self.file_metadata.create_index("user_id")
            self.file_metadata.create_index("file_key", unique=True)
            self.file_metadata.create_index([("user_id", 1), ("upload_date", -1)])
            self.file_metadata.create_index("upload_date")
            self.file_metadata.create_index("is_active")
            self.file_metadata.create_index("content_type")

            print("✅ Database indexes created successfully")
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to create some indexes: {e}")


# Global database configuration instance
_db_config: Optional[DatabaseConfig] = None


def get_db_config() -> DatabaseConfig:
    """Get or create database configuration instance."""
    global _db_config
    
    if _db_config is None:
        _db_config = DatabaseConfig()
        # Create indexes on first connection
        _db_config.create_indexes()
    
    return _db_config


def close_db_connection():
    """Close database connection."""
    global _db_config
    
    if _db_config:
        _db_config.close()
        _db_config = None


# Utility functions
def ensure_user_exists(user_id: str, display_name: str = None, email: str = None) -> bool:
    """Ensure user exists in database."""
    try:
        db_config = get_db_config()
        
        # Check if user exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        
        if not existing_user:
            # Create new user
            user = User(
                user_id=user_id,
                display_name=display_name or user_id,
                email=email,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            user_doc = user.to_dict()
            db_config.users.insert_one(user_doc)
            print(f"✅ New user created: {user_id}")
            return True
        else:
            # Update last login
            db_config.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_login": datetime.utcnow().isoformat()}}
            )
            return True
            
    except Exception as e:
        print(f"❌ Failed to ensure user exists: {e}")
        return False


def ensure_session_exists(session_id: str, user_id: str) -> bool:
    """Ensure session exists in database."""
    try:
        db_config = get_db_config()
        
        # Check if session exists
        existing_session = db_config.sessions.find_one({"session_id": session_id})
        
        if not existing_session:
            # Create new session
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=f"Session {session_id[:8]}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                total_messages=0,
                is_active=True
            )
            
            session_doc = session.to_dict()
            db_config.sessions.insert_one(session_doc)
            print(f"✅ New session created: {session_id}")
            return True
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to ensure session exists: {e}")
        return False
