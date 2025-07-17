"""
Intent classification logic for routing user input to appropriate agents.
"""
from typing import Dict, List, Callable
from src.core.types import AgentState, IntentType


class IntentClassifier:
    """Simple rule-based intent classifier."""
    
    def __init__(self):
        """Initialize the classifier with keyword mappings."""
        self.intent_keywords: Dict[IntentType, List[str]] = {
            "math": ["math", "solve", "calculate", "equation", "problem", "toán", "giải", "tính", "+", "-", "*", "/", "=", "x +", "x -"],
            "poem": ["poem", "poetry", "verse", "thơ", "bài thơ", "viết thơ", "write a poem", "create a verse", "compose"],
            "english": ["english", "explain", "translate", "tiếng anh", "giải thích", "describe", "what is", "how does", "machine learning", "quantum"]
        }
        
        self.default_intent: IntentType = "english"
    
    def classify(self, text: str) -> IntentType:
        """
        Classify the intent based on keywords in the input text.
        
        Args:
            text: Input text to classify
            
        Returns:
            The classified intent type
        """
        text_lower = text.lower()
        
        # Count matches for each intent
        intent_scores: Dict[IntentType, int] = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return intent with highest score, or default if no matches
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return self.default_intent
    
    def classify_state(self, state: AgentState) -> AgentState:
        """
        Classify intent and update the state.
        This method can be used directly in the graph.
        """
        try:
            intent = self.classify(state["input"])
            state["intent"] = intent
            state["error"] = None
        except Exception as e:
            state["intent"] = self.default_intent
            state["error"] = f"Error in intent classification: {str(e)}"
        
        return state
