"""Optional anonymous web search through Parallel's Streamable HTTP MCP server."""

import asyncio
import json
from datetime import datetime
from uuid import uuid4

from ..state import Source
from .search import SearchProvider


class ParallelSearch(SearchProvider):
    """Return Parallel search excerpts as sources for the researcher."""

    name = "parallel"
    endpoint = "https://search.parallel.ai/mcp"
    user_agent = (
        "Autonomous-Deep-Research-Agent/2.0 "
        "(+https://github.com/md-hameem/Autonomous-Deep-Research-Agent)"
    )

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        # Reuse one identifier across related searches from this provider.
        self.session_id = uuid4().hex

    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        """Search anonymously, bounding the full MCP exchange and result count."""
        if max_results <= 0:
            return []

        try:
            import httpx
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client

            async with asyncio.timeout(self.timeout):
                async with httpx.AsyncClient(
                    headers={"User-Agent": self.user_agent}, timeout=self.timeout
                ) as client:
                    async with streamable_http_client(
                        self.endpoint, http_client=client
                    ) as (read, write, _):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(
                                "web_search",
                                arguments={
                                    "objective": query,
                                    "search_queries": [query],
                                    "session_id": self.session_id,
                                },
                            )

            if result.isError:
                raise RuntimeError("Parallel search returned an MCP tool error")

            data = result.structuredContent
            if data is None:
                # MCP clients may receive the same JSON in a text content block.
                text = next(block.text for block in result.content if block.type == "text")
                data = json.loads(text)

            return [
                Source(
                    url=item["url"],
                    title=item.get("title") or item["url"],
                    content="\n\n".join(item.get("excerpts", [])),
                    query=query,
                    provider=self.name,
                    retrieved_at=datetime.now().isoformat(),
                )
                for item in data["results"][:max_results]
            ]
        except Exception as exc:
            # Match other providers' graceful failure behavior. Cancellation is
            # a BaseException and propagates to the caller instead.
            print(f"[Parallel] Search error for '{query}': {exc}")
            return []
