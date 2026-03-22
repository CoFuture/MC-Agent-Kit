"""Base classes and data structures for the plugin system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PluginState(Enum):
    """Plugin lifecycle state."""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginPriority(Enum):
    """Plugin execution priority."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class PluginMetadata:
    """Plugin metadata definition.

    Attributes:
        name: Unique plugin identifier
        version: Plugin version (semver)
        description: Brief description
        author: Plugin author
        priority: Execution priority
        dependencies: List of required plugin names
        provides: List of capabilities this plugin provides
        homepage: Optional homepage URL
        license: License identifier
    """

    name: str
    version: str
    description: str = ""
    author: str = ""
    priority: PluginPriority = PluginPriority.NORMAL
    dependencies: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    homepage: str | None = None
    license: str = "MIT"

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if not self.name:
            raise ValueError("Plugin name cannot be empty")
        if not self.version:
            raise ValueError("Plugin version cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "provides": self.provides,
            "homepage": self.homepage,
            "license": self.license,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginMetadata":
        """Create metadata from dictionary."""
        priority = data.get("priority", PluginPriority.NORMAL.value)
        if isinstance(priority, int):
            priority = PluginPriority(priority)
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            priority=priority,
            dependencies=data.get("dependencies", []),
            provides=data.get("provides", []),
            homepage=data.get("homepage"),
            license=data.get("license", "MIT"),
        )


@dataclass
class PluginResult:
    """Result of plugin execution.

    Attributes:
        success: Whether execution was successful
        data: Result data
        error: Error message if failed
        duration_ms: Execution time in milliseconds
    """

    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class PluginBase(ABC):
    """Abstract base class for all plugins.

    All plugins must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self) -> None:
        """Initialize plugin."""
        self._state: PluginState = PluginState.UNLOADED
        self._metadata: PluginMetadata | None = None
        self._config: dict[str, Any] = {}

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Raises:
            RuntimeError: If metadata not set
        """
        if self._metadata is None:
            raise RuntimeError("Plugin metadata not set")
        return self._metadata

    @property
    def state(self) -> PluginState:
        """Get current plugin state."""
        return self._state

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.metadata.name

    def set_config(self, config: dict[str, Any]) -> None:
        """Set plugin configuration."""
        self._config = config

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set_metadata(self, metadata: PluginMetadata) -> None:
        """Set plugin metadata."""
        self._metadata = metadata

    @abstractmethod
    def on_load(self) -> None:
        """Called when plugin is loaded.

        Override this method to perform initialization tasks
        such as loading resources, setting up connections, etc.
        """
        ...

    @abstractmethod
    def on_unload(self) -> None:
        """Called when plugin is unloaded.

        Override this method to perform cleanup tasks
        such as closing connections, releasing resources, etc.
        """
        ...

    def on_enable(self) -> None:
        """Called when plugin is enabled.

        Default implementation does nothing.
        Override to perform enable-specific tasks.
        """
        pass

    def on_disable(self) -> None:
        """Called when plugin is disabled.

        Default implementation does nothing.
        Override to perform disable-specific tasks.
        """
        pass

    def execute(self, *args: Any, **kwargs: Any) -> PluginResult:
        """Execute plugin functionality.

        Override this method to implement main plugin logic.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            PluginResult with execution outcome
        """
        return PluginResult(success=True, data=None)


class PluginInfo:
    """Information about a loaded plugin."""

    def __init__(
        self,
        metadata: PluginMetadata,
        plugin_path: Path | None = None,
        plugin_class: type[PluginBase] | None = None,
    ) -> None:
        """Initialize plugin info.

        Args:
            metadata: Plugin metadata
            plugin_path: Path to plugin file/directory
            plugin_class: Plugin class reference
        """
        self.metadata = metadata
        self.plugin_path = plugin_path
        self.plugin_class = plugin_class
        self.instance: PluginBase | None = None
        self.state = PluginState.UNLOADED
        self.load_time: float = 0.0
        self.error: str | None = None

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.metadata.name

    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.metadata.version

    @property
    def is_loaded(self) -> bool:
        """Check if plugin is loaded."""
        return self.state in (PluginState.LOADED, PluginState.ENABLED)

    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.state == PluginState.ENABLED

    def to_dict(self) -> dict[str, Any]:
        """Convert plugin info to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.metadata.description,
            "author": self.metadata.author,
            "state": self.state.value,
            "is_loaded": self.is_loaded,
            "is_enabled": self.is_enabled,
            "load_time": self.load_time,
            "error": self.error,
        }
