#!/usr/bin/env python3
"""
Main application entry point for the multi-agent system.
"""
import sys
import logging


from src.config.settings import config
from graph import create_agent_graph


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
        # Create the agent graph
        graph = create_agent_graph()

        # Create initial state
        initial_state = {
            "input": user_input,
            "intent": None,
            "result": None,
            "error": None
        }

        # Process through the graph
        final_state = graph.invoke(initial_state)

        return final_state

    except Exception as e:
        logging.error(f"Error processing input: {str(e)}")
        return {
            "input": user_input,
            "intent": None,
            "result": None,
            "error": f"System error: {str(e)}"
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

            print(f"\n🎯 Intent: {result.get('intent', 'Unknown')}")

            if result.get('error'):
                print(f"❌ Error: {result['error']}")
            elif result.get('result'):
                print(f"✅ Result:\n{result['result']}")
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
        print(f"Intent: {result.get('intent', 'Unknown')}")

        if result.get('error'):
            print(f"Error: {result['error']}")
            sys.exit(1)
        elif result.get('result'):
            print(f"Result: {result['result']}")
        else:
            print("No result generated")
            sys.exit(1)
    else:
        # Run in interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()