"""Plugin system for MC-Agent-Kit."""

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginInfo,
    PluginMetadata,
    PluginPriority,
    PluginResult,
    PluginState,
)
from mc_agent_kit.contrib.plugin.loader import (
    PluginLoader,
    PluginRegistry,
)
from mc_agent_kit.contrib.plugin.manager import (
    PluginManager,
    PluginManagerConfig,
)

__all__ = [
    # Base
    "PluginBase",
    "PluginMetadata",
    "PluginResult",
    "PluginState",
    "PluginPriority",
    "PluginInfo",
    # Loader
    "PluginRegistry",
    "PluginLoader",
    # Manager
    "PluginManager",
    "PluginManagerConfig",
]
