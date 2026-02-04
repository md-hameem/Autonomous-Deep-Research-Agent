"""
Search Providers - Multi-provider search abstraction.

Supports Tavily, Wikipedia, and extensible to other providers.
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
