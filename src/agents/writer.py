"""
Writer Agent - Generates comprehensive research reports.

Creates well-structured markdown reports with proper citations
and formatting.
"""

from typing import Any
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ..state import AgentState
from ..config import get_config


class WriterAgent(BaseAgent):
    """
    Generates comprehensive, well-structured research reports.
    
    Features:
    - Professional markdown formatting
    - Citation management
    - Executive summary
    - Key findings extraction
    """
    
    SYSTEM_PROMPT = """You are an expert research writer. Create a comprehensive, 
well-structured markdown research report based on the provided research data.

Your report should include:
1. **Title**: Clear, descriptive title
2. **Executive Summary**: 2-3 paragraph overview of key findings
3. **Table of Contents**: Major sections
4. **Introduction**: Context and scope
5. **Main Sections**: Organized by topic/theme with:
   - Clear headers and subheaders
   - Key findings in bullet points
   - Data and statistics when available
   - Balanced perspectives
6. **Key Insights**: Actionable takeaways
7. **Conclusion**: Summary of findings
8. **References**: Properly formatted citations

Writing guidelines:
- Use professional, informative tone
- Support claims with sources
- Highlight important points with **bold**
- Use tables for comparative data
- Include direct quotes when impactful
- Be thorough but readable
"""

    def __init__(self):
        super().__init__("Writer")
        
    def _format_citations(self, sources: list[dict], style: str = "apa") -> str:
        """Format citations in the specified style."""
        citations = []
        
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Unknown Title")
            url = source.get("url", "")
            retrieved = source.get("retrieved_at", datetime.now().isoformat())[:10]
            
            if style == "apa":
                citation = f"[{i}] {title}. Retrieved {retrieved}, from {url}"
            elif style == "mla":
                citation = f"[{i}] \"{title}.\" Web. {retrieved}. <{url}>"
            else:  # chicago
                citation = f"[{i}] \"{title},\" accessed {retrieved}, {url}"
                
            citations.append(citation)
            
        return "\n".join(citations)
        
    def run(self, state: AgentState) -> dict[str, Any]:
        """Generate the final research report."""
        topic = state["topic"]
        research_data = state.get("research_data", [])
        sources = state.get("sources", [])
        quality_report = state.get("quality_report", {})
        config = get_config()
        
        # Compile research for the writer
        research_content = "\n\n---\n\n".join(research_data)
        
        # Add quality context
        quality_context = ""
        if quality_report:
            quality_context = f"""
Research Quality Assessment:
- Overall Score: {quality_report.get('overall_score', 'N/A')}/10
- Completeness: {quality_report.get('completeness', 'N/A')}/10
- Source Diversity: {quality_report.get('source_diversity', 'N/A')}/10
"""
        
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"""Write a comprehensive research report on: "{topic}"

{quality_context}

Research Data:
{research_content}

Generate a thorough, well-organized markdown report.""")
        ]
        
        response = self.llm.invoke(messages)
        report = response.content
        
        # Add metadata footer
        citations = self._format_citations(sources[:15], config.citation_style)
        
        footer = f"""

---

## References

{citations}

---

*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*Research quality score: {quality_report.get('overall_score', 'N/A')}/10*
"""
        
        final_report = report + footer
        
        log_msgs = [
            self.log(f"Generated report: {len(final_report)} characters"),
            self.log(f"Included {len(sources[:15])} citations in {config.citation_style.upper()} format")
        ]
        
        return {
            "final_report": final_report,
            "status": "complete",
            "messages": log_msgs
        }


# Singleton instance
writer_agent = WriterAgent()


def write_report(state: AgentState) -> dict[str, Any]:
    """Node function wrapper for the writer agent."""
    return writer_agent.run(state)
