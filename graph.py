"""
Simple single-agent conversation system.
Replaces the complex multi-agent orchestration with a unified approach.
"""
# Import the simple graph system
from src.core.simple_graph import (
    create_simple_agent_graph,
    create_initial_state,
    process_user_input
)


# Backward compatibility functions - delegate to simple graph
def create_agent_graph():
    """Create and configure the simple conversation agent graph."""
    return create_simple_agent_graph()


# Create the simple graph instance
graph = create_agent_graph()


# Import AgentState for backward compatibility
from src.core.types import AgentState

# Re-export create_initial_state from simple_graph for backward compatibility
# This ensures existing code continues to work


if __name__ == "__main__":
    # Example usage with simple conversation system
    print("🚀 Testing Simple Conversation Agent System")
    print("=" * 50)

    test_cases = [
        "Please solve this math problem: 2x + 3 = 7",
        "Write a poem about artificial intelligence",
        "Viết một bài thơ về mùa xuân",
        "Explain machine learning"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_input}")
        print("-" * 40)

        # Process using simple graph
        result = process_user_input(test_input)

        # Display results
        print(f"✅ Success: {result.get('success', False)}")
        print(f"🤖 Result:\n{result.get('result', 'No result')}")

        if result.get('error'):
            print(f"❌ Error: {result['error']}")

        metadata = result.get('metadata', {})
        if metadata:
            print(f"📊 Metadata: {metadata}")

        print("=" * 50)