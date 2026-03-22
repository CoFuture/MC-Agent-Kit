# Weather Plugin

A plugin that integrates with weather APIs to provide weather information.

## Features

- Get current weather for any location
- Get multi-day weather forecasts
- Support JSON and text output formats
- Configurable API endpoint

## Installation

1. Copy the `weather_plugin` directory to your plugins folder
2. The plugin will be automatically loaded by MC-Agent-Kit

## Usage

### Get Current Weather

```python
from mc_agent_kit.plugin import PluginManager

manager = PluginManager()
manager.load_plugin("path/to/weather_plugin")

result = manager.execute_plugin(
    "weather_plugin",
    "get_weather",
    location="Beijing",
)
print(result.data)
# Output:
# {
#     "location": "Beijing",
#     "temperature": "25",
#     "description": "Partly cloudy",
#     "humidity": "65",
#     "wind_speed": "15",
#     "wind_direction": "NE",
#     "feels_like": "26"
# }
```

### Get Weather Forecast

```python
result = manager.execute_plugin(
    "weather_plugin",
    "forecast",
    location="Shanghai",
    days=3,
)
print(result.data)
# Output:
# {
#     "location": "Shanghai",
#     "forecast": [
#         {"date": "2026-03-22", "max_temp": "28", "min_temp": "18", ...},
#         {"date": "2026-03-23", "max_temp": "26", "min_temp": "17", ...},
#         {"date": "2026-03-24", "max_temp": "24", "min_temp": "16", ...}
#     ]
# }
```

### Text Format

```python
result = manager.execute_plugin(
    "weather_plugin",
    "get_weather",
    location="Tokyo",
    format="text",
)
print(result.data["raw"])
# Output: "Tokyo: ⛅ Partly cloudy, 22°C"
```

## Configuration

The plugin supports the following configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_url` | string | `https://wttr.in` | Weather API endpoint |
| `timeout` | int | `10` | Request timeout in seconds |
| `default_format` | string | `json` | Default output format |

Example:

```python
manager.set_plugin_config("weather_plugin", {
    "api_url": "https://wttr.in",
    "timeout": 15,
    "default_format": "json",
})
```

## Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `get_weather` | Get current weather | `location` (required), `format` |
| `forecast` | Get weather forecast | `location` (required), `days` (1-7) |
| `help` | Show help information | None |

## API

This plugin uses the [wttr.in](https://wttr.in) weather API, which is free and requires no API key.

## Error Handling

The plugin handles errors gracefully:

```python
result = manager.execute_plugin("weather_plugin", "get_weather")
# result.success = False
# result.error = "Location is required. Example: location='Beijing'"
```

## License

MIT License