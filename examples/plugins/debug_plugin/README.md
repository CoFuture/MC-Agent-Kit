# Debug Assistant Plugin

A plugin that helps with debugging code and analyzing errors.

## Features

- Analyze error messages and provide suggestions
- Detect common code issues
- Parse and format tracebacks
- Provide fix suggestions with code examples

## Installation

1. Copy the `debug_plugin` directory to your plugins folder
2. The plugin will be automatically loaded by MC-Agent-Kit

## Usage

### Analyze an Error

```python
from mc_agent_kit.plugin import PluginManager

manager = PluginManager()
manager.load_plugin("path/to/debug_plugin")

result = manager.execute_plugin(
    "debug_plugin",
    "analyze_error",
    error="NameError: name 'my_var' is not defined",
)
print(result.data["suggestions"])
# Output: [
#     "Check if the variable is defined before use",
#     "Check for typos in variable name",
#     "Import required modules",
# ]
```

### Analyze Code for Issues

```python
code = '''
try:
    do_something()
except:
    pass
'''

result = manager.execute_plugin(
    "debug_plugin",
    "analyze_code",
    code=code,
)
for issue in result.data["issues"]:
    print(f"Line {issue['line']}: {issue['description']}")
# Output: Line 3: Bare 'except:' catches all exceptions including KeyboardInterrupt
```

### Format a Traceback

```python
result = manager.execute_plugin(
    "debug_plugin",
    "format_traceback",
    traceback='''Traceback (most recent call last):
  File "test.py", line 10, in <module>
    raise ValueError("Invalid input")
ValueError: Invalid input''',
)
print(result.data["parsed"])
```

### List Known Error Patterns

```python
result = manager.execute_plugin("debug_plugin", "list_patterns")
for pattern in result.data["patterns"]:
    print(f"- {pattern['error_type']}: {pattern['description']}")
```

## Supported Error Types

| Error Type | Description |
|------------|-------------|
| NameError | Variable or function not defined |
| TypeError | Incorrect argument type |
| KeyError | Key not found in dictionary |
| IndexError | List index out of range |
| AttributeError | Object missing attribute |
| ValueError | Invalid value |
| IndentationError | Incorrect indentation |
| SyntaxError | Syntax error in code |
| ImportError | Failed to import module |
| ZeroDivisionError | Division by zero |

## Code Analysis

The plugin detects the following code issues:

| Issue | Severity | Description |
|-------|----------|-------------|
| BareExcept | warning | Bare except catches all exceptions |
| BooleanComparison | info | Unnecessary comparison with True/False |
| PrintStatement | info | Potential debug code |
| EmptyFinally | info | Empty finally block |

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_suggestions` | int | `5` | Maximum suggestions to return |
| `include_code_examples` | bool | `true` | Include code fix examples |

## License

MIT License