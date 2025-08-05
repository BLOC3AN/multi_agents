"""
Database Connection Pool Manager
Provides optimized database connections with pooling and caching
"""
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import time

class DatabaseConnectionPool:
    """Singleton database connection pool manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._connections = {}
        self._connection_cache = {}
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        self._initialized = True
    
    def get_connection(self, connection_type: str = "default"):
        """Get a database connection with caching."""
        current_time = time.time()
        
        # Health check every 30 seconds
        if current_time - self._last_health_check > self._health_check_interval:
            self._health_check()
            self._last_health_check = current_time
        
        if connection_type not in self._connections:
            self._connections[connection_type] = self._create_connection()
        
        return self._connections[connection_type]
    
    def _create_connection(self):
        """Create a new database connection."""
        try:
            from src.database.models import get_db_config
            return get_db_config()
        except Exception as e:
            print(f"❌ Failed to create database connection: {e}")
            return None
    
    def _health_check(self):
        """Perform health check on connections."""
        for conn_type, connection in list(self._connections.items()):
            if connection is None:
                continue
                
            try:
                # Simple ping to check connection health
                connection.admin.command('ping')
            except Exception as e:
                print(f"⚠️ Connection {conn_type} unhealthy, recreating: {e}")
                self._connections[conn_type] = self._create_connection()
    
    def close_all_connections(self):
        """Close all database connections."""
        for connection in self._connections.values():
            if connection:
                try:
                    connection.close()
                except:
                    pass
        self._connections.clear()
        self._connection_cache.clear()

# Global connection pool instance
db_pool = DatabaseConnectionPool()

def get_pooled_db_connection():
    """Get a pooled database connection."""
    return db_pool.get_connection()

class CachedDatabaseOperations:
    """Database operations with caching for frequently accessed data."""
    
    def __init__(self):
        self._user_cache = {}
        self._session_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def _is_cache_valid(self, cache_entry):
        """Check if cache entry is still valid."""
        if not cache_entry:
            return False
        return time.time() - cache_entry['timestamp'] < self._cache_ttl
    
    def get_user(self, user_id: str, use_cache: bool = True):
        """Get user with caching."""
        cache_key = f"user_{user_id}"
        
        if use_cache and cache_key in self._user_cache:
            cache_entry = self._user_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['data']
        
        # Fetch from database
        db_config = get_pooled_db_connection()
        if not db_config:
            return None
        
        user_doc = db_config.users.find_one({"user_id": user_id})
        
        # Cache the result
        if use_cache:
            self._user_cache[cache_key] = {
                'data': user_doc,
                'timestamp': time.time()
            }
        
        return user_doc
    
    def get_admin(self, admin_id: str, use_cache: bool = True):
        """Get admin with caching."""
        cache_key = f"admin_{admin_id}"
        
        if use_cache and cache_key in self._user_cache:
            cache_entry = self._user_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['data']
        
        # Fetch from database
        db_config = get_pooled_db_connection()
        if not db_config:
            return None
        
        admin_doc = db_config.admins.find_one({"admin_id": admin_id})
        
        # Cache the result
        if use_cache:
            self._user_cache[cache_key] = {
                'data': admin_doc,
                'timestamp': time.time()
            }
        
        return admin_doc
    
    def get_session(self, session_id: str, use_cache: bool = True):
        """Get session with caching."""
        cache_key = f"session_{session_id}"
        
        if use_cache and cache_key in self._session_cache:
            cache_entry = self._session_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['data']
        
        # Fetch from database
        db_config = get_pooled_db_connection()
        if not db_config:
            return None
        
        session_doc = db_config.sessions.find_one({"session_id": session_id})
        
        # Cache the result
        if use_cache:
            self._session_cache[cache_key] = {
                'data': session_doc,
                'timestamp': time.time()
            }
        
        return session_doc
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate user cache entry."""
        cache_key = f"user_{user_id}"
        if cache_key in self._user_cache:
            del self._user_cache[cache_key]
        
        admin_cache_key = f"admin_{user_id}"
        if admin_cache_key in self._user_cache:
            del self._user_cache[admin_cache_key]
    
    def invalidate_session_cache(self, session_id: str):
        """Invalidate session cache entry."""
        cache_key = f"session_{session_id}"
        if cache_key in self._session_cache:
            del self._session_cache[cache_key]
    
    def clear_cache(self):
        """Clear all cache entries."""
        self._user_cache.clear()
        self._session_cache.clear()

# Global cached database operations instance
cached_db_ops = CachedDatabaseOperations()

def get_cached_db_operations():
    """Get the cached database operations instance."""
    return cached_db_ops

# Utility functions for backward compatibility
def ensure_user_exists_optimized(user_id: str, display_name: str = None, email: str = None):
    """Optimized version of ensure_user_exists with caching."""
    db_config = get_pooled_db_connection()
    if not db_config:
        return
    
    try:
        cached_ops = get_cached_db_operations()
        
        # Check cache first
        existing_user = cached_ops.get_user(user_id)
        existing_admin = cached_ops.get_admin(user_id)
        
        if not existing_user and not existing_admin:
            # Import User model only when needed
            from src.database.models import User
            
            # Create new user
            user = User(
                user_id=user_id,
                display_name=display_name or user_id,
                email=email,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            user_doc = user.to_dict()
            db_config.users.insert_one(user_doc)
            
            # Invalidate cache
            cached_ops.invalidate_user_cache(user_id)
            
            print(f"✅ New user created: {user_id}")
        elif existing_user:
            # Update last login for regular user
            db_config.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            # Invalidate cache
            cached_ops.invalidate_user_cache(user_id)
        elif existing_admin:
            # Update last login for admin user
            db_config.admins.update_one(
                {"admin_id": user_id},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            # Invalidate cache
            cached_ops.invalidate_user_cache(user_id)
            
    except Exception as e:
        print(f"❌ Failed to ensure user exists: {e}")

def ensure_session_exists_optimized(session_id: str, user_id: str):
    """Optimized version of ensure_session_exists with caching."""
    db_config = get_pooled_db_connection()
    if not db_config:
        return
    
    try:
        cached_ops = get_cached_db_operations()
        
        # Check cache first
        existing_session = cached_ops.get_session(session_id)
        
        if not existing_session:
            # Import ChatSession model only when needed
            from src.database.models import ChatSession
            
            # Create new session
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=f"Session {session_id[:8]}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                total_messages=0,
                is_active=True
            )
            
            session_doc = session.to_dict()
            db_config.sessions.insert_one(session_doc)
            
            # Invalidate cache
            cached_ops.invalidate_session_cache(session_id)
            
            print(f"✅ New session created: {session_id}")
            
    except Exception as e:
        print(f"❌ Failed to ensure session exists: {e}")
