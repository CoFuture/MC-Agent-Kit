"""Backwards compatibility for plugin module.

This module re-exports from contrib.plugin for backwards compatibility.
"""

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
    "PluginBase",
    "PluginMetadata",
    "PluginResult",
    "PluginState",
    "PluginPriority",
    "PluginInfo",
    "PluginRegistry",
    "PluginLoader",
    "PluginManager",
    "PluginManagerConfig",
]
