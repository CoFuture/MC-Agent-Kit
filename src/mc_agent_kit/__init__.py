"""
MC-Agent-Kit: AI Agent 辅助 Minecraft ModSDK 开发工具包

提供自动化游戏启动、日志捕获、知识库检索、Agent Skills 等功能。
"""

__version__ = "1.24.0"

# Import modules lazily to avoid circular imports
# Core modules are imported on-demand in CLI

__all__ = [
    # Core modules
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
    # Contrib modules
    "contrib",
    "completion",
    "performance",
    "plugin",
    # New modules
    "cli_enhanced",
    "config",
    "docs",
    "stats",
]


def __getattr__(name: str):
    """Lazy import modules to avoid circular imports."""
    if name in ("knowledge_base", "knowledge", "launcher", "log_capture",
                "skills", "scaffold", "retrieval", "generator", "autofix",
                "execution", "contrib", "cli_enhanced", "config", "docs", "stats"):
        return __import__(f"mc_agent_kit.{name}", fromlist=[name])
    if name in ("completion", "performance", "plugin"):
        return __import__(f"mc_agent_kit.contrib.{name}", fromlist=[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
