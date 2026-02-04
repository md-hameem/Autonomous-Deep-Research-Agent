# 🔬 Autonomous Deep Research Agent

A CLI-based research agent powered by **LangGraph** and **Tavily** that autonomously researches any topic and generates comprehensive markdown reports.

## ✨ Features

- **Intelligent Planning**: Automatically breaks down research topics into targeted search queries
- **Deep Web Search**: Uses Tavily API for high-quality, AI-optimized search results
- **Structured Reports**: Generates well-organized markdown reports with sources
- **Flexible LLM Support**: Works with Anthropic Claude or OpenAI GPT models
- **Error Resilient**: Gracefully handles API failures without crashing

## 🏗️ Architecture

```
┌─────────┐    ┌──────────┐    ┌────────────┐    ┌────────┐
│  START  │───▶│  Planner │───▶│ Researcher │───▶│ Writer │───▶ END
└─────────┘    └──────────┘    └────────────┘    └────────┘
                    │                │                │
                    ▼                ▼                ▼
               Generate         Execute Web      Compile
               Search           Searches via     Markdown
               Queries          Tavily API       Report
```

## 📁 Project Structure

```
├── main.py           # CLI entry point
├── graph.py          # LangGraph workflow definition
├── nodes.py          # Node functions (planner, researcher, writer)
├── state.py          # AgentState TypedDict definition
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
└── reports/          # Generated reports (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Then edit `.env`:
```env
TAVILY_API_KEY=your_tavily_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
# or
OPENAI_API_KEY=your_openai_key_here
LLM_PROVIDER=openai
```

### 3. Run the Agent

**Interactive mode:**
```bash
python main.py
```

**With a topic:**
```bash
python main.py "Impact of quantum computing on cryptography"
```

## 📄 Example Output

```
============================================================
🚀 AUTONOMOUS DEEP RESEARCH AGENT
============================================================

📌 Topic: Impact of quantum computing on cryptography
============================================================

📋 Research Plan Generated:
   1. quantum computing cryptography threats 2024
   2. post-quantum cryptography algorithms NIST
   3. quantum-resistant encryption implementations
   4. quantum computing timeline predictions

🔍 Executing 4 searches...
   Searching: quantum computing cryptography threats 2024
   Searching: post-quantum cryptography algorithms NIST
   ...
   ✅ Collected data from 4 searches

📝 Writing research report...
   ✅ Report generated successfully!

✅ RESEARCH COMPLETE!
📄 Report saved to: reports/20240115_123456_Impact_of_quantum_computing.md
```

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TAVILY_API_KEY` | Your Tavily API key (required) | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key (alternative) | - |
| `LLM_PROVIDER` | `anthropic` or `openai` | `anthropic` |

## 📚 Dependencies

- **LangGraph** - State machine orchestration
- **LangChain** - LLM interface layer
- **Tavily** - AI-optimized web search API
- **Pydantic** - Structured output validation
- **python-dotenv** - Environment management

## 🛠️ How It Works

1. **Planner Node**: Uses the LLM to generate 3-5 targeted search queries based on your topic
2. **Researcher Node**: Executes each query using Tavily's advanced search API, collecting top results
3. **Writer Node**: Synthesizes all research data into a comprehensive, structured markdown report

## 📜 License

MIT License - feel free to use and modify!
