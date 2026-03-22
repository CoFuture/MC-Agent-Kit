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
from .dependency import (
    Dependency,
    DependencyCheckResult,
    DependencyManager,
    DependencyReport,
    DependencyStatus,
    DependencyType,
)
from .loader import PluginLoader, PluginRegistry
from .manager import PluginManager
from .sandbox import (
    CodeValidator,
    PluginSandbox,
    RestrictedOperationError,
    SandboxConfig,
    SandboxContext,
    SandboxPermission,
    SandboxViolation,
)
from .version import (
    CompatibilityReport,
    Version,
    VersionChecker,
    VersionCompatibility,
    VersionRange,
    check_plugin_version,
)
from .hot_reload import (
    HotReloadConfig,
    HotReloadStatus,
    PluginHotReloader,
    ReloadEvent,
    WatchedPlugin,
    create_hot_reloader,
    reload_all_plugins,
)

__all__ = [
    # Base classes
    "PluginBase",
    "PluginInfo",
    "PluginMetadata",
    "PluginPriority",
    "PluginResult",
    "PluginState",
    # Loader and Registry
    "PluginLoader",
    "PluginRegistry",
    # Manager
    "PluginManager",
    # Sandbox
    "PluginSandbox",
    "SandboxConfig",
    "SandboxContext",
    "SandboxPermission",
    "SandboxViolation",
    "CodeValidator",
    "RestrictedOperationError",
    # Version
    "Version",
    "VersionRange",
    "VersionChecker",
    "VersionCompatibility",
    "CompatibilityReport",
    "check_plugin_version",
    # Dependency
    "Dependency",
    "DependencyType",
    "DependencyStatus",
    "DependencyCheckResult",
    "DependencyReport",
    "DependencyManager",
    # Hot Reload
    "PluginHotReloader",
    "HotReloadConfig",
    "HotReloadStatus",
    "ReloadEvent",
    "WatchedPlugin",
    "create_hot_reloader",
    "reload_all_plugins",
]