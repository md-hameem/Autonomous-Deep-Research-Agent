"""
Planner Agent - Generates targeted research queries.

Analyzes the research topic and creates comprehensive search
queries covering different aspects of the subject.
"""

from typing import Any
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ..state import AgentState


class ResearchPlan(BaseModel):
    """Structured output for research planning."""
    queries: list[str] = Field(
        description="List of 3-5 targeted, specific search queries"
    )
    aspects: list[str] = Field(
        description="Key aspects or angles being researched"
    )
    reasoning: str = Field(
        description="Brief explanation of the research strategy"
    )


class PlannerAgent(BaseAgent):
    """
    Plans research by breaking down topics into targeted queries.
    
    Uses structured output for reliable parsing and includes
    reasoning for transparency.
    """
    
    SYSTEM_PROMPT = """You are an expert research planner. Your job is to analyze a research 
topic and create a comprehensive research plan with 3-5 targeted search queries.

Your queries should:
1. Cover different aspects/angles of the topic
2. Be specific enough for relevant search results
3. Include recent developments (2024-2025 if applicable)
4. Together provide comprehensive topic coverage

For each plan, identify the key aspects being researched and briefly explain your strategy.

Examples of good query breakdowns:
Topic: "Impact of AI on healthcare"
- Queries: ["AI diagnostic tools hospital implementations 2024", "machine learning drug discovery breakthroughs", "AI patient monitoring automation case studies", "healthcare AI ethics regulations 2024"]
- Aspects: ["Current implementations", "Drug discovery", "Patient care", "Ethics/regulations"]
- Reasoning: "Covering practical implementations, R&D applications, patient-facing uses, and regulatory landscape"
"""
    
    def __init__(self):
        super().__init__("Planner")
        
    def run(self, state: AgentState) -> dict[str, Any]:
        """Generate research plan from topic."""
        topic = state["topic"]
        revision = state.get("revision_number", 0)
        
        # Use structured output
        structured_llm = self.llm.with_structured_output(ResearchPlan)
        
        # Build context for refinement iterations
        context = ""
        if revision > 0 and state.get("quality_report"):
            report = state["quality_report"]
            suggestions = report.get("suggestions", [])
            if suggestions:
                context = f"\n\nPrevious research was insufficient. Additional areas to explore:\n"
                context += "\n".join(f"- {s}" for s in suggestions)
        
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"Create a research plan for: {topic}{context}")
        ]
        
        result = structured_llm.invoke(messages)
        
        log_msg = self.log(f"Generated {len(result.queries)} queries covering: {', '.join(result.aspects)}")
        
        return {
            "plan": result.queries,
            "status": "awaiting_approval",
            "messages": [log_msg, self.log(f"Strategy: {result.reasoning}")]
        }


# Singleton instance
planner_agent = PlannerAgent()


def plan_research(state: AgentState) -> dict[str, Any]:
    """Node function wrapper for the planner agent."""
    return planner_agent.run(state)
