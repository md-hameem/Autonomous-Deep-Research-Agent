#!/usr/bin/env python3
"""
Autonomous Deep Research Agent - CLI Entry Point

This is the main entry point for running the research agent.
It accepts a research topic from the user and runs the full
research workflow to generate a comprehensive markdown report.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def validate_environment() -> bool:
    """Validate that required environment variables are set."""
    required = ["TAVILY_API_KEY"]
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    
    if provider == "openai":
        required.append("OPENAI_API_KEY")
    else:
        required.append("ANTHROPIC_API_KEY")
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Copy .env.example to .env and fill in your API keys.")
        return False
    
    return True


def save_report(topic: str, report: str) -> Path:
    """Save the generated report to a markdown file."""
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Generate filename from topic and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
    safe_topic = safe_topic[:50].strip().replace(" ", "_")
    filename = f"{timestamp}_{safe_topic}.md"
    
    filepath = reports_dir / filename
    filepath.write_text(report, encoding="utf-8")
    
    return filepath


def run_research_agent(topic: str) -> str:
    """
    Run the research agent workflow for the given topic.
    
    Args:
        topic: The research topic/query from the user
        
    Returns:
        The generated markdown report
    """
    from graph import research_graph
    
    print(f"\n{'='*60}")
    print("🚀 AUTONOMOUS DEEP RESEARCH AGENT")
    print(f"{'='*60}")
    print(f"\n📌 Topic: {topic}")
    print(f"{'='*60}")
    
    # Initialize the state
    initial_state = {
        "topic": topic,
        "plan": [],
        "research_data": [],
        "final_report": "",
        "revision_number": 0
    }
    
    # Run the workflow
    print("\n⏳ Starting research workflow...\n")
    
    final_state = research_graph.invoke(initial_state)
    
    return final_state["final_report"]


def main():
    """Main CLI entry point."""
    print("\n" + "="*60)
    print("  🔬 AUTONOMOUS DEEP RESEARCH AGENT")
    print("  Powered by LangGraph + Tavily")
    print("="*60)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Get topic from command line or prompt
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        print("\nEnter your research topic (or 'quit' to exit):")
        topic = input("📝 Topic: ").strip()
        
        if topic.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!")
            sys.exit(0)
    
    if not topic:
        print("❌ Please provide a research topic.")
        sys.exit(1)
    
    try:
        # Run the research agent
        report = run_research_agent(topic)
        
        # Save the report
        filepath = save_report(topic, report)
        
        print(f"\n{'='*60}")
        print("✅ RESEARCH COMPLETE!")
        print(f"{'='*60}")
        print(f"\n📄 Report saved to: {filepath}")
        print(f"\n{'='*60}")
        print("📋 REPORT PREVIEW")
        print(f"{'='*60}\n")
        
        # Print the report (or first 2000 chars if very long)
        if len(report) > 2000:
            print(report[:2000])
            print(f"\n... [Report truncated - see full report at {filepath}]")
        else:
            print(report)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error during research: {e}")
        raise


if __name__ == "__main__":
    main()
