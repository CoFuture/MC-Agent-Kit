"""
日志分析增强模块

提供结构化日志解析、错误模式匹配、性能瓶颈识别和建议生成功能。
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntryType(Enum):
    """日志条目类型"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MODSDK = "modsdk"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class PerformanceIssueType(Enum):
    """性能问题类型"""
    SLOW_OPERATION = "slow_operation"
    MEMORY_LEAK = "memory_leak"
    HIGH_CPU = "high_cpu"
    BLOCKING_IO = "blocking_io"
    EXCESSIVE_LOGGING = "excessive_logging"
    REPEATED_OPERATION = "repeated_operation"


@dataclass
class LogEntry:
    """结构化日志条目"""
    raw: str
    level: LogLevel
    entry_type: LogEntryType
    timestamp: datetime | None
    message: str
    source: str | None = None
    line_number: int | None = None
    file_path: str | None = None
    thread_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "level": self.level.value,
            "entry_type": self.entry_type.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message": self.message,
            "source": self.source,
            "line_number": self.line_number,
            "file_path": self.file_path,
            "thread_id": self.thread_id,
            "context": self.context,
        }


@dataclass
class LogPattern:
    """日志模式"""
    id: str
    name: str
    pattern: re.Pattern
    entry_type: LogEntryType
    severity: LogLevel
    description: str
    suggestions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    
    def match(self, text: str) -> re.Match | None:
        """匹配文本"""
        return self.pattern.search(text)


@dataclass
class PerformanceIssue:
    """性能问题"""
    issue_type: PerformanceIssueType
    description: str
    location: str
    severity: LogLevel
    metrics: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_type": self.issue_type.value,
            "description": self.description,
            "location": self.location,
            "severity": self.severity.value,
            "metrics": self.metrics,
            "suggestions": self.suggestions,
        }


@dataclass
class LogAnalysisResult:
    """日志分析结果"""
    entries: list[LogEntry] = field(default_factory=list)
    errors: list[LogEntry] = field(default_factory=list)
    warnings: list[LogEntry] = field(default_factory=list)
    performance_issues: list[PerformanceIssue] = field(default_factory=list)
    patterns_matched: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    statistics: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [e.to_dict() for e in self.warnings],
            "performance_issues": [p.to_dict() for p in self.performance_issues],
            "patterns_matched": dict(self.patterns_matched),
            "statistics": self.statistics,
            "suggestions": self.suggestions,
        }


class StructuredLogParser:
    """
    结构化日志解析器
    
    将原始日志文本解析为结构化数据。
    """
    
    def __init__(self) -> None:
        self._patterns: list[tuple[re.Pattern, dict[str, Any]]] = []
        self._load_builtin_patterns()
    
    def _load_builtin_patterns(self) -> None:
        """加载内置日志格式模式"""
        patterns = [
            # Python 标准日志格式
            (
                re.compile(
                    r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+'
                    r'\[(\w+)\]\s+'
                    r'(\S+):\s+'
                    r'(.+)'
                ),
                {
                    "timestamp_format": "%Y-%m-%d %H:%M:%S,%f",
                    "level_group": 2,
                    "source_group": 3,
                    "message_group": 4,
                }
            ),
            # 简单格式: [LEVEL] message
            (
                re.compile(r'\[(\w+)\]\s+(.+)'),
                {
                    "level_group": 1,
                    "message_group": 2,
                }
            ),
            # Minecraft 日志格式
            (
                re.compile(
                    r'\[(\d{2}:\d{2}:\d{2})\]\s+'
                    r'\[(\w+)/(?:\w+)\]:\s+'
                    r'(.+)'
                ),
                {
                    "timestamp_group": 1,
                    "level_group": 2,
                    "message_group": 3,
                }
            ),
            # ModSDK 日志格式
            (
                re.compile(
                    r'\[ModSDK\]\s+'
                    r'\[(\w+)\]\s+'
                    r'(.+)'
                ),
                {
                    "level_group": 1,
                    "message_group": 2,
                    "entry_type": LogEntryType.MODSDK,
                }
            ),
        ]
        
        for pattern, config in patterns:
            self._patterns.append((pattern, config))
    
    def parse(self, log_text: str) -> list[LogEntry]:
        """
        解析日志文本
        
        Args:
            log_text: 日志文本
            
        Returns:
            LogEntry 列表
        """
        entries = []
        lines = log_text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            entry = self._parse_line(line)
            entries.append(entry)
        
        return entries
    
    def _parse_line(self, line: str) -> LogEntry:
        """解析单行日志"""
        for pattern, config in self._patterns:
            match = pattern.match(line)
            if match:
                return self._create_entry(match, line, config)
        
        # 无法解析，尝试推断
        return self._infer_entry(line)
    
    def _create_entry(
        self,
        match: re.Match,
        raw: str,
        config: dict[str, Any],
    ) -> LogEntry:
        """创建日志条目"""
        # 提取时间戳
        timestamp = None
        if "timestamp_group" in config:
            try:
                ts_str = match.group(config["timestamp_group"])
                if "timestamp_format" in config:
                    timestamp = datetime.strptime(ts_str, config["timestamp_format"])
                else:
                    # 尝试简单时间解析
                    timestamp = datetime.strptime(ts_str, "%H:%M:%S")
                    timestamp = timestamp.replace(year=datetime.now().year)
            except (ValueError, IndexError):
                pass
        
        # 提取级别
        level = LogLevel.INFO
        if "level_group" in config:
            level_str = match.group(config["level_group"]).upper()
            level = self._str_to_level(level_str)
        
        # 提取消息
        message = match.group(config["message_group"]) if "message_group" in config else raw
        
        # 提取来源
        source = match.group(config["source_group"]) if "source_group" in config else None
        
        # 条目类型
        entry_type = config.get("entry_type", self._infer_entry_type(message, level))
        
        return LogEntry(
            raw=raw,
            level=level,
            entry_type=entry_type,
            timestamp=timestamp,
            message=message,
            source=source,
        )
    
    def _infer_entry(self, line: str) -> LogEntry:
        """推断日志条目"""
        # 检查是否包含错误关键词
        line_lower = line.lower()
        
        if "error" in line_lower or "exception" in line_lower:
            level = LogLevel.ERROR
            entry_type = LogEntryType.ERROR
        elif "warning" in line_lower or "warn" in line_lower:
            level = LogLevel.WARNING
            entry_type = LogEntryType.WARNING
        elif "debug" in line_lower:
            level = LogLevel.DEBUG
            entry_type = LogEntryType.DEBUG
        else:
            level = LogLevel.INFO
            entry_type = LogEntryType.INFO
        
        return LogEntry(
            raw=line,
            level=level,
            entry_type=entry_type,
            timestamp=None,
            message=line,
        )
    
    def _infer_entry_type(self, message: str, level: LogLevel) -> LogEntryType:
        """推断条目类型"""
        message_lower = message.lower()
        
        if "modsdk" in message_lower or "minecraft" in message_lower:
            return LogEntryType.MODSDK
        elif level == LogLevel.ERROR:
            return LogEntryType.ERROR
        elif level == LogLevel.WARNING:
            return LogEntryType.WARNING
        else:
            return LogEntryType.INFO
    
    def _str_to_level(self, level_str: str) -> LogLevel:
        """字符串转日志级别"""
        mapping = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "WARN": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL,
            "FATAL": LogLevel.CRITICAL,
        }
        return mapping.get(level_str, LogLevel.INFO)


class LogPatternMatcher:
    """
    日志模式匹配器
    
    匹配已知的日志模式并提供识别。
    """
    
    def __init__(self) -> None:
        self._patterns: dict[str, LogPattern] = {}
        self._load_builtin_patterns()
    
    def _load_builtin_patterns(self) -> None:
        """加载内置模式"""
        patterns = [
            # Python 错误模式
            LogPattern(
                id="python_traceback",
                name="Python Traceback",
                pattern=re.compile(r'Traceback\s*\(most recent call last\)', re.MULTILINE),
                entry_type=LogEntryType.ERROR,
                severity=LogLevel.ERROR,
                description="Python 异常追踪",
                suggestions=["查看完整 traceback 定位错误源"],
                tags=["python", "error"],
            ),
            LogPattern(
                id="python_name_error",
                name="NameError",
                pattern=re.compile(r"NameError:\s*name\s+['\"](\w+)['\"]\s+is not defined"),
                entry_type=LogEntryType.ERROR,
                severity=LogLevel.ERROR,
                description="变量未定义错误",
                suggestions=["检查变量是否已定义", "检查变量名拼写"],
                tags=["python", "error", "name"],
            ),
            LogPattern(
                id="python_key_error",
                name="KeyError",
                pattern=re.compile(r"KeyError:\s*['\"]?(\w+)['\"]?"),
                entry_type=LogEntryType.ERROR,
                severity=LogLevel.ERROR,
                description="字典键不存在",
                suggestions=["使用 dict.get() 方法", "检查键名是否正确"],
                tags=["python", "error", "dict"],
            ),
            LogPattern(
                id="python_attribute_error",
                name="AttributeError",
                pattern=re.compile(r"AttributeError:\s*.+\s+has no attribute\s+['\"](\w+)['\"]"),
                entry_type=LogEntryType.ERROR,
                severity=LogLevel.ERROR,
                description="属性不存在错误",
                suggestions=["检查属性名", "使用 getattr() 方法"],
                tags=["python", "error", "attribute"],
            ),
            LogPattern(
                id="python_type_error",
                name="TypeError",
                pattern=re.compile(r"TypeError:\s*(.+)"),
                entry_type=LogEntryType.ERROR,
                severity=LogLevel.ERROR,
                description="类型错误",
                suggestions=["检查参数类型", "添加类型转换"],
                tags=["python", "error", "type"],
            ),
            LogPattern(
                id="python_syntax_error",
                name="SyntaxError",
                pattern=re.compile(r"SyntaxError:\s*(.+)"),
                entry_type=LogEntryType.ERROR,
                severity=LogLevel.ERROR,
                description="语法错误",
                suggestions=["检查语法", "检查括号匹配"],
                tags=["python", "error", "syntax"],
            ),
            
            # ModSDK 特定模式
            LogPattern(
                id="modsdk_api_error",
                name="ModSDK API Error",
                pattern=re.compile(r"(GetEngineType|GetConfig|CreateEngine|ListenEvent).*failed", re.IGNORECASE),
                entry_type=LogEntryType.MODSDK,
                severity=LogLevel.ERROR,
                description="ModSDK API 调用失败",
                suggestions=["检查 API 参数", "确认服务端/客户端作用域"],
                tags=["modsdk", "api", "error"],
            ),
            LogPattern(
                id="modsdk_entity_error",
                name="ModSDK Entity Error",
                pattern=re.compile(r"(CreateEngineEntity|DestroyEntity|GetEngineEntity).*failed", re.IGNORECASE),
                entry_type=LogEntryType.MODSDK,
                severity=LogLevel.ERROR,
                description="ModSDK 实体操作失败",
                suggestions=["检查实体 ID", "确认实体已创建"],
                tags=["modsdk", "entity", "error"],
            ),
            LogPattern(
                id="modsdk_event_error",
                name="ModSDK Event Error",
                pattern=re.compile(r"(ListenEvent|UnListenEvent|NotifyToMultiplayer).*failed", re.IGNORECASE),
                entry_type=LogEntryType.MODSDK,
                severity=LogLevel.WARNING,
                description="ModSDK 事件操作失败",
                suggestions=["检查事件名称", "检查回调函数"],
                tags=["modsdk", "event", "error"],
            ),
            
            # 性能模式
            LogPattern(
                id="slow_operation",
                name="Slow Operation",
                pattern=re.compile(r"(took|elapsed|duration)[:\s]+(\d+(?:\.\d+)?)\s*(s|ms|seconds?)", re.IGNORECASE),
                entry_type=LogEntryType.PERFORMANCE,
                severity=LogLevel.WARNING,
                description="慢操作警告",
                suggestions=["优化操作逻辑", "考虑异步处理"],
                tags=["performance", "slow"],
            ),
            LogPattern(
                id="memory_warning",
                name="Memory Warning",
                pattern=re.compile(r"(memory|内存)[:\s]+(\d+(?:\.\d+)?)\s*(MB|GB|%)", re.IGNORECASE),
                entry_type=LogEntryType.PERFORMANCE,
                severity=LogLevel.WARNING,
                description="内存使用警告",
                suggestions=["检查内存泄漏", "优化数据结构"],
                tags=["performance", "memory"],
            ),
            
            # 安全模式
            LogPattern(
                id="security_warning",
                name="Security Warning",
                pattern=re.compile(r"(security|安全|permission|权限|denied|拒绝)", re.IGNORECASE),
                entry_type=LogEntryType.SECURITY,
                severity=LogLevel.WARNING,
                description="安全警告",
                suggestions=["检查权限配置", "验证用户身份"],
                tags=["security", "warning"],
            ),
        ]
        
        for pattern in patterns:
            self._patterns[pattern.id] = pattern
    
    def add_pattern(self, pattern: LogPattern) -> None:
        """添加模式"""
        self._patterns[pattern.id] = pattern
    
    def match(self, text: str) -> list[LogPattern]:
        """
        匹配文本
        
        Args:
            text: 日志文本
            
        Returns:
            匹配的模式列表
        """
        matched = []
        for pattern in self._patterns.values():
            if pattern.match(text):
                matched.append(pattern)
        return matched
    
    def get_pattern(self, pattern_id: str) -> LogPattern | None:
        """获取模式"""
        return self._patterns.get(pattern_id)
    
    def list_patterns(self) -> list[LogPattern]:
        """列出所有模式"""
        return list(self._patterns.values())


class PerformanceAnalyzer:
    """
    性能分析器
    
    识别性能瓶颈和问题。
    """
    
    def __init__(self) -> None:
        self._thresholds: dict[str, float] = {
            "slow_operation_ms": 1000.0,  # 1秒
            "memory_percent": 80.0,       # 80%
            "repeated_threshold": 10,     # 重复次数阈值
        }
        self._operation_times: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def set_threshold(self, name: str, value: float) -> None:
        """设置阈值"""
        self._thresholds[name] = value
    
    def analyze(self, entries: list[LogEntry]) -> list[PerformanceIssue]:
        """
        分析性能问题
        
        Args:
            entries: 日志条目列表
            
        Returns:
            性能问题列表
        """
        issues = []
        
        for entry in entries:
            # 分析慢操作
            slow_issue = self._analyze_slow_operation(entry)
            if slow_issue:
                issues.append(slow_issue)
            
            # 分析内存问题
            memory_issue = self._analyze_memory(entry)
            if memory_issue:
                issues.append(memory_issue)
        
        # 分析重复操作
        repeated_issues = self._analyze_repeated_operations(entries)
        issues.extend(repeated_issues)
        
        return issues
    
    def _analyze_slow_operation(self, entry: LogEntry) -> PerformanceIssue | None:
        """分析慢操作"""
        # 匹配时间模式
        time_match = re.search(
            r'(took|elapsed|duration|耗时)[:\s]+(\d+(?:\.\d+)?)\s*(s|ms|seconds?|毫秒)',
            entry.message,
            re.IGNORECASE
        )
        
        if not time_match:
            return None
        
        value = float(time_match.group(2))
        unit = time_match.group(3).lower()
        
        # 转换为毫秒
        if unit in ("s", "seconds", "秒"):
            value_ms = value * 1000
        else:
            value_ms = value
        
        threshold = self._thresholds["slow_operation_ms"]
        
        if value_ms > threshold:
            return PerformanceIssue(
                issue_type=PerformanceIssueType.SLOW_OPERATION,
                description=f"操作耗时 {value_ms:.0f}ms，超过阈值 {threshold}ms",
                location=entry.source or "unknown",
                severity=LogLevel.WARNING,
                metrics={
                    "duration_ms": value_ms,
                    "threshold_ms": threshold,
                },
                suggestions=[
                    "优化操作逻辑",
                    "考虑使用缓存",
                    "检查是否有不必要的循环",
                ],
            )
        
        return None
    
    def _analyze_memory(self, entry: LogEntry) -> PerformanceIssue | None:
        """分析内存问题"""
        memory_match = re.search(
            r'(memory|内存)[:\s]+(\d+(?:\.\d+)?)\s*(MB|GB|%)',
            entry.message,
            re.IGNORECASE
        )
        
        if not memory_match:
            return None
        
        value = float(memory_match.group(2))
        unit = memory_match.group(3).upper()
        
        # 检查百分比
        if unit == "%":
            threshold = self._thresholds["memory_percent"]
            if value > threshold:
                return PerformanceIssue(
                    issue_type=PerformanceIssueType.MEMORY_LEAK,
                    description=f"内存使用率 {value}%，超过阈值 {threshold}%",
                    location=entry.source or "unknown",
                    severity=LogLevel.WARNING,
                    metrics={
                        "memory_percent": value,
                        "threshold_percent": threshold,
                    },
                    suggestions=[
                        "检查是否有内存泄漏",
                        "释放不需要的大对象",
                        "优化数据结构",
                    ],
                )
        
        return None
    
    def _analyze_repeated_operations(self, entries: list[LogEntry]) -> list[PerformanceIssue]:
        """分析重复操作"""
        issues = []
        
        # 统计相似消息
        message_counts: dict[str, int] = defaultdict(int)
        for entry in entries:
            # 简化消息用于统计
            simplified = re.sub(r'\d+', 'N', entry.message[:50])
            message_counts[simplified] += 1
        
        threshold = self._thresholds["repeated_threshold"]
        
        for message, count in message_counts.items():
            if count > threshold:
                issues.append(PerformanceIssue(
                    issue_type=PerformanceIssueType.REPEATED_OPERATION,
                    description=f"相似操作重复 {count} 次",
                    location="multiple",
                    severity=LogLevel.INFO,
                    metrics={
                        "count": count,
                        "threshold": threshold,
                        "message_preview": message,
                    },
                    suggestions=[
                        "考虑批量处理",
                        "检查循环逻辑",
                        "使用缓存减少重复计算",
                    ],
                ))
        
        return issues


class SuggestionGenerator:
    """
    建议生成器
    
    基于分析结果生成修复建议。
    """
    
    def __init__(self) -> None:
        self._templates: dict[str, list[str]] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self) -> None:
        """加载内置建议模板"""
        self._templates = {
            "NameError": [
                "检查变量是否已定义",
                "检查变量名拼写是否正确",
                "检查变量作用域",
                "添加必要的 import 语句",
            ],
            "KeyError": [
                "使用 dict.get(key, default) 安全访问",
                "检查键名拼写是否正确",
                "使用 'key in dict' 检查键是否存在",
            ],
            "AttributeError": [
                "检查属性名拼写是否正确",
                "使用 getattr(obj, attr, default) 安全访问",
                "检查对象是否为 None",
            ],
            "TypeError": [
                "检查参数类型是否正确",
                "添加必要的类型转换",
                "检查函数参数数量",
            ],
            "IndexError": [
                "检查索引是否在有效范围内",
                "使用安全的索引访问方式",
                "检查列表是否为空",
            ],
            "ModSDKError": [
                "检查 API 参数是否正确",
                "确认当前是服务端还是客户端",
                "检查 API 版本兼容性",
            ],
            "PerformanceIssue": [
                "优化算法复杂度",
                "使用缓存减少重复计算",
                "考虑异步处理",
                "减少不必要的操作",
            ],
        }
    
    def generate(
        self,
        entry_type: str,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        生成建议
        
        Args:
            entry_type: 条目类型
            context: 上下文信息
            
        Returns:
            建议列表
        """
        suggestions = list(self._templates.get(entry_type, []))
        
        # 基于上下文添加特定建议
        if context:
            if context.get("has_traceback"):
                suggestions.insert(0, "查看完整 traceback 定位错误源")
            
            if context.get("file_path"):
                suggestions.append(f"检查文件 {context['file_path']}")
        
        return suggestions


class EnhancedLogAnalyzer:
    """
    增强日志分析器
    
    整合所有日志分析功能。
    """
    
    def __init__(self) -> None:
        self.parser = StructuredLogParser()
        self.pattern_matcher = LogPatternMatcher()
        self.performance_analyzer = PerformanceAnalyzer()
        self.suggestion_generator = SuggestionGenerator()
    
    def analyze(self, log_text: str) -> LogAnalysisResult:
        """
        分析日志
        
        Args:
            log_text: 日志文本
            
        Returns:
            LogAnalysisResult
        """
        result = LogAnalysisResult()
        
        # 解析日志
        result.entries = self.parser.parse(log_text)
        
        # 分类和处理
        for entry in result.entries:
            # 按级别分类
            if entry.level == LogLevel.ERROR:
                result.errors.append(entry)
            elif entry.level == LogLevel.WARNING:
                result.warnings.append(entry)
            
            # 匹配模式
            patterns = self.pattern_matcher.match(entry.raw)
            for pattern in patterns:
                result.patterns_matched[pattern.id] += 1
                entry.context["matched_pattern"] = pattern.id
        
        # 分析性能问题
        result.performance_issues = self.performance_analyzer.analyze(result.entries)
        
        # 生成统计
        result.statistics = self._generate_statistics(result)
        
        # 生成建议
        result.suggestions = self._generate_suggestions(result)
        
        return result
    
    def analyze_file(self, file_path: str) -> LogAnalysisResult:
        """分析日志文件"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                log_text = f.read()
            return self.analyze(log_text)
        except Exception as e:
            result = LogAnalysisResult()
            result.suggestions.append(f"无法读取日志文件: {e}")
            return result
    
    def _generate_statistics(self, result: LogAnalysisResult) -> dict[str, Any]:
        """生成统计信息"""
        stats = {
            "total_entries": len(result.entries),
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "performance_issue_count": len(result.performance_issues),
            "entries_by_level": defaultdict(int),
            "entries_by_type": defaultdict(int),
        }
        
        for entry in result.entries:
            stats["entries_by_level"][entry.level.value] += 1
            stats["entries_by_type"][entry.entry_type.value] += 1
        
        # 转换 defaultdict 为 dict
        stats["entries_by_level"] = dict(stats["entries_by_level"])
        stats["entries_by_type"] = dict(stats["entries_by_type"])
        
        return stats
    
    def _generate_suggestions(self, result: LogAnalysisResult) -> list[str]:
        """生成建议"""
        suggestions = []
        
        # 基于错误生成建议
        for error in result.errors[:5]:  # 只处理前5个错误
            pattern_id = error.context.get("matched_pattern")
            if pattern_id:
                pattern = self.pattern_matcher.get_pattern(pattern_id)
                if pattern:
                    suggestions.extend(pattern.suggestions)
        
        # 基于性能问题生成建议
        for issue in result.performance_issues:
            suggestions.extend(issue.suggestions)
        
        # 去重
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)
        
        return unique_suggestions[:10]  # 最多10条建议


# 便捷函数
def create_log_analyzer() -> EnhancedLogAnalyzer:
    """创建日志分析器"""
    return EnhancedLogAnalyzer()


def analyze_log(log_text: str) -> LogAnalysisResult:
    """分析日志"""
    analyzer = EnhancedLogAnalyzer()
    return analyzer.analyze(log_text)


def analyze_log_file(file_path: str) -> LogAnalysisResult:
    """分析日志文件"""
    analyzer = EnhancedLogAnalyzer()
    return analyzer.analyze_file(file_path)