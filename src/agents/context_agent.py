"""
Context agent for intent classification using LLM.
"""
from src.core.intent_classifier import IntentClassifier
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory
from src.config.settings import config

# Create a global classifier instance for backward compatibility
_llm_factory = LLMFactory(config.llm)
_classifier = IntentClassifier(_llm_factory)

def context_agent(state: AgentState) -> AgentState:
    """
    LLM-powered intent classification agent.
    Uses LLM to intelligently determine user intent.
    """
    return _classifier.classify_state(state)
