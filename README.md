<div align="center">

# 🔬 Autonomous Deep Research Agent

### Production-Grade Multi-Agent Research System

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-00ADD8?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

*An AI-powered research assistant that autonomously investigates any topic using specialized agents, parallel web searches, and quality-controlled report generation.*

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Usage](#-usage) • [API Reference](#-api-reference)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🤖 Multi-Agent Architecture
Four specialized AI agents work together:
- **Planner** — Creates targeted search strategies
- **Researcher** — Executes parallel web searches
- **Critic** — Evaluates quality & completeness
- **Writer** — Generates structured reports

</td>
<td width="50%">

### ⚡ High Performance
- **Parallel Execution** — 3-5x faster research
- **Smart Caching** — SQLite-based result caching
- **Async I/O** — Non-blocking operations
- **Rate Limiting** — Respects API limits

</td>
</tr>
<tr>
<td width="50%">

### 🔍 Advanced Research
- **Multi-Provider Search** — Tavily + Wikipedia + Serper
- **Quality Scoring** — 1-10 relevance ratings
- **Fact Checking** — Cross-reference validation
- **Iterative Refinement** — Auto-improves weak results

</td>
<td width="50%">

### 🎨 Modern Interface
- **Streamlit Web UI** — Beautiful dark theme
- **Real-time Streaming** — Live progress updates
- **CLI Support** — Full command-line interface
- **REST API** — FastAPI with WebSocket

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- [Tavily API Key](https://tavily.com) (free tier available), or enable [Parallel search](#optional-parallel-search)
- [Anthropic](https://console.anthropic.com) or [OpenAI](https://platform.openai.com) API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/autonomous-research-agent.git
cd autonomous-research-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

### Run the Application

<table>
<tr>
<td>

**🎨 Web Interface**
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

</td>
<td>

**💻 Command Line**
```bash
python main.py "Your research topic"
```

</td>
<td>

**🌐 API Server**
```bash
uvicorn api.main:app --reload
```
Opens at `http://localhost:8000`

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        🎯 WORKFLOW ORCHESTRATOR                      │
│                    (LangGraph State Machine)                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  📋 PLANNER   │           │ 🔍 RESEARCHER │           │  🔬 CRITIC    │
│               │           │               │           │               │
│ • Analyze     │     ┌────▶│ • Parallel    │           │ • Score       │
│   topic       │     │     │   search      │           │   quality     │
│ • Generate    │─────┘     │ • Multi-      │──────────▶│ • Check       │
│   queries     │           │   provider    │           │   coverage    │
│ • Strategy    │           │ • Rate &      │           │ • Suggest     │
│   planning    │           │   cache       │           │   refinements │
└───────────────┘           └───────────────┘           └───────┬───────┘
                                                                │
                            ┌───────────────┐                   │
                            │  📝 WRITER    │◀──────────────────┘
                            │               │
                            │ • Structure   │
                            │   report      │
                            │ • Citations   │
                            │ • Formatting  │
                            └───────────────┘
```

### Workflow

1. **Planning** → Planner breaks topic into 3-5 targeted search queries
2. **Research** → Researcher executes queries in parallel via Tavily + Wikipedia
3. **Evaluation** → Critic scores quality (completeness, diversity, consistency)
4. **Refinement** → If score < 7/10, loops back with improvement suggestions
5. **Writing** → Writer compiles sources into structured markdown report

---

## 📁 Project Structure

```
autonomous-research-agent/
│
├── 🎨 app.py                 # Streamlit Web UI
├── 💻 main.py                # CLI Entry Point
├── 📦 pyproject.toml         # Project configuration
│
├── src/                      # Core Package
│   ├── config.py             # Configuration management
│   ├── state.py              # State definitions
│   ├── graph.py              # LangGraph workflow
│   │
│   ├── agents/               # Specialized Agents
│   │   ├── base.py           # Base agent class
│   │   ├── planner.py        # Research planning
│   │   ├── researcher.py     # Parallel search
│   │   ├── critic.py         # Quality evaluation
│   │   └── writer.py         # Report generation
│   │
│   └── tools/                # Utilities
│       ├── search.py         # Search providers
│       └── cache.py          # SQLite caching
│
├── api/                      # REST API
│   └── main.py               # FastAPI + WebSocket
│
├── tests/                    # Test Suite
├── reports/                  # Generated Reports
└── data/                     # Cache Storage
```

---

## 💻 Usage

### Web Interface

The Streamlit UI provides the most user-friendly experience:

```bash
streamlit run app.py
```

**Features:**
- 🌙 Modern dark theme with glassmorphism
- 📊 Real-time quality metrics
- 📋 Live agent activity log
- 📥 One-click report download

### Command Line

```bash
# Basic usage
python main.py "Impact of quantum computing on cryptography"

# With options
python main.py --output ./my_reports --max-revisions 3 "AI in healthcare"
```

**Options:**
| Flag | Description | Default |
|------|-------------|---------|
| `--output, -o` | Output directory | `reports/` |
| `--max-revisions, -r` | Max refinement loops | `2` |

### Programmatic API

```python
from src.graph import run_research

# Run research
result = run_research("Climate change mitigation strategies")

# Access results
print(result["final_report"])
print(f"Quality: {result['quality_report']['overall_score']}/10")
print(f"Sources: {len(result['sources'])}")
```

---

## 🌐 API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/research/start` | Start new research session |
| `GET` | `/api/research/{id}` | Get session status |
| `POST` | `/api/research/{id}/approve` | Approve research plan |
| `GET` | `/api/research/{id}/report` | Get final report |

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/research/{session_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Types: 'message', 'status', 'plan', 'quality', 'complete'
  console.log(data.type, data.content);
};
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TAVILY_API_KEY` | Tavily search API | Unless Parallel is enabled |
| `PARALLEL_SEARCH_ENABLED` | Add anonymous Parallel search | Default: `false` |
| `ANTHROPIC_API_KEY` | Claude API key | One of these |
| `OPENAI_API_KEY` | OpenAI API key | required |
| `LLM_PROVIDER` | `anthropic` or `openai` | Default: `anthropic` |
| `SERPER_API_KEY` | Google Search (optional) | ❌ |

### Optional Parallel Search

Enable free web search with [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
by adding this to `.env` before starting the application:

```dotenv
PARALLEL_SEARCH_ENABLED=true
```

No Parallel account or API key is needed. Anonymous searches use Fast mode and
have free-tier rate limits. You can omit `TAVILY_API_KEY` when Parallel is enabled;
if you keep it, both providers run alongside Wikipedia. Your LLM API key is still
required. Leave this setting unset or set it to `false` to keep the existing
Tavily and Wikipedia setup.

Start the CLI as usual, for example:

```bash
python main.py "Recent advances in quantum error correction"
```

The researcher sends each planned query to `https://search.parallel.ai/mcp`
using Streamable HTTP and turns search excerpts into sources for scoring and
report generation. Each search has a 30-second timeout; failed or rate-limited
searches contribute no sources while other providers continue. This integration
uses `web_search` only.

### Advanced Configuration

```python
from src.config import get_config

config = get_config()

# Search settings
config.search.max_results_per_query = 10
config.search.max_parallel_searches = 8

# Quality thresholds
config.quality.min_quality_score = 8.0
config.quality.max_refinement_iterations = 3

# Cache settings
config.cache.ttl_hours = 48
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ using [LangGraph](https://langchain-ai.github.io/langgraph/), [Streamlit](https://streamlit.io), and [Tavily](https://tavily.com)**

⭐ Star this repo if you find it useful!

</div>
