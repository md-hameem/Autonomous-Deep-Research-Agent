"""
Researcher Agent - Executes parallel web searches.

Uses asyncio for concurrent search execution across multiple
providers with automatic retry and quality scoring.
"""

import asyncio
from typing import Any
from datetime import datetime

from .base import BaseAgent
from ..state import AgentState, Source
from ..config import get_config
from ..tools.search import SearchProvider, TavilySearch, WikipediaSearch


class ResearcherAgent(BaseAgent):
    """
    Executes research queries in parallel with quality scoring.
    
    Features:
    - Parallel search execution
    - Multiple search providers
    - Automatic retry with backoff
    - Source quality scoring
    """
    
    def __init__(self):
        super().__init__("Researcher")
        self.providers: list[SearchProvider] = []
        self._init_providers()
        
    def _init_providers(self):
        """Initialize available search providers."""
        config = get_config()
        
        # Always add Tavily if available
        if config.tavily_api_key:
            self.providers.append(TavilySearch(config.tavily_api_key))
            
        # Add Wikipedia for factual grounding
        self.providers.append(WikipediaSearch())
        
    async def _search_query(self, query: str, provider: SearchProvider) -> list[Source]:
        """Execute a single search query with retry logic."""
        config = get_config()
        
        for attempt in range(config.search.retry_attempts):
            try:
                results = await provider.search(
                    query=query,
                    max_results=config.search.max_results_per_query
                )
                return results
            except Exception as e:
                if attempt < config.search.retry_attempts - 1:
                    await asyncio.sleep(config.search.retry_delay * (attempt + 1))
                else:
                    # Return empty on final failure
                    return []
                    
        return []
    
    async def _execute_parallel_searches(self, queries: list[str]) -> list[Source]:
        """Execute all queries in parallel across providers."""
        config = get_config()
        all_sources: list[Source] = []
        
        # Create tasks for all query-provider combinations
        tasks = []
        for query in queries:
            for provider in self.providers:
                tasks.append(self._search_query(query, provider))
                
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(config.search.max_parallel_searches)
        
        async def limited_search(task):
            async with semaphore:
                return await task
                
        results = await asyncio.gather(*[limited_search(t) for t in tasks])
        
        # Flatten results
        for result_list in results:
            all_sources.extend(result_list)
            
        return all_sources
    
    def _score_sources(self, sources: list[Source], topic: str) -> list[Source]:
        """Score sources based on relevance and quality."""
        # Simple scoring based on content length and keyword matching
        topic_keywords = set(topic.lower().split())
        
        for source in sources:
            # Relevance score based on keyword overlap
            content_words = set(source.content.lower().split())
            overlap = len(topic_keywords & content_words)
            source.relevance_score = min(10, overlap * 2)
            
            # Quality score based on content length and provider
            length_score = min(5, len(source.content) / 500)
            provider_bonus = 2 if source.provider in ["tavily", "wikipedia"] else 0
            source.quality_score = min(10, length_score + provider_bonus + 3)
            
        # Sort by combined score
        sources.sort(key=lambda s: s.quality_score + s.relevance_score, reverse=True)
        
        return sources
    
    def run(self, state: AgentState) -> dict[str, Any]:
        """Execute research queries and collect sources."""
        queries = state["plan"]
        topic = state["topic"]
        
        log_msgs = [self.log(f"Executing {len(queries)} queries across {len(self.providers)} providers")]
        
        # Run async searches
        sources = asyncio.run(self._execute_parallel_searches(queries))
        
        # Score and sort sources
        sources = self._score_sources(sources, topic)
        
        # Format research data
        research_data = []
        for source in sources[:15]:  # Top 15 sources
            data = f"""
### {source.title}
**Source:** {source.url}
**Provider:** {source.provider} | **Quality:** {source.quality_score:.1f}/10

{source.content[:1000]}
"""
            research_data.append(data)
            
        log_msgs.append(self.log(f"Collected {len(sources)} sources, selected top 15"))
        
        return {
            "sources": [s.to_dict() for s in sources],
            "research_data": research_data,
            "status": "evaluating",
            "messages": log_msgs
        }


# Singleton instance
researcher_agent = ResearcherAgent()


def execute_research(state: AgentState) -> dict[str, Any]:
    """Node function wrapper for the researcher agent."""
    return researcher_agent.run(state)
