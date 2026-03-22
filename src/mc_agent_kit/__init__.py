"""
MC-Agent-Kit: AI Agent 辅助 Minecraft ModSDK 开发工具包

提供自动化游戏启动、日志捕获、知识库检索、Agent Skills 等功能。
"""

__version__ = "1.13.0"

from . import contrib, knowledge, knowledge_base, launcher, log_capture, retrieval, scaffold, skills

# 向后兼容：将 contrib 子模块暴露在顶层
from .contrib import completion, performance, plugin

# 其他核心模块
from . import autofix, execution, generator

__all__ = [
    # 核心模块
    "knowledge_base",
    "knowledge",
    "launcher",
    "log_capture",
    "skills",
    "scaffold",
    "retrieval",
    "generator",
    "autofix",
    "execution",
    # 贡献模块
    "contrib",
    "completion",
    "performance",
    "plugin",
]