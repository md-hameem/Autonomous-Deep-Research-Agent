"""
Test suite for the Research Agent.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Tests for configuration module."""
    
    def test_config_loads(self):
        """Test that config loads without errors."""
        from src.config import get_config
        config = get_config()
        assert config is not None
        
    def test_config_validation(self):
        """Test config validation returns errors for missing keys."""
        from src.config import Config
        config = Config()
        config.tavily_api_key = ""
        config.anthropic_api_key = ""
        config.openai_api_key = ""
        
        errors = config.validate()
        assert len(errors) > 0


class TestState:
    """Tests for state module."""
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        from src.state import create_initial_state
        
        state = create_initial_state("test topic")
        
        assert state["topic"] == "test topic"
        assert state["plan"] == []
        assert state["status"] == "planning"
        
    def test_source_dataclass(self):
        """Test Source dataclass."""
        from src.state import Source
        
        source = Source(
            url="https://example.com",
            title="Test",
            content="Content",
            query="query",
            provider="test"
        )
        
        data = source.to_dict()
        assert data["url"] == "https://example.com"
        assert data["provider"] == "test"


class TestAgents:
    """Tests for agent modules."""
    
    def test_planner_agent_init(self):
        """Test planner agent initialization."""
        from src.agents.planner import PlannerAgent
        
        agent = PlannerAgent()
        assert agent.name == "Planner"
        
    def test_critic_agent_init(self):
        """Test critic agent initialization."""
        from src.agents.critic import CriticAgent
        
        agent = CriticAgent()
        assert agent.name == "Critic"


class TestSearch:
    """Tests for search providers."""
    
    def test_wikipedia_search_init(self):
        """Test Wikipedia search initialization."""
        from src.tools.search import WikipediaSearch
        
        search = WikipediaSearch()
        assert search.name == "wikipedia"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
