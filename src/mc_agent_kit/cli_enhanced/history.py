"""Command history management for MC-Agent-Kit CLI.

This module provides persistent command history with:
- Save/load to file
- Search capabilities
- Session management
- History navigation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import re


@dataclass
class HistoryEntry:
    """A single history entry."""
    command: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    working_dir: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "working_dir": self.working_dir,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        """Create from dictionary."""
        return cls(
            command=data.get("command", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            session_id=data.get("session_id", ""),
            working_dir=data.get("working_dir", ""),
            exit_code=data.get("exit_code", 0),
            duration_ms=data.get("duration_ms", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class HistoryConfig:
    """Configuration for command history."""
    history_file: str | None = None
    max_entries: int = 1000
    max_sessions: int = 10
    save_immediately: bool = True
    deduplicate: bool = True
    ignore_patterns: list[str] = field(default_factory=lambda: ["exit", "quit", "clear", "cls"])
    case_sensitive_search: bool = False


class CommandHistory:
    """Command history manager.

    Features:
    - Persistent storage to file
    - Search by keyword or regex
    - Session tracking
    - History deduplication
    - Navigation support
    """

    def __init__(self, config: HistoryConfig | None = None):
        """Initialize history manager.

        Args:
            config: History configuration
        """
        self.config = config or HistoryConfig()
        self._entries: list[HistoryEntry] = []
        self._current_session: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._dirty = False

        # Load existing history
        if self.config.history_file:
            self.load()

    def add(
        self,
        command: str,
        exit_code: int = 0,
        duration_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> HistoryEntry:
        """Add a command to history.

        Args:
            command: Command string
            exit_code: Exit code of the command
            duration_ms: Execution duration in milliseconds
            metadata: Additional metadata

        Returns:
            The created history entry
        """
        import os

        # Check ignore patterns
        cmd_stripped = command.strip()
        if cmd_stripped.lower() in [p.lower() for p in self.config.ignore_patterns]:
            # Still add but don't deduplicate
            pass

        # Deduplicate consecutive identical commands
        if self.config.deduplicate and self._entries:
            last = self._entries[-1]
            if last.command == cmd_stripped:
                return last

        entry = HistoryEntry(
            command=cmd_stripped,
            session_id=self._current_session,
            working_dir=os.getcwd(),
            exit_code=exit_code,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        self._entries.append(entry)
        self._dirty = True

        # Trim history if needed
        if len(self._entries) > self.config.max_entries:
            # Keep entries from recent sessions
            self._trim_history()

        # Save immediately if configured
        if self.config.save_immediately and self.config.history_file:
            self.save()

        return entry

    def _trim_history(self) -> None:
        """Trim history to max entries, keeping recent sessions intact."""
        if len(self._entries) <= self.config.max_entries:
            return

        # Get unique sessions sorted by time
        sessions: dict[str, list[HistoryEntry]] = {}
        for entry in reversed(self._entries):
            if entry.session_id not in sessions:
                sessions[entry.session_id] = []
            sessions[entry.session_id].append(entry)

        # Keep entries from most recent sessions
        kept_entries: list[HistoryEntry] = []
        for session_id in list(sessions.keys())[:self.config.max_sessions]:
            kept_entries.extend(sessions[session_id])

        # Sort by timestamp
        kept_entries.sort(key=lambda e: e.timestamp)

        # Trim if still too long
        if len(kept_entries) > self.config.max_entries:
            kept_entries = kept_entries[-self.config.max_entries:]

        self._entries = kept_entries

    def get(self, index: int) -> HistoryEntry | None:
        """Get entry by index.

        Args:
            index: Entry index (negative indices count from end)

        Returns:
            History entry or None
        """
        if -len(self._entries) <= index < len(self._entries):
            return self._entries[index]
        return None

    def get_last(self, n: int = 10) -> list[HistoryEntry]:
        """Get last n entries.

        Args:
            n: Number of entries to return

        Returns:
            List of history entries
        """
        return self._entries[-n:] if n > 0 else []

    def search(
        self,
        query: str,
        regex: bool = False,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[HistoryEntry]:
        """Search history.

        Args:
            query: Search query
            regex: Treat query as regex pattern
            session_id: Filter by session ID
            limit: Maximum results

        Returns:
            List of matching entries
        """
        results: list[HistoryEntry] = []

        if regex:
            try:
                pattern = re.compile(query, 0 if self.config.case_sensitive_search else re.IGNORECASE)
                matcher = lambda cmd: bool(pattern.search(cmd))
            except re.error:
                return results
        else:
            query_lower = query.lower() if not self.config.case_sensitive_search else query
            matcher = lambda cmd: query_lower in (cmd.lower() if not self.config.case_sensitive_search else cmd)

        for entry in reversed(self._entries):
            if session_id and entry.session_id != session_id:
                continue
            if matcher(entry.command):
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def get_sessions(self) -> list[str]:
        """Get list of session IDs.

        Returns:
            List of unique session IDs
        """
        sessions: list[str] = []
        for entry in self._entries:
            if entry.session_id and entry.session_id not in sessions:
                sessions.append(entry.session_id)
        return sessions

    def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with session statistics
        """
        entries = [e for e in self._entries if e.session_id == session_id]
        if not entries:
            return {}

        return {
            "session_id": session_id,
            "command_count": len(entries),
            "success_count": sum(1 for e in entries if e.exit_code == 0),
            "error_count": sum(1 for e in entries if e.exit_code != 0),
            "total_duration_ms": sum(e.duration_ms for e in entries),
            "first_command": entries[0].timestamp if entries else None,
            "last_command": entries[-1].timestamp if entries else None,
        }

    def clear(self, session_id: str | None = None) -> int:
        """Clear history.

        Args:
            session_id: Clear only this session, or all if None

        Returns:
            Number of entries removed
        """
        if session_id:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e.session_id != session_id]
            removed = before - len(self._entries)
        else:
            removed = len(self._entries)
            self._entries = []

        if removed > 0:
            self._dirty = True
            if self.config.save_immediately and self.config.history_file:
                self.save()

        return removed

    def save(self, path: str | None = None) -> bool:
        """Save history to file.

        Args:
            path: Optional path override

        Returns:
            True if saved successfully
        """
        save_path = Path(path or self.config.history_file or "")
        if not save_path:
            return False

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": 1,
                "sessions": self.get_sessions(),
                "entries": [e.to_dict() for e in self._entries],
            }

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            self._dirty = False
            return True
        except Exception:
            return False

    def load(self, path: str | None = None) -> bool:
        """Load history from file.

        Args:
            path: Optional path override

        Returns:
            True if loaded successfully
        """
        load_path = Path(path or self.config.history_file or "")
        if not load_path or not load_path.exists():
            return False

        try:
            with open(load_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("version") == 1:
                self._entries = [HistoryEntry.from_dict(e) for e in data.get("entries", [])]

            self._dirty = False
            return True
        except Exception:
            return False

    @property
    def count(self) -> int:
        """Get number of entries."""
        return len(self._entries)

    @property
    def is_dirty(self) -> bool:
        """Check if history has unsaved changes."""
        return self._dirty


def create_history(config: HistoryConfig | None = None) -> CommandHistory:
    """Create a history manager.

    Args:
        config: History configuration

    Returns:
        CommandHistory instance
    """
    return CommandHistory(config)