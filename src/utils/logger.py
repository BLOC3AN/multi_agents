"""
Enhanced logging system for Multi-Agent System.
Provides structured logging with different levels and formatters.
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        
        return json.dumps(log_entry)


class MultiAgentLogger:
    """Enhanced logger for Multi-Agent System."""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers."""
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with JSON format
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / f"{self.name}.log")
        file_handler.setLevel(logging.DEBUG)
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with extra fields."""
        extra = {}
        for key, value in kwargs.items():
            extra[key] = value
        
        self.logger.log(level, message, extra=extra)
    
    def log_request(self, method: str, endpoint: str, user_id: Optional[str] = None, 
                   request_id: Optional[str] = None):
        """Log HTTP request."""
        self.info(
            f"🌐 {method} {endpoint}",
            user_id=user_id,
            request_id=request_id,
            event_type="http_request"
        )
    
    def log_response(self, status_code: int, processing_time: float, 
                    user_id: Optional[str] = None, request_id: Optional[str] = None):
        """Log HTTP response."""
        emoji = "✅" if status_code < 400 else "❌"
        self.info(
            f"{emoji} Response {status_code} ({processing_time:.2f}ms)",
            user_id=user_id,
            request_id=request_id,
            processing_time=processing_time,
            status_code=status_code,
            event_type="http_response"
        )
    
    def log_socket_event(self, event: str, user_id: Optional[str] = None, 
                        session_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """Log Socket.IO event."""
        self.info(
            f"🔌 Socket event: {event}",
            user_id=user_id,
            session_id=session_id,
            event_type="socket_event",
            socket_event=event,
            data=data
        )
    
    def log_agent_processing(self, intent: str, processing_time: float, 
                           success: bool, user_id: Optional[str] = None,
                           session_id: Optional[str] = None):
        """Log agent processing."""
        emoji = "🤖✅" if success else "🤖❌"
        status = "success" if success else "failed"
        self.info(
            f"{emoji} Agent processing {intent} - {status} ({processing_time:.2f}ms)",
            user_id=user_id,
            session_id=session_id,
            intent=intent,
            processing_time=processing_time,
            success=success,
            event_type="agent_processing"
        )
    
    def log_database_operation(self, operation: str, collection: str, 
                             success: bool, processing_time: float):
        """Log database operation."""
        emoji = "🗄️✅" if success else "🗄️❌"
        status = "success" if success else "failed"
        self.info(
            f"{emoji} DB {operation} on {collection} - {status} ({processing_time:.2f}ms)",
            operation=operation,
            collection=collection,
            success=success,
            processing_time=processing_time,
            event_type="database_operation"
        )


# Global logger instances
socketio_logger = MultiAgentLogger("socketio", os.getenv("LOG_LEVEL", "INFO"))
api_logger = MultiAgentLogger("api", os.getenv("LOG_LEVEL", "INFO"))
agent_logger = MultiAgentLogger("agent", os.getenv("LOG_LEVEL", "INFO"))
database_logger = MultiAgentLogger("database", os.getenv("LOG_LEVEL", "INFO"))
system_logger = MultiAgentLogger("system", os.getenv("LOG_LEVEL", "INFO"))


def get_logger(name: str) -> MultiAgentLogger:
    """Get or create a logger instance."""
    return MultiAgentLogger(name, os.getenv("LOG_LEVEL", "INFO"))
