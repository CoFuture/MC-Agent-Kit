"""
日志解析器

解析游戏日志，提取结构化信息。
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class LogEntry:
    """解析后的日志条目"""
    raw: str
    level: LogLevel = LogLevel.UNKNOWN
    timestamp: datetime | None = None
    source: str | None = None
    message: str = ""
    is_error: bool = False
    is_python_traceback: bool = False


class LogParser:
    """
    日志解析器。

    解析 Minecraft 游戏日志，识别错误和 Python 异常。
    """

    # 常见日志格式模式
    PATTERNS = {
        # 标准格式: [时间][级别][来源] 消息
        "standard": re.compile(
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]'
            r'\[(\w+)\]'
            r'(?:\[([^\]]+)\])?\s*(.*)'
        ),
        # 简单格式: [级别] 消息
        "simple": re.compile(r'\[(\w+)\]\s*(.*)'),
        # Python traceback
        "traceback": re.compile(r'Traceback\s*\(most recent call last\)'),
        # Python 错误行
        "python_error": re.compile(r'(\w+Error|\w+Exception):\s*(.*)'),
    }

    # 错误关键词
    ERROR_KEYWORDS = [
        "error", "exception", "failed", "failure", "crash",
        "fatal", "critical", "错误", "异常", "崩溃"
    ]

    # 警告关键词
    WARNING_KEYWORDS = [
        "warning", "warn", "deprecated", "注意", "警告"
    ]

    def parse(self, log_text: str) -> LogEntry:
        """
        解析单条日志。

        Args:
            log_text: 原始日志文本

        Returns:
            LogEntry 对象
        """
        entry = LogEntry(raw=log_text.strip())

        # 检查 Python traceback
        if self.PATTERNS["traceback"].search(log_text):
            entry.is_python_traceback = True
            entry.is_error = True
            entry.level = LogLevel.ERROR
            entry.message = log_text
            return entry

        # 检查 Python 错误
        py_match = self.PATTERNS["python_error"].search(log_text)
        if py_match:
            entry.is_error = True
            entry.level = LogLevel.ERROR
            entry.message = py_match.group(0)
            return entry

        # 尝试匹配标准格式
        std_match = self.PATTERNS["standard"].search(log_text)
        if std_match:
            timestamp_str = std_match.group(1)
            level_str = std_match.group(2).upper()
            source = std_match.group(3)
            message = std_match.group(4)

            # 解析时间戳
            try:
                entry.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

            # 解析级别
            entry.level = self._parse_level(level_str)
            entry.source = source
            entry.message = message
            entry.is_error = entry.level in (LogLevel.ERROR, LogLevel.FATAL)

            return entry

        # 尝试匹配简单格式
        simple_match = self.PATTERNS["simple"].search(log_text)
        if simple_match:
            level_str = simple_match.group(1).upper()
            message = simple_match.group(2)

            entry.level = self._parse_level(level_str)
            entry.message = message
            entry.is_error = entry.level in (LogLevel.ERROR, LogLevel.FATAL)

            return entry

        # 无法匹配格式，使用关键词判断
        entry.message = log_text
        entry.level = self._detect_level_by_keyword(log_text)
        entry.is_error = entry.level in (LogLevel.ERROR, LogLevel.FATAL)

        return entry

    def _parse_level(self, level_str: str) -> LogLevel:
        """解析日志级别字符串"""
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "WARN": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "FATAL": LogLevel.FATAL,
            "CRITICAL": LogLevel.FATAL,
        }
        return level_map.get(level_str, LogLevel.UNKNOWN)

    def _detect_level_by_keyword(self, text: str) -> LogLevel:
        """通过关键词检测日志级别"""
        text_lower = text.lower()

        for keyword in self.ERROR_KEYWORDS:
            if keyword in text_lower:
                return LogLevel.ERROR

        for keyword in self.WARNING_KEYWORDS:
            if keyword in text_lower:
                return LogLevel.WARNING

        return LogLevel.INFO

    def parse_batch(self, logs: list[str]) -> list[LogEntry]:
        """
        批量解析日志。

        Args:
            logs: 原始日志文本列表

        Returns:
            LogEntry 列表
        """
        return [self.parse(log) for log in logs]

    def extract_errors(self, logs: list[str]) -> list[LogEntry]:
        """
        提取所有错误日志。

        Args:
            logs: 原始日志文本列表

        Returns:
            错误的 LogEntry 列表
        """
        entries = self.parse_batch(logs)
        return [e for e in entries if e.is_error]
