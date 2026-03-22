"""Batch processing utilities for MC-Agent-Kit."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 100
    flush_interval: float = 5.0
    max_buffer_size: int = 1000


@dataclass
class BatchStats:
    """Statistics for batch processing."""
    total_items: int = 0
    total_batches: int = 0
    total_time: float = 0.0
    avg_batch_time: float = 0.0

    @property
    def items_per_second(self) -> float:
        """Calculate items processed per second."""
        return self.total_items / self.total_time if self.total_time > 0 else 0.0


class LogBatchProcessor:
    """Processor for batch log processing."""

    def __init__(self, config: BatchConfig | None = None):
        """Initialize the batch processor.

        Args:
            config: Optional configuration.
        """
        self._config = config or BatchConfig()
        self._buffer: list[Any] = []
        self._stats = BatchStats()
        self._last_flush = time.time()
        self._processor: Callable | None = None

    def set_processor(self, processor: Callable[[list[Any]], Any]) -> None:
        """Set the batch processor function.

        Args:
            processor: Function to process batches.
        """
        self._processor = processor

    def add(self, item: Any) -> None:
        """Add an item to the batch buffer.

        Args:
            item: Item to add.
        """
        self._buffer.append(item)
        self._stats.total_items += 1

        # Auto-flush if buffer is full
        if len(self._buffer) >= self._config.batch_size:
            self.flush()

        # Auto-flush based on time
        if time.time() - self._last_flush > self._config.flush_interval:
            self.flush()

    def flush(self) -> Any | None:
        """Flush the buffer and process items.

        Returns:
            Result from processor or None.
        """
        if not self._buffer:
            return None

        if self._processor:
            start = time.time()
            result = self._processor(self._buffer)
            elapsed = time.time() - start

            self._stats.total_batches += 1
            self._stats.total_time += elapsed
            self._stats.avg_batch_time = self._stats.total_time / self._stats.total_batches
        else:
            result = None

        self._buffer.clear()
        self._last_flush = time.time()
        return result

    @property
    def stats(self) -> BatchStats:
        """Get processing statistics."""
        return self._stats

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer.clear()


class LogAggregator:
    """Aggregator for log entries."""

    def __init__(self, max_entries: int = 1000):
        """Initialize the aggregator.

        Args:
            max_entries: Maximum entries to keep.
        """
        self._max_entries = max_entries
        self._entries: list[Any] = []
        self._counts: dict[str, int] = {}

    def add(self, entry: Any, category: str = "default") -> None:
        """Add a log entry.

        Args:
            entry: The log entry.
            category: Entry category.
        """
        self._entries.append(entry)
        self._counts[category] = self._counts.get(category, 0) + 1

        # Trim if over capacity
        while len(self._entries) > self._max_entries:
            self._entries.pop(0)

    def get_entries(self, limit: int = 100) -> list[Any]:
        """Get recent entries.

        Args:
            limit: Maximum entries to return.

        Returns:
            List of entries.
        """
        return self._entries[-limit:]

    def get_counts(self) -> dict[str, int]:
        """Get category counts.

        Returns:
            Dictionary of category counts.
        """
        return self._counts.copy()

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._counts.clear()
