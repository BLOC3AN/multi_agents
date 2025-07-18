"""
Configuration management for the multi-agent system.
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.2
    top_p: float = 0.2
    top_k: int = 40


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "multi_agent_system"
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None


@dataclass
class CacheConfig:
    """Configuration for caching."""
    user_cache_ttl: int = 3600  # 1 hour
    session_cache_ttl: int = 7200  # 2 hours
    context_cache_ttl: int = 1800  # 30 minutes
    message_cache_ttl: int = 1800  # 30 minutes
    processing_status_ttl: int = 300  # 5 minutes


@dataclass
class AppConfig:
    """Main application configuration."""
    llm: LLMConfig
    database: DatabaseConfig
    cache: CacheConfig
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        return cls(
            llm=LLMConfig(
                provider=os.getenv("LLM_PROVIDER", "gemini"),
                model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
                top_p=float(os.getenv("LLM_TOP_P", "0.2")),
                top_k=int(os.getenv("LLM_TOP_K", "40")),
            ),
            database=DatabaseConfig(
                mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
                mongodb_database=os.getenv("MONGODB_DATABASE", "multi_agent_system"),
                redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
                redis_db=int(os.getenv("REDIS_DB", "0")),
                redis_password=os.getenv("REDIS_PASSWORD")
            ),
            cache=CacheConfig(
                user_cache_ttl=int(os.getenv("USER_CACHE_TTL", "3600")),
                session_cache_ttl=int(os.getenv("SESSION_CACHE_TTL", "7200")),
                context_cache_ttl=int(os.getenv("CONTEXT_CACHE_TTL", "1800")),
                message_cache_ttl=int(os.getenv("MESSAGE_CACHE_TTL", "1800")),
                processing_status_ttl=int(os.getenv("PROCESSING_STATUS_TTL", "300"))
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )


# Global configuration instance
config = AppConfig.from_env()
