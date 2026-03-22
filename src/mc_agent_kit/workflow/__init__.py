"""
端到端工作流模块

整合 MCP 闭环：查文档 → 创建项目 → 启动测试 → 诊断错误
"""

from .end_to_end import (
    EndToEndWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepResult,
    create_workflow,
    run_development_cycle,
)

__all__ = [
    "EndToEndWorkflow",
    "WorkflowConfig",
    "WorkflowResult",
    "WorkflowStep",
    "WorkflowStepResult",
    "create_workflow",
    "run_development_cycle",
]