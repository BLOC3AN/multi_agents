"""
Shared types and data structures for the multi-agent system.
"""
from typing import TypedDict, Literal, Optional


class AgentState(TypedDict):
    """Shared state structure for all agents in the system."""
    input: str
    intent: Optional[Literal["math", "english", "poem"]]
    result: Optional[str]
    error: Optional[str]


class AgentResponse(TypedDict):
    """Standard response structure from agents."""
    success: bool
    result: Optional[str]
    error: Optional[str]


# Intent types
IntentType = Literal["math", "english", "poem"]
