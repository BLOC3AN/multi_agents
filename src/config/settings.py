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
class AppConfig:
    """Main application configuration."""
    llm: LLMConfig
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
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )


# Global configuration instance
config = AppConfig.from_env()
