"""
English agent for explaining concepts in English.
"""
from src.core.base_agent import BaseAgent
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory


class EnglishAgent(BaseAgent):
    """Agent specialized in explaining concepts in English."""

    def get_agent_name(self) -> str:
        """Return the name of this agent."""
        return "EnglishAgent"

    def get_prompt(self, user_input: str, context: list = None) -> str:
        """Generate the prompt for English explanations with optional context."""
        prompt = "You are a knowledgeable assistant. Provide clear and helpful explanations.\n\n"

        # Add conversation context if available
        if context and len(context) > 0:
            prompt += "Previous conversation context:\n"
            for msg in context[-3:]:  # Use last 3 messages for context
                if msg.get("user_input"):
                    prompt += f"User: {msg['user_input']}\n"
                if msg.get("agent_response"):
                    prompt += f"Assistant: {msg['agent_response'][:200]}...\n"
            prompt += "\n"

        prompt += f"Current question:\n{user_input}\n\nPlease provide a clear explanation:"
        return prompt


# Legacy function for backward compatibility
def english_agent(state: AgentState) -> AgentState:
    """
    Legacy function for backward compatibility.
    Use EnglishAgent class directly for new code.
    """
    from src.config.settings import config

    factory = LLMFactory(config.llm)
    agent = EnglishAgent(factory)
    return agent.process(state)