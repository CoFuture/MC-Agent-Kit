"""
ModSDK 调试辅助 Skill

提供错误诊断和解决方案建议功能。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..base import BaseSkill, SkillCategory, SkillMetadata, SkillPriority, SkillResult

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""

    ERROR = "error"  # 错误
    WARNING = "warning"  # 警告
    INFO = "info"  # 信息


class ErrorCategory(Enum):
    """错误分类"""

    SYNTAX = "syntax"  # 语法错误
    RUNTIME = "runtime"  # 运行时错误
    API = "api"  # API 调用错误
    EVENT = "event"  # 事件相关错误
    CONFIG = "config"  # 配置错误
    NETWORK = "network"  # 网络错误
    PERMISSION = "permission"  # 权限错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class DiagnosedError:
    """诊断结果"""

    error_type: str  # 错误类型
    message: str  # 错误消息
    category: ErrorCategory  # 错误分类
    severity: ErrorSeverity  # 严重程度
    line_number: int | None = None  # 行号
    file_name: str | None = None  # 文件名
    context: str | None = None  # 上下文代码
    suggestions: list[str] | None = None  # 解决建议


@dataclass
class ErrorPattern:
    """错误模式定义"""

    pattern: str  # 正则表达式模式
    error_type: str  # 错误类型
    category: ErrorCategory  # 错误分类
    severity: ErrorSeverity  # 严重程度
    suggestions: list[str]  # 解决建议
    description: str = ""  # 模式描述


# 常见错误模式
COMMON_ERROR_PATTERNS: list[ErrorPattern] = [
    # 语法错误
    ErrorPattern(
        pattern=r"SyntaxError:\s*(.+)",
        error_type="SyntaxError",
        category=ErrorCategory.SYNTAX,
        severity=ErrorSeverity.ERROR,
        description="Python 语法错误",
        suggestions=[
            "检查代码语法是否正确",
            "检查括号、引号是否匹配",
            "检查缩进是否正确",
        ],
    ),
    ErrorPattern(
        pattern=r"IndentationError:\s*(.+)",
        error_type="IndentationError",
        category=ErrorCategory.SYNTAX,
        severity=ErrorSeverity.ERROR,
        description="缩进错误",
        suggestions=[
            "检查代码缩进是否使用空格（推荐 4 个空格）",
            "避免混用 Tab 和空格",
        ],
    ),
    # 运行时错误
    ErrorPattern(
        pattern=r"NameError:\s*name\s+'(\w+)'\s+is\s+not\s+defined",
        error_type="NameError",
        category=ErrorCategory.RUNTIME,
        severity=ErrorSeverity.ERROR,
        description="变量未定义",
        suggestions=[
            "检查变量名是否拼写正确",
            "确保变量在使用前已定义",
            "检查是否缺少 import 语句",
        ],
    ),
    ErrorPattern(
        pattern=r"TypeError:\s*(.+)",
        error_type="TypeError",
        category=ErrorCategory.RUNTIME,
        severity=ErrorSeverity.ERROR,
        description="类型错误",
        suggestions=[
            "检查参数类型是否正确",
            "检查是否调用了不存在的方法",
        ],
    ),
    ErrorPattern(
        pattern=r"AttributeError:\s*'(\w+)'\s+object\s+has\s+no\s+attribute\s+'(\w+)'",
        error_type="AttributeError",
        category=ErrorCategory.RUNTIME,
        severity=ErrorSeverity.ERROR,
        description="属性不存在",
        suggestions=[
            "检查属性名是否拼写正确",
            "确认对象类型是否正确",
            "查看 API 文档确认可用属性",
        ],
    ),
    ErrorPattern(
        pattern=r"KeyError:\s*(.+)",
        error_type="KeyError",
        category=ErrorCategory.RUNTIME,
        severity=ErrorSeverity.ERROR,
        description="字典键不存在",
        suggestions=[
            "检查键名是否正确",
            "使用 dict.get() 方法安全获取",
        ],
    ),
    ErrorPattern(
        pattern=r"IndexError:\s*(.+)",
        error_type="IndexError",
        category=ErrorCategory.RUNTIME,
        severity=ErrorSeverity.ERROR,
        description="索引越界",
        suggestions=[
            "检查索引是否在有效范围内",
            "使用 len() 检查列表长度",
        ],
    ),
    # API 错误
    ErrorPattern(
        pattern=r"component\s+(\w+)\s+not\s+found",
        error_type="ComponentNotFound",
        category=ErrorCategory.API,
        severity=ErrorSeverity.ERROR,
        description="组件未找到",
        suggestions=[
            "检查组件名称是否正确",
            "确认当前作用域支持该组件",
            "查看 API 文档确认组件可用性",
        ],
    ),
    ErrorPattern(
        pattern=r"API\s+(\w+)\s+not\s+found",
        error_type="APINotFound",
        category=ErrorCategory.API,
        severity=ErrorSeverity.ERROR,
        description="API 未找到",
        suggestions=[
            "检查 API 名称是否拼写正确",
            "确认当前作用域支持该 API",
            "查看 API 文档确认可用性",
        ],
    ),
    ErrorPattern(
        pattern=r"Invalid\s+parameter:\s*(.+)",
        error_type="InvalidParameter",
        category=ErrorCategory.API,
        severity=ErrorSeverity.ERROR,
        description="参数无效",
        suggestions=[
            "检查参数类型是否正确",
            "检查参数值是否在有效范围内",
            "查看 API 文档确认参数要求",
        ],
    ),
    # 事件错误
    ErrorPattern(
        pattern=r"Event\s+(\w+)\s+not\s+registered",
        error_type="EventNotRegistered",
        category=ErrorCategory.EVENT,
        severity=ErrorSeverity.WARNING,
        description="事件未注册",
        suggestions=[
            "确保在系统初始化时注册事件监听",
            "检查事件名称是否正确",
            "确认事件命名空间是否正确",
        ],
    ),
    ErrorPattern(
        pattern=r"ListenForEvent\s+failed:\s*(.+)",
        error_type="EventListenFailed",
        category=ErrorCategory.EVENT,
        severity=ErrorSeverity.ERROR,
        description="事件监听失败",
        suggestions=[
            "检查事件名称和命名空间",
            "确认回调函数签名正确",
            "检查作用域是否匹配",
        ],
    ),
    # 配置错误
    ErrorPattern(
        pattern=r"Config\s+file\s+not\s+found:\s*(.+)",
        error_type="ConfigNotFound",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.ERROR,
        description="配置文件未找到",
        suggestions=[
            "检查配置文件路径是否正确",
            "确保配置文件存在",
            "检查文件权限",
        ],
    ),
    ErrorPattern(
        pattern=r"Invalid\s+config:\s*(.+)",
        error_type="InvalidConfig",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.ERROR,
        description="配置无效",
        suggestions=[
            "检查配置格式是否正确",
            "确认必填配置项是否完整",
            "查看配置文档",
        ],
    ),
    # ModSDK 特定错误
    ErrorPattern(
        pattern=r"mod\s+not\s+loaded",
        error_type="ModNotLoaded",
        category=ErrorCategory.RUNTIME,
        severity=ErrorSeverity.ERROR,
        description="Mod 未加载",
        suggestions=[
            "检查 Mod 是否正确安装",
            "查看游戏日志了解加载情况",
            "确认 Mod 版本兼容性",
        ],
    ),
    ErrorPattern(
        pattern=r"addon\s+not\s+found:\s*(.+)",
        error_type="AddonNotFound",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.ERROR,
        description="Addon 未找到",
        suggestions=[
            "检查 Addon 目录是否正确",
            "确认 behavior_packs / resource_packs 配置",
            "检查 world_packs.json 配置",
        ],
    ),
    # 通用警告
    ErrorPattern(
        pattern=r"WARNING:\s*(.+)",
        error_type="Warning",
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.WARNING,
        description="警告信息",
        suggestions=[
            "查看警告详情",
            "评估是否需要处理",
        ],
    ),
]


class ModSDKDebugSkill(BaseSkill):
    """ModSDK 调试辅助 Skill

    提供错误日志分析和解决方案建议，支持：
    - 错误日志解析
    - 错误类型识别
    - 解决方案建议
    - 常见问题匹配

    使用示例:
        skill = ModSDKDebugSkill()

        # 诊断错误日志
        result = skill.execute(log_content="SyntaxError: invalid syntax")

        # 分析日志文件
        result = skill.execute(action="analyze", log_content="...")

        # 获取常见错误列表
        result = skill.execute(action="list_errors")
    """

    def __init__(self):
        """初始化 Skill"""
        super().__init__(
            metadata=SkillMetadata(
                name="modsdk-debug",
                description="分析 ModSDK 错误日志，提供诊断和解决方案建议",
                version="1.0.0",
                author="MC-Agent-Kit",
                category=SkillCategory.DEBUG,
                priority=SkillPriority.HIGH,
                tags=["modsdk", "debug", "error", "diagnosis"],
                examples=[
                    "诊断错误: execute(log_content='SyntaxError: invalid syntax')",
                    "获取常见错误: execute(action='list_errors')",
                ],
            )
        )
        self._patterns: list[ErrorPattern] = []

    def initialize(self) -> bool:
        """初始化错误模式"""
        if self._initialized:
            return True

        self._patterns = COMMON_ERROR_PATTERNS.copy()
        self._initialized = True
        return True

    def execute(
        self,
        log_content: str | None = None,
        action: str = "diagnose",
        error_type: str | None = None,
        **kwargs,
    ) -> SkillResult:
        """执行调试辅助

        Args:
            log_content: 日志内容
            action: 操作类型 (diagnose/analyze/list_errors)
            error_type: 按错误类型过滤

        Returns:
            SkillResult: 诊断结果
        """
        if not self._initialized:
            self.initialize()

        try:
            if action == "list_errors":
                return self._list_error_patterns()
            elif action == "analyze":
                if not log_content:
                    return SkillResult(
                        success=False,
                        error="请提供 log_content 参数",
                    )
                return self._analyze_log(log_content)
            elif action == "diagnose":
                if not log_content:
                    return SkillResult(
                        success=False,
                        error="请提供 log_content 参数",
                    )
                return self._diagnose(log_content)
            else:
                return SkillResult(
                    success=False,
                    error=f"未知操作: {action}",
                    suggestions=["diagnose", "analyze", "list_errors"],
                )

        except Exception as e:
            logger.error(f"调试分析失败: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                message="调试分析失败",
            )

    def _diagnose(self, log_content: str) -> SkillResult:
        """诊断错误日志

        Args:
            log_content: 日志内容

        Returns:
            诊断结果
        """
        diagnosed_errors: list[dict[str, Any]] = []

        for pattern in self._patterns:
            matches = re.finditer(pattern.pattern, log_content, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                error = DiagnosedError(
                    error_type=pattern.error_type,
                    message=match.group(0),
                    category=pattern.category,
                    severity=pattern.severity,
                    suggestions=pattern.suggestions.copy(),
                )

                # 尝试提取行号
                line_match = re.search(r"line\s+(\d+)", log_content)
                if line_match:
                    error.line_number = int(line_match.group(1))

                # 尝试提取文件名
                file_match = re.search(r"File\s+\"([^\"]+)\"", log_content)
                if file_match:
                    error.file_name = file_match.group(1)

                diagnosed_errors.append(
                    {
                        "error_type": error.error_type,
                        "message": error.message,
                        "category": error.category.value,
                        "severity": error.severity.value,
                        "line_number": error.line_number,
                        "file_name": error.file_name,
                        "suggestions": error.suggestions,
                    }
                )

        if not diagnosed_errors:
            return SkillResult(
                success=True,
                data=[],
                message="未识别到已知错误模式",
                suggestions=[
                    "检查日志格式是否正确",
                    "提供更完整的错误日志",
                    "使用 action='list_errors' 查看支持的错误类型",
                ],
            )

        return SkillResult(
            success=True,
            data=diagnosed_errors,
            message=f"识别到 {len(diagnosed_errors)} 个错误",
        )

    def _analyze_log(self, log_content: str) -> SkillResult:
        """分析日志内容

        提供更详细的分析，包括：
        - 错误统计
        - 错误上下文
        - 推荐处理顺序

        Args:
            log_content: 日志内容

        Returns:
            分析结果
        """
        # 先诊断
        diagnose_result = self._diagnose(log_content)
        if not diagnose_result.success:
            return diagnose_result

        errors = diagnose_result.data

        # 统计
        error_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}

        for error in errors:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

            severity = error["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            category = error["category"]
            category_counts[category] = category_counts.get(category, 0) + 1

        # 按严重程度排序
        severity_order = {"error": 0, "warning": 1, "info": 2}
        sorted_errors = sorted(
            errors,
            key=lambda e: severity_order.get(e["severity"], 99),
        )

        # 提取日志行
        lines = log_content.strip().split("\n")

        return SkillResult(
            success=True,
            data={
                "errors": sorted_errors,
                "statistics": {
                    "total_errors": len(errors),
                    "by_type": error_counts,
                    "by_severity": severity_counts,
                    "by_category": category_counts,
                },
                "total_lines": len(lines),
            },
            message=f"分析完成，发现 {len(errors)} 个错误",
            suggestions=self._get_priority_suggestions(sorted_errors),
        )

    def _list_error_patterns(self) -> SkillResult:
        """列出支持的错误模式"""
        patterns = [
            {
                "error_type": p.error_type,
                "category": p.category.value,
                "severity": p.severity.value,
                "description": p.description,
            }
            for p in self._patterns
        ]

        return SkillResult(
            success=True,
            data=patterns,
            message=f"共 {len(patterns)} 个错误模式",
        )

    def _get_priority_suggestions(self, errors: list[dict]) -> list[str]:
        """获取优先处理建议

        Args:
            errors: 错误列表

        Returns:
            建议列表
        """
        suggestions = []

        # 统计错误类型
        error_types: dict[str, int] = {}
        for error in errors:
            if error["severity"] == "error":
                error_types[error["error_type"]] = error_types.get(error["error_type"], 0) + 1

        if error_types:
            top_error = max(error_types, key=error_types.get)
            suggestions.append(f"优先处理: {top_error} ({error_types[top_error]} 次)")

        suggestions.append("建议从错误类型最多的问题开始修复")
        suggestions.append("修复后重新运行测试验证")

        return suggestions

    def add_error_pattern(self, pattern: ErrorPattern) -> None:
        """添加自定义错误模式

        Args:
            pattern: 错误模式
        """
        self._patterns.append(pattern)

    def diagnose_simple(self, error_message: str) -> SkillResult:
        """简化的诊断接口

        Args:
            error_message: 错误消息

        Returns:
            诊断结果
        """
        return self._diagnose(error_message)
