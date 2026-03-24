"""Plugin loader for MC-Agent-Kit."""

from __future__ import annotations
import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginInfo,
    PluginMetadata,
    PluginState,
)


@dataclass
class PluginRegistryEntry:
    """Entry in the plugin registry."""
    info: PluginInfo
    instance: PluginBase | None = None


class PluginRegistry:
    """Registry for plugins."""

    def __init__(self):
        """Initialize the registry."""
        self._plugins: dict[str, PluginRegistryEntry] = {}
        self._by_capability: dict[str, list[str]] = {}

    def register(self, plugin: PluginBase) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin to register.
        """
        name = plugin.metadata.name
        self._plugins[name] = PluginRegistryEntry(
            info=PluginInfo(
                metadata=plugin.metadata,
                state=plugin.state,
            ),
            instance=plugin,
        )

        # Index by capability
        for cap in plugin.metadata.capabilities:
            if cap not in self._by_capability:
                self._by_capability[cap] = []
            self._by_capability[cap].append(name)

    def unregister(self, name: str) -> bool:
        """Unregister a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if unregistered.
        """
        if name not in self._plugins:
            return False

        entry = self._plugins[name]
        for cap in entry.info.metadata.capabilities:
            if cap in self._by_capability and name in self._by_capability[cap]:
                self._by_capability[cap].remove(name)

        del self._plugins[name]
        return True

    def get(self, name: str) -> PluginBase | None:
        """Get a plugin by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin instance or None.
        """
        entry = self._plugins.get(name)
        return entry.instance if entry else None

    def get_by_capability(self, capability: str) -> list[PluginBase]:
        """Get plugins by capability.

        Args:
            capability: Capability name.

        Returns:
            List of plugin instances.
        """
        names = self._by_capability.get(capability, [])
        return [self._plugins[name].instance for name in names if name in self._plugins]

    def list_all(self) -> list[PluginInfo]:
        """List all registered plugins.

        Returns:
            List of plugin info.
        """
        return [entry.info for entry in self._plugins.values()]

    def has_dependency_cycle(self, plugin_name: str, visited: set | None = None) -> bool:
        """Check for dependency cycles.

        Args:
            plugin_name: Plugin name to check.
            visited: Set of visited plugins.

        Returns:
            True if cycle detected.
        """
        if visited is None:
            visited = set()

        if plugin_name in visited:
            return True

        if plugin_name not in self._plugins:
            return False

        visited.add(plugin_name)
        entry = self._plugins[plugin_name]

        for dep in entry.info.metadata.dependencies:
            if self.has_dependency_cycle(dep, visited.copy()):
                return True

        return False


class PluginLoader:
    """Loader for plugins from files."""

    def __init__(self, registry: PluginRegistry | None = None):
        """Initialize the loader.

        Args:
            registry: Optional plugin registry.
        """
        self._registry = registry or PluginRegistry()

    def load_from_file(self, path: Path) -> PluginBase | None:
        """Load a plugin from a file.

        Args:
            path: Path to plugin file.

        Returns:
            Loaded plugin or None.
        """
        if not path.exists():
            return None

        spec = importlib.util.spec_from_file_location("plugin_module", path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for Plugin class
        plugin_class = getattr(module, "Plugin", None)
        if not plugin_class or not issubclass(plugin_class, PluginBase):
            return None

        # Create instance
        try:
            metadata = getattr(module, "METADATA", None)
            if not metadata:
                metadata = PluginMetadata(name=path.stem, version="1.0.0")

            plugin = plugin_class(metadata)
            plugin._state = PluginState.LOADED
            self._registry.register(plugin)
            return plugin
        except Exception:
            return None

    def load_from_directory(self, path: Path) -> list[PluginBase]:
        """Load all plugins from a directory.

        Args:
            path: Directory path.

        Returns:
            List of loaded plugins.
        """
        plugins = []
        if not path.is_dir():
            return plugins

        for file in path.glob("*.py"):
            if file.name.startswith("_"):
                continue
            plugin = self.load_from_file(file)
            if plugin:
                plugins.append(plugin)

        return plugins

    def load_from_manifest(self, manifest_path: Path) -> PluginBase | None:
        """Load a plugin from a manifest file.

        Args:
            manifest_path: Path to manifest.json.

        Returns:
            Loaded plugin or None.
        """
        import json

        if not manifest_path.exists():
            return None

        with open(manifest_path) as f:
            data = json.load(f)

        PluginMetadata(
            name=data.get("name", "unknown"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author"),
            dependencies=data.get("dependencies", []),
            capabilities=data.get("capabilities", []),
        )

        # Load main module
        main_file = manifest_path.parent / data.get("main", "plugin.py")
        return self.load_from_file(main_file)
