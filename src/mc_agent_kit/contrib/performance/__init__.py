"""Performance optimization module for MC-Agent-Kit."""

from mc_agent_kit.contrib.performance.cache import (
    LRUCache,
    KnowledgeCache,
)
from mc_agent_kit.contrib.performance.batch import (
    LogBatchProcessor,
    LogAggregator,
)
from mc_agent_kit.contrib.performance.optimization import (
    CodeGenOptimizer,
    TemplatePool,
)

__all__ = [
    "LRUCache",
    "KnowledgeCache",
    "LogBatchProcessor",
    "LogAggregator",
    "CodeGenOptimizer",
    "TemplatePool",
]