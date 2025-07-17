"""
Poem agent for creating poetry based on input.
"""
from src.core.base_agent import BaseAgent
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory


class PoemAgent(BaseAgent):
    """Agent specialized in creating poetry."""

    def get_agent_name(self) -> str:
        """Return the name of this agent."""
        return "PoemAgent"

    def get_prompt(self, user_input: str) -> str:
        """Generate the prompt for poetry creation."""
        return f"Viết một bài thơ ngắn dựa trên nội dung:\n\n{user_input}"


# Legacy function for backward compatibility
def poem_agent(state: AgentState) -> AgentState:
    """
    Legacy function for backward compatibility.
    Use PoemAgent class directly for new code.
    """
    from src.config.settings import config

    factory = LLMFactory(config.llm)
    agent = PoemAgent(factory)
    return agent.process(state)