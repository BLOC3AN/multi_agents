#!/usr/bin/env python3
"""
Main application entry point for the multi-agent system.
"""
import sys
import logging


from src.config.settings import config
from graph import create_agent_graph, create_initial_state


def setup_logging():
    """Setup logging configuration."""
    level = logging.DEBUG if config.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def process_input(user_input: str) -> dict:
    """
    Process user input through the multi-agent system.

    Args:
        user_input: The user's input text

    Returns:
        Dictionary containing the processing result
    """
    try:
        # Create the enhanced parallel agent graph
        graph = create_agent_graph()

        # Create initial state for enhanced system
        initial_state = create_initial_state(user_input)

        # Process through the graph
        final_state = graph.invoke(initial_state)

        return final_state

    except Exception as e:
        logging.error(f"Error processing input: {str(e)}")
        return {
            "input": user_input,
            "detected_intents": None,
            "primary_intent": None,
            "agent_results": None,
            "final_result": None,
            "errors": [f"System error: {str(e)}"],
            "processing_mode": None,
            "execution_summary": None
        }


def interactive_mode():
    """Run the application in interactive mode."""
    print("🤖 Multi-Agent System")
    print("Type 'quit' or 'exit' to stop")
    print("-" * 40)

    while True:
        try:
            user_input = input("\n💬 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("🔄 Processing...")
            result = process_input(user_input)

            # Display enhanced results
            print(f"\n🎯 Primary Intent: {result.get('primary_intent', 'Unknown')}")
            print(f"🔄 Processing Mode: {result.get('processing_mode', 'Unknown')}")

            # Show detected intents if multiple
            detected_intents = result.get('detected_intents', [])
            if detected_intents and len(detected_intents) > 1:
                intents_str = ", ".join([f"{i.intent}({i.confidence:.2f})" for i in detected_intents])
                print(f"🎪 Multiple Intents: {intents_str}")

            # Show final result
            if result.get('errors') and len(result.get('errors', [])) > 0:
                print(f"❌ Errors: {', '.join(result['errors'])}")
            elif result.get('final_result'):
                print(f"✅ Result:\n{result['final_result']}")
            else:
                print("⚠️  No result generated")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")


def main():
    """Main application function."""
    setup_logging()

    if len(sys.argv) > 1:
        # Process single input from command line
        user_input = " ".join(sys.argv[1:])
        result = process_input(user_input)

        print(f"Input: {result['input']}")
        print(f"Primary Intent: {result.get('primary_intent', 'Unknown')}")
        print(f"Processing Mode: {result.get('processing_mode', 'Unknown')}")

        if result.get('errors') and len(result.get('errors', [])) > 0:
            print(f"Errors: {', '.join(result['errors'])}")
            sys.exit(1)
        elif result.get('final_result'):
            print(f"Result: {result['final_result']}")
        else:
            print("No result generated")
            sys.exit(1)
    else:
        # Run in interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()