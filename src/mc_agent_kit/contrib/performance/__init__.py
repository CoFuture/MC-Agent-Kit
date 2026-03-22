"""Performance optimization module for MC-Agent-Kit."""

from mc_agent_kit.contrib.performance.batch import (
    LogAggregator,
    LogBatchProcessor,
)
from mc_agent_kit.contrib.performance.cache import (
    KnowledgeCache,
    LRUCache,
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
