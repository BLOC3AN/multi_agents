"""
Math agent for solving mathematical problems.
"""
from src.core.base_agent import BaseAgent
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory


class MathAgent(BaseAgent):
    """Agent specialized in solving mathematical problems."""

    def get_agent_name(self) -> str:
        """Return the name of this agent."""
        return "MathAgent"

    def get_prompt(self, user_input: str) -> str:
        """Generate the prompt for math problems."""
        return f"Bạn hãy giải toán sau đây chi tiết bằng tiếng Việt:\n\n{user_input}"


# Legacy function for backward compatibility
def math_agent(state: AgentState) -> AgentState:
    """
    Legacy function for backward compatibility.
    Use MathAgent class directly for new code.
    """
    from src.config.settings import config

    factory = LLMFactory(config.llm)
    agent = MathAgent(factory)
    return agent.process(state)
