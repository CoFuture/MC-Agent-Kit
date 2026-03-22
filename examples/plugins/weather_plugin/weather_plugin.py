"""Weather API integration plugin.

This plugin demonstrates how to create a plugin that integrates
with external APIs to provide weather information.

Features:
- Get current weather for any location
- Get weather forecast
- Support multiple output formats (JSON, text)
- Configurable API endpoint
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any

# Import plugin base from mc_agent_kit
from mc_agent_kit.plugin import PluginBase, PluginMetadata, PluginResult

logger = logging.getLogger(__name__)


class WeatherPlugin(PluginBase):
    """Weather API integration plugin.

    Provides weather information through external API calls.

    Example:
        >>> plugin = WeatherPlugin()
        >>> plugin.set_metadata(metadata)
        >>> plugin.on_load()
        >>> result = plugin.execute("get_weather", location="Beijing")
        >>> print(result.data)
    """

    def __init__(self) -> None:
        """Initialize weather plugin."""
        self._api_url = "https://wttr.in"
        self._timeout = 10
        self._default_format = "json"

    def set_config(self, config: dict[str, Any]) -> None:
        """Set plugin configuration.

        Args:
            config: Configuration dictionary
        """
        self._api_url = config.get("api_url", self._api_url)
        self._timeout = config.get("timeout", self._timeout)
        self._default_format = config.get("default_format", self._default_format)

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info("Weather plugin loaded (API: %s)", self._api_url)

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        logger.info("Weather plugin enabled")

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        logger.info("Weather plugin disabled")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info("Weather plugin unloaded")

    def execute(self, action: str = "get_weather", **kwargs: Any) -> PluginResult:
        """Execute plugin action.

        Args:
            action: Action to perform:
                - "get_weather": Get current weather
                - "forecast": Get weather forecast
                - "help": Get help information
            **kwargs: Action-specific arguments:
                - location: Location name (required for most actions)
                - format: Output format ("json" or "text")
                - days: Number of forecast days (for forecast action)

        Returns:
            PluginResult with weather data
        """
        try:
            if action == "get_weather":
                return self._get_weather(kwargs)
            elif action == "forecast":
                return self._get_forecast(kwargs)
            elif action == "help":
                return self._get_help()
            else:
                return PluginResult(
                    success=False,
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            logger.error("Error executing weather action: %s", e)
            return PluginResult(success=False, error=str(e))

    def _get_weather(self, kwargs: dict[str, Any]) -> PluginResult:
        """Get current weather.

        Args:
            kwargs: Arguments including 'location' and optional 'format'

        Returns:
            PluginResult with weather data
        """
        location = kwargs.get("location")
        if not location:
            return PluginResult(
                success=False,
                error="Location is required. Example: location='Beijing'",
            )

        format_type = kwargs.get("format", self._default_format)

        try:
            if format_type == "json":
                url = f"{self._api_url}/{location}?format=j1"
            else:
                url = f"{self._api_url}/{location}?format=3"

            data = self._fetch_url(url)

            if format_type == "json":
                parsed = json.loads(data)
                current = parsed.get("current_condition", [{}])[0]

                result_data = {
                    "location": location,
                    "temperature": current.get("temp_C", "N/A"),
                    "description": current.get("weatherDesc", [{}])[0].get("value", "N/A"),
                    "humidity": current.get("humidity", "N/A"),
                    "wind_speed": current.get("windspeedKmph", "N/A"),
                    "wind_direction": current.get("winddir16Point", "N/A"),
                    "feels_like": current.get("FeelsLikeC", "N/A"),
                }
            else:
                result_data = {"raw": data.strip()}

            return PluginResult(
                success=True,
                data=result_data,
            )

        except urllib.error.URLError as e:
            return PluginResult(
                success=False,
                error=f"Failed to fetch weather: {e}",
            )
        except json.JSONDecodeError as e:
            return PluginResult(
                success=False,
                error=f"Failed to parse weather data: {e}",
            )

    def _get_forecast(self, kwargs: dict[str, Any]) -> PluginResult:
        """Get weather forecast.

        Args:
            kwargs: Arguments including 'location', optional 'days'

        Returns:
            PluginResult with forecast data
        """
        location = kwargs.get("location")
        if not location:
            return PluginResult(
                success=False,
                error="Location is required. Example: location='Beijing'",
            )

        days = min(kwargs.get("days", 3), 7)  # Max 7 days

        try:
            url = f"{self._api_url}/{location}?format=j1"
            data = self._fetch_url(url)
            parsed = json.loads(data)

            weather_data = parsed.get("weather", [])[:days]
            forecast = []

            for day in weather_data:
                forecast.append({
                    "date": day.get("date", "N/A"),
                    "max_temp": day.get("maxtempC", "N/A"),
                    "min_temp": day.get("mintempC", "N/A"),
                    "avg_temp": day.get("avgtempC", "N/A"),
                    "sunrise": day.get("astronomy", [{}])[0].get("sunrise", "N/A"),
                    "sunset": day.get("astronomy", [{}])[0].get("sunset", "N/A"),
                })

            return PluginResult(
                success=True,
                data={
                    "location": location,
                    "forecast": forecast,
                },
            )

        except Exception as e:
            return PluginResult(
                success=False,
                error=f"Failed to fetch forecast: {e}",
            )

    def _get_help(self) -> PluginResult:
        """Get help information.

        Returns:
            PluginResult with help text
        """
        return PluginResult(
            success=True,
            data={
                "actions": [
                    {
                        "name": "get_weather",
                        "description": "Get current weather for a location",
                        "params": {
                            "location": "Location name (required)",
                            "format": "Output format: 'json' or 'text' (default: json)",
                        },
                    },
                    {
                        "name": "forecast",
                        "description": "Get weather forecast for a location",
                        "params": {
                            "location": "Location name (required)",
                            "days": "Number of days (1-7, default: 3)",
                        },
                    },
                    {
                        "name": "help",
                        "description": "Show this help information",
                        "params": {},
                    },
                ],
                "example_usage": [
                    "execute('get_weather', location='Beijing')",
                    "execute('get_weather', location='Shanghai', format='text')",
                    "execute('forecast', location='Tokyo', days=5)",
                ],
            },
        )

    def _fetch_url(self, url: str) -> str:
        """Fetch URL content.

        Args:
            url: URL to fetch

        Returns:
            Response content as string
        """
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "MC-Agent-Kit/1.0"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            return response.read().decode("utf-8")


# Plugin entry point
def create_plugin() -> WeatherPlugin:
    """Create plugin instance.

    Returns:
        WeatherPlugin instance
    """
    return WeatherPlugin()