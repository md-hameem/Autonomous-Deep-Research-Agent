"""
Configuration Management for the Research Agent.

Centralized configuration with environment variable loading
and sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Literal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    
    def __post_init__(self):
        if not self.model:
            if self.provider == "openai":
                self.model = "gpt-4o"
            else:
                self.model = "claude-sonnet-4-20250514"


@dataclass
class SearchConfig:
    """Search provider configuration."""
    max_results_per_query: int = 5
    search_depth: Literal["basic", "advanced"] = "advanced"
    max_parallel_searches: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass  
class QualityConfig:
    """Quality control configuration."""
    min_quality_score: float = 7.0  # 1-10 scale
    max_refinement_iterations: int = 2
    min_sources_per_topic: int = 3
    enable_fact_checking: bool = True


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    database_path: str = "data/research_cache.db"
    ttl_hours: int = 24  # Time to live for cached results


@dataclass
class Config:
    """Main configuration container."""
    # API Keys
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    serper_api_key: str = field(default_factory=lambda: os.getenv("SERPER_API_KEY", ""))
    
    # Sub-configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Output settings
    output_dir: str = "reports"
    citation_style: Literal["apa", "mla", "chicago"] = "apa"
    
    def __post_init__(self):
        # Set LLM provider from environment
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        self.llm.provider = provider
        
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.tavily_api_key:
            errors.append("TAVILY_API_KEY is required")
            
        if self.llm.provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic")
        elif self.llm.provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
            
        return errors


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config
