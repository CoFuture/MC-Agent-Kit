"""Plugin base classes for MC-Agent-Kit."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginState(Enum):
    """Plugin lifecycle state."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginPriority(Enum):
    """Plugin priority for ordering."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str = ""
    author: str | None = None
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    priority: PluginPriority = PluginPriority.NORMAL
    min_version: str | None = None
    max_version: str | None = None


@dataclass
class PluginResult:
    """Result of plugin execution."""
    success: bool
    data: Any = None
    error: str | None = None
    message: str = ""


@dataclass
class PluginInfo:
    """Plugin information."""
    metadata: PluginMetadata
    state: PluginState
    path: str | None = None
    error: str | None = None


class PluginBase(ABC):
    """Abstract base class for plugins."""

    def __init__(self, metadata: PluginMetadata):
        """Initialize the plugin.

        Args:
            metadata: Plugin metadata.
        """
        self._metadata = metadata
        self._state = PluginState.UNLOADED

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self._metadata

    @property
    def state(self) -> PluginState:
        """Get plugin state."""
        return self._state

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin.

        Returns:
            True if successful.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> PluginResult:
        """Execute the plugin.

        Args:
            **kwargs: Execution parameters.

        Returns:
            Execution result.
        """
        pass

    def enable(self) -> bool:
        """Enable the plugin.

        Returns:
            True if successful.
        """
        if self._state == PluginState.LOADED:
            self._state = PluginState.ENABLED
            return True
        return False

    def disable(self) -> bool:
        """Disable the plugin.

        Returns:
            True if successful.
        """
        if self._state == PluginState.ENABLED:
            self._state = PluginState.DISABLED
            return True
        return False
