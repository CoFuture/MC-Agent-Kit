"""
贡献模块

包含非 MVP 核心的实验性功能，将在后续迭代中完善。

当前包含：
- completion: 代码补全（P2）
- performance: 性能优化（P2）
- plugin: 插件系统（P2）

这些模块不是当前开发重点，保留供后续迭代使用。
"""

# 导出子模块以保持向后兼容
from . import completion, performance, plugin

__all__ = [
    "completion",
    "performance",
    "plugin",
]