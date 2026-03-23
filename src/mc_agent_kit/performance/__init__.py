"""Backwards compatibility for performance module.

This module re-exports from contrib.performance for backwards compatibility.
"""

from mc_agent_kit.contrib.performance.batch import (
    BatchConfig,
    BatchStats,
    LogAggregator,
    LogBatchProcessor,
)
from mc_agent_kit.contrib.performance.cache import KnowledgeCache, LRUCache
from mc_agent_kit.contrib.performance.optimization import (
    CodeGenOptimizer,
    OptimizationStats,
    TemplatePool,
)
from .optimized import (
    CacheEntry,
    CacheMetrics,
    EnhancedLRUCache,
    LazyLoader,
    ParallelProcessor,
    PerformanceMonitor,
    SmartCache,
    get_parallel_processor,
    get_performance_monitor,
    get_smart_cache,
)

__all__ = [
    # Original exports
    "LRUCache",
    "KnowledgeCache",
    "LogBatchProcessor",
    "LogAggregator",
    "BatchConfig",
    "BatchStats",
    "CodeGenOptimizer",
    "TemplatePool",
    "OptimizationStats",
    # Optimized exports
    "CacheEntry",
    "CacheMetrics",
    "EnhancedLRUCache",
    "LazyLoader",
    "ParallelProcessor",
    "PerformanceMonitor",
    "SmartCache",
    "get_parallel_processor",
    "get_performance_monitor",
    "get_smart_cache",
]
