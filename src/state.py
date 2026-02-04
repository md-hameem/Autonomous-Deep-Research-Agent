"""
Enhanced State Management for the Advanced Research Agent.

Extends the basic state with quality metrics, source tracking,
and human-in-the-loop status.
"""

from typing import TypedDict, Annotated, Literal, Optional
from operator import add
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Source:
    """Represents a research source with quality metadata."""
    url: str
    title: str
    content: str
    query: str
    provider: str  # tavily, serper, wikipedia
    quality_score: float = 0.0  # 1-10
    relevance_score: float = 0.0  # 1-10
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "query": self.query,
            "provider": self.provider,
            "quality_score": self.quality_score,
            "relevance_score": self.relevance_score,
            "retrieved_at": self.retrieved_at
        }


@dataclass
class QualityReport:
    """Quality assessment of the research."""
    overall_score: float = 0.0  # 1-10
    completeness: float = 0.0
    source_diversity: float = 0.0
    fact_consistency: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    needs_refinement: bool = False
    
    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "completeness": self.completeness,
            "source_diversity": self.source_diversity,
            "fact_consistency": self.fact_consistency,
            "suggestions": self.suggestions,
            "needs_refinement": self.needs_refinement
        }


class AgentState(TypedDict):
    """
    Enhanced shared state for the advanced research agent.
    
    Attributes:
        topic: The user's original research query/topic
        plan: List of targeted search queries
        plan_approved: Whether human approved the plan (HITL)
        sources: Collected sources with quality metadata
        research_data: Formatted research content strings
        quality_report: Quality assessment from critic agent
        final_report: The generated markdown report
        revision_number: Current iteration count
        status: Current workflow status
        error: Any error message
        messages: Agent communication log
    """
    # Core research state
    topic: str
    plan: list[str]
    plan_approved: bool
    
    # Source tracking
    sources: list[dict]  # List of Source.to_dict()
    research_data: Annotated[list[str], add]
    
    # Quality control
    quality_report: Optional[dict]  # QualityReport.to_dict()
    
    # Output
    final_report: str
    
    # Workflow control
    revision_number: int
    max_revisions: int
    status: Literal["planning", "awaiting_approval", "researching", "evaluating", "writing", "complete", "error"]
    error: Optional[str]
    
    # Agent messages for debugging/streaming
    messages: Annotated[list[str], add]


def create_initial_state(topic: str, max_revisions: int = 2) -> AgentState:
    """Create an initial state for a new research session."""
    return AgentState(
        topic=topic,
        plan=[],
        plan_approved=False,
        sources=[],
        research_data=[],
        quality_report=None,
        final_report="",
        revision_number=0,
        max_revisions=max_revisions,
        status="planning",
        error=None,
        messages=[]
    )
