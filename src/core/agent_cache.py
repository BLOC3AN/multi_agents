"""
Agent Cache Manager
Provides caching for agent instances and LLM responses to improve performance
"""
import hashlib
import time
import threading
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
import json

class AgentCacheManager:
    """Singleton cache manager for agents and LLM responses."""
    
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
            
        self._agent_cache = {}
        self._llm_response_cache = {}
        self._cache_stats = {
            'agent_hits': 0,
            'agent_misses': 0,
            'llm_hits': 0,
            'llm_misses': 0
        }
        self._response_cache_ttl = 3600  # 1 hour for LLM responses
        self._agent_cache_ttl = 7200    # 2 hours for agent instances
        self._max_cache_size = 1000     # Maximum cache entries
        self._initialized = True
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict, ttl: int) -> bool:
        """Check if cache entry is still valid."""
        if not cache_entry:
            return False
        return time.time() - cache_entry['timestamp'] < ttl
    
    def _cleanup_expired_entries(self, cache_dict: Dict, ttl: int):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in cache_dict.items()
            if current_time - entry['timestamp'] > ttl
        ]
        for key in expired_keys:
            del cache_dict[key]
    
    def _enforce_cache_size_limit(self, cache_dict: Dict):
        """Enforce maximum cache size by removing oldest entries."""
        if len(cache_dict) > self._max_cache_size:
            # Sort by timestamp and remove oldest entries
            sorted_items = sorted(
                cache_dict.items(),
                key=lambda x: x[1]['timestamp']
            )
            # Keep only the newest entries
            entries_to_keep = sorted_items[-self._max_cache_size:]
            cache_dict.clear()
            cache_dict.update(dict(entries_to_keep))
    
    def get_cached_agent(self, agent_type: str, config: Dict = None) -> Optional[Any]:
        """Get cached agent instance."""
        cache_key = self._generate_cache_key(agent_type, config)
        
        # Cleanup expired entries periodically
        if len(self._agent_cache) % 100 == 0:
            self._cleanup_expired_entries(self._agent_cache, self._agent_cache_ttl)
        
        if cache_key in self._agent_cache:
            cache_entry = self._agent_cache[cache_key]
            if self._is_cache_valid(cache_entry, self._agent_cache_ttl):
                self._cache_stats['agent_hits'] += 1
                return cache_entry['data']
            else:
                # Remove expired entry
                del self._agent_cache[cache_key]
        
        self._cache_stats['agent_misses'] += 1
        return None
    
    def cache_agent(self, agent_type: str, agent_instance: Any, config: Dict = None):
        """Cache agent instance."""
        cache_key = self._generate_cache_key(agent_type, config)
        
        self._agent_cache[cache_key] = {
            'data': agent_instance,
            'timestamp': time.time()
        }
        
        # Enforce cache size limit
        self._enforce_cache_size_limit(self._agent_cache)
    
    def get_cached_llm_response(self, prompt: str, model_config: Dict = None) -> Optional[str]:
        """Get cached LLM response."""
        cache_key = self._generate_cache_key(prompt, model_config)
        
        # Cleanup expired entries periodically
        if len(self._llm_response_cache) % 50 == 0:
            self._cleanup_expired_entries(self._llm_response_cache, self._response_cache_ttl)
        
        if cache_key in self._llm_response_cache:
            cache_entry = self._llm_response_cache[cache_key]
            if self._is_cache_valid(cache_entry, self._response_cache_ttl):
                self._cache_stats['llm_hits'] += 1
                return cache_entry['data']
            else:
                # Remove expired entry
                del self._llm_response_cache[cache_key]
        
        self._cache_stats['llm_misses'] += 1
        return None
    
    def cache_llm_response(self, prompt: str, response: str, model_config: Dict = None):
        """Cache LLM response."""
        cache_key = self._generate_cache_key(prompt, model_config)
        
        self._llm_response_cache[cache_key] = {
            'data': response,
            'timestamp': time.time()
        }
        
        # Enforce cache size limit
        self._enforce_cache_size_limit(self._llm_response_cache)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_agent_requests = self._cache_stats['agent_hits'] + self._cache_stats['agent_misses']
        total_llm_requests = self._cache_stats['llm_hits'] + self._cache_stats['llm_misses']
        
        return {
            'agent_cache_size': len(self._agent_cache),
            'llm_cache_size': len(self._llm_response_cache),
            'agent_hit_rate': (
                self._cache_stats['agent_hits'] / total_agent_requests * 100
                if total_agent_requests > 0 else 0
            ),
            'llm_hit_rate': (
                self._cache_stats['llm_hits'] / total_llm_requests * 100
                if total_llm_requests > 0 else 0
            ),
            'total_agent_requests': total_agent_requests,
            'total_llm_requests': total_llm_requests,
            'cache_stats': self._cache_stats.copy()
        }
    
    def clear_cache(self, cache_type: str = 'all'):
        """Clear cache entries."""
        if cache_type in ['all', 'agents']:
            self._agent_cache.clear()
        if cache_type in ['all', 'llm']:
            self._llm_response_cache.clear()
        if cache_type == 'all':
            self._cache_stats = {
                'agent_hits': 0,
                'agent_misses': 0,
                'llm_hits': 0,
                'llm_misses': 0
            }

# Global cache manager instance
agent_cache_manager = AgentCacheManager()

def get_agent_cache_manager():
    """Get the global agent cache manager."""
    return agent_cache_manager

# Cached agent creation functions
def create_cached_conversation_agent():
    """Create or get cached conversation agent."""
    cache_manager = get_agent_cache_manager()
    
    # Try to get from cache first
    cached_agent = cache_manager.get_cached_agent('conversation')
    if cached_agent:
        return cached_agent
    
    # Create new agent if not in cache
    try:
        from src.core.simple_graph import create_conversation_agent
        agent = create_conversation_agent()
        
        # Cache the agent
        cache_manager.cache_agent('conversation', agent)
        return agent
    except Exception as e:
        print(f"❌ Failed to create conversation agent: {e}")
        return None

def create_cached_rag_agent():
    """Create or get cached RAG agent."""
    cache_manager = get_agent_cache_manager()
    
    # Try to get from cache first
    cached_agent = cache_manager.get_cached_agent('rag')
    if cached_agent:
        return cached_agent
    
    # Create new agent if not in cache
    try:
        from src.core.simple_graph import create_rag_agent
        agent = create_rag_agent()
        
        # Cache the agent
        cache_manager.cache_agent('rag', agent)
        return agent
    except Exception as e:
        print(f"❌ Failed to create RAG agent: {e}")
        return None

def get_cached_agent_graph():
    """Get or create cached agent graph."""
    cache_manager = get_agent_cache_manager()
    
    # Try to get from cache first
    cached_graph = cache_manager.get_cached_agent('graph')
    if cached_graph:
        return cached_graph
    
    # Create new graph if not in cache
    try:
        from src.core.simple_graph import create_simple_agent_graph
        graph = create_simple_agent_graph()
        
        # Cache the graph
        cache_manager.cache_agent('graph', graph)
        return graph
    except Exception as e:
        print(f"❌ Failed to create agent graph: {e}")
        return None

# LRU cache for frequently used functions
@lru_cache(maxsize=128)
def get_cached_llm_factory(provider: str, model: str, temperature: float = 0.2):
    """Get cached LLM factory instance."""
    try:
        from src.llms.llm_factory import LLMFactory
        from src.config.settings import LLMConfig
        
        config = LLMConfig(
            provider=provider,
            model=model,
            temperature=temperature
        )
        return LLMFactory(config)
    except Exception as e:
        print(f"❌ Failed to create LLM factory: {e}")
        return None

def process_with_cached_llm(prompt: str, model_config: Dict = None) -> Optional[str]:
    """Process prompt with cached LLM response."""
    cache_manager = get_agent_cache_manager()
    
    # Try to get cached response first
    cached_response = cache_manager.get_cached_llm_response(prompt, model_config)
    if cached_response:
        return cached_response
    
    # Process with LLM if not cached
    try:
        # This would be implemented based on your LLM setup
        # For now, return None to indicate no cached response
        return None
    except Exception as e:
        print(f"❌ Failed to process LLM request: {e}")
        return None
