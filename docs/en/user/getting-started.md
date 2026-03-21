# Getting Started

This guide will help you get started with MC-Agent-Kit in 5 minutes.

## Prerequisites

- Python 3.13 or higher
- Minecraft Bedrock Edition (for game launcher features)
- ModSDK documentation (optional, for knowledge base features)

## Quick Start

### 1. Install MC-Agent-Kit

```bash
pip install mc-agent-kit
```

### 2. CLI Quick Reference

```bash
# List available skills
mc-agent list skills

# Search API documentation
mc-agent api search GetConfig

# Search event documentation
mc-agent event search onPlayerJoin

# Generate code from template
mc-agent gen template event_listener --params event_name=onPlayerJoin

# Diagnose error logs
mc-agent debug diagnose --log "SyntaxError: invalid syntax"
```

### 3. Python API

```python
from mc_agent_kit import CodeGenerator

# Generate code
generator = CodeGenerator()
code = generator.generate(
    template_name="event_listener",
    params={"event_name": "onPlayerJoin"}
)
print(code)
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `mc-agent list skills` | List all available skills |
| `mc-agent list templates` | List code templates |
| `mc-agent api search <query>` | Search API documentation |
| `mc-agent event search <query>` | Search event documentation |
| `mc-agent gen template <name>` | Generate code from template |
| `mc-agent debug diagnose` | Diagnose error logs |

## OpenClaw Integration

MC-Agent-Kit is designed to work with OpenClaw AI agents. The skills are automatically available when the package is installed.

See the `skills/` directory for skill definitions.

## Next Steps

- Read the [Installation Guide](installation.md) for detailed setup
- Learn about [Configuration](configuration.md)
- Try the [Hello World Tutorial](tutorial/hello-world.md)
- Check the [FAQ](faq.md) for common issues