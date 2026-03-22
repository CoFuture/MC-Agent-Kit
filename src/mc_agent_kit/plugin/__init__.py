"""Backwards compatibility for plugin module.

This module re-exports from contrib.plugin for backwards compatibility.
"""

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginState,
    PluginPriority,
    PluginInfo,
)
from mc_agent_kit.contrib.plugin.loader import (
    PluginRegistry,
    PluginLoader,
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