"""
MongoDB models for user management and conversation tracking.
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, asdict
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
import uuid
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logger first
logger = logging.getLogger(__name__)

# Debug: Check if MongoDB URI is loaded
mongodb_uri = os.getenv("MONGODB_URI")
if mongodb_uri:
    logger.info(f"✅ MongoDB URI loaded: {mongodb_uri[:20]}...")
else:
    logger.error("❌ MongoDB URI not found in environment variables")




@dataclass
class User:
    """User model for authentication and management."""
    user_id: str
    password_hash: str  # Password hash for authentication
    password: str  # Plain password for admin management
    display_name: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.preferences is None:
            self.preferences = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO strings for MongoDB
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'].isoformat()
        if data.get('last_login'):
            data['last_login'] = data['last_login'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from MongoDB document."""
        # Remove MongoDB's _id field
        data = data.copy()
        data.pop('_id', None)

        # Convert ISO strings back to datetime objects
        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at') and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('last_login') and isinstance(data['last_login'], str):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)


@dataclass
class ChatSession:
    """Chat session model for tracking conversations."""
    session_id: str
    user_id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    total_messages: int = 0
    session_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.session_metadata is None:
            self.session_metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        """Create ChatSession from MongoDB document."""
        # Remove MongoDB's _id field
        data = data.copy()
        data.pop('_id', None)

        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at') and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ChatMessage:
    """Individual chat message model."""
    message_id: Union[str, None]
    session_id: str
    user_id: str  # Added user_id field
    user_input: str
    agent_response: Optional[str] = None
    detected_intents: Optional[List[Dict[str, Any]]] = None
    primary_intent: Optional[str] = None
    processing_mode: Optional[str] = None
    agent_results: Optional[Dict[str, Any]] = None
    execution_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    processing_time: Optional[int] = None
    errors: Optional[List[str]] = None
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None  # Added metadata field

    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.detected_intents is None:
            self.detected_intents = []
        if self.agent_results is None:
            self.agent_results = {}
        if self.execution_summary is None:
            self.execution_summary = {}
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create ChatMessage from MongoDB document."""
        # Remove MongoDB's _id field
        data = data.copy()
        data.pop('_id', None)

        if data.get('created_at') and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class SystemLog:
    """System logs for monitoring and debugging."""
    log_id: str
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, DEBUG
    component: str  # Which component generated the log
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.log_id is None:
            self.log_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.additional_data is None:
            self.additional_data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        data = asdict(self)
        if data.get('timestamp'):
            data['timestamp'] = data['timestamp'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemLog':
        """Create SystemLog from MongoDB document."""
        # Remove MongoDB's _id field
        data = data.copy()
        data.pop('_id', None)

        if data.get('timestamp') and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


# MongoDB and Redis configuration
class DatabaseConfig:
    """MongoDB and Redis configuration and connection management."""

    def __init__(self, mongodb_uri: Optional[str] = None, redis_url: Optional[str] = None):
        """Initialize database configuration."""
        # Try to get MongoDB URI from environment
        env_mongodb_uri = os.getenv("MONGODB_URI")
        if not env_mongodb_uri:
            # Fallback: try to load .env again
            load_dotenv()
            env_mongodb_uri = os.getenv("MONGODB_URI")

        self.mongodb_uri = mongodb_uri or env_mongodb_uri or "mongodb://localhost:27017"
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.database_name = os.getenv("MONGODB_DATABASE", "multi_agent_system")

        # Debug log
        if "localhost:27017" in self.mongodb_uri:
            logger.warning("⚠️ Using localhost MongoDB - check if .env is loaded properly")
        else:
            logger.info("✅ Using online MongoDB")

        # MongoDB client with error handling
        try:
            self.mongo_client = MongoClient(self.mongodb_uri)
            # Test connection
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            if "must be escaped" in str(e):
                logger.error("💡 Fix: Encode username/password in MongoDB URI using urllib.parse.quote_plus")
                logger.error("💡 Example: mongodb+srv://encoded_user:encoded_pass@cluster.mongodb.net/db")
            raise
        self.db: Database = self.mongo_client[self.database_name]

        # Collections
        self.users: Collection = self.db.users
        self.sessions: Collection = self.db.chat_sessions
        self.messages: Collection = self.db.chat_messages
        self.logs: Collection = self.db.system_logs

        # Redis client (imported here to avoid circular imports)
        try:
            import redis
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        except ImportError:
            logger.warning("Redis not available. Caching will be disabled.")
            self.redis_client = None

    def create_indexes(self):
        """Create MongoDB indexes for better performance."""
        try:
            # User indexes
            self.users.create_index("user_id", unique=True)
            self.users.create_index("email", unique=True, sparse=True)

            # Session indexes
            self.sessions.create_index("session_id", unique=True)
            self.sessions.create_index("user_id")
            self.sessions.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])

            # Message indexes
            self.messages.create_index("message_id", unique=True)
            self.messages.create_index("session_id")
            self.messages.create_index([("session_id", ASCENDING), ("created_at", ASCENDING)])

            # Log indexes
            self.logs.create_index([("timestamp", DESCENDING)])
            self.logs.create_index("level")
            self.logs.create_index("component")
            self.logs.create_index("user_id", sparse=True)
            self.logs.create_index("session_id", sparse=True)

            logger.info("✅ MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")

    def test_connection(self) -> bool:
        """Test MongoDB and Redis connections."""
        try:
            # Test MongoDB
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")

            # Test Redis (optional)
            if self.redis_client:
                try:
                    self.redis_client.ping()
                    logger.info("✅ Redis connection successful")
                except Exception as redis_error:
                    logger.warning(f"⚠️ Redis connection failed: {redis_error}")
                    logger.warning("⚠️ Continuing without Redis caching")
                    self.redis_client = None
            else:
                logger.info("ℹ️ Redis not configured, caching disabled")

            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def close_connections(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
        if self.redis_client:
            self.redis_client.close()


# Global database instance - lazy initialization
db_config = None


def get_db_config():
    """Get database configuration with lazy initialization."""
    global db_config
    if db_config is None:
        db_config = DatabaseConfig()
    return db_config


def safe_redis_operation(operation_func, *args, **kwargs):
    """Safely execute Redis operations with error handling."""
    db = get_db_config()
    if not db.redis_client:
        return None

    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"⚠️ Redis operation failed: {e}")
        return None


def init_database():
    """Initialize the database and create indexes."""
    db = get_db_config()
    db.create_indexes()
    return db.test_connection()


# Utility functions for common operations
def create_user(user_id: str, display_name: Optional[str] = None, email: Optional[str] = None) -> User:
    """Create a new user."""
    try:
        db = get_db_config()
        user = User(
            user_id=user_id,
            display_name=display_name or user_id,
            email=email
        )

        # Insert into MongoDB
        result = db.users.insert_one(user.to_dict())

        # Cache in Redis if available
        if db.redis_client:
            cache_key = f"user:{user_id}"
            safe_redis_operation(db.redis_client.setex, cache_key, 3600, str(user.to_dict()))

        logger.info(f"✅ Created user: {user_id}")
        return user
    except Exception as e:
        logger.error(f"❌ Failed to create user {user_id}: {e}")
        raise


def get_user(user_id: str) -> Optional[User]:
    """Get user by user_id with Redis caching."""
    try:
        # Try Redis cache first if available
        cache_key = f"user:{user_id}"
        cached_data = safe_redis_operation(db_config.redis_client.get, cache_key) if db_config.redis_client else None
        if cached_data:
            # Note: In production, use proper JSON serialization
            pass

        # Query MongoDB
        user_doc = db_config.users.find_one({"user_id": user_id})
        if user_doc:
            user = User.from_dict(user_doc)

            # Update cache if available
            if db_config.redis_client:
                cache_key = f"user:{user_id}"
                safe_redis_operation(db_config.redis_client.setex, cache_key, 3600, str(user.to_dict()))

            return user
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get user {user_id}: {e}")
        return None


def create_chat_session(user_id: str, session_id: Optional[str] = None) -> ChatSession:
    """Create a new chat session."""
    try:
        chat_session = ChatSession(
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id
        )

        # Insert into MongoDB
        result = db_config.sessions.insert_one(chat_session.to_dict())

        # Cache in Redis if available
        if db_config.redis_client:
            cache_key = f"session:{chat_session.session_id}"
            safe_redis_operation(db_config.redis_client.setex, cache_key, 7200, str(chat_session.to_dict()))

        logger.info(f"✅ Created session: {chat_session.session_id}")
        return chat_session
    except Exception as e:
        logger.error(f"❌ Failed to create session: {e}")
        raise


def get_user_sessions(user_id: str, limit: int = 50) -> List[ChatSession]:
    """Get user's chat sessions."""
    try:
        # Query MongoDB
        session_docs = db_config.sessions.find(
            {"user_id": user_id}
        ).sort("updated_at", DESCENDING).limit(limit)

        sessions = [ChatSession.from_dict(doc) for doc in session_docs]
        return sessions
    except Exception as e:
        logger.error(f"❌ Failed to get sessions for user {user_id}: {e}")
        return []


def save_chat_message(
    session_id: str,
    user_input: str,
    agent_response: Optional[str] = None,
    processing_data: Optional[Dict[str, Any]] = None
) -> ChatMessage:
    """Save a chat message to the database."""
    try:
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            user_input=user_input,
            agent_response=agent_response,
            detected_intents=processing_data.get("detected_intents") if processing_data else None,
            primary_intent=processing_data.get("primary_intent") if processing_data else None,
            processing_mode=processing_data.get("processing_mode") if processing_data else None,
            agent_results=processing_data.get("agent_results") if processing_data else None,
            execution_summary=processing_data.get("execution_summary") if processing_data else None,
            processing_time=processing_data.get("processing_time") if processing_data else None,
            errors=processing_data.get("errors") if processing_data else None,
            success=processing_data.get("success", True) if processing_data else True
        )

        # Insert into MongoDB
        result = db_config.messages.insert_one(message.to_dict())

        # Update session message count
        db_config.sessions.update_one(
            {"session_id": session_id},
            {
                "$inc": {"total_messages": 1},
                "$set": {"updated_at": datetime.utcnow().isoformat()}
            }
        )

        # Cache recent messages in Redis
        if db_config.redis_client:
            cache_key = f"session_messages:{session_id}"
            recent_messages = get_session_messages(session_id, limit=20)
            messages_data = [msg.to_dict() for msg in recent_messages]
            safe_redis_operation(db_config.redis_client.setex, cache_key, 1800, str(messages_data))

        logger.info(f"✅ Saved message for session: {session_id}")
        return message
    except Exception as e:
        logger.error(f"❌ Failed to save message: {e}")
        raise


def get_session_messages(session_id: str, limit: int = 100) -> List[ChatMessage]:
    """Get messages for a specific session with Redis caching."""
    try:
        # Try Redis cache first for recent messages
        if db_config.redis_client and limit <= 20:
            cache_key = f"session_messages:{session_id}"
            cached_data = safe_redis_operation(db_config.redis_client.get, cache_key)
            if cached_data:
                # Note: In production, use proper JSON serialization
                pass

        # Query MongoDB
        message_docs = db_config.messages.find(
            {"session_id": session_id}
        ).sort("created_at", ASCENDING).limit(limit)

        messages = [ChatMessage.from_dict(doc) for doc in message_docs]
        return messages
    except Exception as e:
        logger.error(f"❌ Failed to get messages for session {session_id}: {e}")
        return []


def get_conversation_context(session_id: str, max_messages: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversation context for agents with Redis caching."""
    try:
        # Try Redis cache first
        cache_key = f"context:{session_id}"
        cached_context = safe_redis_operation(db_config.redis_client.get, cache_key) if db_config.redis_client else None
        if cached_context:
            # Note: In production, use proper JSON serialization
            pass

        # Get messages from database
        messages = get_session_messages(session_id, limit=max_messages)

        context = []
        for msg in messages[-max_messages:]:
            context.append({
                "user_input": msg.user_input,
                "agent_response": msg.agent_response,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "primary_intent": msg.primary_intent
            })

        # Cache the context
        if db_config.redis_client:
            cache_key = f"context:{session_id}"
            safe_redis_operation(db_config.redis_client.setex, cache_key, 600, str(context))

        return context
    except Exception as e:
        logger.error(f"❌ Failed to get context for session {session_id}: {e}")
        return []
