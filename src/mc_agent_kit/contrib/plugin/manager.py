"""Plugin manager for MC-Agent-Kit."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginInfo,
    PluginResult,
    PluginState,
)
from mc_agent_kit.contrib.plugin.loader import PluginLoader, PluginRegistry


@dataclass
class PluginManagerConfig:
    """Configuration for plugin manager."""
    plugin_dirs: list[Path] = field(default_factory=list)
    auto_load: bool = True
    auto_enable: bool = True
    scan_on_startup: bool = True


class PluginManager:
    """High-level plugin manager."""

    def __init__(self, config: PluginManagerConfig | None = None):
        """Initialize the manager.

        Args:
            config: Optional configuration.
        """
        self._config = config or PluginManagerConfig()
        self._registry = PluginRegistry()
        self._loader = PluginLoader(self._registry)
        self._plugins: dict[str, PluginBase] = {}

        if self._config.scan_on_startup:
            self.scan()

    def scan(self) -> list[PluginInfo]:
        """Scan plugin directories for plugins.

        Returns:
            List of found plugin info.
        """
        found = []
        for dir_path in self._config.plugin_dirs:
            if dir_path.exists():
                plugins = self._loader.load_from_directory(dir_path)
                for plugin in plugins:
                    found.append(PluginInfo(
                        metadata=plugin.metadata,
                        state=plugin.state,
                    ))
                    self._plugins[plugin.metadata.name] = plugin

                    if self._config.auto_enable:
                        plugin.enable()

        return found

    def load(self, path: Path) -> PluginInfo | None:
        """Load a plugin from a path.

        Args:
            path: Path to plugin file or directory.

        Returns:
            Plugin info or None.
        """
        if path.is_dir():
            manifest = path / "plugin.json"
            if manifest.exists():
                plugin = self._loader.load_from_manifest(manifest)
            else:
                return None
        else:
            plugin = self._loader.load_from_file(path)

        if plugin:
            self._plugins[plugin.metadata.name] = plugin
            return PluginInfo(
                metadata=plugin.metadata,
                state=plugin.state,
            )
        return None

    def unload(self, name: str) -> bool:
        """Unload a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if unloaded.
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]
        plugin.shutdown()
        del self._plugins[name]
        self._registry.unregister(name)
        return True

    def enable(self, name: str) -> bool:
        """Enable a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if enabled.
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]
        return plugin.enable()

    def disable(self, name: str) -> bool:
        """Disable a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if disabled.
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]
        return plugin.disable()

    def execute(self, name: str, **kwargs: Any) -> PluginResult | None:
        """Execute a plugin.

        Args:
            name: Plugin name.
            **kwargs: Execution parameters.

        Returns:
            Execution result or None.
        """
        if name not in self._plugins:
            return None

        plugin = self._plugins[name]
        if plugin.state != PluginState.ENABLED:
            return PluginResult(
                success=False,
                error=f"Plugin {name} is not enabled (state: {plugin.state.value})",
            )

        return plugin.execute(**kwargs)

    def get(self, name: str) -> PluginBase | None:
        """Get a plugin by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin instance or None.
        """
        return self._plugins.get(name)

    def list_all(self) -> list[PluginInfo]:
        """List all loaded plugins.

        Returns:
            List of plugin info.
        """
        return [
            PluginInfo(
                metadata=p.metadata,
                state=p.state,
            )
            for p in self._plugins.values()
        ]

    def shutdown(self) -> None:
        """Shutdown all plugins."""
        for plugin in list(self._plugins.values()):
            try:
                plugin.shutdown()
            except Exception:
                pass
        self._plugins.clear()
