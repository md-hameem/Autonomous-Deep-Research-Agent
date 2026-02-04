"""
Base Agent class with shared LLM initialization.
"""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel

from ..config import get_config
from ..state import AgentState


class BaseAgent(ABC):
    """Base class for all specialized agents."""
    
    def __init__(self, name: str):
        self.name = name
        self._llm = None
        
    @property
    def llm(self) -> BaseChatModel:
        """Lazy-load the LLM based on configuration."""
        if self._llm is None:
            config = get_config()
            
            if config.llm.provider == "openai":
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=config.llm.model,
                    temperature=config.llm.temperature,
                    max_tokens=config.llm.max_tokens
                )
            else:
                from langchain_anthropic import ChatAnthropic
                self._llm = ChatAnthropic(
                    model=config.llm.model,
                    temperature=config.llm.temperature,
                    max_tokens=config.llm.max_tokens
                )
                
        return self._llm
    
    @abstractmethod
    def run(self, state: AgentState) -> dict[str, Any]:
        """Execute the agent's task and return state updates."""
        pass
    
    def log(self, message: str) -> str:
        """Create a formatted log message."""
        return f"[{self.name}] {message}"
