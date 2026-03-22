"""
错误诊断器模块

分析错误日志，诊断问题并提供修复建议。
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorType(Enum):
    """错误类型"""

    SYNTAX_ERROR = "syntax_error"  # 语法错误
    NAME_ERROR = "name_error"  # 名称错误
    TYPE_ERROR = "type_error"  # 类型错误
    INDEX_ERROR = "index_error"  # 索引错误
    KEY_ERROR = "key_error"  # 键错误
    ATTRIBUTE_ERROR = "attribute_error"  # 属性错误
    IMPORT_ERROR = "import_error"  # 导入错误
    VALUE_ERROR = "value_error"  # 值错误
    RUNTIME_ERROR = "runtime_error"  # 运行时错误
    INDENTATION_ERROR = "indentation_error"  # 缩进错误
    ZERO_DIVISION_ERROR = "zero_division_error"  # 除零错误
    FILE_ERROR = "file_error"  # 文件错误
    MODSDK_ERROR = "modsdk_error"  # ModSDK 专用错误
    UNKNOWN = "unknown"  # 未知错误


class FixConfidence(Enum):
    """修复信心等级"""

    HIGH = "high"  # 高信心（可以自动修复）
    MEDIUM = "medium"  # 中等信心（建议人工确认）
    LOW = "low"  # 低信心（需要人工处理）


@dataclass
class ErrorInfo:
    """错误信息"""

    error_type: ErrorType  # 错误类型
    message: str  # 错误消息
    raw_log: str  # 原始日志
    line_number: int | None = None  # 行号
    column: int | None = None  # 列号
    file_path: str | None = None  # 文件路径
    function_name: str | None = None  # 函数名
    traceback: str | None = None  # 完整 traceback
    context: dict[str, Any] = field(default_factory=dict)  # 额外上下文


@dataclass
class FixSuggestion:
    """修复建议"""

    description: str  # 修复描述
    confidence: FixConfidence  # 信心等级
    code_before: str | None = None  # 修复前代码
    code_after: str | None = None  # 修复后代码
    explanation: str = ""  # 解释说明
    auto_fixable: bool = False  # 是否可自动修复
    priority: int = 0  # 优先级（越高越优先）


@dataclass
class DiagnosisResult:
    """诊断结果"""

    error_info: ErrorInfo  # 错误信息
    suggestions: list[FixSuggestion]  # 修复建议
    related_docs: list[str] = field(default_factory=list)  # 相关文档
    similar_issues: list[str] = field(default_factory=list)  # 类似问题


class ErrorDiagnoser:
    """
    错误诊断器。

    分析错误日志，识别错误类型，并提供修复建议。

    使用示例:
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("NameError: name 'x' is not defined")
        for suggestion in result.suggestions:
            print(suggestion.description)
    """

    # 错误模式定义
    ERROR_PATTERNS: list[tuple[ErrorType, re.Pattern, dict[str, Any]]] = [
        (
            ErrorType.SYNTAX_ERROR,
            re.compile(r"SyntaxError:\s*(.+?)(?:\s+at\s+line\s+(\d+))?"),
            {},
        ),
        (
            ErrorType.NAME_ERROR,
            re.compile(r"NameError:\s*name\s+['\"](\w+)['\"]\s+is not defined"),
            {},
        ),
        (
            ErrorType.TYPE_ERROR,
            re.compile(r"TypeError:\s*(.+)"),
            {},
        ),
        (
            ErrorType.INDEX_ERROR,
            re.compile(r"IndexError:\s*(.+)"),
            {},
        ),
        (
            ErrorType.KEY_ERROR,
            re.compile(r"KeyError:\s*['\"]?(\w+)['\"]?"),
            {},
        ),
        (
            ErrorType.ATTRIBUTE_ERROR,
            re.compile(r"AttributeError:\s*.+\s+has no attribute\s+['\"](\w+)['\"]"),
            {},
        ),
        (
            ErrorType.IMPORT_ERROR,
            re.compile(r"ImportError:\s*(.+)"),
            {},
        ),
        (
            ErrorType.VALUE_ERROR,
            re.compile(r"ValueError:\s*(.+)"),
            {},
        ),
        (
            ErrorType.INDENTATION_ERROR,
            re.compile(r"IndentationError:\s*(.+)"),
            {},
        ),
        (
            ErrorType.ZERO_DIVISION_ERROR,
            re.compile(r"ZeroDivisionError:\s*(.+)"),
            {},
        ),
        (
            ErrorType.FILE_ERROR,
            re.compile(r"(FileNotFoundError|PermissionError|IOError):\s*(.+)"),
            {},
        ),
        (
            ErrorType.MODSDK_ERROR,
            re.compile(r"(GetEngineType|GetConfig|CreateEngine|ListenEvent).*failed"),
            {"is_modsdk": True},
        ),
    ]

    # Traceback 行号提取模式
    TRACEBACK_LINE_PATTERN = re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+)')

    def __init__(self) -> None:
        """初始化诊断器"""
        self._custom_patterns: list[tuple[ErrorType, re.Pattern, dict[str, Any]]] = []

    def add_custom_pattern(
        self, error_type: ErrorType, pattern: re.Pattern, context: dict[str, Any] | None = None
    ) -> None:
        """添加自定义错误模式"""
        self._custom_patterns.append((error_type, pattern, context or {}))

    def diagnose(self, error_log: str) -> DiagnosisResult:
        """
        诊断错误日志。

        Args:
            error_log: 错误日志

        Returns:
            DiagnosisResult: 诊断结果
        """
        # 解析错误信息
        error_info = self._parse_error(error_log)

        # 生成修复建议
        suggestions = self._generate_suggestions(error_info)

        # 收集相关文档
        related_docs = self._get_related_docs(error_info)

        # 查找类似问题
        similar_issues = self._find_similar_issues(error_info)

        return DiagnosisResult(
            error_info=error_info,
            suggestions=suggestions,
            related_docs=related_docs,
            similar_issues=similar_issues,
        )

    def diagnose_traceback(self, traceback_text: str) -> DiagnosisResult:
        """
        诊断完整 traceback。

        Args:
            traceback_text: 完整 traceback 文本

        Returns:
            DiagnosisResult: 诊断结果
        """
        # 提取最后一行错误
        lines = traceback_text.strip().split("\n")
        error_line = ""
        for line in reversed(lines):
            if "Error:" in line or "Exception:" in line:
                error_line = line
                break

        # 解析错误
        result = self.diagnose(error_line or traceback_text)
        result.error_info.traceback = traceback_text

        # 提取文件和行号
        file_matches = list(self.TRACEBACK_LINE_PATTERN.finditer(traceback_text))
        if file_matches:
            last_match = file_matches[-1]
            result.error_info.file_path = last_match.group(1)
            result.error_info.line_number = int(last_match.group(2))

        return result

    def _parse_error(self, error_log: str) -> ErrorInfo:
        """解析错误日志"""
        all_patterns = self.ERROR_PATTERNS + self._custom_patterns

        for error_type, pattern, context in all_patterns:
            match = pattern.search(error_log)
            if match:
                info = ErrorInfo(
                    error_type=error_type,
                    message=match.group(0),
                    raw_log=error_log,
                    context=context.copy(),
                )

                # 提取额外信息
                groups = match.groups()
                if groups:
                    info.context["captured_groups"] = list(groups)

                    # 对于 NameError，保存变量名
                    if error_type == ErrorType.NAME_ERROR:
                        info.context["undefined_name"] = groups[0]
                    # 对于 KeyError，保存键名
                    elif error_type == ErrorType.KEY_ERROR:
                        info.context["missing_key"] = groups[0]
                    # 对于 AttributeError，保存属性名
                    elif error_type == ErrorType.ATTRIBUTE_ERROR:
                        info.context["missing_attribute"] = groups[0]

                return info

        # 未知错误
        return ErrorInfo(
            error_type=ErrorType.UNKNOWN,
            message=error_log,
            raw_log=error_log,
        )

    def _generate_suggestions(self, error_info: ErrorInfo) -> list[FixSuggestion]:
        """生成修复建议"""
        suggestions = []

        if error_info.error_type == ErrorType.NAME_ERROR:
            undefined_name = error_info.context.get("undefined_name", "")
            suggestions.extend(
                [
                    FixSuggestion(
                        description=f"定义变量 '{undefined_name}'",
                        confidence=FixConfidence.MEDIUM,
                        explanation=f"变量 '{undefined_name}' 在使用前未定义。",
                        auto_fixable=False,
                        priority=1,
                    ),
                    FixSuggestion(
                        description=f"检查 '{undefined_name}' 是否拼写错误",
                        confidence=FixConfidence.HIGH,
                        explanation="可能是变量名拼写错误或大小写不匹配。",
                        auto_fixable=False,
                        priority=2,
                    ),
                    FixSuggestion(
                        description=f"检查 '{undefined_name}' 是否在正确的作用域中",
                        confidence=FixConfidence.MEDIUM,
                        explanation="变量可能在其他作用域中定义，无法在当前位置访问。",
                        auto_fixable=False,
                        priority=0,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.KEY_ERROR:
            missing_key = error_info.context.get("missing_key", "")
            suggestions.extend(
                [
                    FixSuggestion(
                        description=f"使用 .get('{missing_key}', default) 方法安全访问",
                        confidence=FixConfidence.HIGH,
                        code_before=f"dict['{missing_key}']",
                        code_after=f"dict.get('{missing_key}', default_value)",
                        explanation="使用 .get() 方法可以在键不存在时返回默认值而不是报错。",
                        auto_fixable=True,
                        priority=2,
                    ),
                    FixSuggestion(
                        description=f"检查键 '{missing_key}' 是否存在于字典中",
                        confidence=FixConfidence.MEDIUM,
                        explanation="在使用前检查键是否存在：if 'key' in dict: ...",
                        auto_fixable=False,
                        priority=1,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.INDEX_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="检查索引是否在有效范围内",
                        confidence=FixConfidence.HIGH,
                        explanation="列表/数组索引超出范围。检查 len(list) 确认有效索引范围。",
                        auto_fixable=False,
                        priority=1,
                    ),
                    FixSuggestion(
                        description="使用安全索引访问",
                        confidence=FixConfidence.MEDIUM,
                        code_before="list[i]",
                        code_after="list[i] if 0 <= i < len(list) else default",
                        explanation="添加边界检查避免索引越界。",
                        auto_fixable=True,
                        priority=0,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.TYPE_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="检查参数类型",
                        confidence=FixConfidence.MEDIUM,
                        explanation=f"类型错误：{error_info.message}",
                        auto_fixable=False,
                        priority=1,
                    ),
                    FixSuggestion(
                        description="添加类型转换",
                        confidence=FixConfidence.LOW,
                        explanation="可能需要使用 int(), str(), float() 等进行类型转换。",
                        auto_fixable=False,
                        priority=0,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.ATTRIBUTE_ERROR:
            missing_attr = error_info.context.get("missing_attribute", "")
            suggestions.extend(
                [
                    FixSuggestion(
                        description=f"检查对象是否具有属性 '{missing_attr}'",
                        confidence=FixConfidence.HIGH,
                        explanation=f"对象没有属性 '{missing_attr}'。检查对象类型和属性名。",
                        auto_fixable=False,
                        priority=1,
                    ),
                    FixSuggestion(
                        description=f"使用 getattr(obj, '{missing_attr}', default) 安全访问",
                        confidence=FixConfidence.MEDIUM,
                        code_before=f"obj.{missing_attr}",
                        code_after=f"getattr(obj, '{missing_attr}', default_value)",
                        explanation="使用 getattr 可以在属性不存在时返回默认值。",
                        auto_fixable=True,
                        priority=0,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.SYNTAX_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="检查语法错误",
                        confidence=FixConfidence.HIGH,
                        explanation="代码存在语法错误。检查括号、引号是否匹配，关键字是否正确。",
                        auto_fixable=False,
                        priority=2,
                    ),
                    FixSuggestion(
                        description="检查缩进是否正确",
                        confidence=FixConfidence.MEDIUM,
                        explanation="Python 对缩进敏感，确保使用一致的缩进（空格或 Tab）。",
                        auto_fixable=False,
                        priority=1,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.IMPORT_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="检查模块是否已安装",
                        confidence=FixConfidence.HIGH,
                        explanation="模块可能未安装。尝试使用 pip install 安装所需模块。",
                        auto_fixable=False,
                        priority=1,
                    ),
                    FixSuggestion(
                        description="检查模块名称是否正确",
                        confidence=FixConfidence.MEDIUM,
                        explanation="确认模块名称拼写正确。",
                        auto_fixable=False,
                        priority=0,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.INDENTATION_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="修复缩进错误",
                        confidence=FixConfidence.HIGH,
                        explanation="缩进不一致。确保同级代码块使用相同缩进。",
                        auto_fixable=True,
                        priority=1,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.ZERO_DIVISION_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="添加除零检查",
                        confidence=FixConfidence.HIGH,
                        code_before="result = a / b",
                        code_after="result = a / b if b != 0 else default",
                        explanation="在除法前检查除数是否为零。",
                        auto_fixable=True,
                        priority=1,
                    ),
                ]
            )

        elif error_info.error_type == ErrorType.MODSDK_ERROR:
            suggestions.extend(
                [
                    FixSuggestion(
                        description="检查 ModSDK API 参数",
                        confidence=FixConfidence.HIGH,
                        explanation="ModSDK API 调用失败。检查参数类型和值是否正确。",
                        auto_fixable=False,
                        priority=1,
                    ),
                    FixSuggestion(
                        description="确认游戏对象是否存在",
                        confidence=FixConfidence.MEDIUM,
                        explanation="API 调用可能需要特定游戏对象存在。",
                        auto_fixable=False,
                        priority=0,
                    ),
                ]
            )

        else:
            suggestions.append(
                FixSuggestion(
                    description="查看错误消息了解详情",
                    confidence=FixConfidence.LOW,
                    explanation=f"未知错误类型：{error_info.message}",
                    auto_fixable=False,
                    priority=0,
                )
            )

        # 按优先级排序
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        return suggestions

    def _get_related_docs(self, error_info: ErrorInfo) -> list[str]:
        """获取相关文档链接"""
        docs = []

        if error_info.error_type == ErrorType.MODSDK_ERROR:
            docs.extend(
                [
                    "ModSDK API 文档",
                    "Apollo 开发指南",
                ]
            )

        return docs

    def _find_similar_issues(self, error_info: ErrorInfo) -> list[str]:
        """查找类似问题"""
        # 在实际实现中，可以查询知识库或在线问题库
        return []

    def analyze_code(self, code: str) -> list[ErrorInfo]:
        """
        分析代码，检测潜在错误。

        Args:
            code: Python 代码

        Returns:
            检测到的错误列表
        """
        errors = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(
                ErrorInfo(
                    error_type=ErrorType.SYNTAX_ERROR,
                    message=str(e),
                    raw_log=code,
                    line_number=e.lineno,
                    column=e.offset,
                )
            )

        return errors

    def get_fixable_errors(self) -> list[ErrorType]:
        """获取可自动修复的错误类型"""
        return [
            ErrorType.KEY_ERROR,
            ErrorType.ATTRIBUTE_ERROR,
            ErrorType.INDEX_ERROR,
            ErrorType.ZERO_DIVISION_ERROR,
            ErrorType.INDENTATION_ERROR,
        ]
