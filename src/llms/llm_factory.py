"""
LLM Factory for creating LLM instances based on configuration.
"""
from typing import Protocol, runtime_checkable

from src.config.settings import LLMConfig
from src.llms.gemini import GeminiProvider
from src.llms.openai import OpenAIProvider


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    def create_llm(self):
        """Create and return an LLM instance."""
        ...


class LLMFactory:
    """Factory for creating LLM instances."""
    
    def __init__(self, config: LLMConfig):
        """Initialize with configuration."""
        self.config = config
        self._providers = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
        }
    
    def create_llm(self):
        """Create an LLM instance based on configuration."""
        provider_class = self._providers.get(self.config.provider)
        
        if provider_class is None:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
        
        provider = provider_class(self.config)
        return provider.create_llm()
    
    def register_provider(self, name: str, provider_class: type):
        """Register a new LLM provider."""
        self._providers[name] = provider_class
    
    def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())
