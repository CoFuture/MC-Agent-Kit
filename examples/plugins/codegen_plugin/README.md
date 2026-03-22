# Code Generation Plugin

A plugin that generates code snippets and templates.

## Features

- Generate Python classes, functions, dataclasses, and enums
- Generate unittest test files
- Generate common code snippets
- Configurable code style (docstrings, type hints)

## Installation

1. Copy the `codegen_plugin` directory to your plugins folder
2. The plugin will be automatically loaded by MC-Agent-Kit

## Usage

### Generate a Class

```python
from mc_agent_kit.plugin import PluginManager

manager = PluginManager()
manager.load_plugin("path/to/codegen_plugin")

result = manager.execute_plugin(
    "codegen_plugin",
    "generate",
    template="class",
    name="User",
    attributes=[
        {"name": "name", "type": "str"},
        {"name": "age", "type": "int", "default": 0},
    ],
    methods=[
        {"name": "greet", "params": [], "return": "str"},
    ],
)
print(result.data["code"])
```

Output:
```python
"""User class."""

class User:
    """User class."""

    def __init__(self, name: str, age: int = 0):
        """Initialize instance."""
        pass
        self.name = name
        self.age = age

    def greet(self) -> str:
        """greet method."""
        pass
```

### Generate a Function

```python
result = manager.execute_plugin(
    "codegen_plugin",
    "generate",
    template="function",
    name="calculate_sum",
    params=["a: int", "b: int"],
    return="int",
)
```

### Generate a Dataclass

```python
result = manager.execute_plugin(
    "codegen_plugin",
    "generate",
    template="dataclass",
    name="Person",
    fields=[
        {"name": "name", "type": "str"},
        {"name": "age", "type": "int", "default": 0},
    ],
)
```

### Generate a Unit Test

```python
result = manager.execute_plugin(
    "codegen_plugin",
    "generate",
    template="unittest",
    test_class="Calculator",
    methods=["test_add", "test_subtract"],
)
```

### List Templates

```python
result = manager.execute_plugin("codegen_plugin", "list")
for template in result.data["templates"]:
    print(f"- {template['name']}: {template['description']}")
```

### Generate Snippets

```python
# Generate a print debug statement
result = manager.execute_plugin(
    "codegen_plugin",
    "snippet",
    type="print",
    name="my_variable",
)
print(result.data["code"])
# Output: print(f"{my_variable} = {my_variable}")
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_style` | string | `pep8` | Code style |
| `add_docstrings` | bool | `true` | Add docstrings |
| `add_type_hints` | bool | `true` | Add type hints |

## Templates

| Template | Description |
|----------|-------------|
| `class` | Generate a Python class |
| `function` | Generate a Python function |
| `dataclass` | Generate a Python dataclass |
| `enum` | Generate a Python enum |
| `unittest` | Generate a unittest test class |

## Snippets

| Snippet | Description |
|---------|-------------|
| `print` | Debug print statement |
| `log_debug` | Logger debug statement |
| `log_info` | Logger info statement |
| `try_except` | Try-except block |
| `if_name_main` | if __name__ == "__main__" block |

## License

MIT License