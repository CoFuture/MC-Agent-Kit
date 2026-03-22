"""Plugin manager for high-level plugin operations."""

import logging
from pathlib import Path
from typing import Any

from .base import PluginBase, PluginInfo, PluginResult, PluginState
from .loader import PluginLoader, PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """High-level plugin management.

    Provides a unified interface for:
    - Plugin discovery and loading
    - Plugin lifecycle management
    - Plugin execution
    - Configuration management
    """

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        """Initialize plugin manager.

        Args:
            registry: Optional plugin registry to use
        """
        self.registry = registry or PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self._configs: dict[str, dict[str, Any]] = {}

    def add_plugin_directory(self, path: Path | str) -> None:
        """Add a directory to search for plugins.

        Args:
            path: Directory path
        """
        self.loader.add_search_path(path)

    def remove_plugin_directory(self, path: Path | str) -> bool:
        """Remove a plugin search directory.

        Args:
            path: Directory path to remove

        Returns:
            True if removed, False otherwise
        """
        return self.loader.remove_search_path(path)

    def discover_plugins(self) -> list[Path]:
        """Discover available plugins.

        Returns:
            List of discovered plugin paths
        """
        return self.loader.discover_plugins()

    def load_plugin(self, path: Path | str) -> PluginInfo | None:
        """Load a plugin from path.

        Args:
            path: Path to plugin

        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        plugin_info = self.loader.load_from_path(path)
        if plugin_info:
            try:
                self.registry.register(plugin_info)
                return plugin_info
            except ValueError as e:
                logger.warning("Failed to register plugin: %s", e)
                return None
        return None

    def load_all_plugins(self) -> list[PluginInfo]:
        """Load all discovered plugins.

        Returns:
            List of loaded plugins
        """
        return self.loader.load_all()

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin.

        Args:
            name: Plugin name

        Returns:
            True if unloaded, False otherwise
        """
        plugin_info = self.registry.get(name)
        if not plugin_info:
            return False

        # Disable first if enabled
        if plugin_info.is_enabled:
            self.disable_plugin(name)

        return self.loader.unload(name)

    def enable_plugin(self, name: str) -> bool:
        """Enable a loaded plugin.

        Args:
            name: Plugin name

        Returns:
            True if enabled, False otherwise
        """
        plugin_info = self.registry.get(name)
        if not plugin_info:
            logger.warning("Plugin not found: %s", name)
            return False

        if plugin_info.state == PluginState.ENABLED:
            return True

        # Check dependencies
        for dep in plugin_info.metadata.dependencies:
            dep_info = self.registry.get(dep)
            if not dep_info or not dep_info.is_enabled:
                logger.warning(
                    "Dependency '%s' not enabled for plugin '%s'", dep, name
                )
                return False

        # Initialize if not loaded
        if plugin_info.instance is None and plugin_info.plugin_class:
            try:
                plugin_info.instance = plugin_info.plugin_class()
                plugin_info.instance.set_metadata(plugin_info.metadata)
            except Exception as e:
                logger.error("Failed to instantiate plugin %s: %s", name, e)
                plugin_info.state = PluginState.ERROR
                plugin_info.error = str(e)
                return False

        # Load and enable
        if plugin_info.instance:
            try:
                # Apply config if any
                if name in self._configs:
                    plugin_info.instance.set_config(self._configs[name])

                plugin_info.instance.on_load()
                plugin_info.instance.on_enable()
                plugin_info.state = PluginState.ENABLED
                return True
            except Exception as e:
                logger.error("Failed to enable plugin %s: %s", name, e)
                plugin_info.state = PluginState.ERROR
                plugin_info.error = str(e)
                return False

        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if disabled, False otherwise
        """
        plugin_info = self.registry.get(name)
        if not plugin_info:
            return False

        if plugin_info.state != PluginState.ENABLED:
            return True

        if plugin_info.instance:
            try:
                plugin_info.instance.on_disable()
            except Exception as e:
                logger.error("Error disabling plugin %s: %s", name, e)

        plugin_info.state = PluginState.DISABLED
        return True

    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin.

        Args:
            name: Plugin name

        Returns:
            True if reloaded, False otherwise
        """
        plugin_info = self.registry.get(name)
        if not plugin_info:
            return False

        # Save config
        config = self._configs.get(name, {})

        # Unload
        self.unload_plugin(name)

        # Reload from path
        if plugin_info.plugin_path:
            new_info = self.load_plugin(plugin_info.plugin_path)
            if new_info:
                # Restore config and enable
                self._configs[name] = config
                return self.enable_plugin(name)

        return False

    def execute_plugin(
        self, name: str, *args: Any, **kwargs: Any
    ) -> PluginResult | None:
        """Execute a plugin.

        Args:
            name: Plugin name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            PluginResult or None if plugin not found
        """
        plugin_info = self.registry.get(name)
        if not plugin_info:
            return None

        if not plugin_info.is_enabled:
            logger.warning("Plugin '%s' is not enabled", name)
            return PluginResult(
                success=False, error=f"Plugin '{name}' is not enabled"
            )

        if not plugin_info.instance:
            return PluginResult(
                success=False, error=f"Plugin '{name}' has no instance"
            )

        return plugin_info.instance.execute(*args, **kwargs)

    def get_plugin(self, name: str) -> PluginInfo | None:
        """Get plugin by name.

        Args:
            name: Plugin name

        Returns:
            PluginInfo or None
        """
        return self.registry.get(name)

    def get_plugin_instance(self, name: str) -> PluginBase | None:
        """Get plugin instance by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        plugin_info = self.registry.get(name)
        if plugin_info:
            return plugin_info.instance
        return None

    def get_all_plugins(self) -> list[PluginInfo]:
        """Get all registered plugins.

        Returns:
            List of all plugins
        """
        return self.registry.get_all()

    def get_enabled_plugins(self) -> list[PluginInfo]:
        """Get all enabled plugins.

        Returns:
            List of enabled plugins
        """
        return self.registry.get_enabled()

    def get_plugins_by_capability(self, capability: str) -> list[PluginInfo]:
        """Get plugins providing a capability.

        Args:
            capability: Capability name

        Returns:
            List of plugins with the capability
        """
        return self.registry.get_by_capability(capability)

    def set_plugin_config(self, name: str, config: dict[str, Any]) -> None:
        """Set plugin configuration.

        Args:
            name: Plugin name
            config: Configuration dictionary
        """
        self._configs[name] = config

        # Apply to running plugin
        plugin_info = self.registry.get(name)
        if plugin_info and plugin_info.instance:
            plugin_info.instance.set_config(config)

    def get_plugin_config(self, name: str) -> dict[str, Any]:
        """Get plugin configuration.

        Args:
            name: Plugin name

        Returns:
            Configuration dictionary
        """
        return self._configs.get(name, {})

    def get_plugin_status(self, name: str) -> dict[str, Any] | None:
        """Get plugin status.

        Args:
            name: Plugin name

        Returns:
            Status dictionary or None
        """
        plugin_info = self.registry.get(name)
        if plugin_info:
            return plugin_info.to_dict()
        return None

    def get_all_status(self) -> list[dict[str, Any]]:
        """Get status of all plugins.

        Returns:
            List of status dictionaries
        """
        return [p.to_dict() for p in self.registry.get_all()]

    def has_plugin(self, name: str) -> bool:
        """Check if plugin exists.

        Args:
            name: Plugin name

        Returns:
            True if exists, False otherwise
        """
        return self.registry.has_plugin(name)

    def has_capability(self, capability: str) -> bool:
        """Check if capability is available.

        Args:
            capability: Capability name

        Returns:
            True if available, False otherwise
        """
        return self.registry.has_capability(capability)

    def get_capabilities(self) -> list[str]:
        """Get all available capabilities.

        Returns:
            List of capability names
        """
        return self.registry.get_capabilities()

    def shutdown(self) -> None:
        """Shutdown all plugins."""
        for plugin_info in self.registry.get_all():
            if plugin_info.is_enabled:
                self.disable_plugin(plugin_info.name)
            if plugin_info.is_loaded:
                self.unload_plugin(plugin_info.name)