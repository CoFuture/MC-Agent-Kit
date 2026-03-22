# Plugin Development Guide

This guide explains how to develop plugins for MC-Agent-Kit.

## Overview

MC-Agent-Kit provides a plugin system that allows extending functionality with third-party plugins. Plugins can add new capabilities, integrate with external services, or customize existing behavior.

## Quick Start

### 1. Create Plugin Directory

```bash
mkdir my_plugin
cd my_plugin
```

### 2. Create plugin.json

```json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "My awesome plugin",
    "author": "Your Name",
    "license": "MIT",
    "entry": "my_plugin.py",
    "dependencies": [],
    "provides": ["my_capability"]
}
```

### 3. Create Plugin Implementation

```python
from mc_agent_kit.plugin import PluginBase, PluginMetadata, PluginResult

class MyPlugin(PluginBase):
    def on_load(self) -> None:
        """Initialize plugin resources."""
        pass

    def on_unload(self) -> None:
        """Cleanup resources."""
        pass

    def execute(self, *args, **kwargs) -> PluginResult:
        """Main plugin logic."""
        return PluginResult(success=True, data={"message": "Hello!"})

__plugin__ = PluginMetadata(
    name="my_plugin",
    version="1.0.0",
    description="My awesome plugin",
)
```

## Plugin Manifest (plugin.json)

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique plugin identifier |
| `version` | string | Semantic version (e.g., "1.0.0") |
| `description` | string | Brief description |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `author` | string | "" | Plugin author |
| `license` | string | "MIT" | License identifier |
| `homepage` | string | null | Homepage URL |
| `entry` | string | "plugin.py" | Entry point file |
| `dependencies` | array | [] | List of dependencies |
| `provides` | array | [] | Capabilities provided |
| `metadata` | object | {} | Additional metadata |

### Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `min_core_version` | string | Minimum MC-Agent-Kit version |
| `max_core_version` | string | Maximum supported version |
| `supported_api_versions` | array | Supported API versions |

## Plugin Lifecycle

### on_load()

Called when the plugin is loaded into memory. Use for:
- Loading configuration files
- Initializing connections
- Setting up resources

### on_unload()

Called when the plugin is unloaded. Use for:
- Closing connections
- Releasing resources
- Saving state

### on_enable()

Called when the plugin is enabled. Use for:
- Starting background tasks
- Registering callbacks
- Activating features

### on_disable()

Called when the plugin is disabled. Use for:
- Stopping background tasks
- Unregistering callbacks
- Deactivating features

### execute()

Main plugin functionality. Override to implement your plugin's logic.

```python
def execute(self, *args, **kwargs) -> PluginResult:
    """Execute plugin functionality."""
    try:
        # Your logic here
        result = {"data": "value"}
        return PluginResult(success=True, data=result)
    except Exception as e:
        return PluginResult(success=False, error=str(e))
```

## PluginResult

The return type for plugin execution:

```python
from mc_agent_kit.plugin import PluginResult

# Success
result = PluginResult(success=True, data={"key": "value"})

# Error
result = PluginResult(success=False, error="Something went wrong")

# With duration
result = PluginResult(success=True, data=data, duration_ms=123.45)
```

## Configuration

Plugins can receive configuration from the plugin manager:

```python
def on_enable(self) -> None:
    api_key = self.get_config("api_key", "default_key")
    timeout = self.get_config("timeout", 30)
```

Set configuration before enabling:

```python
manager.set_plugin_config("my_plugin", {
    "api_key": "secret",
    "timeout": 60,
})
manager.enable_plugin("my_plugin")
```

## Dependencies

### Plugin Dependencies

Declare dependencies on other plugins:

```json
{
    "dependencies": [
        {"name": "base_plugin", "version": ">=1.0.0"}
    ]
}
```

### Python Package Dependencies

Check for required packages:

```python
from mc_agent_kit.plugin.dependency import check_python_package

def on_load(self) -> None:
    result = check_python_package("requests", ">=2.0.0")
    if not result.is_satisfied:
        raise RuntimeError(f"Missing dependency: {result.message}")
```

## Version Compatibility

Specify version constraints:

```json
{
    "metadata": {
        "min_core_version": "1.0.0",
        "max_core_version": "2.0.0",
        "supported_api_versions": [">=1.0.0", "<2.0.0"]
    }
}
```

### Version Range Formats

- Exact: `"1.0.0"`
- Greater than: `">1.0.0"`
- Greater or equal: `">=1.0.0"`
- Less than: `"<2.0.0"`
- Range: `">=1.0.0,<2.0.0"`
- Caret: `"^1.0.0"` (compatible with 1.x.x)
- Tilde: `"~1.0.0"` (compatible with 1.0.x)

## Sandbox Security

For untrusted plugins, use sandbox isolation:

```python
from mc_agent_kit.plugin import PluginSandbox, SandboxConfig

# Create restricted sandbox
config = SandboxConfig.restricted()
sandbox = PluginSandbox(config)

# Validate code before loading
code = open("plugin.py").read()
is_valid, issues = sandbox.validate_code(code)
if not is_valid:
    print(f"Security issues: {issues}")
```

### Sandbox Permissions

| Permission | Network | Subprocess | File Write |
|------------|---------|------------|------------|
| FULL | ✅ | ✅ | ✅ |
| STANDARD | ❌ | ❌ | ❌ |
| RESTRICTED | ❌ | ❌ | ❌ |

### Blocked Modules (Default)

- `os`, `subprocess`, `sys`, `builtins`
- `importlib`, `ctypes`, `multiprocessing`

## Capabilities

Plugins can declare capabilities they provide:

```json
{
    "provides": ["greeting", "translation", "weather"]
}
```

Query plugins by capability:

```python
plugins = manager.get_plugins_by_capability("greeting")
for plugin in plugins:
    result = manager.execute_plugin(plugin.name)
```

## Testing Plugins

### Unit Tests

```python
import pytest
from my_plugin import MyPlugin

def test_plugin_execute():
    plugin = MyPlugin()
    result = plugin.execute()
    assert result.success
    assert "data" in result.data
```

### Integration Tests

```python
from mc_agent_kit.plugin import PluginManager

def test_plugin_integration():
    manager = PluginManager()
    manager.load_plugin("./my_plugin")
    manager.enable_plugin("my_plugin")
    result = manager.execute_plugin("my_plugin")
    assert result.success
```

## Best Practices

1. **Keep plugins focused** - Each plugin should do one thing well
2. **Handle errors gracefully** - Return PluginResult with error messages
3. **Clean up resources** - Always implement on_unload()
4. **Document capabilities** - Clearly describe what your plugin provides
5. **Test thoroughly** - Include unit and integration tests
6. **Follow semver** - Use semantic versioning
7. **Declare dependencies** - List all required plugins and packages

## Example Plugins

See `examples/plugins/` for complete examples:

- `hello_plugin` - Basic hello world example
- More examples coming soon

## Publishing Plugins

1. Create a GitHub repository for your plugin
2. Include plugin.json and implementation
3. Add LICENSE and README.md
4. Share the repository URL with users

## Troubleshooting

### Plugin not loading

- Check plugin.json syntax
- Verify entry point file exists
- Check for import errors in logs

### Dependency errors

- Ensure all dependencies are installed
- Check version constraints
- Enable dependencies in correct order

### Sandbox violations

- Review blocked modules
- Adjust sandbox permissions if needed
- Avoid dangerous operations

## API Reference

For complete API documentation, see:
- `mc_agent_kit.plugin.base` - Base classes
- `mc_agent_kit.plugin.manager` - PluginManager
- `mc_agent_kit.plugin.sandbox` - Security sandbox
- `mc_agent_kit.plugin.version` - Version checking
- `mc_agent_kit.plugin.dependency` - Dependency management
