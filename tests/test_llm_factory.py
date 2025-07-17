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
            seed=42
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
    
    @patch('src.llms.llm_factory.GeminiProvider')
    def test_gemini_provider_creation(self, mock_gemini_provider):
        """Test creation of Gemini provider."""
        mock_instance = Mock()
        mock_llm = Mock()
        mock_instance.create_llm.return_value = mock_llm
        mock_gemini_provider.return_value = mock_instance

        result = self.factory.create_llm()

        mock_gemini_provider.assert_called_once_with(self.config)
        mock_instance.create_llm.assert_called_once()
        assert result == mock_llm
    
    @patch('src.llms.llm_factory.OpenAIProvider')
    def test_openai_provider_creation(self, mock_openai_provider):
        """Test creation of OpenAI provider."""
        config = LLMConfig(provider="openai")
        factory = LLMFactory(config)

        mock_instance = Mock()
        mock_llm = Mock()
        mock_instance.create_llm.return_value = mock_llm
        mock_openai_provider.return_value = mock_instance

        result = factory.create_llm()

        mock_openai_provider.assert_called_once_with(config)
        mock_instance.create_llm.assert_called_once()
        assert result == mock_llm
    
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
