"""Exercise Parallel through its MCP transport and the researcher calling path."""

import asyncio
import json

import httpx
import pytest

# Import before patching the HTTP client so the SDK is fully initialized.
import mcp.client.streamable_http

from src.config import Config, SearchConfig
from src.state import create_initial_state
from src.tools.parallel_search import ParallelSearch


@pytest.fixture
def anonymous_config(monkeypatch):
    """Isolate provider selection from environment credentials and .env values."""
    for key in (
        "TAVILY_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
        "SERPER_API_KEY", "PARALLEL_API_KEY", "PARALLEL_SEARCH_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)
    config = Config(
        tavily_api_key="", anthropic_api_key="", openai_api_key="", serper_api_key=""
    )
    monkeypatch.setattr("src.config.config", config)
    return config


@pytest.fixture
def mcp_server(monkeypatch):
    """Mock only the HTTP boundary, retaining SDK initialization and tool dispatch."""
    requests = []
    clients = []
    settings = {"mode": "structured"}
    real_client = httpx.AsyncClient

    async def respond(request):
        requests.append(request)
        assert str(request.url) == ParallelSearch.endpoint
        assert request.headers["user-agent"] == ParallelSearch.user_agent
        assert "authorization" not in request.headers
        message = json.loads(request.content)
        method = message["method"]
        if method == "notifications/initialized":
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "parallel-fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {"tools": [{
                "name": "web_search",
                "inputSchema": {"type": "object"},
            }]}
        elif method == "tools/call":
            mode = settings["mode"]
            if mode == "http_error":
                return httpx.Response(503, text="Service unavailable")
            if mode == "wait":
                settings["started"].set()
                await asyncio.Event().wait()
            if mode == "rpc_error":
                return httpx.Response(200, json={
                    "jsonrpc": "2.0", "id": message["id"],
                    "error": {"code": -32000, "message": "Search unavailable"},
                })
            data = {"search_id": "search_fixture", "session_id": "fixture", "results": [
                {"url": "https://example.org/research", "title": "Quantum research",
                 "excerpts": ["Quantum error correction advances.", "A second excerpt."]},
                {"url": "https://example.org/second", "title": None,
                 "excerpts": ["More quantum evidence."]},
            ]}
            if mode == "malformed":
                result = {"content": [{"type": "text", "text": "not JSON"}]}
            elif mode == "tool_error":
                result = {"isError": True, "content": [
                    {"type": "text", "text": "Free-tier rate limit reached"}
                ]}
            else:
                result = {"content": [{"type": "text", "text": json.dumps(data)}]}
                if mode == "structured":
                    result["structuredContent"] = data
        else:
            pytest.fail(f"Unexpected MCP method: {method}")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    def client_factory(*args, **kwargs):
        client = real_client(*args, **kwargs, transport=httpx.MockTransport(respond))
        clients.append(client)
        return client

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    return settings, requests, clients


def tool_calls(requests):
    """Return actual tool-call messages observed at the HTTP boundary."""
    return [json.loads(r.content) for r in requests
            if json.loads(r.content)["method"] == "tools/call"]


def test_defaults_and_explicit_selection(anonymous_config, monkeypatch):
    """Keep default providers and require explicit opt-in to replace the key need."""
    from src.agents.researcher import ResearcherAgent

    assert [p.name for p in ResearcherAgent().providers] == ["wikipedia"]
    assert "TAVILY_API_KEY is required" in anonymous_config.validate()
    anonymous_config.tavily_api_key = "saved-tavily-choice"
    assert [p.name for p in ResearcherAgent().providers] == ["tavily", "wikipedia"]
    monkeypatch.setenv("PARALLEL_SEARCH_ENABLED", "true")
    anonymous_config.search = SearchConfig()
    assert [p.name for p in ResearcherAgent().providers] == ["tavily", "parallel", "wikipedia"]
    anonymous_config.tavily_api_key = ""
    assert [p.name for p in ResearcherAgent().providers] == ["parallel", "wikipedia"]
    errors = anonymous_config.validate()
    assert "TAVILY_API_KEY is required" not in errors
    assert any("API_KEY is required" in error for error in errors)
    monkeypatch.setenv("PARALLEL_SEARCH_ENABLED", "false")
    anonymous_config.search = SearchConfig()
    assert not anonymous_config.search.parallel_enabled


def test_researcher_consumes_mcp_sources(anonymous_config, mcp_server, monkeypatch):
    """Run selection, MCP execution, scoring and report-context formatting together."""
    from src.agents.researcher import ResearcherAgent
    from src.tools.search import WikipediaSearch

    anonymous_config.search.parallel_enabled = True
    anonymous_config.search.max_results_per_query = 1

    async def no_wikipedia(*args, **kwargs):
        return []

    monkeypatch.setattr(WikipediaSearch, "search", no_wikipedia)
    state = create_initial_state("quantum error correction")
    state["plan"] = ["quantum error correction advances", "quantum error correction evidence"]
    result = ResearcherAgent().run(state)
    assert result["status"] == "evaluating"
    assert len(result["sources"]) == 2
    assert all(s["provider"] == "parallel" and s["quality_score"] > 0 for s in result["sources"])
    assert "Quantum error correction advances." in result["research_data"][0]
    assert "https://example.org/research" in result["research_data"][0]
    _, requests, clients = mcp_server
    calls = tool_calls(requests)
    assert len(calls) == 2
    session_ids = set()
    for call in calls:
        assert call["params"]["name"] == "web_search"
        args = call["params"]["arguments"]
        assert args["objective"] in state["plan"]
        assert args["search_queries"] == [args["objective"]]
        session_ids.add(args["session_id"])
    assert len(session_ids) == 1
    assert len(session_ids.pop()) == 32
    assert clients and all(c.is_closed for c in clients)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["structured", "text"])
async def test_results_and_text_fallback(mode, mcp_server):
    """Map excerpts, nullable titles and query metadata from either MCP encoding."""
    settings, requests, clients = mcp_server
    settings["mode"] = mode
    sources = await ParallelSearch().search("quantum research evidence", max_results=2)
    assert len(sources) == 2
    assert sources[0].content == "Quantum error correction advances.\n\nA second excerpt."
    assert sources[0].query == "quantum research evidence"
    assert sources[0].retrieved_at
    assert sources[1].title == sources[1].url
    assert tool_calls(requests)
    assert all(c.is_closed for c in clients)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["http_error", "rpc_error", "tool_error", "malformed"])
async def test_provider_errors_are_contained(mode, mcp_server):
    """Remote failures and invalid output do not stop other research providers."""
    settings, requests, clients = mcp_server
    settings["mode"] = mode
    assert await ParallelSearch().search("quantum research evidence") == []
    assert tool_calls(requests)
    assert all(c.is_closed for c in clients)


@pytest.mark.asyncio
async def test_timeout_cleans_up_transport(mcp_server):
    """Bound a stalled tool call, including MCP context cleanup."""
    settings, requests, clients = mcp_server
    settings.update(mode="wait", started=asyncio.Event())
    assert await ParallelSearch(timeout=0.1).search("quantum research evidence") == []
    assert settings["started"].is_set()
    assert all(c.is_closed for c in clients)


@pytest.mark.asyncio
async def test_cancellation_propagates(mcp_server):
    """Cancellation must not become an empty successful result."""
    settings, requests, clients = mcp_server
    settings.update(mode="wait", started=asyncio.Event())
    task = asyncio.create_task(ParallelSearch().search("quantum research evidence"))
    await asyncio.wait_for(settings["started"].wait(), timeout=2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert all(c.is_closed for c in clients)


@pytest.mark.asyncio
async def test_zero_results_avoids_network(mcp_server):
    """Honor a disabled result count without calling the server."""
    assert await ParallelSearch().search("query", max_results=0) == []
    assert mcp_server[1] == []
