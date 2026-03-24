"""Code generation optimization for MC-Agent-Kit."""

from __future__ import annotations
import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class OptimizationStats:
    """Statistics for optimization."""
    total_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class TemplatePool:
    """Pool for pre-loaded templates."""

    def __init__(self):
        """Initialize the template pool."""
        self._templates: dict[str, Any] = {}
        self._load_times: dict[str, float] = {}

    def register(self, name: str, template: Any) -> None:
        """Register a template.

        Args:
            name: Template name.
            template: Template object.
        """
        self._templates[name] = template
        self._load_times[name] = time.time()

    def get(self, name: str) -> Any | None:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            Template or None if not found.
        """
        return self._templates.get(name)

    def preload(self, templates: dict[str, Any]) -> None:
        """Pre-load multiple templates.

        Args:
            templates: Dictionary of name -> template.
        """
        for name, template in templates.items():
            self.register(name, template)

    @property
    def stats(self) -> dict:
        """Get pool statistics."""
        return {
            "total_templates": len(self._templates),
            "templates": list(self._templates.keys()),
        }


class CodeGenOptimizer:
    """Optimizer for code generation."""

    def __init__(self, cache_size: int = 100, cache_ttl: float = 3600):
        """Initialize the optimizer.

        Args:
            cache_size: Maximum cache entries.
            cache_ttl: Cache time-to-live in seconds.
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl
        self._stats = OptimizationStats()
        self._template_keys: dict[str, list[str]] = {}

    def _make_cache_key(self, template_name: str, params: dict) -> str:
        """Create a cache key from template name and params.

        Args:
            template_name: Template name.
            params: Template parameters.

        Returns:
            Cache key string.
        """
        param_str = str(sorted(params.items()))
        key = f"{template_name}:{param_str}"
        return hashlib.md5(key.encode()).hexdigest()

    def generate(
        self,
        template_name: str,
        generator: Callable[[dict], Any],
        params: dict | None = None,
        use_cache: bool = True,
    ) -> Any:
        """Generate code with optional caching.

        Args:
            template_name: Name of the template.
            generator: Generator function.
            params: Template parameters.
            use_cache: Whether to use caching.

        Returns:
            Generated code.
        """
        params = params or {}
        self._stats.total_calls += 1

        if use_cache:
            cache_key = self._make_cache_key(template_name, params)

            # Check cache
            if cache_key in self._cache:
                result, created_at = self._cache[cache_key]
                if time.time() - created_at < self._cache_ttl:
                    self._stats.cache_hits += 1
                    return result
                else:
                    del self._cache[cache_key]

            self._stats.cache_misses += 1

        # Generate
        start = time.time()
        result = generator(params)
        elapsed = time.time() - start

        self._stats.total_time += elapsed
        self._stats.avg_time = self._stats.total_time / self._stats.total_calls

        # Cache result
        if use_cache:
            cache_key = self._make_cache_key(template_name, params)
            self._cache[cache_key] = (result, time.time())

            # Track cache keys by template
            if template_name not in self._template_keys:
                self._template_keys[template_name] = []
            self._template_keys[template_name].append(cache_key)

            # Evict old entries
            while len(self._cache) > self._cache_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]

        return result

    def invalidate_cache(self, template_name: str | None = None) -> None:
        """Invalidate cache entries.

        Args:
            template_name: Optional template name to invalidate.
        """
        if template_name:
            # Invalidate by template name
            if template_name in self._template_keys:
                for key in self._template_keys[template_name]:
                    if key in self._cache:
                        del self._cache[key]
                del self._template_keys[template_name]
        else:
            # Clear all
            self._cache.clear()
            self._template_keys.clear()

    @property
    def stats(self) -> OptimizationStats:
        """Get optimization statistics."""
        return self._stats
