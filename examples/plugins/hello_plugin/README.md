# Hello Plugin Example

A simple example plugin demonstrating the MC-Agent-Kit plugin system.

## Features

- Basic plugin lifecycle hooks (load, unload, enable, disable)
- Simple greeting functionality
- Plugin metadata definition
- No external dependencies

## Installation

Copy this directory to your MC-Agent-Kit plugins folder:

```bash
# Example: Copy to default plugins directory
cp -r hello_plugin ~/.mc-agent-kit/plugins/
```

Or add the path to your plugin manager configuration:

```python
from mc_agent_kit.plugin import PluginManager

manager = PluginManager()
manager.add_plugin_directory("./examples/plugins/hello_plugin")
```

## Usage

### Enable the plugin

```python
from mc_agent_kit.plugin import PluginManager

manager = PluginManager()
manager.add_plugin_directory("./examples/plugins/hello_plugin")
manager.load_all_plugins()
manager.enable_plugin("hello_plugin")
```

### Execute the plugin

```python
# Basic usage
result = manager.execute_plugin("hello_plugin", name="Alice")
print(result.data["greeting"])
# Output: Hello, Alice! Welcome to MC-Agent-Kit!

# Default name
result = manager.execute_plugin("hello_plugin")
print(result.data["greeting"])
# Output: Hello, World! Welcome to MC-Agent-Kit!
```

### Get plugin info

```python
info = manager.get_plugin("hello_plugin")
if info:
    print(f"Name: {info.name}")
    print(f"Version: {info.version}")
    print(f"Description: {info.metadata.description}")
    print(f"State: {info.state}")
```

## Plugin Structure

```
hello_plugin/
├── plugin.json        # Plugin manifest (metadata)
├── hello_plugin.py    # Plugin implementation
└── README.md          # This file
```

### plugin.json

The manifest file contains plugin metadata:

```json
{
    "name": "hello_plugin",
    "version": "1.0.0",
    "description": "A simple hello world plugin example",
    "author": "MC-Agent-Kit Team",
    "entry": "hello_plugin.py",
    "dependencies": [],
    "provides": ["greeting"]
}
```

### hello_plugin.py

The main plugin file:

```python
from mc_agent_kit.plugin import PluginBase, PluginMetadata, PluginResult

class HelloPlugin(PluginBase):
    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass

    def execute(self, name: str = "World") -> PluginResult:
        """Execute plugin functionality."""
        return PluginResult(success=True, data={"greeting": f"Hello, {name}!"})
```

## Extending the Plugin

### Adding Configuration

```python
def on_enable(self) -> None:
    """Enable with custom greeting."""
    custom_greeting = self.get_config("greeting", "Hello")
    print(f"Using custom greeting: {custom_greeting}")

# Set config before enabling
manager.set_plugin_config("hello_plugin", {"greeting": "Hi"})
manager.enable_plugin("hello_plugin")
```

### Adding Dependencies

Update `plugin.json`:

```json
{
    "dependencies": [
        {"name": "another_plugin", "version": ">=1.0.0"}
    ]
}
```

### Using Sandbox

```python
from mc_agent_kit.plugin import SandboxConfig, PluginSandbox

# Create sandbox with restricted permissions
config = SandboxConfig.restricted()
sandbox = PluginSandbox(config)

# Validate plugin code before loading
is_valid, issues = sandbox.validate_code(plugin_code)
if not is_valid:
    print(f"Plugin code has issues: {issues}")
```

## License

MIT License - See LICENSE file for details.
