"""Plugin marketplace for MC-Agent-Kit."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable
import time


class PluginCategory(Enum):
    """Plugin category."""
    UTILITY = "utility"
    CODE_GEN = "code_gen"
    DEBUG = "debug"
    ANALYSIS = "analysis"
    PERFORMANCE = "performance"
    OTHER = "other"


class PluginStatus(Enum):
    """Plugin status in marketplace."""
    AVAILABLE = "available"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update_available"
    DEPRECATED = "deprecated"


@dataclass
class PluginMarketInfo:
    """Plugin information in marketplace."""
    name: str
    version: str
    description: str = ""
    author: Optional[str] = None
    category: PluginCategory = PluginCategory.OTHER
    status: PluginStatus = PluginStatus.AVAILABLE
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None


@dataclass
class SearchResult:
    """Search result from marketplace."""
    plugin: PluginMarketInfo
    score: float = 0.0
    matched_tags: list[str] = field(default_factory=list)


@dataclass
class MarketplaceConfig:
    """Configuration for marketplace."""
    registry_url: str = "https://plugins.mc-agent-kit.dev"
    cache_ttl: float = 3600
    auto_update: bool = False


class PluginMarketplace:
    """Plugin marketplace for discovering and installing plugins."""

    def __init__(self, config: Optional[MarketplaceConfig] = None):
        """Initialize the marketplace.

        Args:
            config: Optional configuration.
        """
        self._config = config or MarketplaceConfig()
        self._plugins: dict[str, PluginMarketInfo] = {}
        self._last_sync: Optional[float] = None

        # Register some example plugins
        self._register_examples()

    def _register_examples(self) -> None:
        """Register example plugins."""
        examples = [
            PluginMarketInfo(
                name="hello-world",
                version="1.0.0",
                description="Hello World plugin example",
                category=PluginCategory.UTILITY,
                status=PluginStatus.AVAILABLE,
                tags=["example", "hello"],
            ),
            PluginMarketInfo(
                name="code-formatter",
                version="2.1.0",
                description="Code formatting plugin",
                category=PluginCategory.CODE_GEN,
                status=PluginStatus.AVAILABLE,
                tags=["format", "code"],
            ),
            PluginMarketInfo(
                name="debug-helper",
                version="1.5.0",
                description="Debugging helper plugin",
                category=PluginCategory.DEBUG,
                status=PluginStatus.AVAILABLE,
                tags=["debug", "logging"],
            ),
            PluginMarketInfo(
                name="performance-monitor",
                version="3.0.0",
                description="Performance monitoring plugin",
                category=PluginCategory.PERFORMANCE,
                status=PluginStatus.AVAILABLE,
                tags=["performance", "monitoring"],
            ),
        ]
        for plugin in examples:
            self._plugins[plugin.name] = plugin

    def search(
        self,
        query: str,
        category: Optional[PluginCategory] = None,
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search for plugins.

        Args:
            query: Search query.
            category: Optional category filter.
            tags: Optional tags filter.
            limit: Maximum results.

        Returns:
            List of search results.
        """
        results = []
        query_lower = query.lower()

        for name, plugin in self._plugins.items():
            # Filter by category
            if category and plugin.category != category:
                continue

            # Filter by tags
            if tags and not any(t in plugin.tags for t in tags):
                continue

            # Score by name/description match
            score = 0.0
            matched_tags = []

            if query_lower in plugin.name.lower():
                score += 10.0
            if query_lower in plugin.description.lower():
                score += 5.0
            for tag in plugin.tags:
                if query_lower in tag.lower():
                    score += 2.0
                    matched_tags.append(tag)

            if score > 0:
                results.append(SearchResult(
                    plugin=plugin,
                    score=score,
                    matched_tags=matched_tags,
                ))

        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def get_plugin(self, name: str) -> Optional[PluginMarketInfo]:
        """Get plugin by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin info or None.
        """
        return self._plugins.get(name)

    def list_all(self, category: Optional[PluginCategory] = None) -> list[PluginMarketInfo]:
        """List all plugins.

        Args:
            category: Optional category filter.

        Returns:
            List of plugin info.
        """
        if category:
            return [p for p in self._plugins.values() if p.category == category]
        return list(self._plugins.values())

    def install(self, name: str) -> bool:
        """Install a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if installed.
        """
        if name in self._plugins:
            self._plugins[name].status = PluginStatus.INSTALLED
            return True
        return False

    def uninstall(self, name: str) -> bool:
        """Uninstall a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if uninstalled.
        """
        if name in self._plugins:
            self._plugins[name].status = PluginStatus.AVAILABLE
            return True
        return False

    def update(self, name: str) -> bool:
        """Update a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if updated.
        """
        if name in self._plugins:
            self._plugins[name].status = PluginStatus.INSTALLED
            return True
        return False

    @property
    def stats(self) -> dict:
        """Get marketplace statistics."""
        return {
            "total_plugins": len(self._plugins),
            "installed": sum(1 for p in self._plugins.values() if p.status == PluginStatus.INSTALLED),
            "available": sum(1 for p in self._plugins.values() if p.status == PluginStatus.AVAILABLE),
        }