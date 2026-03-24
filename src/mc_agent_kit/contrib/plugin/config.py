"""Plugin configuration management for MC-Agent-Kit.

This module provides configuration management for plugins.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class PluginConfig:
    """Configuration for a single plugin."""
    enabled: bool = True
    settings: dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key.
            default: Default value if not found.
            
        Returns:
            Setting value or default.
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: Setting key.
            value: Setting value.
        """
        self.settings[key] = value
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "enabled": self.enabled,
            "settings": self.settings,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginConfig":
        """Create from dictionary.
        
        Args:
            data: Dictionary data.
            
        Returns:
            PluginConfig instance.
        """
        return cls(
            enabled=data.get("enabled", True),
            settings=data.get("settings", {}),
        )


@dataclass
class PluginConfigSchema:
    """Schema for plugin configuration."""
    key: str
    type: str  # "string", "int", "float", "bool", "list", "dict"
    default: Any = None
    description: str = ""
    required: bool = False
    choices: list[Any] | None = None
    min_value: float | None = None
    max_value: float | None = None
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate a value against the schema.
        
        Args:
            value: Value to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check required
        if self.required and value is None:
            return False, f"Required field '{self.key}' is missing"
        
        # Check type
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "bool": lambda v: isinstance(v, bool),
            "list": lambda v: isinstance(v, list),
            "dict": lambda v: isinstance(v, dict),
        }
        
        if self.type in type_validators:
            if not type_validators[self.type](value):
                return False, f"Field '{self.key}' must be of type {self.type}"
        
        # Check choices
        if self.choices and value not in self.choices:
            return False, f"Field '{self.key}' must be one of {self.choices}"
        
        # Check range
        if self.min_value is not None and isinstance(value, (int, float)):
            if value < self.min_value:
                return False, f"Field '{self.key}' must be >= {self.min_value}"
        
        if self.max_value is not None and isinstance(value, (int, float)):
            if value > self.max_value:
                return False, f"Field '{self.key}' must be <= {self.max_value}"
        
        return True, ""


class PluginConfigManager:
    """Manager for plugin configurations."""
    
    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the config manager.
        
        Args:
            config_dir: Directory for config files.
        """
        self._config_dir = config_dir or Path.home() / ".mc-agent-kit" / "plugins"
        self._configs: dict[str, PluginConfig] = {}
        self._schemas: dict[str, list[PluginConfigSchema]] = {}
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
    
    def register_schema(self, plugin_name: str, schemas: list[PluginConfigSchema]) -> None:
        """Register configuration schema for a plugin.
        
        Args:
            plugin_name: Plugin name.
            schemas: List of configuration schemas.
        """
        self._schemas[plugin_name] = schemas
    
    def get_config(self, plugin_name: str) -> PluginConfig:
        """Get configuration for a plugin.
        
        Args:
            plugin_name: Plugin name.
            
        Returns:
            Plugin configuration.
        """
        if plugin_name not in self._configs:
            self._configs[plugin_name] = self._load_config(plugin_name)
        return self._configs[plugin_name]
    
    def set_config(self, plugin_name: str, config: PluginConfig) -> None:
        """Set configuration for a plugin.
        
        Args:
            plugin_name: Plugin name.
            config: Plugin configuration.
        """
        self._configs[plugin_name] = config
        self._save_config(plugin_name, config)
    
    def update_setting(self, plugin_name: str, key: str, value: Any) -> bool:
        """Update a single setting.
        
        Args:
            plugin_name: Plugin name.
            key: Setting key.
            value: Setting value.
            
        Returns:
            True if successful.
        """
        # Validate against schema
        if plugin_name in self._schemas:
            for schema in self._schemas[plugin_name]:
                if schema.key == key:
                    is_valid, error = schema.validate(value)
                    if not is_valid:
                        return False
                    break
        
        config = self.get_config(plugin_name)
        config.set(key, value)
        self._save_config(plugin_name, config)
        return True
    
    def validate_config(self, plugin_name: str, config: PluginConfig) -> list[str]:
        """Validate configuration against schema.
        
        Args:
            plugin_name: Plugin name.
            config: Configuration to validate.
            
        Returns:
            List of validation errors.
        """
        errors = []
        
        if plugin_name not in self._schemas:
            return errors
        
        for schema in self._schemas[plugin_name]:
            value = config.get(schema.key, schema.default)
            is_valid, error = schema.validate(value)
            if not is_valid:
                errors.append(error)
        
        return errors
    
    def _load_config(self, plugin_name: str) -> PluginConfig:
        """Load configuration from file.
        
        Args:
            plugin_name: Plugin name.
            
        Returns:
            Plugin configuration.
        """
        config_file = self._config_dir / f"{plugin_name}.json"
        
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return PluginConfig.from_dict(data)
            except Exception:
                pass
        
        # Return default config with schema defaults
        config = PluginConfig()
        if plugin_name in self._schemas:
            for schema in self._schemas[plugin_name]:
                if schema.default is not None:
                    config.set(schema.key, schema.default)
        
        return config
    
    def _save_config(self, plugin_name: str, config: PluginConfig) -> None:
        """Save configuration to file.
        
        Args:
            plugin_name: Plugin name.
            config: Configuration to save.
        """
        config_file = self._config_dir / f"{plugin_name}.json"
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
    
    def list_configs(self) -> dict[str, PluginConfig]:
        """List all plugin configurations.
        
        Returns:
            Dictionary mapping plugin names to configurations.
        """
        # Load any config files that haven't been loaded yet
        for config_file in self._config_dir.glob("*.json"):
            plugin_name = config_file.stem
            if plugin_name not in self._configs:
                self._configs[plugin_name] = self._load_config(plugin_name)
        
        return dict(self._configs)
    
    def reset_config(self, plugin_name: str) -> None:
        """Reset configuration to defaults.
        
        Args:
            plugin_name: Plugin name.
        """
        config = PluginConfig()
        if plugin_name in self._schemas:
            for schema in self._schemas[plugin_name]:
                if schema.default is not None:
                    config.set(schema.key, schema.default)
        
        self._configs[plugin_name] = config
        self._save_config(plugin_name, config)
    
    def export_all(self) -> dict[str, Any]:
        """Export all configurations.
        
        Returns:
            Dictionary of all configurations.
        """
        return {
            name: config.to_dict()
            for name, config in self.list_configs().items()
        }
    
    def import_all(self, data: dict[str, Any]) -> int:
        """Import configurations.
        
        Args:
            data: Dictionary of configurations.
            
        Returns:
            Number of configurations imported.
        """
        count = 0
        for plugin_name, config_data in data.items():
            config = PluginConfig.from_dict(config_data)
            self._configs[plugin_name] = config
            self._save_config(plugin_name, config)
            count += 1
        
        return count