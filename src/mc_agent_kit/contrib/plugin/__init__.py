"""Plugin system for MC-Agent-Kit.

This module provides a plugin architecture that allows extending
the functionality of MC-Agent-Kit with third-party plugins.
"""

from .auto_install import (
    DependencyInfo,
    DependencyInstaller,
    DependencyInstallerConfig,
    DependencyType,
    InstallReport,
    InstallResult,
    InstallStatus,
    create_dependency_installer,
)
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
    DependencyType as PluginDependencyType,
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
from .loader import PluginLoader, PluginRegistry
from .manager import PluginManager
from .marketplace import (
    MarketplaceConfig,
    PluginCategory,
    PluginMarketInfo,
    PluginMarketplace,
    PluginStatus,
    SearchResult,
    create_marketplace,
)
from .performance import (
    MetricType,
    PerformanceAlert,
    PerformanceMetric,
    PerformanceMonitorConfig,
    PluginPerformanceMonitor,
    PluginStats,
    create_performance_monitor,
)
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
    # Marketplace
    "PluginMarketplace",
    "PluginMarketInfo",
    "PluginCategory",
    "PluginStatus",
    "MarketplaceConfig",
    "SearchResult",
    "create_marketplace",
    # Performance Monitor
    "PluginPerformanceMonitor",
    "PluginStats",
    "PerformanceMetric",
    "PerformanceAlert",
    "MetricType",
    "PerformanceMonitorConfig",
    "create_performance_monitor",
    # Auto Install
    "DependencyInstaller",
    "DependencyInfo",
    "DependencyInstallerConfig",
    "InstallReport",
    "InstallResult",
    "InstallStatus",
    "create_dependency_installer",
]
