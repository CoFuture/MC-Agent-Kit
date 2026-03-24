"""File monitoring plugin for MC-Agent-Kit.

Provides file system monitoring capabilities for detecting changes.
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginPriority,
    PluginState,
)
from mc_agent_kit.contrib.plugin.hooks import HookType, HookPriority, register_hook, trigger_hooks


class FileEventType(Enum):
    """File event type."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """File system event."""
    event_type: FileEventType
    path: str
    old_path: str | None = None  # For moved events
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_directory: bool = False
    size: int | None = None
    checksum: str | None = None


@dataclass
class WatchTarget:
    """A watched path configuration."""
    path: str
    recursive: bool = True
    patterns: list[str] = field(default_factory=list)  # File patterns to match
    ignore_patterns: list[str] = field(default_factory=list)  # Patterns to ignore
    callback: Callable[[FileEvent], None] | None = None


class FileMonitorPlugin(PluginBase):
    """Plugin for monitoring file system changes."""

    def __init__(self) -> None:
        """Initialize the file monitor plugin."""
        metadata = PluginMetadata(
            name="file-monitor",
            version="1.0.0",
            description="File system monitoring plugin",
            author="MC-Agent-Kit",
            capabilities=["monitoring", "filesystem", "watch"],
            priority=PluginPriority.NORMAL,
        )
        super().__init__(metadata)
        self._watches: dict[str, WatchTarget] = {}
        self._file_states: dict[str, dict[str, Any]] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._poll_interval = 1.0  # seconds
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if successful.
        """
        # Set state to LOADED
        self._state = PluginState.LOADED
        return True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self.stop_monitoring()

    def execute(self, **kwargs: Any) -> PluginResult:
        """Execute a monitoring operation.
        
        Args:
            **kwargs: Operation parameters.
                - operation: Operation to perform (watch, unwatch, list, start, stop)
                - path: Path to watch
                - recursive: Watch recursively (default True)
                - patterns: File patterns to match
                - callback: Callback function
        
        Returns:
            Execution result.
        """
        operation = kwargs.get("operation", "list")
        
        operations = {
            "watch": self._watch,
            "unwatch": self._unwatch,
            "list": self._list_watches,
            "start": self._start,
            "stop": self._stop,
            "status": self._status,
            "check": self._check_changes,
        }
        
        if operation not in operations:
            return PluginResult(
                success=False,
                error=f"Unknown operation: {operation}",
            )
        
        try:
            result = operations[operation](**kwargs)
            return PluginResult(success=True, data=result)
        except Exception as e:
            return PluginResult(success=False, error=str(e))

    def _watch(self, **kwargs: Any) -> dict[str, Any]:
        """Add a watch target.
        
        Returns:
            Watch info.
        """
        path = kwargs.get("path")
        if not path:
            raise ValueError("Path is required")
        
        path = str(Path(path).resolve())
        
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
        
        with self._lock:
            target = WatchTarget(
                path=path,
                recursive=kwargs.get("recursive", True),
                patterns=kwargs.get("patterns", []),
                ignore_patterns=kwargs.get("ignore_patterns", []),
                callback=kwargs.get("callback"),
            )
            self._watches[path] = target
            
            # Initialize file states
            self._scan_directory(target)
        
        return {
            "path": path,
            "recursive": target.recursive,
            "file_count": len([f for f in self._file_states if f.startswith(path)]),
        }

    def _unwatch(self, **kwargs: Any) -> dict[str, Any]:
        """Remove a watch target.
        
        Returns:
            Unwatch info.
        """
        path = kwargs.get("path")
        if not path:
            raise ValueError("Path is required")
        
        path = str(Path(path).resolve())
        
        with self._lock:
            if path in self._watches:
                del self._watches[path]
                # Clean up file states
                self._file_states = {
                    k: v for k, v in self._file_states.items()
                    if not k.startswith(path)
                }
                return {"removed": True, "path": path}
            return {"removed": False, "reason": "Not watching this path"}

    def _list_watches(self, **kwargs: Any) -> dict[str, Any]:
        """List all watches.
        
        Returns:
            List of watches.
        """
        with self._lock:
            watches = []
            for path, target in self._watches.items():
                file_count = len([f for f in self._file_states if f.startswith(path)])
                watches.append({
                    "path": path,
                    "recursive": target.recursive,
                    "patterns": target.patterns,
                    "file_count": file_count,
                })
            return {"watches": watches}

    def _start(self, **kwargs: Any) -> dict[str, Any]:
        """Start monitoring thread.
        
        Returns:
            Start status.
        """
        if self._running:
            return {"status": "already_running"}
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        return {"status": "started"}

    def _stop(self, **kwargs: Any) -> dict[str, Any]:
        """Stop monitoring thread.
        
        Returns:
            Stop status.
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        return {"status": "stopped"}

    def _status(self, **kwargs: Any) -> dict[str, Any]:
        """Get monitoring status.
        
        Returns:
            Status info.
        """
        with self._lock:
            return {
                "running": self._running,
                "watch_count": len(self._watches),
                "tracked_files": len(self._file_states),
                "poll_interval": self._poll_interval,
            }

    def _check_changes(self, **kwargs: Any) -> dict[str, Any]:
        """Check for changes manually.
        
        Returns:
            Changes detected.
        """
        events = self._detect_changes()
        return {"changes": len(events), "events": [self._event_to_dict(e) for e in events]}

    def _scan_directory(self, target: WatchTarget) -> None:
        """Scan directory and initialize file states.
        
        Args:
            target: Watch target.
        """
        path = Path(target.path)
        
        if path.is_file():
            self._record_file_state(str(path))
            return
        
        if target.recursive:
            iterator = path.rglob("*")
        else:
            iterator = path.glob("*")
        
        for item in iterator:
            if item.is_file():
                file_path = str(item)
                if self._matches_patterns(file_path, target):
                    self._record_file_state(file_path)

    def _record_file_state(self, file_path: str) -> None:
        """Record current state of a file.
        
        Args:
            file_path: Path to file.
        """
        try:
            stat = os.stat(file_path)
            self._file_states[file_path] = {
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "checksum": self._calculate_checksum(file_path),
            }
        except OSError:
            pass

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of a file.
        
        Args:
            file_path: Path to file.
            
        Returns:
            MD5 hex digest.
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except OSError:
            return ""

    def _matches_patterns(self, file_path: str, target: WatchTarget) -> bool:
        """Check if file matches watch patterns.
        
        Args:
            file_path: File path.
            target: Watch target.
            
        Returns:
            True if matches.
        """
        import fnmatch
        
        filename = os.path.basename(file_path)
        
        # Check ignore patterns
        for pattern in target.ignore_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return False
        
        # If no patterns, match all
        if not target.patterns:
            return True
        
        # Check include patterns
        for pattern in target.patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False

    def _detect_changes(self) -> list[FileEvent]:
        """Detect changes in watched directories.
        
        Returns:
            List of detected events.
        """
        events = []
        
        with self._lock:
            # Check for modified and deleted files
            for file_path, state in list(self._file_states.items()):
                if not os.path.exists(file_path):
                    events.append(FileEvent(
                        event_type=FileEventType.DELETED,
                        path=file_path,
                        size=state["size"],
                    ))
                    del self._file_states[file_path]
                    continue
                
                try:
                    stat = os.stat(file_path)
                    if stat.st_mtime > state["mtime"]:
                        new_checksum = self._calculate_checksum(file_path)
                        if new_checksum != state["checksum"]:
                            events.append(FileEvent(
                                event_type=FileEventType.MODIFIED,
                                path=file_path,
                                size=stat.st_size,
                                checksum=new_checksum,
                            ))
                            self._file_states[file_path] = {
                                "size": stat.st_size,
                                "mtime": stat.st_mtime,
                                "checksum": new_checksum,
                            }
                except OSError:
                    pass
            
            # Check for new files
            for target in self._watches.values():
                events.extend(self._find_new_files(target))
        
        return events

    def _find_new_files(self, target: WatchTarget) -> list[FileEvent]:
        """Find newly created files.
        
        Args:
            target: Watch target.
            
        Returns:
            List of creation events.
        """
        events = []
        path = Path(target.path)
        
        if path.is_file():
            if str(path) not in self._file_states:
                self._record_file_state(str(path))
                events.append(FileEvent(
                    event_type=FileEventType.CREATED,
                    path=str(path),
                ))
            return events
        
        if target.recursive:
            iterator = path.rglob("*")
        else:
            iterator = path.glob("*")
        
        for item in iterator:
            if item.is_file():
                file_path = str(item)
                if file_path not in self._file_states and self._matches_patterns(file_path, target):
                    self._record_file_state(file_path)
                    events.append(FileEvent(
                        event_type=FileEventType.CREATED,
                        path=file_path,
                    ))
        
        return events

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                events = self._detect_changes()
                for event in events:
                    self._handle_event(event)
            except Exception:
                pass
            
            time.sleep(self._poll_interval)

    def _handle_event(self, event: FileEvent) -> None:
        """Handle a file event.
        
        Args:
            event: File event to handle.
        """
        # Trigger hook
        trigger_hooks(HookType.ON_FILE_CHANGE, event)
        
        # Find matching watch and call callback
        with self._lock:
            for target in self._watches.values():
                if event.path.startswith(target.path):
                    if target.callback:
                        try:
                            target.callback(event)
                        except Exception:
                            pass
                    break

    def _event_to_dict(self, event: FileEvent) -> dict[str, Any]:
        """Convert event to dictionary.
        
        Args:
            event: File event.
            
        Returns:
            Dictionary representation.
        """
        return {
            "event_type": event.event_type.value,
            "path": event.path,
            "old_path": event.old_path,
            "timestamp": event.timestamp,
            "is_directory": event.is_directory,
            "size": event.size,
        }

    def watch(
        self,
        path: str,
        recursive: bool = True,
        patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        callback: Callable[[FileEvent], None] | None = None,
    ) -> dict[str, Any]:
        """Add a watch (convenience method).
        
        Args:
            path: Path to watch.
            recursive: Watch recursively.
            patterns: File patterns to match.
            ignore_patterns: Patterns to ignore.
            callback: Callback function.
            
        Returns:
            Watch info.
        """
        return self.execute(
            operation="watch",
            path=path,
            recursive=recursive,
            patterns=patterns or [],
            ignore_patterns=ignore_patterns or [],
            callback=callback,
        ).data

    def start_monitoring(self) -> dict[str, Any]:
        """Start monitoring (convenience method).
        
        Returns:
            Start status.
        """
        return self.execute(operation="start").data

    def stop_monitoring(self) -> dict[str, Any]:
        """Stop monitoring (convenience method).
        
        Returns:
            Stop status.
        """
        return self.execute(operation="stop").data