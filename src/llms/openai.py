"""
OpenAI LLM provider implementation.
"""
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from src.config.settings import LLMConfig


class OpenAIProvider:
    """OpenAI LLM provider."""

    def __init__(self, config: LLMConfig):
        """Initialize with configuration."""
        self.config = config

    def create_llm(self):
        """Create and return an OpenAI LLM instance."""
        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            seed=self.config.seed,
        )


if __name__ == "__main__":
    from src.config.settings import config
    provider = OpenAIProvider(config.llm)
    llm = provider.create_llm()
    print(llm.invoke([HumanMessage(content="Hello world")]))