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
from mc_agent_kit.contrib.plugin.marketplace import (
    PluginMarketplace,
    PluginMarketInfo,
    MarketplaceConfig,
    PluginCategory,
    PluginStatus,
)
from mc_agent_kit.contrib.plugin.hooks import (
    HookRegistry,
    HookInfo,
    HookResult,
    HookPriority,
    HookType,
    register_hook,
    trigger_hooks,
    get_hook_registry,
    hook_decorator,
)
from mc_agent_kit.contrib.plugin.config import (
    PluginConfig,
    PluginConfigManager,
    PluginConfigSchema,
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
    # Marketplace
    "PluginMarketplace",
    "PluginMarketInfo",
    "MarketplaceConfig",
    "PluginCategory",
    "PluginStatus",
    # Hooks
    "HookRegistry",
    "HookInfo",
    "HookResult",
    "HookPriority",
    "HookType",
    "register_hook",
    "trigger_hooks",
    "get_hook_registry",
    "hook_decorator",
    # Config
    "PluginConfig",
    "PluginConfigManager",
    "PluginConfigSchema",
]
