"""Configuration manager for MC-Agent-Kit.

This module provides configuration management with:
- Multiple sources (file, environment, defaults)
- Hot reload support
- Type-safe access
- Change notifications
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from enum import Enum
import json
import os
import yaml


class ConfigSource(Enum):
    """Configuration source priority."""
    DEFAULT = 0
    FILE = 10
    ENVIRONMENT = 20
    RUNTIME = 30


@dataclass
class ConfigValue:
    """A configuration value with metadata."""
    key: str
    value: Any
    source: ConfigSource = ConfigSource.DEFAULT
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Convert key to dotted path format."""
        self.key = self.key.replace("-", "_").replace("/", ".")


@dataclass
class ManagerConfig:
    """Configuration for the manager."""
    config_file: str | None = None
    env_prefix: str = "MC_AGENT_"
    auto_reload: bool = False
    reload_interval: float = 1.0  # seconds
    deep_merge: bool = True
    case_sensitive: bool = False


class ConfigManager:
    """Configuration manager with hot reload support.

    Features:
    - Load from multiple sources
    - Environment variable override
    - Hot reload with file watching
    - Change notifications
    - Type coercion
    """

    def __init__(self, config: ManagerConfig | None = None):
        """Initialize config manager.

        Args:
            config: Manager configuration
        """
        self.config = config or ManagerConfig()
        self._values: dict[str, ConfigValue] = {}
        self._defaults: dict[str, Any] = {}
        self._callbacks: dict[str, list[Callable[[str, Any, Any], None]]] = {}
        self._last_modified: float = 0.0
        self._watching = False

        # Load initial config
        if self.config.config_file:
            self.load_file(self.config.config_file)

    def set_default(self, key: str, value: Any) -> None:
        """Set a default value.

        Args:
            key: Configuration key (dotted path)
            value: Default value
        """
        key = self._normalize_key(key)
        self._defaults[key] = value

        # Set if no value exists
        if key not in self._values:
            self._set_value(key, value, ConfigSource.DEFAULT)

    def get(
        self,
        key: str,
        default: Any = None,
        coerce_type: type | None = None,
    ) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (dotted path)
            default: Default value if not found
            coerce_type: Type to coerce value to

        Returns:
            Configuration value
        """
        key = self._normalize_key(key)

        # Check environment variable first (highest priority)
        env_key = self._get_env_key(key)
        env_value = os.environ.get(env_key)
        if env_value is not None:
            value = self._parse_env_value(env_value)
            if coerce_type:
                value = self._coerce(value, coerce_type)
            return value

        # Check loaded values
        if key in self._values:
            value = self._values[key].value
            if coerce_type:
                value = self._coerce(value, coerce_type)
            return value

        # Check defaults
        if key in self._defaults:
            value = self._defaults[key]
            if coerce_type:
                value = self._coerce(value, coerce_type)
            return value

        return default

    def set(
        self,
        key: str,
        value: Any,
        source: ConfigSource = ConfigSource.RUNTIME,
    ) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (dotted path)
            value: Value to set
            source: Value source
        """
        key = self._normalize_key(key)
        old_value = self.get(key)
        self._set_value(key, value, source)

        # Notify callbacks
        self._notify_change(key, old_value, value)

    def _set_value(self, key: str, value: Any, source: ConfigSource) -> None:
        """Internal method to set value."""
        self._values[key] = ConfigValue(
            key=key,
            value=value,
            source=source,
        )

    def _normalize_key(self, key: str) -> str:
        """Normalize configuration key."""
        if not self.config.case_sensitive:
            return key.lower().replace("-", "_").replace("/", ".")
        return key.replace("/", ".")

    def _get_env_key(self, key: str) -> str:
        """Get environment variable name for a key."""
        return self.config.env_prefix + key.upper().replace(".", "_")

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value.

        Supports:
        - JSON values
        - Boolean (true/false/yes/no/1/0)
        - Numbers
        - Strings
        """
        # Try JSON parse
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value

    def _coerce(self, value: Any, target_type: type) -> Any:
        """Coerce value to target type."""
        try:
            if target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ("true", "yes", "1")
                return bool(value)
            return target_type(value)
        except (ValueError, TypeError):
            return value

    def load_file(self, path: str | None = None) -> bool:
        """Load configuration from file.

        Supports JSON and YAML formats.

        Args:
            path: File path (uses config_file if not provided)

        Returns:
            True if loaded successfully
        """
        load_path = Path(path or self.config.config_file or "")
        if not load_path or not load_path.exists():
            return False

        try:
            with open(load_path, "r", encoding="utf-8") as f:
                if load_path.suffix in (".yaml", ".yml"):
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)

            # Flatten nested dict
            self._load_dict(data, "")

            # Update last modified
            self._last_modified = load_path.stat().st_mtime

            return True
        except Exception:
            return False

    def _load_dict(self, data: dict, prefix: str) -> None:
        """Load dictionary into flat config values.

        Args:
            data: Dictionary to load
            prefix: Key prefix
        """
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict) and self.config.deep_merge:
                self._load_dict(value, full_key)
            else:
                self._set_value(full_key, value, ConfigSource.FILE)

    def save_file(self, path: str | None = None) -> bool:
        """Save configuration to file.

        Args:
            path: File path (uses config_file if not provided)

        Returns:
            True if saved successfully
        """
        save_path = Path(path or self.config.config_file or "")
        if not save_path:
            return False

        try:
            # Build nested dict from flat values
            data: dict[str, Any] = {}
            for key, cv in self._values.items():
                parts = key.split(".")
                current = data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = cv.value

            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w", encoding="utf-8") as f:
                if save_path.suffix in (".yaml", ".yml"):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    json.dump(data, f, indent=2)

            return True
        except Exception:
            return False

    def reload(self) -> bool:
        """Reload configuration from file.

        Returns:
            True if reloaded successfully
        """
        if self.config.config_file:
            return self.load_file()
        return False

    def watch(self, callback: Callable[[], None] | None = None) -> None:
        """Start watching config file for changes.

        Args:
            callback: Optional callback on change
        """
        if not self.config.config_file or self._watching:
            return

        self._watching = True
        # Note: Actual file watching would require threading/async
        # This is a placeholder for the interface

    def unwatch(self) -> None:
        """Stop watching config file."""
        self._watching = False

    def on_change(
        self,
        key: str,
        callback: Callable[[str, Any, Any], None],
    ) -> None:
        """Register a change callback for a key.

        Args:
            key: Configuration key
            callback: Callback function (key, old_value, new_value)
        """
        key = self._normalize_key(key)
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)

    def _notify_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify callbacks of a change."""
        for callback in self._callbacks.get(key, []):
            try:
                callback(key, old_value, new_value)
            except Exception:
                pass

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values.

        Returns:
            Dictionary of all values
        """
        return {key: cv.value for key, cv in self._values.items()}

    def clear(self, source: ConfigSource | None = None) -> None:
        """Clear configuration values.

        Args:
            source: Only clear values from this source
        """
        if source is None:
            self._values.clear()
        else:
            self._values = {
                k: v for k, v in self._values.items()
                if v.source != source
            }

    def export_env(self) -> dict[str, str]:
        """Export configuration as environment variables.

        Returns:
            Dictionary of env var names to values
        """
        result: dict[str, str] = {}
        for key, cv in self._values.items():
            env_key = self._get_env_key(key)
            if isinstance(cv.value, (dict, list)):
                result[env_key] = json.dumps(cv.value)
            else:
                result[env_key] = str(cv.value)
        return result


def create_config_manager(config: ManagerConfig | None = None) -> ConfigManager:
    """Create a configuration manager.

    Args:
        config: Manager configuration

    Returns:
        ConfigManager instance
    """
    return ConfigManager(config)