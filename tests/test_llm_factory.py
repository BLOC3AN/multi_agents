"""
Tests for the LLM factory.
"""
import pytest
from unittest.mock import Mock, patch
from src.llms.llm_factory import LLMFactory
from src.config.settings import LLMConfig


class TestLLMFactory:
    """Test cases for LLMFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = LLMConfig(
            provider="gemini",
            model="gemini-2.0-flash",
            temperature=0.2,
            top_p=0.2,
            top_k=40,
        )
        self.factory = LLMFactory(self.config)
    
    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = self.factory.get_available_providers()
        assert "gemini" in providers
        assert "openai" in providers
        assert isinstance(providers, list)
    
    def test_unsupported_provider(self):
        """Test error handling for unsupported provider."""
        config = LLMConfig(provider="unsupported")
        factory = LLMFactory(config)
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            factory.create_llm()
    
    def test_gemini_provider_creation(self):
        """Test creation of Gemini provider."""
        # Test that gemini provider is used by default
        result = self.factory.create_llm()
        assert result is not None
        # Just verify it doesn't crash and returns something
    
    def test_openai_provider_creation(self):
        """Test creation of OpenAI provider."""
        config = LLMConfig(provider="openai")
        factory = LLMFactory(config)

        # This will fail without API key, but that's expected
        # We're just testing the factory logic
        try:
            result = factory.create_llm()
            assert result is not None
        except Exception as e:
            # Expected to fail without API key
            assert "api_key" in str(e).lower()
    
    def test_register_provider(self):
        """Test registering a new provider."""
        class CustomProvider:
            def __init__(self, config):
                self.config = config
            
            def create_llm(self):
                return Mock()
        
        self.factory.register_provider("custom", CustomProvider)
        providers = self.factory.get_available_providers()
        assert "custom" in providers
        
        # Test using the custom provider
        config = LLMConfig(provider="custom")
        factory = LLMFactory(config)
        factory.register_provider("custom", CustomProvider)
        
        llm = factory.create_llm()
        assert llm is not None
