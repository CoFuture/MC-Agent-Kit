"""Plugin hot reload functionality.

Integrates file watching with plugin management for automatic plugin reloading.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .manager import PluginManager

logger = logging.getLogger(__name__)


class HotReloadStatus(Enum):
    """Hot reload status."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class HotReloadConfig:
    """Hot reload configuration.

    Attributes:
        watch_interval_ms: Interval for checking file changes (ms)
        debounce_ms: Debounce time before reloading (ms)
        auto_enable: Auto-enable reloaded plugins
        notify_callback: Callback for reload notifications
        exclude_patterns: File patterns to exclude
    """

    watch_interval_ms: int = 500
    debounce_ms: int = 300
    auto_enable: bool = True
    notify_callback: Callable[[str, bool, str], None] | None = None
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["__pycache__", "*.pyc", ".git", "test_*"]
    )


@dataclass
class ReloadEvent:
    """Reload event record.

    Attributes:
        plugin_name: Name of the reloaded plugin
        file_path: Path to the changed file
        success: Whether reload succeeded
        error: Error message if failed
        timestamp: When the event occurred
        reload_time_ms: Time taken to reload
    """

    plugin_name: str
    file_path: str
    success: bool
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    reload_time_ms: float = 0.0


@dataclass
class WatchedPlugin:
    """Information about a watched plugin.

    Attributes:
        name: Plugin name
        path: Plugin path
        last_modified: Last modification timestamp
        checksum: File checksum
    """

    name: str
    path: Path
    last_modified: float = 0.0
    checksum: str = ""


class PluginHotReloader:
    """Plugin hot reload manager.

    Provides automatic file watching and plugin reloading.
    Integrates with PluginManager for lifecycle management.

    Example:
        >>> manager = PluginManager()
        >>> reloader = PluginHotReloader(manager)
        >>> reloader.watch_plugin("my_plugin", Path("/plugins/my_plugin"))
        >>> reloader.start()
        >>> # Plugins will auto-reload on file changes
        >>> reloader.stop()
    """

    def __init__(
        self,
        manager: PluginManager,
        config: HotReloadConfig | None = None,
    ) -> None:
        """Initialize plugin hot reloader.

        Args:
            manager: Plugin manager instance
            config: Hot reload configuration
        """
        self.manager = manager
        self.config = config or HotReloadConfig()
        self._watched: dict[str, WatchedPlugin] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._events: list[ReloadEvent] = []
        self._max_events = 100
        self._pending_changes: dict[str, float] = {}  # path -> first change time
        self._on_reload_callbacks: list[Callable[[ReloadEvent], None]] = []

    def watch_plugin(self, name: str, path: Path | str) -> None:
        """Add a plugin to watch.

        Args:
            name: Plugin name
            path: Path to plugin directory or file
        """
        path = Path(path)
        with self._lock:
            if name in self._watched:
                logger.warning("Plugin '%s' already being watched", name)
                return

            self._watched[name] = WatchedPlugin(
                name=name,
                path=path,
                last_modified=self._get_modified_time(path),
                checksum=self._compute_checksum(path),
            )
            logger.info("Watching plugin '%s' at %s", name, path)

    def unwatch_plugin(self, name: str) -> bool:
        """Remove a plugin from watch list.

        Args:
            name: Plugin name

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self._watched:
                del self._watched[name]
                logger.info("Stopped watching plugin '%s'", name)
                return True
            return False

    def watch_directory(self, directory: Path | str) -> None:
        """Watch a directory for plugins.

        Automatically discovers and watches all plugins in the directory.

        Args:
            directory: Directory path
        """
        directory = Path(directory)
        if not directory.exists():
            logger.warning("Directory does not exist: %s", directory)
            return

        for plugin_dir in directory.iterdir():
            if plugin_dir.is_dir():
                # Check for plugin.json
                manifest = plugin_dir / "plugin.json"
                if manifest.exists():
                    self.watch_plugin(plugin_dir.name, plugin_dir)

    def start(self) -> None:
        """Start watching for changes."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info("Plugin hot reload started")

    def stop(self) -> None:
        """Stop watching for changes."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Plugin hot reload stopped")

    def reload_plugin(self, name: str) -> ReloadEvent:
        """Force reload a plugin.

        Args:
            name: Plugin name

        Returns:
            ReloadEvent with result
        """
        start_time = time.time()
        plugin_info = self._watched.get(name)

        if not plugin_info:
            return ReloadEvent(
                plugin_name=name,
                file_path="",
                success=False,
                error=f"Plugin '{name}' not being watched",
            )

        try:
            # Use manager's reload method
            success = self.manager.reload_plugin(name)
            reload_time = (time.time() - start_time) * 1000

            event = ReloadEvent(
                plugin_name=name,
                file_path=str(plugin_info.path),
                success=success,
                reload_time_ms=reload_time,
            )

            self._record_event(event)

            # Update watched info
            with self._lock:
                if name in self._watched:
                    self._watched[name].last_modified = self._get_modified_time(
                        plugin_info.path
                    )
                    self._watched[name].checksum = self._compute_checksum(
                        plugin_info.path
                    )

            if success:
                logger.info("Reloaded plugin '%s' in %.2fms", name, reload_time)
            else:
                logger.warning("Failed to reload plugin '%s'", name)

            return event

        except Exception as e:
            reload_time = (time.time() - start_time) * 1000
            event = ReloadEvent(
                plugin_name=name,
                file_path=str(plugin_info.path),
                success=False,
                error=str(e),
                reload_time_ms=reload_time,
            )
            self._record_event(event)
            logger.error("Error reloading plugin '%s': %s", name, e)
            return event

    def get_status(self) -> dict[str, Any]:
        """Get hot reloader status.

        Returns:
            Status dictionary
        """
        with self._lock:
            return {
                "running": self._running,
                "watched_count": len(self._watched),
                "watched_plugins": list(self._watched.keys()),
                "recent_events": len(self._events),
            }

    def get_events(self, limit: int = 20) -> list[ReloadEvent]:
        """Get recent reload events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        return self._events[-limit:]

    def add_reload_callback(self, callback: Callable[[ReloadEvent], None]) -> None:
        """Add a callback for reload events.

        Args:
            callback: Function to call on reload
        """
        self._on_reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[[ReloadEvent], None]) -> None:
        """Remove a reload callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._on_reload_callbacks:
            self._on_reload_callbacks.remove(callback)

    def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            try:
                self._check_changes()
            except Exception as e:
                logger.error("Error in watch loop: %s", e)

            time.sleep(self.config.watch_interval_ms / 1000)

    def _check_changes(self) -> None:
        """Check for file changes."""
        current_time = time.time()
        changes_to_process: list[tuple[str, WatchedPlugin]] = []

        with self._lock:
            for name, plugin_info in self._watched.items():
                try:
                    new_modified = self._get_modified_time(plugin_info.path)
                    new_checksum = self._compute_checksum(plugin_info.path)

                    if new_checksum != plugin_info.checksum:
                        # File changed, add to pending
                        if name not in self._pending_changes:
                            self._pending_changes[name] = current_time
                        elif (
                            current_time - self._pending_changes[name]
                            >= self.config.debounce_ms / 1000
                        ):
                            # Debounce period passed, queue for reload
                            changes_to_process.append((name, plugin_info))
                            del self._pending_changes[name]

                except Exception as e:
                    logger.warning("Error checking plugin '%s': %s", name, e)

        # Process changes outside lock
        for name, plugin_info in changes_to_process:
            self._handle_change(name, plugin_info)

    def _handle_change(self, name: str, plugin_info: WatchedPlugin) -> None:
        """Handle a detected change.

        Args:
            name: Plugin name
            plugin_info: Plugin info
        """
        logger.info("Detected change in plugin '%s'", name)
        event = self.reload_plugin(name)

        # Notify callbacks
        for callback in self._on_reload_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error("Callback error: %s", e)

        # Notify via config callback
        if self.config.notify_callback:
            try:
                self.config.notify_callback(
                    name, event.success, event.error or "Reloaded successfully"
                )
            except Exception as e:
                logger.error("Notify callback error: %s", e)

    def _record_event(self, event: ReloadEvent) -> None:
        """Record a reload event.

        Args:
            event: Event to record
        """
        self._events.append(event)
        # Trim old events
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

    def _get_modified_time(self, path: Path) -> float:
        """Get last modified time for a path.

        Args:
            path: Path to check

        Returns:
            Last modified timestamp
        """
        if path.is_file():
            return path.stat().st_mtime
        elif path.is_dir():
            # Get the latest modification time in the directory
            max_mtime = path.stat().st_mtime
            for item in path.rglob("*"):
                if item.is_file() and not self._should_exclude(item):
                    try:
                        mtime = item.stat().st_mtime
                        if mtime > max_mtime:
                            max_mtime = mtime
                    except Exception:
                        pass
            return max_mtime
        return 0.0

    def _compute_checksum(self, path: Path) -> str:
        """Compute checksum for a path.

        Args:
            path: Path to check

        Returns:
            Checksum string
        """
        import hashlib

        hasher = hashlib.md5()

        if path.is_file():
            try:
                with open(path, "rb") as f:
                    hasher.update(f.read())
            except Exception:
                pass
        elif path.is_dir():
            # Hash all files in directory
            for item in sorted(path.rglob("*")):
                if item.is_file() and not self._should_exclude(item):
                    try:
                        with open(item, "rb") as f:
                            hasher.update(f.read())
                    except Exception:
                        pass

        return hasher.hexdigest()

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded.

        Args:
            path: Path to check

        Returns:
            True if should exclude
        """
        import fnmatch

        path_str = str(path)
        name = path.name

        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
        return False


# API functions for convenience

def create_hot_reloader(
    manager: PluginManager,
    watch_dirs: list[Path | str] | None = None,
    config: HotReloadConfig | None = None,
) -> PluginHotReloader:
    """Create and optionally start a hot reloader.

    Args:
        manager: Plugin manager
        watch_dirs: Optional directories to watch
        config: Hot reload configuration

    Returns:
        Configured PluginHotReloader
    """
    reloader = PluginHotReloader(manager, config)

    if watch_dirs:
        for directory in watch_dirs:
            reloader.watch_directory(directory)

    return reloader


def reload_all_plugins(manager: PluginManager) -> list[ReloadEvent]:
    """Reload all loaded plugins.

    Args:
        manager: Plugin manager

    Returns:
        List of reload events
    """
    events = []
    for plugin_info in manager.get_all_plugins():
        if plugin_info.is_loaded:
            # Use the manager's reload method
            success = manager.reload_plugin(plugin_info.name)
            events.append(
                ReloadEvent(
                    plugin_name=plugin_info.name,
                    file_path=str(plugin_info.plugin_path or ""),
                    success=success,
                )
            )
    return events