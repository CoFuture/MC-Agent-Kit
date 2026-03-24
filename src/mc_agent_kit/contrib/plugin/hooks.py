"""Plugin hooks system for MC-Agent-Kit.

This module provides a hook system for plugins to extend functionality.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class HookPriority(Enum):
    """Hook priority for ordering."""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    MONITOR = 200  # Always runs last for monitoring/logging


@dataclass
class HookInfo:
    """Information about a registered hook."""
    name: str
    callback: Callable[..., Any]
    priority: HookPriority = HookPriority.NORMAL
    plugin_name: str | None = None
    description: str = ""


@dataclass
class HookResult:
    """Result from hook execution."""
    success: bool
    result: Any = None
    error: str | None = None
    hook_name: str = ""
    plugin_name: str | None = None


class HookType(Enum):
    """Predefined hook types for MC-Agent-Kit."""
    # Lifecycle hooks
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"
    
    # Knowledge base hooks
    ON_INDEX_BUILD = "on_index_build"
    ON_INDEX_UPDATE = "on_index_update"
    ON_SEARCH = "on_search"
    ON_SEARCH_RESULT = "on_search_result"
    
    # Code generation hooks
    ON_CODE_GENERATE = "on_code_generate"
    ON_CODE_GENERATED = "on_code_generated"
    ON_CODE_REVIEW = "on_code_review"
    
    # Project hooks
    ON_PROJECT_CREATE = "on_project_create"
    ON_PROJECT_LOAD = "on_project_load"
    ON_PROJECT_SAVE = "on_project_save"
    
    # File hooks
    ON_FILE_READ = "on_file_read"
    ON_FILE_WRITE = "on_file_write"
    ON_FILE_CHANGE = "on_file_change"
    
    # Execution hooks
    ON_EXECUTION_START = "on_execution_start"
    ON_EXECUTION_END = "on_execution_end"
    ON_EXECUTION_ERROR = "on_execution_error"
    
    # Debug hooks
    ON_ERROR = "on_error"
    ON_LOG = "on_log"
    ON_DIAGNOSE = "on_diagnose"


class HookRegistry:
    """Registry for hooks with priority-based execution."""

    def __init__(self) -> None:
        """Initialize the hook registry."""
        self._hooks: dict[str, list[HookInfo]] = defaultdict(list)

    def register(
        self,
        hook_type: str | HookType,
        callback: Callable[..., Any],
        priority: HookPriority = HookPriority.NORMAL,
        plugin_name: str | None = None,
        description: str = "",
    ) -> str:
        """Register a hook callback.

        Args:
            hook_type: Type of hook (e.g., HookType.ON_SEARCH or custom string).
            callback: Function to call when hook is triggered.
            priority: Priority for ordering.
            plugin_name: Name of plugin registering the hook.
            description: Description of what the hook does.

        Returns:
            Hook name for unregistration.
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type
        
        hook_info = HookInfo(
            name=hook_name,
            callback=callback,
            priority=priority,
            plugin_name=plugin_name,
            description=description,
        )
        
        self._hooks[hook_name].append(hook_info)
        # Sort by priority (higher priority runs first)
        self._hooks[hook_name].sort(key=lambda h: h.priority.value, reverse=True)
        
        return hook_name

    def unregister(self, hook_type: str | HookType, callback: Callable[..., Any]) -> bool:
        """Unregister a hook callback.

        Args:
            hook_type: Type of hook.
            callback: The callback to remove.

        Returns:
            True if the hook was removed.
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type
        
        if hook_name not in self._hooks:
            return False
        
        for i, hook in enumerate(self._hooks[hook_name]):
            if hook.callback == callback:
                self._hooks[hook_name].pop(i)
                return True
        
        return False

    def unregister_plugin(self, plugin_name: str) -> int:
        """Unregister all hooks from a plugin.

        Args:
            plugin_name: Name of the plugin.

        Returns:
            Number of hooks removed.
        """
        count = 0
        for hook_name in list(self._hooks.keys()):
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name]
                if h.plugin_name != plugin_name
            ]
            count += len([h for h in self._hooks[hook_name] if h.plugin_name == plugin_name])
        
        return count

    def trigger(
        self,
        hook_type: str | HookType,
        *args: Any,
        **kwargs: Any,
    ) -> list[HookResult]:
        """Trigger all hooks of a given type.

        Args:
            hook_type: Type of hook to trigger.
            *args: Positional arguments to pass to callbacks.
            **kwargs: Keyword arguments to pass to callbacks.

        Returns:
            List of results from each hook.
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type
        results = []
        
        for hook in self._hooks.get(hook_name, []):
            try:
                result = hook.callback(*args, **kwargs)
                results.append(HookResult(
                    success=True,
                    result=result,
                    hook_name=hook_name,
                    plugin_name=hook.plugin_name,
                ))
            except Exception as e:
                results.append(HookResult(
                    success=False,
                    error=str(e),
                    hook_name=hook_name,
                    plugin_name=hook.plugin_name,
                ))
        
        return results

    def trigger_until(
        self,
        hook_type: str | HookType,
        *args: Any,
        stop_on: Callable[[Any], bool] = lambda r: r is not None,
        **kwargs: Any,
    ) -> Any:
        """Trigger hooks until one returns a truthy value.

        Args:
            hook_type: Type of hook to trigger.
            *args: Positional arguments to pass to callbacks.
            stop_on: Function to determine if we should stop.
            **kwargs: Keyword arguments to pass to callbacks.

        Returns:
            First result that matches the stop condition.
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type
        
        for hook in self._hooks.get(hook_name, []):
            try:
                result = hook.callback(*args, **kwargs)
                if stop_on(result):
                    return result
            except Exception:
                continue
        
        return None

    def get_hooks(self, hook_type: str | HookType) -> list[HookInfo]:
        """Get all hooks of a given type.

        Args:
            hook_type: Type of hook.

        Returns:
            List of hook info.
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type
        return list(self._hooks.get(hook_name, []))

    def list_all(self) -> dict[str, list[HookInfo]]:
        """List all registered hooks.

        Returns:
            Dictionary mapping hook names to hook info lists.
        """
        return dict(self._hooks)


# Global hook registry
_global_registry: HookRegistry | None = None


def get_hook_registry() -> HookRegistry:
    """Get the global hook registry.

    Returns:
        The global HookRegistry instance.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = HookRegistry()
    return _global_registry


def register_hook(
    hook_type: str | HookType,
    callback: Callable[..., Any],
    priority: HookPriority = HookPriority.NORMAL,
    plugin_name: str | None = None,
    description: str = "",
) -> str:
    """Register a hook with the global registry.

    Args:
        hook_type: Type of hook.
        callback: Callback function.
        priority: Priority for ordering.
        plugin_name: Plugin name.
        description: Description.

    Returns:
        Hook name.
    """
    return get_hook_registry().register(
        hook_type, callback, priority, plugin_name, description
    )


def trigger_hooks(hook_type: str | HookType, *args: Any, **kwargs: Any) -> list[HookResult]:
    """Trigger hooks with the global registry.

    Args:
        hook_type: Type of hook.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        List of results.
    """
    return get_hook_registry().trigger(hook_type, *args, **kwargs)


def hook_decorator(
    hook_type: str | HookType,
    priority: HookPriority = HookPriority.NORMAL,
    plugin_name: str | None = None,
):
    """Decorator to register a function as a hook.

    Args:
        hook_type: Type of hook.
        priority: Priority for ordering.
        plugin_name: Plugin name.

    Returns:
        Decorator function.

    Example:
        @hook_decorator(HookType.ON_SEARCH)
        def my_search_hook(query, **kwargs):
            print(f"Search triggered: {query}")
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        register_hook(hook_type, func, priority, plugin_name, func.__doc__ or "")
        return func
    return decorator