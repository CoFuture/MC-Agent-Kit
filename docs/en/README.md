# MC-Agent-Kit

> **AI Agent Development Toolkit for Minecraft NetEase ModSDK Addon**

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

MC-Agent-Kit enables AI Agents to autonomously complete the development lifecycle for Minecraft NetEase ModSDK Addons:

```
Requirements Analysis → Code Development → Testing & Verification → Iterative Fixes
```

## Features

### Core Capabilities

| Module | Description |
|--------|-------------|
| **Knowledge Base** | Search API documentation, events, and example code |
| **Project Scaffold** | Create standard Addon project structures |
| **Game Launcher** | Launch game with Addon, capture logs for diagnosis |
| **Error Diagnosis** | Analyze logs, identify errors, suggest fixes |
| **Code Generation** | Generate event listeners, API calls, templates |

### CLI Commands

```bash
# Knowledge base
mc-kb search "how to create entity"
mc-kb status

# Project creation
mc-create project MyAddon --template entity
mc-create entity CustomMob --in ./MyAddon

# Game launcher
mc-run ./MyAddon --timeout 60

# Diagnostics
mc-logs --analyze
```

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/MC-Agent-Kit.git
cd MC-Agent-Kit

# Install dependencies
uv sync

# Run tests
uv run pytest
```

## Quick Start

### 1. Search Documentation

```python
from mc_agent_kit.knowledge.retrieval import create_retrieval

retrieval = create_retrieval()
results = retrieval.search("how to create entity", limit=5)

for result in results:
    print(f"{result.type}: {result.name}")
    print(result.description)
```

### 2. Create Project

```python
from mc_agent_kit.scaffold.creator import ProjectCreator

creator = ProjectCreator()
project = creator.create_project(
    name="MyAddon",
    path="./projects",
    template="entity"
)

# Add custom entity
creator.add_entity("CustomZombie", project)
```

### 3. Run Workflow

```python
from mc_agent_kit.workflow.end_to_end import create_workflow, WorkflowConfig

config = WorkflowConfig(
    project_name="MyAddon",
    project_path="./projects",
    template="entity",
)

workflow = create_workflow(config)
result = workflow.run_full_cycle()

print(f"Success: {result.success}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Agent Interface Layer                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────┐    ┌─────────────────────┐   │
│   │      OpenClaw Skills        │    │      CLI Tools      │   │
│   │  (Natural language trigger) │    │  (Simplified CLI)   │   │
│   ├─────────────────────────────┤    ├─────────────────────┤   │
│   │ modsdk-search               │    │ mc-kb search        │   │
│   │ modsdk-diagnose             │    │ mc-create project   │   │
│   │ modsdk-code-gen             │    │ mc-run              │   │
│   └─────────────────────────────┘    │ mc-logs             │   │
│                                       └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Core Capability Layer                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Launcher      Scaffold       KnowledgeBase      Diagnoser    │
│   (Game launch) (Project)      (Search)           (Diagnosis)  │
│                                                                 │
│   Generator     LogCapture     ConfigGen         Autofix       │
│   (Code gen)    (Log capture)  (Config)          (Auto-fix)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
MC-Agent-Kit/
├── docs/               # Documentation
│   ├── VISION.md       # Project vision
│   ├── PRINCIPLES.md   # Development principles
│   ├── ITERATIONS.md   # Iteration history
│   └── en/             # English documentation
├── src/
│   ├── mc_agent_kit/   # Source code
│   │   ├── knowledge/  # Knowledge retrieval
│   │   ├── scaffold/   # Project scaffolding
│   │   ├── launcher/   # Game launcher
│   │   ├── generator/  # Code generation
│   │   ├── workflow/   # Workflow orchestration
│   │   └── ...
│   └── tests/          # Test suite
│       ├── e2e/        # End-to-end tests
│       ├── benchmark/  # Performance benchmarks
│       └── integration/# Integration tests
├── resources/          # Reference materials (read-only)
└── pyproject.toml      # Project configuration
```

## Development

### Requirements

- Python 3.13+
- uv package manager

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mc_agent_kit

# Run specific test categories
uv run pytest src/tests/e2e/      # End-to-end tests
uv run pytest src/tests/benchmark/ -m benchmark  # Performance tests
```

### Code Quality

```bash
# Lint checks
uv run ruff check src/mc_agent_kit

# Type checks
uv run mypy src/mc_agent_kit --ignore-missing-imports
```

## Documentation

- [Vision](docs/en/VISION.md) - Project vision and goals
- [Principles](docs/en/PRINCIPLES.md) - Development principles
- [API Reference](docs/en/API.md) - API documentation

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.31.0 | 2026-03-22 | Code quality improvements, test coverage |
| v1.30.0 | 2026-03-21 | Performance optimization, caching |
| v1.0.0 | 2026-03-01 | Initial release |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run tests to ensure they pass
5. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

- Minecraft NetEase ModSDK Team
- OpenClaw Framework
- All contributors