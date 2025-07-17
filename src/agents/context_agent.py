"""
Context agent for intent classification.
This agent has been replaced by the IntentClassifier class.
"""
# This file is kept for backward compatibility
# The functionality has been moved to src.core.intent_classifier

from src.core.intent_classifier import IntentClassifier
from src.core.types import AgentState

# Create a global classifier instance for backward compatibility
_classifier = IntentClassifier()

def context_agent(state: AgentState) -> AgentState:
    """
    Legacy function for backward compatibility.
    Use IntentClassifier.classify_state() directly for new code.
    """
    return _classifier.classify_state(state)
