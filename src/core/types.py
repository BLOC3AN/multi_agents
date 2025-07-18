"""
Shared types and data structures for the multi-agent system.
"""
from typing import TypedDict, Literal, Optional, Dict, List
from dataclasses import dataclass


# Intent types
IntentType = Literal["math", "english", "poem"]


@dataclass
class IntentScore:
    """Intent with confidence score."""
    intent: IntentType
    confidence: float
    reasoning: Optional[str] = None


@dataclass
class AgentResult:
    """Result from a single agent."""
    agent_name: str
    intent: IntentType
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class AgentState(TypedDict):
    """Enhanced state structure supporting multi-intent parallel processing."""
    input: str
    # Multi-intent support
    detected_intents: Optional[List[IntentScore]]
    primary_intent: Optional[IntentType]
    # Parallel results
    agent_results: Optional[Dict[str, AgentResult]]
    # Final aggregated result
    final_result: Optional[str]
    # Error handling
    errors: Optional[List[str]]
    # Metadata
    processing_mode: Optional[Literal["single", "parallel"]]
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


class ParallelExecutionConfig(TypedDict):
    """Configuration for parallel execution."""
    max_concurrent_agents: int
    timeout_seconds: float
    confidence_threshold: float
    require_primary_intent: bool
