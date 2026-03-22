"""Backwards compatibility for performance module.

This module re-exports from contrib.performance for backwards compatibility.
"""

from mc_agent_kit.contrib.performance.cache import LRUCache, KnowledgeCache
from mc_agent_kit.contrib.performance.batch import LogBatchProcessor, LogAggregator, BatchConfig, BatchStats
from mc_agent_kit.contrib.performance.optimization import CodeGenOptimizer, TemplatePool, OptimizationStats

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