"""
日志分析器模块

实现实时日志流处理、错误模式匹配和告警机制。
"""

import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue
from typing import Any, Callable

from .parser import LogEntry, LogLevel, LogParser


class AlertSeverity(Enum):
    """告警严重程度"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


class PatternCategory(Enum):
    """错误模式类别"""

    SYNTAX = "syntax"  # 语法错误
    RUNTIME = "runtime"  # 运行时错误
    API = "api"  # API 错误
    EVENT = "event"  # 事件错误
    CONFIG = "config"  # 配置错误
    NETWORK = "network"  # 网络错误
    MEMORY = "memory"  # 内存错误
    CUSTOM = "custom"  # 自定义错误


@dataclass
class ErrorPattern:
    """错误模式定义"""

    name: str  # 模式名称
    pattern: re.Pattern  # 正则表达式
    category: PatternCategory  # 错误类别
    severity: AlertSeverity  # 严重程度
    description: str = ""  # 描述
    suggestions: list[str] = field(default_factory=list)  # 修复建议
    tags: list[str] = field(default_factory=list)  # 标签


@dataclass
class MatchResult:
    """模式匹配结果"""

    pattern: ErrorPattern  # 匹配的模式
    match: re.Match  # 正则匹配对象
    log_entry: LogEntry  # 原始日志条目
    extracted_info: dict[str, str] = field(default_factory=dict)  # 提取的信息


@dataclass
class Alert:
    """告警信息"""

    severity: AlertSeverity  # 严重程度
    title: str  # 告警标题
    message: str  # 告警消息
    pattern: ErrorPattern | None = None  # 相关模式
    log_entry: LogEntry | None = None  # 相关日志
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    count: int = 1  # 出现次数


@dataclass
class LogStatistics:
    """日志统计"""

    total_logs: int = 0  # 总日志数
    by_level: dict[str, int] = field(default_factory=lambda: defaultdict(int))  # 按级别统计
    by_source: dict[str, int] = field(default_factory=lambda: defaultdict(int))  # 按来源统计
    error_count: int = 0  # 错误数
    warning_count: int = 0  # 警告数
    patterns_matched: dict[str, int] = field(default_factory=lambda: defaultdict(int))  # 模式匹配统计
    start_time: datetime = field(default_factory=datetime.now)  # 统计开始时间


class LogAnalyzer:
    """
    日志分析器。

    提供实时日志分析功能：
    - 流式处理日志
    - 错误模式匹配
    - 告警机制
    - 日志统计

    使用示例:
        analyzer = LogAnalyzer()
        analyzer.add_pattern(error_pattern)
        analyzer.set_alert_callback(on_alert)
        analyzer.start_streaming(log_queue)
    """

    # 内置错误模式
    BUILTIN_PATTERNS: list[ErrorPattern] = [
        ErrorPattern(
            name="SyntaxError",
            pattern=re.compile(r"SyntaxError:\s*(.+)"),
            category=PatternCategory.SYNTAX,
            severity=AlertSeverity.ERROR,
            description="Python 语法错误",
            suggestions=["检查语法", "确保括号和引号匹配"],
        ),
        ErrorPattern(
            name="NameError",
            pattern=re.compile(r"NameError:\s*name\s+'(\w+)'\s+is not defined"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR,
            description="变量未定义",
            suggestions=["检查变量名拼写", "确保变量已定义"],
        ),
        ErrorPattern(
            name="TypeError",
            pattern=re.compile(r"TypeError:\s*(.+)"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR,
            description="类型错误",
            suggestions=["检查参数类型", "确认操作支持该类型"],
        ),
        ErrorPattern(
            name="IndexError",
            pattern=re.compile(r"IndexError:\s*(.+)"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR,
            description="索引越界",
            suggestions=["检查索引范围", "确认列表/数组长度"],
        ),
        ErrorPattern(
            name="KeyError",
            pattern=re.compile(r"KeyError:\s*['\"]?(\w+)['\"]?"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR,
            description="键不存在",
            suggestions=["检查键是否存在", "使用 .get() 方法安全获取"],
        ),
        ErrorPattern(
            name="AttributeError",
            pattern=re.compile(r"AttributeError:\s*(.+)"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR,
            description="属性错误",
            suggestions=["检查属性名", "确认对象类型"],
        ),
        ErrorPattern(
            name="ImportError",
            pattern=re.compile(r"ImportError:\s*(.+)"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR,
            description="导入错误",
            suggestions=["检查模块是否存在", "确认安装了所需依赖"],
        ),
        ErrorPattern(
            name="ModAPIError",
            pattern=re.compile(r"(GetEngineType|GetConfig|CreateEngine|DestroyEngine).*failed"),
            category=PatternCategory.API,
            severity=AlertSeverity.ERROR,
            description="ModAPI 调用失败",
            suggestions=["检查 API 参数", "确认对象存在"],
        ),
        ErrorPattern(
            name="EventError",
            pattern=re.compile(r"(Add.+Event|Remove.+Event|ListenEvent).*error"),
            category=PatternCategory.EVENT,
            severity=AlertSeverity.WARNING,
            description="事件处理错误",
            suggestions=["检查事件名称", "确认回调函数正确"],
        ),
        ErrorPattern(
            name="ConfigError",
            pattern=re.compile(r"(config|Config).*error|invalid.*config"),
            category=PatternCategory.CONFIG,
            severity=AlertSeverity.ERROR,
            description="配置错误",
            suggestions=["检查配置文件格式", "确认配置项正确"],
        ),
        ErrorPattern(
            name="MemoryError",
            pattern=re.compile(r"MemoryError|OutOfMemory|out of memory"),
            category=PatternCategory.MEMORY,
            severity=AlertSeverity.CRITICAL,
            description="内存错误",
            suggestions=["减少内存使用", "检查内存泄漏"],
        ),
        ErrorPattern(
            name="NetworkError",
            pattern=re.compile(r"(ConnectionReset|ConnectionError|SocketError|timeout)"),
            category=PatternCategory.NETWORK,
            severity=AlertSeverity.WARNING,
            description="网络错误",
            suggestions=["检查网络连接", "确认服务器可用"],
        ),
    ]

    def __init__(self, use_builtin_patterns: bool = True):
        """
        初始化日志分析器。

        Args:
            use_builtin_patterns: 是否使用内置错误模式
        """
        self.parser = LogParser()
        self.patterns: list[ErrorPattern] = []
        self._alert_callbacks: list[Callable[[Alert], None]] = []
        self._log_callbacks: list[Callable[[LogEntry], None]] = []
        self._statistics = LogStatistics()
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._log_queue: Queue | None = None

        if use_builtin_patterns:
            self.patterns = list(self.BUILTIN_PATTERNS)

    def add_pattern(self, pattern: ErrorPattern) -> None:
        """添加错误模式"""
        with self._lock:
            self.patterns.append(pattern)

    def remove_pattern(self, name: str) -> bool:
        """
        移除错误模式。

        Args:
            name: 模式名称

        Returns:
            是否移除成功
        """
        with self._lock:
            for i, p in enumerate(self.patterns):
                if p.name == name:
                    self.patterns.pop(i)
                    return True
            return False

    def get_patterns(self) -> list[ErrorPattern]:
        """获取所有错误模式"""
        with self._lock:
            return list(self.patterns)

    def set_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """设置告警回调"""
        self._alert_callbacks.append(callback)

    def set_log_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """设置日志处理回调"""
        self._log_callbacks.append(callback)

    def start_streaming(self, log_queue: Queue) -> None:
        """
        开始流式处理日志。

        Args:
            log_queue: 日志队列
        """
        if self._running:
            return

        self._log_queue = log_queue
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()

    def stop_streaming(self) -> None:
        """停止流式处理"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def _process_loop(self) -> None:
        """处理循环"""
        while self._running and self._log_queue:
            try:
                log_text = self._log_queue.get(timeout=1.0)
                if log_text:
                    self.process_log(log_text)
            except Exception:
                continue

    def process_log(self, log_text: str) -> LogEntry:
        """
        处理单条日志。

        Args:
            log_text: 日志文本

        Returns:
            LogEntry: 解析后的日志条目
        """
        entry = self.parser.parse(log_text)

        with self._lock:
            # 更新统计
            self._statistics.total_logs += 1
            self._statistics.by_level[entry.level.value] += 1

            if entry.source:
                self._statistics.by_source[entry.source] += 1

            if entry.is_error:
                self._statistics.error_count += 1
            elif entry.level == LogLevel.WARNING:
                self._statistics.warning_count += 1

        # 匹配错误模式
        matches = self.match_patterns(entry)

        # 触发告警
        for match in matches:
            self._fire_alert(match)

        # 触发日志回调
        for callback in self._log_callbacks:
            try:
                callback(entry)
            except Exception:
                pass

        return entry

    def match_patterns(self, entry: LogEntry) -> list[MatchResult]:
        """
        匹配错误模式。

        Args:
            entry: 日志条目

        Returns:
            匹配结果列表
        """
        results = []

        with self._lock:
            patterns = list(self.patterns)

        for pattern in patterns:
            match = pattern.pattern.search(entry.raw)
            if match:
                # 提取信息
                extracted = {}
                if match.groups():
                    for i, group in enumerate(match.groups(), 1):
                        if group:
                            extracted[f"group_{i}"] = group

                results.append(
                    MatchResult(
                        pattern=pattern,
                        match=match,
                        log_entry=entry,
                        extracted_info=extracted,
                    )
                )

                # 更新统计
                with self._lock:
                    self._statistics.patterns_matched[pattern.name] += 1

        return results

    def _fire_alert(self, match: MatchResult) -> None:
        """触发告警"""
        alert = Alert(
            severity=match.pattern.severity,
            title=match.pattern.name,
            message=match.log_entry.message,
            pattern=match.pattern,
            log_entry=match.log_entry,
        )

        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass

    def analyze_batch(self, logs: list[str]) -> dict[str, Any]:
        """
        批量分析日志。

        Args:
            logs: 日志列表

        Returns:
            分析结果
        """
        entries = [self.process_log(log) for log in logs]
        errors = [e for e in entries if e.is_error]
        warnings = [e for e in entries if e.level == LogLevel.WARNING]

        # 按错误类型分组
        error_types: dict[str, list[LogEntry]] = defaultdict(list)
        for error in errors:
            matches = self.match_patterns(error)
            if matches:
                for match in matches:
                    error_types[match.pattern.name].append(error)
            else:
                error_types["Unknown"].append(error)

        return {
            "total": len(entries),
            "errors": len(errors),
            "warnings": len(warnings),
            "error_types": {k: len(v) for k, v in error_types.items()},
            "error_entries": errors[:20],  # 只返回前 20 个
            "warning_entries": warnings[:20],
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_logs": self._statistics.total_logs,
                "by_level": dict(self._statistics.by_level),
                "by_source": dict(self._statistics.by_source),
                "error_count": self._statistics.error_count,
                "warning_count": self._statistics.warning_count,
                "patterns_matched": dict(self._statistics.patterns_matched),
                "start_time": self._statistics.start_time.isoformat(),
                "uptime_seconds": (datetime.now() - self._statistics.start_time).total_seconds(),
            }

    def reset_statistics(self) -> None:
        """重置统计"""
        with self._lock:
            self._statistics = LogStatistics()

    def get_top_errors(self, limit: int = 10) -> list[tuple[str, int]]:
        """获取最常见的错误"""
        with self._lock:
            sorted_patterns = sorted(
                self._statistics.patterns_matched.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            return sorted_patterns[:limit]


class LogAggregator:
    """
    日志聚合器。

    聚合多个日志流，提供统一的查询接口。
    """

    def __init__(self, max_logs: int = 10000):
        """
        初始化日志聚合器。

        Args:
            max_logs: 最大保存日志数
        """
        self.max_logs = max_logs
        self._logs: list[LogEntry] = []
        self._lock = threading.Lock()
        self._analyzer = LogAnalyzer()

    def add_log(self, log_text: str) -> LogEntry:
        """添加日志"""
        entry = self._analyzer.process_log(log_text)

        with self._lock:
            self._logs.append(entry)
            if len(self._logs) > self.max_logs:
                self._logs = self._logs[-self.max_logs :]

        return entry

    def query(
        self,
        level: LogLevel | None = None,
        source: str | None = None,
        is_error: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """
        查询日志。

        Args:
            level: 日志级别过滤
            source: 来源过滤
            is_error: 是否错误过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            keyword: 关键词过滤
            limit: 返回数量限制

        Returns:
            匹配的日志条目列表
        """
        with self._lock:
            logs = list(self._logs)

        result = []
        for entry in logs:
            # 应用过滤条件
            if level is not None and entry.level != level:
                continue
            if source is not None and entry.source != source:
                continue
            if is_error is not None and entry.is_error != is_error:
                continue
            if start_time is not None and entry.timestamp and entry.timestamp < start_time:
                continue
            if end_time is not None and entry.timestamp and entry.timestamp > end_time:
                continue
            if keyword is not None and keyword.lower() not in entry.raw.lower():
                continue

            result.append(entry)
            if len(result) >= limit:
                break

        return result

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self._analyzer.get_statistics()

    def clear(self) -> None:
        """清空日志"""
        with self._lock:
            self._logs.clear()
        self._analyzer.reset_statistics()