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

__all__ = [
    "LRUCache",
    "KnowledgeCache",
    "LogBatchProcessor",
    "LogAggregator",
    "BatchConfig",
    "BatchStats",
    "CodeGenOptimizer",
    "TemplatePool",
    "OptimizationStats",
]
