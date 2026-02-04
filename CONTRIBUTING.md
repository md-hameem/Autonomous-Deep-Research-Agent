# Contributing to Autonomous Deep Research Agent

Thank you for your interest in contributing! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/autonomous-deep-research-agent.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your `.env` file with API keys

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

## Making Changes

1. Make your changes
2. Test your changes locally: `python main.py "test topic"`
3. Ensure code passes syntax check: `python -m py_compile *.py`
4. Commit with clear messages: `git commit -m "feat: add new feature"`

## Pull Request Process

1. Update the README.md if needed
2. Push to your fork
3. Open a Pull Request with a clear description

## Code Style

- Follow PEP 8 guidelines
- Add docstrings to functions
- Handle errors gracefully

## Questions?

Open an issue for any questions or suggestions!
