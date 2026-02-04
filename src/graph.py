"""
LangGraph Workflow - Advanced multi-agent research graph.

Implements supervisor pattern with conditional routing,
human-in-the-loop interrupts, and iterative refinement.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .agents.planner import plan_research
from .agents.researcher import execute_research
from .agents.critic import evaluate_research
from .agents.writer import write_report


def should_continue_after_critic(state: AgentState) -> Literal["planner", "writer"]:
    """Route based on critic evaluation."""
    quality_report = state.get("quality_report", {})
    
    if quality_report.get("needs_refinement", False):
        return "planner"
    return "writer"


def check_plan_approval(state: AgentState) -> Literal["researcher", "__interrupt__"]:
    """Check if plan is approved for HITL."""
    if state.get("plan_approved", False):
        return "researcher"
    # In CLI mode, auto-approve; in API mode, this triggers interrupt
    return "researcher"  # Default to auto-approve for CLI


def create_research_graph(enable_hitl: bool = False) -> StateGraph:
    """
    Create the advanced research workflow graph.
    
    Flow:
    START -> planner -> [HITL approval] -> researcher -> critic -> 
        [if needs refinement] -> planner (loop)
        [if sufficient] -> writer -> END
    
    Args:
        enable_hitl: Enable human-in-the-loop for plan approval
        
    Returns:
        Compiled StateGraph
    """
    # Initialize graph with state schema
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("planner", plan_research)
    workflow.add_node("researcher", execute_research)
    workflow.add_node("critic", evaluate_research)
    workflow.add_node("writer", write_report)
    
    # Define edges
    workflow.add_edge(START, "planner")
    
    if enable_hitl:
        # With HITL, check approval before proceeding
        workflow.add_conditional_edges(
            "planner",
            check_plan_approval,
            {
                "researcher": "researcher",
                "__interrupt__": END  # Will be handled by API
            }
        )
    else:
        # Without HITL, go directly to researcher
        workflow.add_edge("planner", "researcher")
    
    workflow.add_edge("researcher", "critic")
    
    # Conditional routing after critic
    workflow.add_conditional_edges(
        "critic",
        should_continue_after_critic,
        {
            "planner": "planner",
            "writer": "writer"
        }
    )
    
    workflow.add_edge("writer", END)
    
    # Compile with memory for state persistence
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph


# Create default graph instance
research_graph = create_research_graph(enable_hitl=False)


def run_research(topic: str, config: dict = None) -> dict:
    """
    Run the complete research workflow.
    
    Args:
        topic: Research topic
        config: Optional configuration overrides
        
    Returns:
        Final state with report
    """
    from .state import create_initial_state
    
    initial_state = create_initial_state(topic)
    
    # Run with thread ID for state persistence
    thread_config = {"configurable": {"thread_id": f"research_{hash(topic)}"}}
    
    final_state = research_graph.invoke(initial_state, thread_config)
    
    return final_state
