"""
Base agent class providing common functionality for all agents.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain.schema import HumanMessage

from src.core.types import AgentState, AgentResponse
from src.llms.llm_factory import LLMFactory


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, llm_factory: LLMFactory):
        """Initialize the agent with an LLM factory."""
        self.llm_factory = llm_factory
        self._llm = None
    
    @property
    def llm(self):
        """Lazy-load the LLM instance."""
        if self._llm is None:
            self._llm = self.llm_factory.create_llm()
        return self._llm
    
    @abstractmethod
    def get_prompt(self, user_input: str) -> str:
        """Generate the prompt for this agent."""
        pass
    
    @abstractmethod
    def get_agent_name(self) -> str:
        """Return the name of this agent."""
        pass
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process the input and update the state.
        This is the main entry point for agent execution.
        """
        try:
            user_input = state["input"]
            prompt = self.get_prompt(user_input)
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            state["result"] = response.content
            state["error"] = None
            
        except Exception as e:
            state["result"] = None
            state["error"] = f"Error in {self.get_agent_name()}: {str(e)}"
        
        return state
    
    def __call__(self, state: AgentState) -> AgentState:
        """Make the agent callable."""
        return self.process(state)
