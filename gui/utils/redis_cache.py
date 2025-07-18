"""
Redis caching utilities for session management and context tracking.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis caching utility class."""
    
    def __init__(self, redis_client):
        """Initialize with Redis client."""
        self.redis = redis_client
        self.enabled = redis_client is not None
    
    def set_user_cache(self, user_id: str, user_data: Dict[str, Any], ttl: int = 3600):
        """Cache user data."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"user:{user_id}"
            self.redis.setex(cache_key, ttl, json.dumps(user_data, default=str))
            logger.debug(f"✅ Cached user data: {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to cache user {user_id}: {e}")
    
    def get_user_cache(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user data."""
        if not self.enabled:
            return None
        
        try:
            cache_key = f"user:{user_id}"
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get cached user {user_id}: {e}")
            return None
    
    def set_session_cache(self, session_id: str, session_data: Dict[str, Any], ttl: int = 7200):
        """Cache session data."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"session:{session_id}"
            self.redis.setex(cache_key, ttl, json.dumps(session_data, default=str))
            logger.debug(f"✅ Cached session data: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to cache session {session_id}: {e}")
    
    def get_session_cache(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data."""
        if not self.enabled:
            return None
        
        try:
            cache_key = f"session:{session_id}"
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get cached session {session_id}: {e}")
            return None
    
    def set_conversation_context(self, session_id: str, context: List[Dict[str, Any]], ttl: int = 1800):
        """Cache conversation context."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"context:{session_id}"
            self.redis.setex(cache_key, ttl, json.dumps(context, default=str))
            logger.debug(f"✅ Cached context for session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to cache context for {session_id}: {e}")
    
    def get_conversation_context(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached conversation context."""
        if not self.enabled:
            return None
        
        try:
            cache_key = f"context:{session_id}"
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get cached context for {session_id}: {e}")
            return None
    
    def set_recent_messages(self, session_id: str, messages: List[Dict[str, Any]], ttl: int = 1800):
        """Cache recent messages for a session."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"messages:{session_id}"
            self.redis.setex(cache_key, ttl, json.dumps(messages, default=str))
            logger.debug(f"✅ Cached messages for session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to cache messages for {session_id}: {e}")
    
    def get_recent_messages(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached recent messages."""
        if not self.enabled:
            return None
        
        try:
            cache_key = f"messages:{session_id}"
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get cached messages for {session_id}: {e}")
            return None
    
    def invalidate_session_cache(self, session_id: str):
        """Invalidate all cache related to a session."""
        if not self.enabled:
            return
        
        try:
            keys_to_delete = [
                f"session:{session_id}",
                f"context:{session_id}",
                f"messages:{session_id}"
            ]
            
            for key in keys_to_delete:
                self.redis.delete(key)
            
            logger.debug(f"✅ Invalidated cache for session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to invalidate cache for {session_id}: {e}")
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate user cache."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"user:{user_id}"
            self.redis.delete(cache_key)
            logger.debug(f"✅ Invalidated cache for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to invalidate cache for user {user_id}: {e}")
    
    def set_processing_status(self, session_id: str, status: str, ttl: int = 300):
        """Set processing status for a session."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"processing:{session_id}"
            status_data = {
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.redis.setex(cache_key, ttl, json.dumps(status_data))
            logger.debug(f"✅ Set processing status for {session_id}: {status}")
        except Exception as e:
            logger.error(f"❌ Failed to set processing status for {session_id}: {e}")
    
    def get_processing_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status for a session."""
        if not self.enabled:
            return None
        
        try:
            cache_key = f"processing:{session_id}"
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get processing status for {session_id}: {e}")
            return None
    
    def clear_processing_status(self, session_id: str):
        """Clear processing status for a session."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"processing:{session_id}"
            self.redis.delete(cache_key)
            logger.debug(f"✅ Cleared processing status for session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to clear processing status for {session_id}: {e}")
    
    def get_active_sessions(self, user_id: str) -> List[str]:
        """Get list of active sessions for a user."""
        if not self.enabled:
            return []
        
        try:
            pattern = f"session:*"
            session_keys = self.redis.keys(pattern)
            
            active_sessions = []
            for key in session_keys:
                session_data = self.redis.get(key)
                if session_data:
                    data = json.loads(session_data)
                    if data.get("user_id") == user_id:
                        session_id = key.split(":")[-1]
                        active_sessions.append(session_id)
            
            return active_sessions
        except Exception as e:
            logger.error(f"❌ Failed to get active sessions for user {user_id}: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}
