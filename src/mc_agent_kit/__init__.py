"""
MC-Agent-Kit: AI Agent 辅助 Minecraft ModSDK 开发工具包

提供自动化游戏启动、日志捕获、知识库检索、Agent Skills 等功能。
"""

__version__ = "0.3.0"

from . import knowledge_base
from . import skills
from . import launcher
from . import log_capture

__all__ = [
    "knowledge_base",
    "skills",
    "launcher",
    "log_capture",
]