# MC-Agent-Kit

[![CI/CD](https://github.com/your-username/mc-agent-kit/workflows/CI%2FCD/badge.svg)](https://github.com/your-username/mc-agent-kit/actions)
[![PyPI version](https://badge.fury.io/py/mc-agent-kit.svg)](https://badge.fury.io/py/mc-agent-kit)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Toolsets and Skills to empower AI Agents for Minecraft ModSDK development.

English | [中文文档](docs/README_CN.md)

## Features

- 🎮 **Game Launcher** - Launch Minecraft with custom Addons without MC Studio
- 📊 **Log Capture & Analysis** - Real-time log capture with intelligent error detection
- 🧠 **Knowledge Base** - Semantic search through ModSDK documentation
- 🤖 **Code Generation** - AI-powered code generation for events, APIs, entities, items
- 🔧 **Code Completion** - Intelligent code completion with best practices checking
- 🐛 **Auto-Fix** - Automatic error diagnosis and fix suggestions
- ⚡ **Performance Optimization** - Caching and batch processing for faster operations

## Installation

### From PyPI

```bash
pip install mc-agent-kit
```

### From Source

```bash
git clone https://github.com/your-username/mc-agent-kit.git
cd mc-agent-kit
uv sync
```

### With Optional Dependencies

```bash
# For knowledge base features
pip install mc-agent-kit[knowledge]

# For development
pip install mc-agent-kit[dev]

# For everything
pip install mc-agent-kit[all]
```

## Quick Start

### CLI Usage

```bash
# Launch game with addon
mc-agent launch --addon-path ./my_addon

# Capture and analyze logs
mc-agent logs --analyze

# Generate code from templates
mc-agent generate event_listener --event OnServerChat

# Search documentation
mc-agent search "如何创建自定义实体"
```

### Python API

```python
from mc_agent_kit import (
    GameLauncher,
    LogCapture,
    KnowledgeBase,
    CodeGenerator,
)

# Launch game
launcher = GameLauncher(game_path="C:/Games/Minecraft")
launcher.launch_addon("./my_addon")

# Capture logs
capture = LogCapture()
capture.start()
# ... game runs ...
logs = capture.get_logs()

# Search knowledge base
kb = KnowledgeBase("./docs")
kb.build_index()
results = kb.search("创建实体")

# Generate code
generator = CodeGenerator()
code = generator.generate_from_template(
    "event_listener",
    {"event_name": "OnServerChat"}
)
```

## OpenClaw Skills

MC-Agent-Kit includes OpenClaw Skills for AI agent integration:

- **modsdk-api-search** - Search ModSDK API documentation
- **modsdk-event-search** - Search event documentation
- **modsdk-code-gen** - Generate ModSDK code
- **modsdk-debug** - Debug and analyze errors
- **modsdk-game-executor** - Execute code in-game
- **modsdk-log-analyzer** - Analyze game logs
- **modsdk-autofix** - Auto-fix common errors

See [skills/](skills/) directory for skill documentation.

## Documentation

- [Getting Started](docs/user/getting_started.md)
- [Installation Guide](docs/user/installation.md)
- [Configuration Guide](docs/user/configuration.md)
- [API Reference](docs/api/README.md)
- [FAQ](docs/user/faq.md)
- [Tutorials](docs/user/tutorials/)

## Examples

Check the [examples/](examples/) directory for sample projects:

- **hello-world** - Basic addon structure
- **custom-entity** - Custom entity creation
- **custom-item** - Custom item creation
- **custom-ui** - UI development

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/your-username/mc-agent-kit.git
cd mc-agent-kit

# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

### Project Structure

```
MC-Agent-Kit/
├── docs/                    # Documentation
├── examples/                # Example projects
├── skills/                  # OpenClaw Skills
├── src/
│   ├── mc_agent_kit/       # Main package
│   │   ├── launcher/       # Game launcher
│   │   ├── log_capture/    # Log capture
│   │   ├── knowledge/      # Knowledge base
│   │   ├── retrieval/      # Search & retrieval
│   │   ├── generator/      # Code generation
│   │   ├── execution/      # Code execution
│   │   ├── completion/     # Code completion
│   │   ├── autofix/        # Auto-fix
│   │   ├── performance/    # Optimization
│   │   └── skills/         # Agent skills
│   └── tests/              # Test suite
├── .github/workflows/      # CI/CD
├── pyproject.toml          # Project config
└── README.md               # This file
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- NetEase Minecraft ModSDK documentation
- OpenClaw framework for AI agent skills
- All contributors and users

## Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for planned features and releases.

---

Made with ❤️ for Minecraft ModSDK developers