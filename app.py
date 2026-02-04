"""
Streamlit UI for the Advanced Research Agent.

Modern, interactive interface with real-time progress streaming,
dark mode, and beautiful design.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🔬 Advanced Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    /* Dark theme enhancement */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Main container */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.8);
        margin-top: 0.5rem;
    }
    
    /* Cards */
    .research-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    /* Progress messages */
    .agent-message {
        background: rgba(102, 126, 234, 0.1);
        border-left: 3px solid #667eea;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 10px 10px 0;
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.9rem;
    }
    
    /* Quality score */
    .quality-score {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Query pills */
    .query-pill {
        display: inline-block;
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.85rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-planning { background: #ffd93d; color: #1a1a2e; }
    .status-researching { background: #6bcb77; color: #1a1a2e; }
    .status-evaluating { background: #4d96ff; color: white; }
    .status-writing { background: #9b59b6; color: white; }
    .status-complete { background: #2ecc71; color: white; }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Animations */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading-pulse {
        animation: pulse 1.5s infinite;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Advanced Research Agent</h1>
        <p>Multi-Agent System • Parallel Search • Quality Control • Real-time Streaming</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with configuration options."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        st.markdown("---")
        
        max_revisions = st.slider(
            "Max Refinement Iterations",
            min_value=0,
            max_value=5,
            value=2,
            help="Number of times to refine research if quality is low"
        )
        
        citation_style = st.selectbox(
            "Citation Style",
            options=["APA", "MLA", "Chicago"],
            index=0
        )
        
        st.markdown("---")
        
        st.markdown("### 🔧 API Status")
        
        # Check API keys
        import os
        tavily_ok = bool(os.getenv("TAVILY_API_KEY"))
        llm_ok = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
        
        if tavily_ok:
            st.success("✅ Tavily API: Connected")
        else:
            st.error("❌ Tavily API: Not configured")
            
        if llm_ok:
            st.success("✅ LLM API: Connected")
        else:
            st.error("❌ LLM API: Not configured")
        
        st.markdown("---")
        
        st.markdown("### 📊 About")
        st.markdown("""
        **v2.0** - Advanced Edition
        - 🤖 4 Specialized Agents
        - 🔍 Parallel Web Search
        - ✅ Quality Control
        - 📝 Citation Management
        """)
        
        return max_revisions, citation_style.lower()


def render_research_input():
    """Render the research topic input."""
    st.markdown("### 📝 Enter Your Research Topic")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        topic = st.text_input(
            "Topic",
            placeholder="e.g., Impact of quantum computing on cryptography",
            label_visibility="collapsed"
        )
    
    with col2:
        start_button = st.button("🚀 Research", type="primary", use_container_width=True)
    
    # Example topics
    st.markdown("**Quick Examples:**")
    example_cols = st.columns(3)
    
    examples = [
        "AI advancements in healthcare 2024",
        "Sustainable energy innovations",
        "Future of remote work technology"
    ]
    
    selected_example = None
    for i, example in enumerate(examples):
        with example_cols[i]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                selected_example = example
    
    return topic or selected_example, start_button or (selected_example is not None)


def render_agent_message(message: str, node: str = ""):
    """Render an agent message with styling."""
    icon_map = {
        "Planner": "📋",
        "Researcher": "🔍",
        "Critic": "🔬",
        "Writer": "📝"
    }
    icon = icon_map.get(node, "🤖")
    
    st.markdown(f"""
    <div class="agent-message">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)


def render_quality_report(quality: dict):
    """Render the quality assessment."""
    if not quality:
        return
        
    st.markdown("### 📊 Research Quality Assessment")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{quality.get('overall_score', 0):.1f}/10")
    with col2:
        st.metric("Completeness", f"{quality.get('completeness', 0):.1f}/10")
    with col3:
        st.metric("Source Diversity", f"{quality.get('source_diversity', 0):.1f}/10")
    with col4:
        st.metric("Fact Consistency", f"{quality.get('fact_consistency', 0):.1f}/10")


def run_research_with_streaming(topic: str, max_revisions: int):
    """Run research with real-time streaming to UI."""
    from src.state import create_initial_state
    from src.graph import create_research_graph
    
    # Create containers for streaming
    status_container = st.empty()
    progress_container = st.container()
    quality_container = st.empty()
    
    # Initialize state
    state = create_initial_state(topic, max_revisions)
    
    # Create graph
    graph = create_research_graph(enable_hitl=False)
    thread_config = {"configurable": {"thread_id": f"streamlit_{hash(topic)}"}}
    
    # Status mapping
    status_icons = {
        "planning": "📋 Planning research...",
        "awaiting_approval": "⏳ Awaiting approval...",
        "researching": "🔍 Executing searches...",
        "evaluating": "🔬 Evaluating quality...",
        "writing": "📝 Writing report...",
        "complete": "✅ Complete!"
    }
    
    all_messages = []
    
    # Stream the research
    try:
        for event in graph.stream(state, thread_config, stream_mode="updates"):
            for node_name, updates in event.items():
                # Update status
                new_status = updates.get("status", "")
                if new_status:
                    with status_container:
                        st.info(status_icons.get(new_status, f"🔄 {new_status}"))
                
                # Display new messages
                new_messages = updates.get("messages", [])
                for msg in new_messages:
                    all_messages.append((node_name, msg))
                
                # Render all messages
                with progress_container:
                    for node, msg in all_messages[-10:]:  # Last 10 messages
                        # Extract node name from message
                        if "[" in msg and "]" in msg:
                            node = msg.split("]")[0].replace("[", "")
                            content = msg.split("]", 1)[1].strip()
                        else:
                            content = msg
                        render_agent_message(content, node)
                
                # Display quality report
                quality = updates.get("quality_report")
                if quality:
                    with quality_container:
                        render_quality_report(quality)
                
                # Update final state
                for key, value in updates.items():
                    if key == "messages":
                        state["messages"] = state.get("messages", []) + value
                    elif key == "research_data":
                        state["research_data"] = state.get("research_data", []) + value
                    else:
                        state[key] = value
        
        return state
        
    except Exception as e:
        st.error(f"❌ Error during research: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


def save_report(topic: str, report: str) -> Path:
    """Save report to file."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)[:50]
    filename = f"{timestamp}_{safe_topic.replace(' ', '_')}.md"
    
    filepath = reports_dir / filename
    filepath.write_text(report, encoding="utf-8")
    
    return filepath


def main():
    """Main Streamlit application."""
    render_header()
    max_revisions, citation_style = render_sidebar()
    
    # Initialize session state
    if "research_complete" not in st.session_state:
        st.session_state.research_complete = False
    if "final_report" not in st.session_state:
        st.session_state.final_report = ""
    if "topic" not in st.session_state:
        st.session_state.topic = ""
    
    # Research input
    topic, start_research = render_research_input()
    
    st.markdown("---")
    
    # Run research
    if start_research and topic:
        st.session_state.research_complete = False
        st.session_state.topic = topic
        
        with st.spinner("Initializing research agents..."):
            final_state = run_research_with_streaming(topic, max_revisions)
        
        if final_state and final_state.get("final_report"):
            st.session_state.research_complete = True
            st.session_state.final_report = final_state["final_report"]
            st.session_state.quality_report = final_state.get("quality_report", {})
            
            # Save report
            filepath = save_report(topic, final_state["final_report"])
            st.success(f"✅ Research complete! Report saved to: {filepath}")
    
    # Display final report
    if st.session_state.research_complete and st.session_state.final_report:
        st.markdown("---")
        st.markdown("## 📄 Research Report")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📖 Rendered", "📝 Markdown", "📊 Stats"])
        
        with tab1:
            st.markdown(st.session_state.final_report)
        
        with tab2:
            st.code(st.session_state.final_report, language="markdown")
            st.download_button(
                "⬇️ Download Report",
                st.session_state.final_report,
                file_name=f"research_{st.session_state.topic[:30].replace(' ', '_')}.md",
                mime="text/markdown"
            )
        
        with tab3:
            quality = st.session_state.get("quality_report", {})
            if quality:
                render_quality_report(quality)
            
            st.markdown("### 📈 Report Statistics")
            report = st.session_state.final_report
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Characters", f"{len(report):,}")
            with col2:
                st.metric("Words", f"{len(report.split()):,}")
            with col3:
                st.metric("Lines", f"{len(report.splitlines()):,}")


if __name__ == "__main__":
    main()
