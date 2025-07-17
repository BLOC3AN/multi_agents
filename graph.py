"""
Multi-agent orchestration using LangGraph.
This module has been refactored for better maintainability and error handling.
"""
from langgraph.graph import StateGraph, END

from src.core.types import AgentState
from src.agents.context_agent import context_agent
from src.agents.math_agent import math_agent
from src.agents.poem_agent import poem_agent
from src.agents.english_agent import english_agent


def route_from_intent(state: AgentState) -> str:
    """Route to appropriate agent based on classified intent."""
    intent = state.get("intent")

    if intent == "math":
        return "MathAgent"
    elif intent == "poem":
        return "PoemAgent"
    elif intent == "english":
        return "EnglishAgent"
    else:
        # Default to English agent if intent is unclear
        return "EnglishAgent"


def create_agent_graph():
    """Create and configure the agent graph."""
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("ContextAgent", context_agent)
    builder.add_node("MathAgent", math_agent)
    builder.add_node("PoemAgent", poem_agent)
    builder.add_node("EnglishAgent", english_agent)

    # Set entry point
    builder.set_entry_point("ContextAgent")

    # Add conditional routing from context agent
    builder.add_conditional_edges(
        "ContextAgent",
        route_from_intent,
        {
            "MathAgent": "MathAgent",
            "EnglishAgent": "EnglishAgent",
            "PoemAgent": "PoemAgent",
        }
    )

    # All agents end the flow
    builder.add_edge("MathAgent", END)
    builder.add_edge("EnglishAgent", END)
    builder.add_edge("PoemAgent", END)

    return builder.compile()


# Create the graph instance
graph = create_agent_graph()


if __name__ == "__main__":
    # Example usage
    test_state = {"input": "Please solve this math problem: 2x + 3 = 7"}
    final_state = graph.invoke(test_state)
    print(f"Input: {final_state['input']}")
    print(f"Intent: {final_state.get('intent', 'Unknown')}")
    print(f"Result: {final_state.get('result', 'No result')}")
    if final_state.get('error'):
        print(f"Error: {final_state['error']}")