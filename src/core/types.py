"""
Shared types and data structures for the single conversation agent system.
"""
from typing import TypedDict, Literal, Optional, Dict, List
from dataclasses import dataclass


# Legacy types kept for backward compatibility
IntentType = Literal["general"]  # Simplified to single type


@dataclass
class IntentScore:
    """Legacy intent score structure - kept for backward compatibility."""
    intent: IntentType
    confidence: float
    reasoning: Optional[str] = None


@dataclass
class AgentResult:
    """Legacy agent result structure - kept for backward compatibility."""
    agent_name: str
    intent: IntentType
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class AgentState(TypedDict):
    """Simplified state structure for single conversation agent."""
    input: str
    # Legacy fields kept for backward compatibility
    detected_intents: Optional[List[IntentScore]]
    primary_intent: Optional[IntentType]
    agent_results: Optional[Dict[str, AgentResult]]
    # Main result field
    final_result: Optional[str]
    # Error handling
    errors: Optional[List[str]]
    # Metadata
    processing_mode: Optional[Literal["single"]]  # Only single mode now
    execution_summary: Optional[Dict[str, any]]
    # Context support
    conversation_context: Optional[List[Dict[str, any]]]
    user_id: Optional[str]
    session_id: Optional[str]


class AgentResponse(TypedDict):
    """Standard response structure from agents."""
    success: bool
    result: Optional[str]
    error: Optional[str]


# Legacy config type - no longer used but kept for compatibility
class ParallelExecutionConfig(TypedDict):
    """Legacy configuration for parallel execution - no longer used."""
    max_concurrent_agents: int
    timeout_seconds: float
    confidence_threshold: float
    require_primary_intent: bool
