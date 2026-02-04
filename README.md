# 🔬 Advanced Autonomous Research Agent

A production-grade, multi-agent research system powered by **LangGraph** that autonomously researches any topic using parallel web searches, quality control, and generates comprehensive markdown reports.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Agent Architecture** | 4 specialized agents (Planner, Researcher, Critic, Writer) |
| ⚡ **Parallel Search** | Concurrent web searches for 3-5x faster research |
| 🔍 **Multi-Provider Search** | Tavily + Wikipedia + Serper (optional) |
| ✅ **Quality Control** | Automatic evaluation and iterative refinement |
| 📊 **Source Scoring** | Relevance and quality scoring for all sources |
| 🔄 **Iterative Refinement** | Loops until quality threshold is met |
| 🎨 **Modern Web UI** | Beautiful Streamlit interface with dark theme |
| 📝 **Citation Management** | APA, MLA, Chicago formatting |
| 💾 **Auto-Save** | Reports saved with timestamps |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    🎯 SUPERVISOR                            │
│            (Orchestrates the research workflow)             │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  📋 PLANNER     │  │  🔍 RESEARCHER  │  │  🔬 CRITIC      │
│  Creates search │  │  Parallel web   │  │  Evaluates      │
│  queries        │  │  searches       │  │  quality        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  📝 WRITER      │
                    │  Generates      │
                    │  final report   │
                    └─────────────────┘
```

**Workflow:**
```
START → Planner → Researcher → Critic → [needs refinement?] → Writer → END
                                  ↑              │
                                  └──────────────┘
```

## 📁 Project Structure

```
├── app.py                 # 🎨 Streamlit Web UI
├── main.py                # 💻 CLI Entry Point
├── src/
│   ├── config.py          # ⚙️ Configuration management
│   ├── state.py           # 📊 State definitions
│   ├── graph.py           # 🔄 LangGraph workflow
│   ├── agents/
│   │   ├── base.py        # Base agent class
│   │   ├── planner.py     # 📋 Research planner
│   │   ├── researcher.py  # 🔍 Parallel searcher
│   │   ├── critic.py      # 🔬 Quality evaluator
│   │   └── writer.py      # 📝 Report generator
│   └── tools/
│       └── search.py      # 🔍 Search providers
├── api/
│   └── main.py            # 🌐 FastAPI backend
├── reports/               # 📄 Generated reports
├── requirements.txt
└── .env.example
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` with your keys:
```env
TAVILY_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
LLM_PROVIDER=anthropic
```

### 3. Run the Application

**🎨 Web UI (Recommended):**
```bash
streamlit run app.py
```

**💻 Command Line:**
```bash
python main.py "Your research topic"
```

**🌐 API Server:**
```bash
uvicorn api.main:app --reload
```

## 📸 Screenshots

The Streamlit UI features:
- 🌙 Modern dark theme with glassmorphism
- 📊 Real-time quality metrics
- 📋 Live agent activity log
- 📥 One-click report download
- 📈 Research statistics

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TAVILY_API_KEY` | Tavily search API key | Required |
| `ANTHROPIC_API_KEY` | Claude API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `LLM_PROVIDER` | `anthropic` or `openai` | `anthropic` |
| `SERPER_API_KEY` | Google search (optional) | - |

## 🔧 Advanced Usage

### Programmatic API

```python
from src.graph import run_research

result = run_research("Impact of AI on healthcare")
print(result["final_report"])
print(f"Quality Score: {result['quality_report']['overall_score']}")
```

### Custom Configuration

```python
from src.config import get_config

config = get_config()
config.search.max_results_per_query = 10
config.quality.min_quality_score = 8.0
```

## 🧪 How It Works

1. **Planner Agent** analyzes your topic and generates 3-5 targeted search queries
2. **Researcher Agent** executes queries in parallel using Tavily + Wikipedia
3. **Critic Agent** evaluates research quality (completeness, diversity, consistency)
4. If quality < 7/10, loops back to Planner for refinement
5. **Writer Agent** compiles everything into a structured markdown report

## 📄 License

MIT License - feel free to use and modify!

---

Built with ❤️ using LangGraph, Streamlit, and Tavily
