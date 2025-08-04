"""
Multi-agent orchestration using LangGraph with parallel execution support.
Enhanced to support multi-intent detection and parallel agent execution.
"""
from langgraph.graph import StateGraph, END

from src.core.types import AgentState, ParallelExecutionConfig
from src.core.intent_classifier import IntentClassifier
from src.core.parallel_orchestrator import ParallelOrchestrator
from src.core.result_aggregator import ResultAggregator
from src.llms.llm_factory import LLMFactory
from src.config.settings import config

# Import agent classes
from src.agents.math_agent import MathAgent
from src.agents.poem_agent import PoemAgent
from src.agents.english_agent import EnglishAgent


# Global instances
llm_factory = LLMFactory(config.llm)
intent_classifier = IntentClassifier(llm_factory)
parallel_orchestrator = ParallelOrchestrator(llm_factory)
result_aggregator = ResultAggregator(llm_factory)

# Register agents with orchestrator
parallel_orchestrator.register_agent("math", lambda: MathAgent(llm_factory))
parallel_orchestrator.register_agent("poem", lambda: PoemAgent(llm_factory))
parallel_orchestrator.register_agent("english", lambda: EnglishAgent(llm_factory))


def classify_intent_node(state: AgentState) -> AgentState:
    """Node for intent classification with multi-intent support."""
    return intent_classifier.classify_state(state)


def execute_agents_node(state: AgentState) -> AgentState:
    """Node for executing agents (single or parallel based on processing mode)."""
    return parallel_orchestrator.execute(state)


def aggregate_results_node(state: AgentState) -> AgentState:
    """Node for aggregating results from multiple agents."""
    return result_aggregator.aggregate_results(state)


def route_to_execution(state: AgentState) -> str:
    """Route to execution based on processing mode."""
    processing_mode = state.get("processing_mode", "single")

    if processing_mode == "parallel":
        return "ExecuteAgents"
    else:
        return "ExecuteAgents"  # Same node handles both modes


def create_agent_graph():
    """Create and configure the enhanced parallel agent graph."""
    builder = StateGraph(AgentState)

    # Add nodes for the new parallel workflow
    builder.add_node("ClassifyIntent", classify_intent_node)
    builder.add_node("ExecuteAgents", execute_agents_node)
    builder.add_node("AggregateResults", aggregate_results_node)

    # Set entry point
    builder.set_entry_point("ClassifyIntent")

    # Linear flow: Classify -> Execute -> Aggregate -> End
    builder.add_edge("ClassifyIntent", "ExecuteAgents")
    builder.add_edge("ExecuteAgents", "AggregateResults")
    builder.add_edge("AggregateResults", END)

    return builder.compile()


# Create the enhanced parallel graph instance
graph = create_agent_graph()


def create_initial_state(user_input: str) -> AgentState:
    """Create initial state for the enhanced graph."""
    return {
        "input": user_input,
        "detected_intents": None,
        "primary_intent": None,
        "agent_results": None,
        "final_result": None,
        "errors": None,
        "processing_mode": None,
        "execution_summary": None
    }


if __name__ == "__main__":
    # Example usage with enhanced parallel system
    print("🚀 Testing Enhanced Parallel Multi-Agent System")
    print("=" * 50)

    test_cases = [
        "Please solve this math problem: 2x + 3 = 7",
        "Write a poem about artificial intelligence and explain what AI is",
        "Viết một bài thơ về mùa xuân",
        "Explain machine learning and calculate 15 + 25"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_input}")
        print("-" * 40)

        # Create initial state
        initial_state = create_initial_state(test_input)

        # Process through enhanced graph
        final_state = graph.invoke(initial_state)

        # Display results
        print(f"🎯 Primary Intent: {final_state.get('primary_intent', 'Unknown')}")
        print(f"🔄 Processing Mode: {final_state.get('processing_mode', 'Unknown')}")

        detected_intents = final_state.get('detected_intents', [])
        if detected_intents:
            print(f"🎪 Detected Intents: {[(i.intent, f'{i.confidence:.2f}') for i in detected_intents]}")

        print(f"✅ Final Result:\n{final_state.get('final_result', 'No result')}")

        if final_state.get('errors'):
            print(f"❌ Errors: {final_state['errors']}")

        print("=" * 50)