"""
Search Providers - Multi-provider search abstraction.

Supports Tavily, Wikipedia, Serper, Exa, and extensible to other providers.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

from ..state import Source


class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    name: str = "base"
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        """Execute a search query and return sources."""
        pass


class TavilySearch(SearchProvider):
    """Tavily AI-optimized search provider."""
    
    name = "tavily"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        
    @property
    def client(self):
        if self._client is None:
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
        
    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        """Execute Tavily search."""
        try:
            # Run sync client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    include_answer=True
                )
            )
            
            sources = []
            for result in response.get("results", []):
                source = Source(
                    url=result.get("url", ""),
                    title=result.get("title", "Untitled"),
                    content=result.get("content", ""),
                    query=query,
                    provider=self.name,
                    retrieved_at=datetime.now().isoformat()
                )
                sources.append(source)
                
            return sources
            
        except Exception as e:
            print(f"[Tavily] Search error for '{query}': {e}")
            return []


class WikipediaSearch(SearchProvider):
    """Wikipedia search for factual grounding."""
    
    name = "wikipedia"
    
    async def search(self, query: str, max_results: int = 3) -> list[Source]:
        """Search Wikipedia and extract content."""
        try:
            import urllib.parse
            import aiohttp
            
            # Use Wikipedia API
            base_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
                "utf8": 1
            }
            
            async with aiohttp.ClientSession() as session:
                # Search for articles
                async with session.get(base_url, params=params) as resp:
                    data = await resp.json()
                    
                sources = []
                for result in data.get("query", {}).get("search", []):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                    
                    # Get full article extract
                    extract_params = {
                        "action": "query",
                        "titles": title,
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "format": "json"
                    }
                    
                    async with session.get(base_url, params=extract_params) as extract_resp:
                        extract_data = await extract_resp.json()
                        pages = extract_data.get("query", {}).get("pages", {})
                        content = ""
                        for page in pages.values():
                            content = page.get("extract", snippet)
                            break
                    
                    source = Source(
                        url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}",
                        title=f"Wikipedia: {title}",
                        content=content[:2000] if content else snippet,
                        query=query,
                        provider=self.name,
                        retrieved_at=datetime.now().isoformat()
                    )
                    sources.append(source)
                    
                return sources
                
        except Exception as e:
            print(f"[Wikipedia] Search error for '{query}': {e}")
            return []


class SerperSearch(SearchProvider):
    """Serper Google Search API provider (optional)."""
    
    name = "serper"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        """Execute Serper Google search."""
        try:
            import aiohttp
            
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": max_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    data = await resp.json()
                    
            sources = []
            for result in data.get("organic", [])[:max_results]:
                source = Source(
                    url=result.get("link", ""),
                    title=result.get("title", "Untitled"),
                    content=result.get("snippet", ""),
                    query=query,
                    provider=self.name,
                    retrieved_at=datetime.now().isoformat()
                )
                sources.append(source)

            return sources

        except Exception as e:
            print(f"[Serper] Search error for '{query}': {e}")
            return []


class ExaSearch(SearchProvider):
    """Exa AI-powered neural search provider.

    Exa returns curated web results with full page text, highlights, and
    AI-generated summaries, which is a good fit for research-grade sourcing.
    Docs: https://exa.ai/docs/reference/search
    """

    name = "exa"

    # Valid Exa search types (see Exa /search reference)
    VALID_TYPES = {"neural", "fast", "auto", "deep-lite", "deep", "deep-reasoning", "instant"}
    # Valid Exa category filters
    VALID_CATEGORIES = {
        "company", "research paper", "news", "personal site",
        "financial report", "people",
    }

    def __init__(
        self,
        api_key: str,
        search_type: str = "auto",
        category: Optional[str] = None,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
        user_location: Optional[str] = None,
        use_highlights: bool = True,
        use_summary: bool = False,
        text_max_characters: int = 2000,
    ):
        self.api_key = api_key
        self.search_type = search_type if search_type in self.VALID_TYPES else "auto"
        self.category = category if category in self.VALID_CATEGORIES else None
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        self.start_published_date = start_published_date
        self.end_published_date = end_published_date
        self.user_location = user_location
        self.use_highlights = use_highlights
        self.use_summary = use_summary
        self.text_max_characters = text_max_characters
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from exa_py import Exa
            self._client = Exa(api_key=self.api_key)
            # Integration attribution header (set on every request)
            self._client.headers["x-exa-integration"] = "autonomous-deep-research-agent"
        return self._client

    def _build_contents_kwargs(self) -> dict:
        """Build the content-retrieval kwargs for search_and_contents."""
        kwargs: dict = {
            "text": {"maxCharacters": self.text_max_characters},
        }
        if self.use_highlights:
            kwargs["highlights"] = True
        if self.use_summary:
            kwargs["summary"] = True
        return kwargs

    def _build_search_kwargs(self, max_results: int) -> dict:
        """Build the search kwargs (type, filters, date ranges)."""
        kwargs: dict = {
            "num_results": max_results,
            "type": self.search_type,
        }
        if self.category:
            kwargs["category"] = self.category
        if self.include_domains:
            kwargs["include_domains"] = self.include_domains
        if self.exclude_domains:
            kwargs["exclude_domains"] = self.exclude_domains
        if self.start_published_date:
            kwargs["start_published_date"] = self.start_published_date
        if self.end_published_date:
            kwargs["end_published_date"] = self.end_published_date
        if self.user_location:
            kwargs["user_location"] = self.user_location
        return kwargs

    @staticmethod
    def _extract_content(result) -> str:
        """Pick the best available body text from an Exa result.

        Cascades through summary -> text -> joined highlights, because any
        subset of these fields may be populated depending on request options.
        """
        summary = getattr(result, "summary", None)
        if summary:
            return summary
        text = getattr(result, "text", None)
        if text:
            return text
        highlights = getattr(result, "highlights", None) or []
        if highlights:
            return " ".join(highlights)
        return ""

    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        """Execute Exa search with content retrieval."""
        try:
            search_kwargs = self._build_search_kwargs(max_results)
            contents_kwargs = self._build_contents_kwargs()

            # exa-py is sync; run in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search_and_contents(
                    query,
                    **search_kwargs,
                    **contents_kwargs,
                ),
            )

            sources: list[Source] = []
            for result in getattr(response, "results", []) or []:
                content = self._extract_content(result)
                source = Source(
                    url=getattr(result, "url", "") or "",
                    title=getattr(result, "title", None) or "Untitled",
                    content=content,
                    query=query,
                    provider=self.name,
                    retrieved_at=datetime.now().isoformat(),
                )
                sources.append(source)

            return sources

        except Exception as e:
            print(f"[Exa] Search error for '{query}': {e}")
            return []
