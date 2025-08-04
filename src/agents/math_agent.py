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

    def get_prompt(self, user_input: str, context: list = None) -> str:
        """Generate the prompt for math problems with optional context."""
        prompt = "Bạn là một chuyên gia toán học. Hãy giải toán chi tiết bằng tiếng Việt.\n\n"

        # Add conversation context if available
        if context and len(context) > 0:
            prompt += "Ngữ cảnh cuộc trò chuyện trước đó:\n"
            for msg in context[-3:]:  # Use last 3 messages for context
                if msg.get("user_input"):
                    prompt += f"Người dùng: {msg['user_input']}\n"
                if msg.get("agent_response"):
                    prompt += f"Trợ lý: {msg['agent_response'][:200]}...\n"
            prompt += "\n"

        prompt += f"Câu hỏi hiện tại:\n{user_input}\n\nHãy giải đáp chi tiết:"
        return prompt



