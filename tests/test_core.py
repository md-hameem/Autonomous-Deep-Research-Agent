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


class TestExaSearch:
    """Tests for the Exa search provider."""

    def test_exa_search_init_defaults(self):
        """ExaSearch initializes with sensible defaults."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(api_key="test-key")
        assert provider.name == "exa"
        assert provider.api_key == "test-key"
        assert provider.search_type == "auto"
        assert provider.category is None
        assert provider.use_highlights is True

    def test_exa_search_rejects_invalid_type(self):
        """Invalid search types fall back to 'auto'."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(api_key="test-key", search_type="keyword")
        assert provider.search_type == "auto"

    def test_exa_search_rejects_invalid_category(self):
        """Invalid categories are dropped."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(api_key="test-key", category="not-a-category")
        assert provider.category is None

    def test_exa_search_accepts_valid_category(self):
        """Valid categories are preserved."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(api_key="test-key", category="research paper")
        assert provider.category == "research paper"

    def test_build_search_kwargs_filters(self):
        """Optional filters flow through to request kwargs."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(
            api_key="test-key",
            search_type="neural",
            category="news",
            include_domains=["example.com"],
            exclude_domains=["spam.com"],
            start_published_date="2024-01-01",
            end_published_date="2024-12-31",
            user_location="US",
        )
        kwargs = provider._build_search_kwargs(max_results=7)
        assert kwargs["num_results"] == 7
        assert kwargs["type"] == "neural"
        assert kwargs["category"] == "news"
        assert kwargs["include_domains"] == ["example.com"]
        assert kwargs["exclude_domains"] == ["spam.com"]
        assert kwargs["start_published_date"] == "2024-01-01"
        assert kwargs["end_published_date"] == "2024-12-31"
        assert kwargs["user_location"] == "US"

    def test_build_contents_kwargs_default(self):
        """Default contents include text + highlights."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(api_key="test-key")
        kwargs = provider._build_contents_kwargs()
        assert "text" in kwargs
        assert kwargs["text"]["maxCharacters"] == 2000
        assert kwargs["highlights"] is True
        assert "summary" not in kwargs

    def test_build_contents_kwargs_with_summary(self):
        """Summary is included when enabled."""
        from src.tools.search import ExaSearch

        provider = ExaSearch(api_key="test-key", use_summary=True, use_highlights=False)
        kwargs = provider._build_contents_kwargs()
        assert kwargs["summary"] is True
        assert "highlights" not in kwargs

    def test_extract_content_prefers_summary(self):
        """Summary wins over text and highlights when present."""
        from src.tools.search import ExaSearch

        class FakeResult:
            summary = "A concise summary."
            text = "Full text body."
            highlights = ["h1", "h2"]

        assert ExaSearch._extract_content(FakeResult()) == "A concise summary."

    def test_extract_content_falls_back_to_text(self):
        """Text is used when summary is absent."""
        from src.tools.search import ExaSearch

        class FakeResult:
            summary = None
            text = "Full text body."
            highlights = ["h1"]

        assert ExaSearch._extract_content(FakeResult()) == "Full text body."

    def test_extract_content_falls_back_to_highlights(self):
        """Highlights are joined when text and summary are absent."""
        from src.tools.search import ExaSearch

        class FakeResult:
            summary = None
            text = None
            highlights = ["first highlight", "second highlight"]

        assert ExaSearch._extract_content(FakeResult()) == "first highlight second highlight"

    def test_extract_content_empty_when_no_fields(self):
        """Empty string when no content fields are available."""
        from src.tools.search import ExaSearch

        class FakeResult:
            summary = None
            text = None
            highlights = None

        assert ExaSearch._extract_content(FakeResult()) == ""

    async def test_search_parses_response(self, monkeypatch):
        """search() parses Exa SDK response objects into Source instances."""
        import sys
        import types

        from src.tools.search import ExaSearch

        class FakeResult:
            def __init__(self, url, title, text=None, summary=None, highlights=None):
                self.url = url
                self.title = title
                self.text = text
                self.summary = summary
                self.highlights = highlights

        class FakeResponse:
            def __init__(self, results):
                self.results = results

        class FakeExaClient:
            def __init__(self, api_key=None):
                self.api_key = api_key
                self.headers = {}

            def search_and_contents(self, query, **kwargs):
                assert query == "quantum computing"
                assert kwargs["num_results"] == 3
                assert kwargs["type"] == "auto"
                assert "text" in kwargs
                return FakeResponse([
                    FakeResult(
                        url="https://a.example/1",
                        title="Article One",
                        text="Body text about quantum computing.",
                    ),
                    FakeResult(
                        url="https://a.example/2",
                        title="Article Two",
                        highlights=["quantum bits", "superposition"],
                    ),
                ])

        # Inject a fake exa_py module so `from exa_py import Exa` resolves to our stub.
        # Mock target must be the source module (exa_py), not the consuming namespace,
        # because ExaSearch imports Exa locally inside the `client` property.
        fake_module = types.ModuleType("exa_py")
        fake_module.Exa = FakeExaClient
        monkeypatch.setitem(sys.modules, "exa_py", fake_module)

        provider = ExaSearch(api_key="test-key")
        sources = await provider.search("quantum computing", max_results=3)

        assert len(sources) == 2
        assert sources[0].url == "https://a.example/1"
        assert sources[0].title == "Article One"
        assert sources[0].content == "Body text about quantum computing."
        assert sources[0].provider == "exa"
        assert sources[1].content == "quantum bits superposition"
        # Integration header must be set on every client
        assert provider.client.headers["x-exa-integration"] == "autonomous-deep-research-agent"

    async def test_search_returns_empty_on_sdk_error(self, monkeypatch):
        """Errors from the SDK are swallowed and return an empty list."""
        import sys
        import types

        from src.tools.search import ExaSearch

        class BoomClient:
            def __init__(self, api_key=None):
                self.headers = {}

            def search_and_contents(self, query, **kwargs):
                raise RuntimeError("network down")

        fake_module = types.ModuleType("exa_py")
        fake_module.Exa = BoomClient
        monkeypatch.setitem(sys.modules, "exa_py", fake_module)

        provider = ExaSearch(api_key="test-key")
        sources = await provider.search("anything")
        assert sources == []


class TestResearcherProviderRegistration:
    """Ensure Exa is only registered when EXA_API_KEY is configured."""

    def test_exa_not_registered_without_key(self, monkeypatch):
        """ResearcherAgent skips Exa when no API key is set."""
        # Force the researcher module to re-init cleanly by removing cached singleton
        import importlib
        import src.agents.researcher as researcher_module
        from src.config import get_config

        cfg = get_config()
        monkeypatch.setattr(cfg, "exa_api_key", "")
        monkeypatch.setattr(cfg, "tavily_api_key", "")
        monkeypatch.setattr(cfg, "serper_api_key", "")

        importlib.reload(researcher_module)
        agent = researcher_module.ResearcherAgent()

        provider_names = {p.name for p in agent.providers}
        assert "exa" not in provider_names

    def test_exa_registered_when_key_set(self, monkeypatch):
        """ResearcherAgent registers Exa when the key is present."""
        import importlib
        import src.agents.researcher as researcher_module
        from src.config import get_config

        cfg = get_config()
        monkeypatch.setattr(cfg, "exa_api_key", "test-key")
        monkeypatch.setattr(cfg, "tavily_api_key", "")
        monkeypatch.setattr(cfg, "serper_api_key", "")

        importlib.reload(researcher_module)
        agent = researcher_module.ResearcherAgent()

        provider_names = {p.name for p in agent.providers}
        assert "exa" in provider_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
