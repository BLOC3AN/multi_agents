"""
Optimized Logging System
Provides high-performance logging with reduced redundancy and better caching
"""
import logging
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from functools import lru_cache
from collections import defaultdict
import hashlib

class OptimizedLogger:
    """High-performance logger with deduplication and caching."""
    
    def __init__(self, name: str, log_file: str = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger(log_file)
        
        # Deduplication cache
        self._message_cache = {}
        self._cache_ttl = 60  # 1 minute
        self._max_cache_size = 1000
        
        # Rate limiting
        self._rate_limit_cache = defaultdict(list)
        self._rate_limit_window = 60  # 1 minute
        self._max_messages_per_window = 100
        
        # Performance tracking
        self._log_stats = {
            'total_messages': 0,
            'deduplicated_messages': 0,
            'rate_limited_messages': 0
        }
        
        self._lock = threading.Lock()
    
    def _setup_logger(self, log_file: str = None):
        """Setup logger with optimized configuration."""
        if self.logger.handlers:
            return  # Already configured
        
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                file_handler.setLevel(logging.INFO)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"⚠️ Failed to setup file handler for {log_file}: {e}")
    
    def _generate_message_hash(self, level: str, message: str) -> str:
        """Generate hash for message deduplication."""
        key_data = f"{level}:{message}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_rate_limited(self, message_hash: str) -> bool:
        """Check if message should be rate limited."""
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - self._rate_limit_window
        self._rate_limit_cache[message_hash] = [
            timestamp for timestamp in self._rate_limit_cache[message_hash]
            if timestamp > cutoff_time
        ]
        
        # Check rate limit
        if len(self._rate_limit_cache[message_hash]) >= self._max_messages_per_window:
            return True
        
        # Add current timestamp
        self._rate_limit_cache[message_hash].append(current_time)
        return False
    
    def _should_log_message(self, level: str, message: str) -> bool:
        """Determine if message should be logged based on deduplication and rate limiting."""
        message_hash = self._generate_message_hash(level, message)
        current_time = time.time()
        
        with self._lock:
            # Check deduplication cache
            if message_hash in self._message_cache:
                cache_entry = self._message_cache[message_hash]
                if current_time - cache_entry['timestamp'] < self._cache_ttl:
                    cache_entry['count'] += 1
                    self._log_stats['deduplicated_messages'] += 1
                    return False
                else:
                    # Cache expired, remove entry
                    del self._message_cache[message_hash]
            
            # Check rate limiting
            if self._is_rate_limited(message_hash):
                self._log_stats['rate_limited_messages'] += 1
                return False
            
            # Add to cache
            self._message_cache[message_hash] = {
                'timestamp': current_time,
                'count': 1,
                'level': level,
                'message': message
            }
            
            # Enforce cache size limit
            if len(self._message_cache) > self._max_cache_size:
                # Remove oldest entries
                oldest_entries = sorted(
                    self._message_cache.items(),
                    key=lambda x: x[1]['timestamp']
                )[:100]  # Remove 100 oldest entries
                for entry_hash, _ in oldest_entries:
                    del self._message_cache[entry_hash]
            
            self._log_stats['total_messages'] += 1
            return True
    
    def _log_with_optimization(self, level: str, message: str, *args, **kwargs):
        """Log message with optimization checks."""
        if not self._should_log_message(level, message):
            return
        
        # Get the actual logging method
        log_method = getattr(self.logger, level.lower())
        log_method(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with optimization."""
        self._log_with_optimization('INFO', message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with optimization."""
        self._log_with_optimization('WARNING', message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with optimization."""
        self._log_with_optimization('ERROR', message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with optimization."""
        self._log_with_optimization('DEBUG', message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message (always logged, no optimization)."""
        self.logger.critical(message, *args, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._lock:
            return {
                'logger_name': self.name,
                'total_messages': self._log_stats['total_messages'],
                'deduplicated_messages': self._log_stats['deduplicated_messages'],
                'rate_limited_messages': self._log_stats['rate_limited_messages'],
                'cache_size': len(self._message_cache),
                'rate_limit_cache_size': len(self._rate_limit_cache),
                'deduplication_rate': (
                    self._log_stats['deduplicated_messages'] / 
                    max(self._log_stats['total_messages'], 1) * 100
                ),
                'rate_limit_rate': (
                    self._log_stats['rate_limited_messages'] / 
                    max(self._log_stats['total_messages'], 1) * 100
                )
            }
    
    def clear_cache(self):
        """Clear all caches."""
        with self._lock:
            self._message_cache.clear()
            self._rate_limit_cache.clear()
            self._log_stats = {
                'total_messages': 0,
                'deduplicated_messages': 0,
                'rate_limited_messages': 0
            }

class SocketIOOptimizedLogger(OptimizedLogger):
    """Specialized logger for SocketIO events."""
    
    def __init__(self):
        super().__init__('socketio_optimized', 'logs/socketio.log')
    
    def log_socket_event(self, event_type: str, user_id: str = None, data: Dict = None):
        """Log socket event with optimization."""
        message = f"🔌 {event_type.upper()}"
        if user_id:
            message += f" - User: {user_id}"
        if data:
            # Limit data size for logging
            data_str = str(data)
            if len(data_str) > 200:
                data_str = data_str[:200] + "..."
            message += f" - Data: {data_str}"
        
        self.info(message)

class APIOptimizedLogger(OptimizedLogger):
    """Specialized logger for API requests."""
    
    def __init__(self):
        super().__init__('api_optimized', 'logs/api.log')
        self._request_stats = defaultdict(int)
    
    def log_request(self, method: str, path: str, user_id: str = None):
        """Log API request with optimization."""
        message = f"🌐 {method} {path}"
        if user_id:
            message += f" - User: {user_id}"
        
        self.info(message)
        self._request_stats[f"{method} {path}"] += 1
    
    def log_response(self, status_code: int, processing_time: float):
        """Log API response with optimization."""
        if status_code >= 400:
            level = 'error' if status_code >= 500 else 'warning'
            message = f"📤 Response: {status_code} - {processing_time:.2f}ms"
            getattr(self, level)(message)
        else:
            # Only log successful responses occasionally to reduce noise
            if processing_time > 1000:  # Only log slow responses
                self.info(f"📤 Response: {status_code} - {processing_time:.2f}ms (slow)")
    
    def get_request_stats(self) -> Dict[str, int]:
        """Get request statistics."""
        return dict(self._request_stats)

# Global optimized logger instances
_logger_cache = {}

@lru_cache(maxsize=10)
def get_optimized_logger(logger_type: str) -> OptimizedLogger:
    """Get optimized logger instance with caching."""
    if logger_type == 'socketio':
        return SocketIOOptimizedLogger()
    elif logger_type == 'api':
        return APIOptimizedLogger()
    elif logger_type == 'system':
        return OptimizedLogger('system_optimized', 'logs/system.log')
    else:
        return OptimizedLogger(logger_type, f'logs/{logger_type}.log')

# Backward compatibility functions
def get_socketio_logger():
    """Get optimized SocketIO logger."""
    return get_optimized_logger('socketio')

def get_api_logger():
    """Get optimized API logger."""
    return get_optimized_logger('api')

def get_system_logger():
    """Get optimized system logger."""
    return get_optimized_logger('system')

# Performance monitoring
def get_all_logger_stats() -> Dict[str, Any]:
    """Get statistics from all loggers."""
    stats = {}
    for logger_type in ['socketio', 'api', 'system']:
        try:
            logger = get_optimized_logger(logger_type)
            stats[logger_type] = logger.get_stats()
        except Exception as e:
            stats[logger_type] = {'error': str(e)}
    
    return stats
