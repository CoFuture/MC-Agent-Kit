"""
端到端工作流模块

整合 MCP 闭环：查文档 → 创建项目 → 启动测试 → 诊断错误
"""

from .cache import (
    CacheEntry,
    WorkflowCache,
    clear_workflow_cache,
    get_workflow_cache,
)
from .cache_enhanced import (
    CacheEntryEnhanced,
    CacheMetrics,
    EnhancedCache,
    WarmupConfig,
    WarmupFunction,
    clear_enhanced_cache,
    get_enhanced_cache,
)
from .end_to_end import (
    EndToEndWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowStepStatus,
    create_workflow,
    run_development_cycle,
)
from .enhanced import (
    EnhancedWorkflow,
    ProgressCallback,
    ProgressInfo,
    RetryConfig,
    RetryPolicy,
    SkipCondition,
    WorkflowControl,
    WorkflowState,
    create_enhanced_workflow,
)

__all__ = [
    # End-to-end workflow
    "EndToEndWorkflow",
    "WorkflowConfig",
    "WorkflowResult",
    "WorkflowStep",
    "WorkflowStepResult",
    "WorkflowStepStatus",
    "create_workflow",
    "run_development_cycle",
    # Cache
    "WorkflowCache",
    "CacheEntry",
    "get_workflow_cache",
    "clear_workflow_cache",
    # Enhanced workflow
    "EnhancedWorkflow",
    "ProgressCallback",
    "ProgressInfo",
    "RetryConfig",
    "RetryPolicy",
    "SkipCondition",
    "WorkflowControl",
    "WorkflowState",
    "create_enhanced_workflow",
    # Enhanced cache
    "CacheEntryEnhanced",
    "CacheMetrics",
    "EnhancedCache",
    "WarmupConfig",
    "WarmupFunction",
    "clear_enhanced_cache",
    "get_enhanced_cache",
]
