"""
Simple single-agent graph to replace the complex multi-agent orchestration.
This provides a clean, straightforward conversation flow.
"""
from langgraph.graph import StateGraph, END
from src.core.types import AgentState
from src.agents.conversation_agent import ConversationAgent
from src.llms.llm_factory import LLMFactory
from src.config.settings import config


def create_conversation_agent() -> ConversationAgent:
    """Create and return a conversation agent instance."""
    llm_factory = LLMFactory(config.llm)
    return ConversationAgent(llm_factory)


def process_conversation_node(state: AgentState) -> AgentState:
    """Node for processing conversation with the single agent."""
    agent = create_conversation_agent()
    return agent.process(state)


def create_simple_agent_graph():
    """
    Create a simple graph with just one conversation agent.
    This replaces the complex multi-agent graph.
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add the single conversation node
    workflow.add_node("conversation", process_conversation_node)
    
    # Set entry point
    workflow.set_entry_point("conversation")
    
    # Add edge to end
    workflow.add_edge("conversation", END)
    
    # Compile the graph
    return workflow.compile()


def create_initial_state(user_input: str, user_id: str = None, session_id: str = None,
                        conversation_context: list = None) -> AgentState:
    """
    Create initial state for the simple conversation system.

    Args:
        user_input: The user's input text
        user_id: Optional user ID
        session_id: Optional session ID
        conversation_context: Optional conversation history

    Returns:
        Initial AgentState for processing
    """
    return {
        "input": user_input,
        "detected_intents": None,
        "primary_intent": None,
        "agent_results": None,
        "final_result": None,
        "errors": None,
        "processing_mode": "single",
        "execution_summary": None,
        "conversation_context": conversation_context or [],
        "user_id": user_id,
        "session_id": session_id
    }


def process_user_input(user_input: str, user_id: str = None, session_id: str = None,
                      conversation_context: list = None) -> dict:
    """
    High-level function to process user input through the simple conversation system.
    
    Args:
        user_input: The user's input text
        user_id: Optional user ID
        session_id: Optional session ID
        conversation_context: Optional conversation history
        
    Returns:
        Dictionary containing the processing result
    """
    try:
        # Create the simple agent graph
        graph = create_simple_agent_graph()
        
        # Create initial state
        initial_state = create_initial_state(
            user_input=user_input,
            user_id=user_id, 
            session_id=session_id,
            conversation_context=conversation_context
        )
        
        # Process through the graph
        final_state = graph.invoke(initial_state)
        
        # Return the result in a consistent format
        return {
            "success": final_state.get("errors") is None or len(final_state.get("errors", [])) == 0,
            "input": user_input,
            "result": final_state.get("final_result"),
            "error": final_state.get("errors")[0] if final_state.get("errors") else None,
            "metadata": final_state.get("metadata", {}),
            "user_id": user_id,
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "input": user_input,
            "result": None,
            "error": f"System error: {str(e)}",
            "metadata": {"error_occurred": True},
            "user_id": user_id,
            "session_id": session_id
        }
