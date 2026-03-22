"""Plugin loader and registry for dynamic plugin management."""

import importlib.util
import json
import logging
import time
from pathlib import Path
from typing import Any

from .base import (
    PluginBase,
    PluginInfo,
    PluginMetadata,
    PluginState,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing loaded plugins.

    The registry provides:
    - Plugin registration and unregistration
    - Plugin lookup by name or capability
    - Dependency resolution
    - State management
    """

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self._plugins: dict[str, PluginInfo] = {}
        self._capabilities: dict[str, list[str]] = {}  # capability -> plugin names

    def register(self, plugin_info: PluginInfo) -> None:
        """Register a plugin.

        Args:
            plugin_info: Plugin information to register

        Raises:
            ValueError: If plugin with same name already exists
        """
        name = plugin_info.name
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' already registered")

        self._plugins[name] = plugin_info

        # Register capabilities
        for capability in plugin_info.metadata.provides:
            if capability not in self._capabilities:
                self._capabilities[capability] = []
            self._capabilities[capability].append(name)

        logger.debug("Registered plugin: %s", name)

    def unregister(self, name: str) -> bool:
        """Unregister a plugin.

        Args:
            name: Plugin name to unregister

        Returns:
            True if plugin was unregistered, False if not found
        """
        if name not in self._plugins:
            return False

        plugin_info = self._plugins[name]

        # Unregister capabilities
        for capability in plugin_info.metadata.provides:
            if capability in self._capabilities:
                try:
                    self._capabilities[capability].remove(name)
                    if not self._capabilities[capability]:
                        del self._capabilities[capability]
                except ValueError:
                    pass

        del self._plugins[name]
        logger.debug("Unregistered plugin: %s", name)
        return True

    def get(self, name: str) -> PluginInfo | None:
        """Get plugin by name.

        Args:
            name: Plugin name

        Returns:
            PluginInfo or None if not found
        """
        return self._plugins.get(name)

    def get_all(self) -> list[PluginInfo]:
        """Get all registered plugins.

        Returns:
            List of all PluginInfo objects
        """
        return list(self._plugins.values())

    def get_by_capability(self, capability: str) -> list[PluginInfo]:
        """Get plugins that provide a capability.

        Args:
            capability: Capability name

        Returns:
            List of plugins providing the capability
        """
        names = self._capabilities.get(capability, [])
        plugins = []
        for name in names:
            info = self._plugins.get(name)
            if info:
                plugins.append(info)
        return plugins

    def get_enabled(self) -> list[PluginInfo]:
        """Get all enabled plugins.

        Returns:
            List of enabled PluginInfo objects
        """
        return [p for p in self._plugins.values() if p.is_enabled]

    def get_by_state(self, state: PluginState) -> list[PluginInfo]:
        """Get plugins by state.

        Args:
            state: Plugin state to filter by

        Returns:
            List of plugins in the given state
        """
        return [p for p in self._plugins.values() if p.state == state]

    def has_plugin(self, name: str) -> bool:
        """Check if plugin is registered.

        Args:
            name: Plugin name

        Returns:
            True if registered, False otherwise
        """
        return name in self._plugins

    def has_capability(self, capability: str) -> bool:
        """Check if any plugin provides a capability.

        Args:
            capability: Capability name

        Returns:
            True if available, False otherwise
        """
        return capability in self._capabilities and len(self._capabilities[capability]) > 0

    def get_capabilities(self) -> list[str]:
        """Get all available capabilities.

        Returns:
            List of capability names
        """
        return list(self._capabilities.keys())

    def resolve_dependencies(self, name: str) -> list[str]:
        """Resolve plugin dependencies in load order.

        Args:
            name: Plugin name

        Returns:
            List of plugin names in dependency order

        Raises:
            ValueError: If dependency cannot be resolved
        """
        resolved: list[str] = []
        visiting: set[str] = set()

        def resolve(plugin_name: str) -> None:
            if plugin_name in resolved:
                return

            if plugin_name in visiting:
                raise ValueError(f"Circular dependency detected: {plugin_name}")

            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                raise ValueError(f"Plugin not found: {plugin_name}")

            visiting.add(plugin_name)

            for dep in plugin_info.metadata.dependencies:
                resolve(dep)

            visiting.remove(plugin_name)
            resolved.append(plugin_name)

        resolve(name)
        return resolved

    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()
        self._capabilities.clear()


class PluginLoader:
    """Plugin loader for discovering and loading plugins.

    Supports loading plugins from:
    - Python files (.py)
    - Python packages (directories with __init__.py)
    - JSON manifest files (plugin.json)
    """

    MANIFEST_FILE = "plugin.json"
    ENTRY_POINT = "plugin.py"

    def __init__(self, registry: PluginRegistry | None = None) -> None:
        """Initialize plugin loader.

        Args:
            registry: Optional plugin registry to use
        """
        self.registry = registry or PluginRegistry()
        self._search_paths: list[Path] = []

    def add_search_path(self, path: Path | str) -> None:
        """Add a search path for plugins.

        Args:
            path: Directory path to search for plugins
        """
        path = Path(path)
        if path not in self._search_paths:
            self._search_paths.append(path)
            logger.debug("Added search path: %s", path)

    def remove_search_path(self, path: Path | str) -> bool:
        """Remove a search path.

        Args:
            path: Path to remove

        Returns:
            True if removed, False if not found
        """
        path = Path(path)
        try:
            self._search_paths.remove(path)
            return True
        except ValueError:
            return False

    def get_search_paths(self) -> list[Path]:
        """Get all search paths.

        Returns:
            List of search paths
        """
        return list(self._search_paths)

    def discover_plugins(self) -> list[Path]:
        """Discover potential plugins in search paths.

        Returns:
            List of paths to discovered plugins
        """
        discovered: list[Path] = []

        for search_path in self._search_paths:
            if not search_path.exists():
                continue

            # Check for plugin directories (with plugin.json or plugin.py)
            for item in search_path.iterdir():
                if item.is_dir():
                    manifest = item / self.MANIFEST_FILE
                    entry = item / self.ENTRY_POINT
                    if manifest.exists() or entry.exists():
                        discovered.append(item)
                elif item.suffix == ".py":
                    discovered.append(item)

        return discovered

    def load_from_path(self, path: Path | str) -> PluginInfo | None:
        """Load a plugin from a path.

        Args:
            path: Path to plugin file or directory

        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        path = Path(path)

        if path.is_file():
            return self._load_from_file(path)
        elif path.is_dir():
            return self._load_from_directory(path)

        logger.warning("Invalid plugin path: %s", path)
        return None

    def _load_from_file(self, file_path: Path) -> PluginInfo | None:
        """Load plugin from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{file_path.stem}", file_path
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load spec from {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if plugin_class is None:
                logger.warning("No plugin class found in %s", file_path)
                return None

            # Create instance and get metadata
            instance = plugin_class()
            metadata = instance.metadata

            # Create plugin info
            plugin_info = PluginInfo(
                metadata=metadata,
                plugin_path=file_path,
                plugin_class=plugin_class,
            )
            plugin_info.instance = instance
            plugin_info.state = PluginState.LOADED
            plugin_info.load_time = time.time()

            return plugin_info

        except Exception as e:
            logger.error("Failed to load plugin from %s: %s", file_path, e)
            return None

    def _load_from_directory(self, dir_path: Path) -> PluginInfo | None:
        """Load plugin from a directory.

        Args:
            dir_path: Path to plugin directory

        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        manifest_path = dir_path / self.MANIFEST_FILE
        entry_path = dir_path / self.ENTRY_POINT

        # Try to load from manifest first
        if manifest_path.exists():
            return self._load_from_manifest(dir_path, manifest_path)

        # Fall back to entry point
        if entry_path.exists():
            return self._load_from_file(entry_path)

        logger.warning("No plugin.json or plugin.py found in %s", dir_path)
        return None

    def _load_from_manifest(
        self, dir_path: Path, manifest_path: Path
    ) -> PluginInfo | None:
        """Load plugin from manifest file.

        Args:
            dir_path: Plugin directory
            manifest_path: Path to plugin.json

        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)

            metadata = PluginMetadata.from_dict(data)

            # Load entry point if specified
            entry_file = data.get("entry", self.ENTRY_POINT)
            entry_path = dir_path / entry_file

            if entry_path.exists():
                plugin_info = self._load_from_file(entry_path)
                if plugin_info:
                    # Override metadata with manifest data
                    plugin_info.plugin_path = dir_path
                    if plugin_info.instance:
                        plugin_info.instance.set_metadata(metadata)
                    plugin_info.metadata = metadata
                return plugin_info

            # Create plugin info without instance
            return PluginInfo(
                metadata=metadata,
                plugin_path=dir_path,
            )

        except Exception as e:
            logger.error("Failed to load manifest %s: %s", manifest_path, e)
            return None

    def _find_plugin_class(self, module: Any) -> type[PluginBase] | None:
        """Find plugin class in a module.

        Args:
            module: Loaded Python module

        Returns:
            Plugin class if found, None otherwise
        """
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginBase)
                and attr is not PluginBase
            ):
                return attr

        return None

    def load_all(self) -> list[PluginInfo]:
        """Load all discovered plugins.

        Returns:
            List of successfully loaded plugins
        """
        loaded: list[PluginInfo] = []

        for plugin_path in self.discover_plugins():
            plugin_info = self.load_from_path(plugin_path)
            if plugin_info:
                try:
                    self.registry.register(plugin_info)
                    loaded.append(plugin_info)
                except ValueError as e:
                    logger.warning("Failed to register plugin: %s", e)

        return loaded

    def unload(self, name: str) -> bool:
        """Unload a plugin.

        Args:
            name: Plugin name to unload

        Returns:
            True if unloaded, False otherwise
        """
        plugin_info = self.registry.get(name)
        if not plugin_info:
            return False

        # Call on_unload if instance exists
        if plugin_info.instance:
            try:
                plugin_info.instance.on_unload()
            except Exception as e:
                logger.error("Error unloading plugin %s: %s", name, e)

        plugin_info.state = PluginState.UNLOADED
        plugin_info.instance = None

        return self.registry.unregister(name)
