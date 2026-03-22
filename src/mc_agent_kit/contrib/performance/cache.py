"""Cache utilities for MC-Agent-Kit."""

from dataclasses import dataclass, field
from typing import Any, Optional
from collections import OrderedDict
import time


@dataclass
class CacheEntry:
    """A cache entry."""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: Optional[float] = None
    hits: int = 0


class LRUCache:
    """Simple LRU cache implementation."""

    def __init__(self, max_size: int = 100, ttl: Optional[float] = None):
        """Initialize the LRU cache.

        Args:
            max_size: Maximum number of entries.
            ttl: Time-to-live in seconds.
        """
        self._max_size = max_size
        self._ttl = ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found/expired.
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # Check TTL
        if self._ttl and time.time() - entry.created_at > self._ttl:
            del self._cache[key]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hits += 1
        return entry.value

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        if key in self._cache:
            del self._cache[key]

        self._cache[key] = CacheEntry(key=key, value=value, ttl=self._ttl)

        # Evict oldest if over capacity
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key.

        Returns:
            True if deleted, False if not found.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        return key in self._cache


class KnowledgeCache:
    """Cache for knowledge base queries."""

    def __init__(self, max_size: int = 1000, ttl: float = 3600):
        """Initialize the knowledge cache.

        Args:
            max_size: Maximum number of entries.
            ttl: Time-to-live in seconds (default: 1 hour).
        """
        self._cache = LRUCache(max_size=max_size, ttl=ttl)
        self._hits = 0
        self._misses = 0

    def get(self, query: str) -> Optional[Any]:
        """Get cached result for a query.

        Args:
            query: The search query.

        Returns:
            Cached result or None.
        """
        result = self._cache.get(query)
        if result is not None:
            self._hits += 1
        else:
            self._misses += 1
        return result

    def set(self, query: str, result: Any) -> None:
        """Cache a query result.

        Args:
            query: The search query.
            result: The result to cache.
        """
        self._cache.set(query, result)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "size": len(self._cache),
        }