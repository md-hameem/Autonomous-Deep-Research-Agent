"""
Critic Agent - Evaluates research quality.

Assesses completeness, source diversity, and fact consistency.
Determines if refinement is needed.
"""

from typing import Any
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ..state import AgentState, QualityReport
from ..config import get_config


class QualityAssessment(BaseModel):
    """Structured output for quality evaluation."""
    overall_score: float = Field(description="Overall quality score 1-10")
    completeness: float = Field(description="How complete is the coverage 1-10")
    source_diversity: float = Field(description="Diversity of sources 1-10")  
    fact_consistency: float = Field(description="Consistency of facts across sources 1-10")
    strengths: list[str] = Field(description="What the research does well")
    gaps: list[str] = Field(description="Missing aspects or weak areas")
    suggestions: list[str] = Field(description="Specific queries to fill gaps")
    sufficient: bool = Field(description="Is research sufficient for a quality report")


class CriticAgent(BaseAgent):
    """
    Evaluates research quality and determines if refinement is needed.
    
    Provides actionable feedback for iterative improvement.
    """
    
    SYSTEM_PROMPT = """You are a research quality evaluator. Analyze the collected research 
data and assess its quality for producing a comprehensive report.

Evaluate these dimensions (1-10 scale):
1. **Completeness**: Does it cover all major aspects of the topic?
2. **Source Diversity**: Are there multiple credible sources with different perspectives?
3. **Fact Consistency**: Do the facts align across sources? Any contradictions?

If the research is insufficient (overall score < 7), provide specific search query suggestions 
to fill the gaps. Be constructive and specific.

Consider:
- Are there enough sources (minimum 5-8 quality sources)?
- Is there recency (recent data/developments)?
- Are multiple perspectives represented?
- Are key questions about the topic answered?
"""

    def __init__(self):
        super().__init__("Critic")
        
    def run(self, state: AgentState) -> dict[str, Any]:
        """Evaluate research quality."""
        topic = state["topic"]
        sources = state.get("sources", [])
        research_data = state.get("research_data", [])
        revision = state.get("revision_number", 0)
        max_revisions = state.get("max_revisions", 2)
        config = get_config()
        
        # Compile research summary for evaluation
        research_summary = f"Topic: {topic}\n\n"
        research_summary += f"Sources collected: {len(sources)}\n\n"
        research_summary += "Research Content:\n" + "\n---\n".join(research_data[:10])
        
        # Use structured output
        structured_llm = self.llm.with_structured_output(QualityAssessment)
        
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"Evaluate this research:\n\n{research_summary}")
        ]
        
        assessment = structured_llm.invoke(messages)
        
        # Determine if refinement is needed
        needs_refinement = (
            not assessment.sufficient and 
            assessment.overall_score < config.quality.min_quality_score and
            revision < max_revisions
        )
        
        quality_report = QualityReport(
            overall_score=assessment.overall_score,
            completeness=assessment.completeness,
            source_diversity=assessment.source_diversity,
            fact_consistency=assessment.fact_consistency,
            suggestions=assessment.suggestions if needs_refinement else [],
            needs_refinement=needs_refinement
        )
        
        log_msgs = [
            self.log(f"Quality Score: {assessment.overall_score:.1f}/10"),
            self.log(f"Strengths: {', '.join(assessment.strengths[:3])}"),
        ]
        
        if needs_refinement:
            log_msgs.append(self.log(f"Needs refinement - gaps: {', '.join(assessment.gaps[:2])}"))
            next_status = "planning"  # Go back to planner
        else:
            log_msgs.append(self.log("Research sufficient, proceeding to report writing"))
            next_status = "writing"
        
        return {
            "quality_report": quality_report.to_dict(),
            "status": next_status,
            "revision_number": revision + (1 if needs_refinement else 0),
            "messages": log_msgs
        }


# Singleton instance
critic_agent = CriticAgent()


def evaluate_research(state: AgentState) -> dict[str, Any]:
    """Node function wrapper for the critic agent."""
    return critic_agent.run(state)
