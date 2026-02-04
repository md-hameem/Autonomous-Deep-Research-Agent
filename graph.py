"""
LangGraph Workflow Definition for the Autonomous Deep Research Agent.

This module defines the StateGraph that orchestrates the research workflow:
START -> planner -> researcher -> writer -> END
"""

from langgraph.graph import StateGraph, START, END

from state import AgentState
from nodes import plan_research, execute_search, write_report


def create_research_graph() -> StateGraph:
    """
    Create and compile the research agent workflow graph.
    
    The workflow follows this flow:
    1. START: Receives the initial topic
    2. planner: Generates targeted search queries
    3. researcher: Executes web searches via Tavily
    4. writer: Compiles findings into a markdown report
    5. END: Returns the final state with report
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the StateGraph with our AgentState schema
    workflow = StateGraph(AgentState)
    
    # Add the three nodes
    workflow.add_node("planner", plan_research)
    workflow.add_node("researcher", execute_search)
    workflow.add_node("writer", write_report)
    
    # Define the edge flow: START -> planner -> researcher -> writer -> END
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    return graph


# Create a singleton instance for import
research_graph = create_research_graph()
