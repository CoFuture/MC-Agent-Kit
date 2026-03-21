"""
日志捕获模块

负责启动 TCP 服务器捕获游戏日志，并解析存储。
提供实时日志分析和聚合功能。
"""

from .parser import LogEntry, LogLevel, LogParser
from .tcp_server import LogServer, start_log_server
from .analyzer import (
    Alert,
    AlertSeverity,
    ErrorPattern,
    LogAggregator,
    LogAnalyzer,
    LogStatistics,
    MatchResult,
    PatternCategory,
)

__all__ = [
    # Parser
    "LogParser",
    "LogEntry",
    "LogLevel",
    # TCP Server
    "LogServer",
    "start_log_server",
    # Analyzer
    "Alert",
    "AlertSeverity",
    "ErrorPattern",
    "LogAggregator",
    "LogAnalyzer",
    "LogStatistics",
    "MatchResult",
    "PatternCategory",
]
