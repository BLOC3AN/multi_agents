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

    def get_prompt(self, user_input: str, context: list = None) -> str:
        """Generate the prompt for poetry creation with optional context."""
        prompt = "Bạn là một nhà thơ tài năng. Hãy sáng tác thơ hay và ý nghĩa.\n\n"

        # Add conversation context if available
        if context and len(context) > 0:
            prompt += "Ngữ cảnh cuộc trò chuyện trước đó:\n"
            for msg in context[-3:]:  # Use last 3 messages for context
                if msg.get("user_input"):
                    prompt += f"Người dùng: {msg['user_input']}\n"
                if msg.get("agent_response"):
                    prompt += f"Trợ lý: {msg['agent_response'][:200]}...\n"
            prompt += "\n"

        prompt += f"Yêu cầu sáng tác:\n{user_input}\n\nHãy viết một bài thơ hay:"
        return prompt


