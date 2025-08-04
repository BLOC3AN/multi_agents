"""
Simple logging system for Multi-Agent System.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Setup a simple logger with console and file handlers."""
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(log_dir / f"{name}.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger instances
socketio_logger = setup_logger("socketio", os.getenv("LOG_LEVEL", "INFO"))
api_logger = setup_logger("api", os.getenv("LOG_LEVEL", "INFO"))
agent_logger = setup_logger("agent", os.getenv("LOG_LEVEL", "INFO"))
database_logger = setup_logger("database", os.getenv("LOG_LEVEL", "INFO"))
system_logger = setup_logger("system", os.getenv("LOG_LEVEL", "INFO"))


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance."""
    return setup_logger(name, os.getenv("LOG_LEVEL", "INFO"))


# Add backward compatibility methods to logger instances
def add_log_response_method(logger):
    """Add log_response method for backward compatibility."""
    def log_response(status_code: int, processing_time: float, **kwargs):
        emoji = "✅" if status_code < 400 else "❌"
        logger.info(f"{emoji} Response {status_code} ({processing_time:.2f}ms)")

    logger.log_response = log_response
    return logger


def add_log_socket_event_method(logger):
    """Add log_socket_event method for backward compatibility."""
    def log_socket_event(event: str, **kwargs):
        logger.info(f"🔌 Socket event: {event}")

    logger.log_socket_event = log_socket_event
    return logger


# Apply backward compatibility to existing loggers
api_logger = add_log_response_method(api_logger)
socketio_logger = add_log_socket_event_method(socketio_logger)
