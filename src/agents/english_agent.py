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

    def get_prompt(self, user_input: str) -> str:
        """Generate the prompt for English explanations."""
        return f"Explain the following in English, clearly and simply:\n\n{user_input}"


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