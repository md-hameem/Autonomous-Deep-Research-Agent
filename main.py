#!/usr/bin/env python3
"""
Advanced Autonomous Research Agent - CLI Entry Point

Production-grade CLI with rich output, progress tracking,
and configuration options.
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║     🔬 ADVANCED AUTONOMOUS RESEARCH AGENT v2.0               ║
║     Multi-Agent | Parallel Search | Quality Control          ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_progress(messages: list[str]):
    """Print progress messages."""
    for msg in messages:
        print(f"  {msg}")


def validate_environment() -> bool:
    """Validate required environment variables."""
    from src.config import get_config
    
    config = get_config()
    errors = config.validate()
    
    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n💡 Copy .env.example to .env and fill in your API keys.")
        return False
    
    return True


def save_report(topic: str, report: str, output_dir: str = "reports") -> Path:
    """Save the generated report to a markdown file."""
    reports_dir = Path(output_dir)
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
    safe_topic = safe_topic[:50].strip().replace(" ", "_")
    filename = f"{timestamp}_{safe_topic}.md"
    
    filepath = reports_dir / filename
    filepath.write_text(report, encoding="utf-8")
    
    return filepath


def run_cli(topic: str, output_dir: str = "reports", max_revisions: int = 2):
    """Run the research agent via CLI."""
    from src.graph import run_research
    from src.state import create_initial_state
    
    print(f"\n📌 Research Topic: {topic}")
    print("=" * 60)
    
    print("\n⏳ Starting multi-agent research workflow...\n")
    
    # Run the research workflow
    final_state = run_research(topic)
    
    # Print all agent messages
    print("\n📋 Agent Activity Log:")
    print("-" * 40)
    for msg in final_state.get("messages", []):
        print(f"  {msg}")
    
    # Get quality report
    quality = final_state.get("quality_report", {})
    if quality:
        print(f"\n📊 Quality Score: {quality.get('overall_score', 'N/A')}/10")
        print(f"   Completeness: {quality.get('completeness', 'N/A')}/10")
        print(f"   Source Diversity: {quality.get('source_diversity', 'N/A')}/10")
    
    # Save report
    report = final_state.get("final_report", "")
    if report:
        filepath = save_report(topic, report, output_dir)
        
        print(f"\n✅ RESEARCH COMPLETE!")
        print(f"📄 Report saved to: {filepath}")
        print(f"📝 Report length: {len(report):,} characters")
        
        # Print preview
        print("\n" + "=" * 60)
        print("📋 REPORT PREVIEW")
        print("=" * 60 + "\n")
        
        preview = report[:2000] if len(report) > 2000 else report
        print(preview)
        
        if len(report) > 2000:
            print(f"\n... [Truncated - see full report at {filepath}]")
    else:
        print("\n❌ No report generated. Check the logs above for errors.")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Advanced Autonomous Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Impact of quantum computing on cryptography"
  python main.py --output ./my_reports "AI in healthcare 2024"
  python main.py --max-revisions 3 "Climate change solutions"
        """
    )
    
    parser.add_argument(
        "topic",
        nargs="?",
        help="Research topic (or enter interactively)"
    )
    parser.add_argument(
        "--output", "-o",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    parser.add_argument(
        "--max-revisions", "-r",
        type=int,
        default=2,
        help="Maximum refinement iterations (default: 2)"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Get topic
    topic = args.topic
    if not topic:
        print("Enter your research topic (or 'quit' to exit):")
        topic = input("📝 Topic: ").strip()
        
        if topic.lower() in ["quit", "exit", "q"]:
            print("\n👋 Goodbye!")
            sys.exit(0)
    
    if not topic:
        print("❌ Please provide a research topic.")
        sys.exit(1)
    
    try:
        run_cli(topic, args.output, args.max_revisions)
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
