"""
Database models and connection management for Multi-Agent System.
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Qdrant model for vector database operations
try:
    from .model_qdrant import (
        QdrantConfig,
        VectorDocument,
        get_qdrant_config,
        create_vector_document,
        generate_document_id
    )
    QDRANT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Qdrant model not available: {e}")
    QDRANT_AVAILABLE = False


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
class Admin:
    """Admin model for administrative user management."""
    admin_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    permissions: Optional[Dict[str, Any]] = None
    role: str = "admin"  # admin, super_admin, etc.
    can_manage_users: bool = True
    can_manage_system: bool = True
    can_view_logs: bool = True
    notes: Optional[str] = None

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
        self.admins: Collection = self.database.admins
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

            # Admins collection indexes
            self.admins.create_index("admin_id", unique=True)
            self.admins.create_index("email", unique=True, sparse=True)
            self.admins.create_index("created_at")
            self.admins.create_index("is_active")
            self.admins.create_index("role")
            
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


# Admin management functions
def create_admin(admin_id: str, password: str, display_name: str = None, email: str = None,
                role: str = "admin", **kwargs) -> bool:
    """Create a new admin user."""
    try:
        db_config = get_db_config()

        # Check if admin already exists
        existing_admin = db_config.admins.find_one({"admin_id": admin_id})
        if existing_admin:
            print(f"❌ Admin already exists: {admin_id}")
            return False

        # Hash password
        from auth_server import hash_password
        password_hash = hash_password(password)

        # Create admin
        admin = Admin(
            admin_id=admin_id,
            password_hash=password_hash,
            display_name=display_name or admin_id,
            email=email,
            role=role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )

        admin_doc = admin.to_dict()
        db_config.admins.insert_one(admin_doc)
        print(f"✅ Admin created: {admin_id}")
        return True

    except Exception as e:
        print(f"❌ Failed to create admin: {e}")
        return False


def get_admin(admin_id: str) -> Optional[Dict[str, Any]]:
    """Get admin by admin_id."""
    try:
        db_config = get_db_config()
        return db_config.admins.find_one({"admin_id": admin_id})
    except Exception as e:
        print(f"❌ Failed to get admin: {e}")
        return None


def update_admin(admin_id: str, **updates) -> bool:
    """Update admin information."""
    try:
        db_config = get_db_config()

        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow().isoformat()

        result = db_config.admins.update_one(
            {"admin_id": admin_id},
            {"$set": updates}
        )

        if result.modified_count > 0:
            print(f"✅ Admin updated: {admin_id}")
            return True
        else:
            print(f"❌ Admin not found or no changes: {admin_id}")
            return False

    except Exception as e:
        print(f"❌ Failed to update admin: {e}")
        return False


def delete_admin(admin_id: str) -> bool:
    """Delete admin (soft delete by setting is_active=False)."""
    try:
        db_config = get_db_config()

        result = db_config.admins.update_one(
            {"admin_id": admin_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow().isoformat()}}
        )

        if result.modified_count > 0:
            print(f"✅ Admin deactivated: {admin_id}")
            return True
        else:
            print(f"❌ Admin not found: {admin_id}")
            return False

    except Exception as e:
        print(f"❌ Failed to delete admin: {e}")
        return False


def list_admins(active_only: bool = True) -> List[Dict[str, Any]]:
    """List all admins."""
    try:
        db_config = get_db_config()

        query = {"is_active": True} if active_only else {}
        admins = list(db_config.admins.find(query))

        # Remove password_hash from results
        for admin in admins:
            admin.pop("password_hash", None)

        return admins

    except Exception as e:
        print(f"❌ Failed to list admins: {e}")
        return []


# Qdrant Vector Database utilities
def is_qdrant_available() -> bool:
    """Check if Qdrant vector database is available."""
    return QDRANT_AVAILABLE


def get_vector_db_info() -> Optional[Dict[str, Any]]:
    """Get vector database information if available."""
    if not QDRANT_AVAILABLE:
        return None

    try:
        qdrant = get_qdrant_config()
        return qdrant.get_collection_info()
    except Exception as e:
        print(f"❌ Failed to get vector DB info: {e}")
        return None


def store_vector_document(text: str,
                         embedding: List[float],
                         user_id: str,
                         title: str = None,
                         source: str = None,
                         **kwargs) -> Optional[str]:
    """
    Store a document with its vector embedding.

    Args:
        text: Document text content
        embedding: Vector embedding (1024 dimensions)
        user_id: User ID for file isolation
        title: Document title
        source: Document source
        **kwargs: Additional metadata

    Returns:
        Document ID if successful, None otherwise
    """
    if not QDRANT_AVAILABLE:
        print("❌ Qdrant not available")
        return None

    try:
        qdrant = get_qdrant_config()
        doc = create_vector_document(
            text=text,
            user_id=user_id,
            title=title,
            source=source,
            **kwargs
        )

        success = qdrant.upsert_document(doc, embedding)
        return doc.id if success else None

    except Exception as e:
        print(f"❌ Failed to store vector document: {e}")
        return None


def search_vector_documents(query_embedding: List[float],
                           limit: int = 10,
                           score_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    Search for similar documents using vector embedding.

    Args:
        query_embedding: Query vector embedding
        limit: Maximum number of results
        score_threshold: Minimum similarity score

    Returns:
        List of similar documents with scores
    """
    if not QDRANT_AVAILABLE:
        print("❌ Qdrant not available")
        return []

    try:
        qdrant = get_qdrant_config()
        return qdrant.search_similar(
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )

    except Exception as e:
        print(f"❌ Failed to search vector documents: {e}")
        return []
