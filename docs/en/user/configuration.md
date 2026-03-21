# Configuration Guide

This guide explains how to configure MC-Agent-Kit.

## Configuration File

MC-Agent-Kit uses a YAML or JSON configuration file.

### Default Locations

The configuration file is searched in the following order:

1. `./mc-agent-kit.yaml` (current directory)
2. `~/.mc-agent-kit/config.yaml` (home directory)
3. `MC_AGENT_KIT_CONFIG` environment variable

### Configuration Format

```yaml
# mc-agent-kit.yaml

# Game Launcher Settings
launcher:
  game_path: "C:/Games/Minecraft"
  dev_mode: true
  log_port: 8080

# Knowledge Base Settings
knowledge_base:
  docs_path: "./docs"
  index_path: "./data/knowledge_base.json"
  auto_rebuild: false

# Code Generation Settings
generator:
  templates_path: "./templates"
  output_path: "./output"

# Log Capture Settings
log_capture:
  port: 8080
  buffer_size: 1000
  auto_analysis: true

# Performance Settings
performance:
  cache_size: 1000
  batch_size: 100
```

## Configuration Options

### Launcher Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `game_path` | string | - | Path to Minecraft installation |
| `dev_mode` | bool | true | Enable developer mode |
| `log_port` | int | 8080 | Port for log server |

### Knowledge Base Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `docs_path` | string | - | Path to ModSDK documentation |
| `index_path` | string | `./data/kb.json` | Path to knowledge base index |
| `auto_rebuild` | bool | false | Auto-rebuild index on changes |

### Generator Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `templates_path` | string | - | Custom templates directory |
| `output_path` | string | `.` | Generated code output directory |

### Log Capture Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `port` | int | 8080 | Log server port |
| `buffer_size` | int | 1000 | Log buffer size |
| `auto_analysis` | bool | true | Automatically analyze logs |

### Performance Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cache_size` | int | 1000 | LRU cache size |
| `batch_size` | int | 100 | Batch processing size |

## Environment Variables

Configuration options can be overridden with environment variables:

```bash
# Launcher
export MC_AGENT_GAME_PATH="/path/to/minecraft"
export MC_AGENT_DEV_MODE="true"

# Knowledge Base
export MC_AGENT_DOCS_PATH="/path/to/docs"
export MC_AGENT_INDEX_PATH="/path/to/kb.json"

# Log Capture
export MC_AGENT_LOG_PORT="8080"

# Performance
export MC_AGENT_CACHE_SIZE="1000"
```

## Using Configuration in Code

```python
from mc_agent_kit import Config

# Load from default locations
config = Config.load()

# Load from specific path
config = Config.load("./my-config.yaml")

# Access configuration
print(config.launcher.game_path)
print(config.knowledge_base.docs_path)
```

## Best Practices

1. **Version Control**: Check your configuration file into version control
2. **Environment Variables**: Use environment variables for sensitive paths
3. **Relative Paths**: Use relative paths for portable configurations
4. **Validation**: Validate configuration on startup