"""Plugin system for MC-Agent-Kit.

This module provides a plugin architecture that allows extending
the functionality of MC-Agent-Kit with third-party plugins.
"""

from .base import (
    PluginBase,
    PluginInfo,
    PluginMetadata,
    PluginPriority,
    PluginResult,
    PluginState,
)
from .loader import PluginLoader, PluginRegistry
from .manager import PluginManager

__all__ = [
    "PluginBase",
    "PluginInfo",
    "PluginMetadata",
    "PluginPriority",
    "PluginResult",
    "PluginState",
    "PluginLoader",
    "PluginRegistry",
    "PluginManager",
]