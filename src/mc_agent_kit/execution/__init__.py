"""
执行模块

提供代码执行、调试、热重载、性能分析和游戏内执行功能。
"""

from .debugger import (
    Breakpoint,
    BreakpointCondition,
    CallFrame,
    Debugger,
    DebuggerState,
    VariableWatch,
)
from .executor import (
    CodeExecutor,
    ExecutionConfig,
    ExecutionManager,
    ExecutionResult,
    ExecutionStatus,
)
from .game_executor import (
    GameExecutionConfig,
    GameExecutionResult,
    GameExecutor,
    GameExecutorState,
    GameSession,
)
from .hot_reload import (
    FileWatcher,
    HotReloader,
    ReloadConfig,
    ReloadResult,
    ReloadStatus,
)
from .performance import (
    MemoryMonitor,
    MemorySnapshot,
    PerformanceAnalyzer,
    PerformanceConfig,
    PerformanceReport,
    ProfilingResult,
    ProfilingStatus,
    Timer,
)

__all__ = [
    # Executor
    "CodeExecutor",
    "ExecutionConfig",
    "ExecutionManager",
    "ExecutionResult",
    "ExecutionStatus",
    # Debugger
    "Breakpoint",
    "BreakpointCondition",
    "CallFrame",
    "Debugger",
    "DebuggerState",
    "VariableWatch",
    # Hot Reload
    "FileWatcher",
    "HotReloader",
    "ReloadConfig",
    "ReloadResult",
    "ReloadStatus",
    # Performance
    "MemoryMonitor",
    "MemorySnapshot",
    "PerformanceAnalyzer",
    "PerformanceConfig",
    "PerformanceReport",
    "ProfilingResult",
    "ProfilingStatus",
    "Timer",
    # Game Executor
    "GameExecutionConfig",
    "GameExecutionResult",
    "GameExecutor",
    "GameExecutorState",
    "GameSession",
]
