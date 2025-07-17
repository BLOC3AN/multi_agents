"""
Parallel orchestrator for running multiple agents concurrently.
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable
from dataclasses import asdict

from src.core.types import AgentState, AgentResult, IntentScore, ParallelExecutionConfig
from src.core.base_agent import BaseAgent
from src.llms.llm_factory import LLMFactory


class ParallelOrchestrator:
    """Orchestrates parallel execution of multiple agents."""
    
    def __init__(self, llm_factory: LLMFactory, config: Optional[ParallelExecutionConfig] = None):
        """Initialize the orchestrator."""
        self.llm_factory = llm_factory
        self.config = config or {
            "max_concurrent_agents": 3,
            "timeout_seconds": 30.0,
            "confidence_threshold": 0.3,
            "require_primary_intent": True
        }
        
        # Registry of available agents
        self._agent_registry: Dict[str, Callable[[], BaseAgent]] = {}
        
    def register_agent(self, intent: str, agent_factory: Callable[[], BaseAgent]):
        """Register an agent factory for a specific intent."""
        self._agent_registry[intent] = agent_factory
    
    def _create_agent_for_intent(self, intent: str) -> Optional[BaseAgent]:
        """Create an agent instance for the given intent."""
        if intent in self._agent_registry:
            return self._agent_registry[intent]()
        return None
    
    def _execute_single_agent(self, agent: BaseAgent, state: AgentState, intent: str) -> AgentResult:
        """Execute a single agent and return the result."""
        start_time = time.time()
        
        try:
            # Create a copy of state for this agent
            agent_state = state.copy()
            result_state = agent.process(agent_state)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                agent_name=agent.get_agent_name(),
                intent=intent,
                success=result_state.get("errors") is None or len(result_state.get("errors", [])) == 0,
                result=result_state.get("final_result") or result_state.get("result"),
                error=result_state.get("errors")[0] if result_state.get("errors") else None,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentResult(
                agent_name=agent.get_agent_name(),
                intent=intent,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def execute_parallel(self, state: AgentState) -> AgentState:
        """
        Execute multiple agents in parallel based on detected intents.
        
        Args:
            state: Current agent state with detected intents
            
        Returns:
            Updated state with results from all agents
        """
        detected_intents = state.get("detected_intents", [])
        
        if not detected_intents:
            # No intents detected, return error
            state["errors"] = state.get("errors", []) + ["No intents detected for parallel execution"]
            return state
        
        # Filter intents by confidence threshold
        eligible_intents = [
            intent_score for intent_score in detected_intents 
            if intent_score.confidence >= self.config["confidence_threshold"]
        ]
        
        if not eligible_intents:
            # Fall back to primary intent if no intents meet threshold
            if state.get("primary_intent"):
                eligible_intents = [IntentScore(
                    intent=state["primary_intent"], 
                    confidence=0.5, 
                    reasoning="Fallback to primary intent"
                )]
        
        # Limit concurrent agents
        max_agents = min(len(eligible_intents), self.config["max_concurrent_agents"])
        eligible_intents = eligible_intents[:max_agents]
        
        # Create agents for eligible intents
        agents_to_execute = []
        for intent_score in eligible_intents:
            agent = self._create_agent_for_intent(intent_score.intent)
            if agent:
                agents_to_execute.append((agent, intent_score.intent))
        
        if not agents_to_execute:
            state["errors"] = state.get("errors", []) + ["No agents available for detected intents"]
            return state
        
        # Execute agents in parallel using ThreadPoolExecutor
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_agents) as executor:
            # Submit all agent executions
            future_to_intent = {
                executor.submit(self._execute_single_agent, agent, state, intent): intent
                for agent, intent in agents_to_execute
            }
            
            # Collect results with timeout
            try:
                for future in as_completed(future_to_intent, timeout=self.config["timeout_seconds"]):
                    intent = future_to_intent[future]
                    try:
                        result = future.result()
                        results[intent] = result
                    except Exception as e:
                        results[intent] = AgentResult(
                            agent_name=f"Unknown_{intent}",
                            intent=intent,
                            success=False,
                            result=None,
                            error=str(e),
                            execution_time=0.0
                        )
            except TimeoutError:
                # Handle timeout
                state["errors"] = state.get("errors", []) + [f"Parallel execution timeout after {self.config['timeout_seconds']}s"]
        
        # Update state with results
        state["agent_results"] = results
        
        # Create execution summary
        state["execution_summary"] = {
            "total_agents": len(agents_to_execute),
            "successful_agents": sum(1 for r in results.values() if r.success),
            "failed_agents": sum(1 for r in results.values() if not r.success),
            "total_execution_time": sum(r.execution_time or 0 for r in results.values()),
            "intents_processed": list(results.keys())
        }
        
        return state
    
    def execute_single(self, state: AgentState) -> AgentState:
        """
        Execute single agent based on primary intent.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with single agent result
        """
        primary_intent = state.get("primary_intent")
        
        if not primary_intent:
            state["errors"] = state.get("errors", []) + ["No primary intent for single execution"]
            return state
        
        agent = self._create_agent_for_intent(primary_intent)
        if not agent:
            state["errors"] = state.get("errors", []) + [f"No agent available for intent: {primary_intent}"]
            return state
        
        # Execute single agent
        result = self._execute_single_agent(agent, state, primary_intent)
        
        # Update state
        state["agent_results"] = {primary_intent: result}
        state["execution_summary"] = {
            "total_agents": 1,
            "successful_agents": 1 if result.success else 0,
            "failed_agents": 0 if result.success else 1,
            "total_execution_time": result.execution_time or 0,
            "intents_processed": [primary_intent]
        }
        
        return state
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Execute agents based on processing mode.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with execution results
        """
        processing_mode = state.get("processing_mode", "single")
        
        if processing_mode == "parallel":
            return self.execute_parallel(state)
        else:
            return self.execute_single(state)
