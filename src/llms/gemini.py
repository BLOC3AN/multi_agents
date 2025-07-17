"""
Gemini LLM provider implementation.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from src.config.settings import LLMConfig


class GeminiProvider:
    """Gemini LLM provider."""

    def __init__(self, config: LLMConfig):
        """Initialize with configuration."""
        self.config = config

    def create_llm(self):
        """Create and return a Gemini LLM instance."""
        return ChatGoogleGenerativeAI(
            model=self.config.model,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
        )


if __name__ == "__main__":
    from src.config.settings import config
    provider = GeminiProvider(config.llm)
    llm = provider.create_llm()
    print(llm.invoke([HumanMessage(content="Hello world")]))
