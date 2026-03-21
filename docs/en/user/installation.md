# Installation Guide

This guide covers different ways to install MC-Agent-Kit.

## Requirements

- **Python**: 3.13 or higher
- **Operating System**: Windows, macOS, or Linux

## Installation Methods

### Method 1: pip (Recommended)

```bash
pip install mc-agent-kit
```

### Method 2: uv

```bash
uv pip install mc-agent-kit
```

### Method 3: From Source

```bash
git clone https://github.com/your-username/mc-agent-kit.git
cd mc-agent-kit
uv sync
```

## Optional Dependencies

MC-Agent-Kit has optional dependencies for additional features:

### Knowledge Base Features

For semantic search and vector storage:

```bash
pip install mc-agent-kit[knowledge]
```

This installs:
- `chromadb` - Vector database
- `sentence-transformers` - Text embeddings
- `llama-index` - LLM framework

### Development

For development and testing:

```bash
pip install mc-agent-kit[dev]
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `ruff` - Linting
- `mypy` - Type checking
- `pytest-cov` - Coverage reporting

### All Dependencies

Install everything:

```bash
pip install mc-agent-kit[all]
```

## Verify Installation

```bash
# Check version
mc-agent --version

# List available commands
mc-agent --help
```

## Troubleshooting

### Python Version

MC-Agent-Kit requires Python 3.13. Check your version:

```bash
python --version
```

### Import Errors

If you get import errors, try reinstalling:

```bash
pip uninstall mc-agent-kit
pip install mc-agent-kit
```

### Permission Issues

On Linux/macOS, you may need:

```bash
pip install mc-agent-kit --user
```

Or use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
pip install mc-agent-kit
```