"""
Tests for the intent classifier.
"""
import pytest
from src.core.intent_classifier import IntentClassifier
from src.core.types import AgentState


class TestIntentClassifier:
    """Test cases for IntentClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = IntentClassifier()
    
    def test_math_intent_detection(self):
        """Test detection of math-related intents."""
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
        test_cases = [
            "explain quantum physics",
            "what is machine learning?",
            "describe how photosynthesis works",
            "giải thích về trí tuệ nhân tạo"
        ]
        
        for text in test_cases:
            intent = self.classifier.classify(text)
            assert intent == "english", f"Failed for: {text}"
    
    def test_default_intent(self):
        """Test default intent for unclear input."""
        unclear_inputs = [
            "hello",
            "how are you?",
            "random text without clear intent"
        ]
        
        for text in unclear_inputs:
            intent = self.classifier.classify(text)
            assert intent == "english", f"Failed for: {text}"
    
    def test_classify_state(self):
        """Test state classification method."""
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
    
    def test_multiple_keywords(self):
        """Test input with multiple intent keywords."""
        # Math should win due to more specific keywords
        text = "explain this math problem and write a poem about it"
        intent = self.classifier.classify(text)
        # This could be either math or poem depending on implementation
        # The current implementation should pick the one with more matches
        assert intent in ["math", "poem"]
