"""
Tests for the intent classifier.
"""
import pytest
from unittest.mock import Mock, patch
from src.core.intent_classifier import IntentClassifier
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory
from src.config.settings import LLMConfig


class TestIntentClassifier:
    """Test cases for IntentClassifier."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock LLM factory and LLM
        self.mock_llm = Mock()
        self.mock_factory = Mock()
        self.mock_factory.create_llm.return_value = self.mock_llm
        self.classifier = IntentClassifier(self.mock_factory)
    
    def test_math_intent_detection(self):
        """Test detection of math-related intents."""
        # Mock LLM response for math intent
        mock_response = Mock()
        mock_response.content = "math"
        self.mock_llm.invoke.return_value = mock_response

        test_cases = [
            "solve this math problem: 2x + 3 = 7",
            "calculate the area of a circle",
            "what is 15 + 25?",
            "giải phương trình này",
            "tính toán diện tích"
        ]

        for text in test_cases:
            intent = self.classifier.classify(text)
            assert intent == "math", f"Failed for: {text}"
    
    def test_poem_intent_detection(self):
        """Test detection of poem-related intents."""
        # Mock LLM response for poem intent
        mock_response = Mock()
        mock_response.content = "poem"
        self.mock_llm.invoke.return_value = mock_response

        test_cases = [
            "write a poem about love",
            "create a verse about nature",
            "viết một bài thơ về mùa xuân",
            "compose poetry about the ocean"
        ]

        for text in test_cases:
            intent = self.classifier.classify(text)
            assert intent == "poem", f"Failed for: {text}"

    def test_english_intent_detection(self):
        """Test detection of English explanation intents."""
        # Mock LLM response for english intent
        mock_response = Mock()
        mock_response.content = "english"
        self.mock_llm.invoke.return_value = mock_response

        test_cases = [
            "explain quantum physics",
            "what is machine learning?",
            "describe how photosynthosis works",
            "giải thích về trí tuệ nhân tạo"
        ]

        for text in test_cases:
            intent = self.classifier.classify(text)
            assert intent == "english", f"Failed for: {text}"
    
    def test_default_intent_on_error(self):
        """Test default intent when LLM fails."""
        # Mock LLM to raise an exception
        self.mock_llm.invoke.side_effect = Exception("LLM error")

        text = "some input"
        intent = self.classifier.classify(text)
        assert intent == "english"  # default intent

    def test_invalid_llm_response(self):
        """Test handling of invalid LLM responses."""
        # Mock LLM response with invalid intent
        mock_response = Mock()
        mock_response.content = "invalid_intent"
        self.mock_llm.invoke.return_value = mock_response

        text = "some input"
        intent = self.classifier.classify(text)
        assert intent == "english"  # default intent

    def test_classify_state(self):
        """Test state classification method."""
        # Mock LLM response for math intent
        mock_response = Mock()
        mock_response.content = "math"
        self.mock_llm.invoke.return_value = mock_response

        state: AgentState = {
            "input": "solve 2x + 5 = 11",
            "intent": None,
            "result": None,
            "error": None
        }

        updated_state = self.classifier.classify_state(state)

        assert updated_state["intent"] == "math"
        assert updated_state["error"] is None
        assert updated_state["input"] == "solve 2x + 5 = 11"

    def test_llm_response_with_extra_text(self):
        """Test handling LLM response with extra text."""
        # Mock LLM response with extra text but containing valid intent
        mock_response = Mock()
        mock_response.content = "The intent is clearly math based on the equation."
        self.mock_llm.invoke.return_value = mock_response

        text = "solve 2x + 3 = 7"
        intent = self.classifier.classify(text)
        assert intent == "math"
