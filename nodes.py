"""
Node Functions for the Autonomous Deep Research Agent.

This module contains the three core nodes:
- plan_research: Generates targeted search queries from the topic
- execute_search: Performs web searches using Tavily API
- write_report: Compiles research into a structured markdown report
"""

import os
from typing import Any
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient

from state import AgentState


# Pydantic model for structured planner output
class ResearchPlan(BaseModel):
    """Structured output for the research planner."""
    queries: list[str] = Field(
        description="List of 3-5 targeted search queries to research the topic comprehensively"
    )


def get_llm():
    """Initialize the LLM based on environment configuration."""
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o", temperature=0.3)
    else:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3)


def plan_research(state: AgentState) -> dict[str, Any]:
    """
    Node A: Plan Research
    
    Takes the user's topic and uses the LLM to generate 3-5 distinct,
    targeted search queries for comprehensive research coverage.
    
    Args:
        state: Current agent state containing the topic
        
    Returns:
        State update with the generated plan (list of search queries)
    """
    topic = state["topic"]
    llm = get_llm()
    
    # Use structured output for reliable parsing
    structured_llm = llm.with_structured_output(ResearchPlan)
    
    system_prompt = """You are a research planning assistant. Your job is to break down 
a research topic into 3-5 distinct, targeted search queries that will help gather 
comprehensive information about the topic.

Each query should:
1. Focus on a different aspect of the topic
2. Be specific enough to return relevant results
3. Together, cover the topic thoroughly

Examples of good query breakdowns:
- For "Impact of AI on healthcare": 
  - "AI diagnostic tools in hospitals 2024"
  - "machine learning drug discovery breakthroughs"
  - "AI patient care automation examples"
  - "healthcare AI regulations and ethics"
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Create a research plan for the following topic: {topic}")
    ]
    
    result = structured_llm.invoke(messages)
    
    print(f"\n📋 Research Plan Generated:")
    for i, query in enumerate(result.queries, 1):
        print(f"   {i}. {query}")
    
    return {"plan": result.queries}


def execute_search(state: AgentState) -> dict[str, Any]:
    """
    Node B: Execute Search
    
    Iterates through the planned search queries and uses the Tavily API
    to perform web searches, collecting the top 2-3 results per query.
    
    Args:
        state: Current agent state containing the plan
        
    Returns:
        State update with research_data (accumulated search results)
    """
    plan = state["plan"]
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    research_results = []
    
    print(f"\n🔍 Executing {len(plan)} searches...")
    
    for query in plan:
        print(f"   Searching: {query}")
        
        try:
            # Perform search with Tavily
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=3,
                include_answer=True
            )
            
            # Format the results
            result_text = f"\n### Search Query: {query}\n"
            
            # Include the AI-generated answer if available
            if response.get("answer"):
                result_text += f"\n**Summary:** {response['answer']}\n"
            
            # Include individual search results
            result_text += "\n**Sources:**\n"
            for result in response.get("results", []):
                title = result.get("title", "Untitled")
                url = result.get("url", "")
                content = result.get("content", "No content available")
                result_text += f"\n- **{title}**\n  URL: {url}\n  {content[:500]}...\n"
            
            research_results.append(result_text)
            
        except Exception as e:
            # Handle errors gracefully - don't crash, note the issue
            error_msg = f"\n### Search Query: {query}\n**Error:** Unable to retrieve results - {str(e)}\n"
            research_results.append(error_msg)
            print(f"   ⚠️  Error searching for '{query}': {e}")
    
    print(f"   ✅ Collected data from {len(research_results)} searches")
    
    return {"research_data": research_results}


def write_report(state: AgentState) -> dict[str, Any]:
    """
    Node C: Write Report
    
    Takes the accumulated research data and uses the LLM to compile
    a comprehensive, structured markdown report.
    
    Args:
        state: Current agent state containing research_data and topic
        
    Returns:
        State update with the final_report (markdown document)
    """
    topic = state["topic"]
    research_data = state["research_data"]
    llm = get_llm()
    
    print("\n📝 Writing research report...")
    
    # Combine all research data
    combined_research = "\n".join(research_data)
    
    system_prompt = """You are an expert research writer. Your task is to synthesize 
research data into a comprehensive, well-structured markdown report.

Your report should:
1. Have a clear title and introduction
2. Be organized with headers and subheaders
3. Use bullet points for key findings
4. Include relevant quotes or data points from sources
5. Have a conclusion section summarizing key insights
6. Include a "Sources" section at the end with URLs

Write in a professional, informative tone. Make the report thorough but readable."""

    user_prompt = f"""Write a comprehensive research report on the topic: "{topic}"

Based on the following research data:

{combined_research}

Generate a well-structured markdown report."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)
    report = response.content
    
    print("   ✅ Report generated successfully!")
    
    return {
        "final_report": report,
        "revision_number": state.get("revision_number", 0) + 1
    }
