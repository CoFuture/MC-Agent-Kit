"""
增强错误诊断模块

提供错误模式识别、自动修复建议、错误知识库、统计报告和预测功能。
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorPatternType(Enum):
    """错误模式类型"""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MODSDK = "modsdk"


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PredictionConfidence(Enum):
    """预测信心"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ErrorPattern:
    """错误模式定义"""
    id: str
    name: str
    pattern_type: ErrorPatternType
    severity: ErrorSeverity
    regex_pattern: str
    description: str
    common_causes: list[str]
    fix_suggestions: list[str]
    related_docs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def matches(self, error_text: str) -> bool:
        """检查是否匹配"""
        return bool(re.search(self.regex_pattern, error_text, re.IGNORECASE | re.MULTILINE))


@dataclass
class ErrorKnowledgeEntry:
    """错误知识库条目"""
    id: str
    error_type: str
    error_message_pattern: str
    title: str
    description: str
    causes: list[str]
    solutions: list[str]
    code_examples: list[str] = field(default_factory=list)
    related_apis: list[str] = field(default_factory=list)
    votes: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "error_type": self.error_type,
            "error_message_pattern": self.error_message_pattern,
            "title": self.title,
            "description": self.description,
            "causes": self.causes,
            "solutions": self.solutions,
            "code_examples": self.code_examples,
            "related_apis": self.related_apis,
            "votes": self.votes,
            "success_rate": self.success_rate,
        }


@dataclass
class ErrorStatistics:
    """错误统计"""
    total_errors: int = 0
    errors_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_severity: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_file: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    most_common_patterns: list[tuple[str, int]] = field(default_factory=list)
    error_trend: list[tuple[str, int]] = field(default_factory=list)  # (date, count)
    fix_success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_errors": self.total_errors,
            "errors_by_type": dict(self.errors_by_type),
            "errors_by_severity": dict(self.errors_by_severity),
            "errors_by_file": dict(self.errors_by_file),
            "most_common_patterns": self.most_common_patterns,
            "error_trend": self.error_trend,
            "fix_success_rate": self.fix_success_rate,
        }


@dataclass
class ErrorPrediction:
    """错误预测结果"""
    predicted_error_type: str
    confidence: PredictionConfidence
    probability: float
    triggers: list[str]
    prevention_suggestions: list[str]
    related_patterns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicted_error_type": self.predicted_error_type,
            "confidence": self.confidence.value,
            "probability": round(self.probability, 2),
            "triggers": self.triggers,
            "prevention_suggestions": self.prevention_suggestions,
            "related_patterns": self.related_patterns,
        }


@dataclass
class EnhancedDiagnosisResult:
    """增强诊断结果"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    pattern_match: str | None
    knowledge_entries: list[ErrorKnowledgeEntry]
    auto_fix_suggestions: list[dict[str, Any]]
    statistics: ErrorStatistics | None
    predictions: list[ErrorPrediction]
    raw_error: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "pattern_match": self.pattern_match,
            "knowledge_entries": [e.to_dict() for e in self.knowledge_entries],
            "auto_fix_suggestions": self.auto_fix_suggestions,
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "predictions": [p.to_dict() for p in self.predictions],
            "raw_error": self.raw_error,
        }


class ErrorPatternRecognizer:
    """
    错误模式识别器

    识别已知的错误模式并提供匹配。
    """

    def __init__(self) -> None:
        self._patterns: list[ErrorPattern] = []
        self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """加载内置错误模式"""
        builtin_patterns = [
            # Python 语法错误
            ErrorPattern(
                id="syntax_indentation",
                name="缩进错误",
                pattern_type=ErrorPatternType.SYNTAX,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"IndentationError:\s*(.+)",
                description="代码缩进不正确",
                common_causes=["混合使用空格和制表符", "缩进层级不一致"],
                fix_suggestions=["统一使用空格或制表符", "检查缩进层级"],
                tags=["python", "syntax"],
            ),
            ErrorPattern(
                id="syntax_invalid",
                name="语法错误",
                pattern_type=ErrorPatternType.SYNTAX,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"SyntaxError:\s*(.+)",
                description="Python 语法不正确",
                common_causes=["括号不匹配", "缺少冒号", "字符串未闭合"],
                fix_suggestions=["检查括号配对", "检查语句结尾冒号", "检查字符串引号"],
                tags=["python", "syntax"],
            ),

            # Python 运行时错误
            ErrorPattern(
                id="runtime_name",
                name="名称错误",
                pattern_type=ErrorPatternType.RUNTIME,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"NameError:\s*name\s+['\"](\w+)['\"]\s+is not defined",
                description="使用了未定义的变量或函数",
                common_causes=["变量未声明", "拼写错误", "作用域问题"],
                fix_suggestions=["检查变量是否已定义", "检查拼写是否正确", "检查作用域"],
                tags=["python", "runtime"],
            ),
            ErrorPattern(
                id="runtime_type",
                name="类型错误",
                pattern_type=ErrorPatternType.RUNTIME,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"TypeError:\s*(.+)",
                description="类型操作不正确",
                common_causes=["类型不匹配", "参数类型错误", "None 类型操作"],
                fix_suggestions=["检查变量类型", "添加类型检查", "处理 None 情况"],
                tags=["python", "runtime"],
            ),
            ErrorPattern(
                id="runtime_key",
                name="键错误",
                pattern_type=ErrorPatternType.RUNTIME,
                severity=ErrorSeverity.MEDIUM,
                regex_pattern=r"KeyError:\s*['\"]?(\w+)['\"]?",
                description="字典键不存在",
                common_causes=["键名拼写错误", "键不存在", "数据结构变化"],
                fix_suggestions=["检查键名拼写", "使用 dict.get() 方法", "检查数据结构"],
                tags=["python", "runtime"],
            ),
            ErrorPattern(
                id="runtime_attribute",
                name="属性错误",
                pattern_type=ErrorPatternType.RUNTIME,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"AttributeError:\s*.+\s+has no attribute\s+['\"](\w+)['\"]",
                description="对象没有该属性",
                common_causes=["属性名拼写错误", "对象类型不正确", "模块导入问题"],
                fix_suggestions=["检查属性名拼写", "检查对象类型", "检查导入"],
                tags=["python", "runtime"],
            ),

            # ModSDK 特定错误
            ErrorPattern(
                id="modsdk_api_not_found",
                name="API 未找到",
                pattern_type=ErrorPatternType.MODSDK,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"(GetEngineType|GetConfig|CreateEngine|ListenEvent).*failed|API.*not found",
                description="ModSDK API 调用失败",
                common_causes=["API 名称错误", "作用域错误", "版本不兼容"],
                fix_suggestions=["检查 API 名称", "确认服务端/客户端作用域", "检查版本兼容性"],
                tags=["modsdk", "api"],
            ),
            ErrorPattern(
                id="modsdk_entity_error",
                name="实体操作错误",
                pattern_type=ErrorPatternType.MODSDK,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"(CreateEngineEntity|DestroyEntity|GetEngineEntity).*failed|entity.*error",
                description="实体操作失败",
                common_causes=["实体 ID 无效", "实体未创建", "作用域错误"],
                fix_suggestions=["检查实体 ID", "确认实体已创建", "检查服务端/客户端"],
                tags=["modsdk", "entity"],
            ),
            ErrorPattern(
                id="modsdk_event_error",
                name="事件监听错误",
                pattern_type=ErrorPatternType.MODSDK,
                severity=ErrorSeverity.MEDIUM,
                regex_pattern=r"(ListenEvent|UnListenEvent|NotifyToMultiplayer).*failed|event.*error",
                description="事件监听失败",
                common_causes=["事件名错误", "回调函数问题", "重复监听"],
                fix_suggestions=["检查事件名称", "检查回调函数签名", "避免重复监听"],
                tags=["modsdk", "event"],
            ),

            # 性能错误
            ErrorPattern(
                id="performance_memory",
                name="内存错误",
                pattern_type=ErrorPatternType.PERFORMANCE,
                severity=ErrorSeverity.HIGH,
                regex_pattern=r"MemoryError|Out of memory|内存不足",
                description="内存不足",
                common_causes=["循环引用", "大对象未释放", "内存泄漏"],
                fix_suggestions=["检查循环引用", "及时释放大对象", "使用弱引用"],
                tags=["performance", "memory"],
            ),
            ErrorPattern(
                id="performance_timeout",
                name="超时错误",
                pattern_type=ErrorPatternType.PERFORMANCE,
                severity=ErrorSeverity.MEDIUM,
                regex_pattern=r"TimeoutError|timeout|超时",
                description="操作超时",
                common_causes=["网络延迟", "处理时间过长", "资源竞争"],
                fix_suggestions=["增加超时时间", "优化处理逻辑", "使用异步操作"],
                tags=["performance", "timeout"],
            ),
        ]

        for pattern in builtin_patterns:
            self._patterns.append(pattern)

    def add_pattern(self, pattern: ErrorPattern) -> None:
        """添加自定义模式"""
        self._patterns.append(pattern)

    def recognize(self, error_text: str) -> list[ErrorPattern]:
        """识别错误模式"""
        matched = []
        for pattern in self._patterns:
            if pattern.matches(error_text):
                matched.append(pattern)
        return matched

    def get_pattern(self, pattern_id: str) -> ErrorPattern | None:
        """获取特定模式"""
        for pattern in self._patterns:
            if pattern.id == pattern_id:
                return pattern
        return None

    def list_patterns(self, pattern_type: ErrorPatternType | None = None) -> list[ErrorPattern]:
        """列出所有模式"""
        if pattern_type:
            return [p for p in self._patterns if p.pattern_type == pattern_type]
        return self._patterns.copy()


class ErrorKnowledgeBase:
    """
    错误知识库

    存储和管理已知错误及解决方案。
    """

    def __init__(self) -> None:
        self._entries: dict[str, ErrorKnowledgeEntry] = {}
        self._lock = threading.Lock()
        self._load_builtin_entries()

    def _load_builtin_entries(self) -> None:
        """加载内置知识条目"""
        builtin_entries = [
            ErrorKnowledgeEntry(
                id="kb_nameerror_undefined",
                error_type="NameError",
                error_message_pattern="name '.*' is not defined",
                title="变量未定义错误",
                description="使用了未定义的变量或函数",
                causes=["变量未声明就使用", "函数名拼写错误", "作用域外访问局部变量"],
                solutions=[
                    "在使用前声明变量",
                    "检查变量名拼写",
                    "使用 global 或 nonlocal 声明",
                ],
                code_examples=[
                    "# 错误示例\nprint(undefined_var)\n\n# 正确示例\nundefined_var = 'value'\nprint(undefined_var)",
                ],
                votes=100,
                success_rate=0.95,
            ),
            ErrorKnowledgeEntry(
                id="kb_keyerror_dict",
                error_type="KeyError",
                error_message_pattern="KeyError: .*",
                title="字典键不存在错误",
                description="访问了字典中不存在的键",
                causes=["键名拼写错误", "数据源变化", "嵌套字典层级错误"],
                solutions=[
                    "使用 dict.get(key, default) 方法",
                    "先用 'key in dict' 检查",
                    "检查数据源结构",
                ],
                code_examples=[
                    "# 错误示例\ndata = {'a': 1}\nprint(data['b'])\n\n# 正确示例\ndata = {'a': 1}\nprint(data.get('b', 'default'))",
                ],
                votes=85,
                success_rate=0.90,
            ),
            ErrorKnowledgeEntry(
                id="kb_modsdk_api",
                error_type="ModSDKError",
                error_message_pattern=".*API.*failed.*",
                title="ModSDK API 调用失败",
                description="ModSDK API 调用返回失败",
                causes=["API 名称错误", "作用域不匹配", "参数类型错误"],
                solutions=[
                    "检查 API 名称拼写",
                    "确认当前是服务端还是客户端",
                    "检查参数类型和数量",
                ],
                code_examples=[
                    "# 服务端 API 示例\nimport mod.server.extraServerApi as serverApi\nserverApi.GetEngineCompFactory().CreateEngineEntity()\n\n# 客户端 API 示例\nimport mod.client.extraClientApi as clientApi\nclientApi.GetEngineCompFactory().CreateEngineEntity()",
                ],
                related_apis=["CreateEngineEntity", "GetEngineCompFactory", "ListenEvent"],
                votes=50,
                success_rate=0.85,
            ),
        ]

        with self._lock:
            for entry in builtin_entries:
                self._entries[entry.id] = entry

    def add_entry(self, entry: ErrorKnowledgeEntry) -> None:
        """添加知识条目"""
        with self._lock:
            self._entries[entry.id] = entry

    def search(self, error_text: str, limit: int = 5) -> list[ErrorKnowledgeEntry]:
        """搜索相关条目"""
        results = []
        error_lower = error_text.lower()

        for entry in self._entries.values():
            # 简单的模式匹配
            pattern = entry.error_message_pattern.lower()
            if any(p in error_lower for p in pattern.split(".*")):
                results.append(entry)

        # 按投票数排序
        results.sort(key=lambda x: x.votes, reverse=True)
        return results[:limit]

    def get_entry(self, entry_id: str) -> ErrorKnowledgeEntry | None:
        """获取特定条目"""
        return self._entries.get(entry_id)

    def update_vote(self, entry_id: str, success: bool) -> None:
        """更新投票和成功率"""
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry:
                entry.votes += 1
                if success:
                    # 简单的移动平均
                    entry.success_rate = (entry.success_rate * (entry.votes - 1) + 1) / entry.votes

    def list_entries(self) -> list[ErrorKnowledgeEntry]:
        """列出所有条目"""
        return list(self._entries.values())


class ErrorStatisticsCollector:
    """
    错误统计收集器

    收集和分析错误统计数据。
    """

    def __init__(self) -> None:
        self._stats = ErrorStatistics()
        self._error_history: list[tuple[float, str, str]] = []  # (timestamp, type, file)
        self._lock = threading.Lock()

    def record_error(
        self,
        error_type: str,
        error_message: str,
        file_path: str | None = None,
    ) -> None:
        """记录错误"""
        with self._lock:
            self._stats.total_errors += 1
            self._stats.errors_by_type[error_type] += 1
            
            # 推断严重程度
            severity = self._infer_severity(error_type)
            self._stats.errors_by_severity[severity] += 1
            
            if file_path:
                self._stats.errors_by_file[file_path] += 1
            
            # 记录历史
            self._error_history.append((time.time(), error_type, file_path or ""))
            
            # 更新趋势
            self._update_trend()

    def _infer_severity(self, error_type: str) -> str:
        """推断错误严重程度"""
        critical_types = {"MemoryError", "SystemError", "RecursionError"}
        high_types = {"NameError", "TypeError", "AttributeError", "SyntaxError"}
        medium_types = {"KeyError", "IndexError", "ValueError"}
        
        if error_type in critical_types:
            return "critical"
        elif error_type in high_types:
            return "high"
        elif error_type in medium_types:
            return "medium"
        return "low"

    def _update_trend(self) -> None:
        """更新错误趋势"""
        # 按天聚合
        from datetime import datetime
        daily_counts: dict[str, int] = defaultdict(int)
        
        for timestamp, _, _ in self._error_history:
            date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            daily_counts[date] += 1
        
        self._stats.error_trend = sorted(daily_counts.items())[-30:]  # 最近30天

    def get_statistics(self) -> ErrorStatistics:
        """获取统计"""
        with self._lock:
            # 更新最常见模式
            sorted_types = sorted(
                self._stats.errors_by_type.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            self._stats.most_common_patterns = sorted_types[:10]
            
            return self._stats

    def reset(self) -> None:
        """重置统计"""
        with self._lock:
            self._stats = ErrorStatistics()
            self._error_history.clear()


class ErrorPredictor:
    """
    错误预测器

    基于历史数据和代码模式预测可能发生的错误。
    """

    def __init__(self, statistics: ErrorStatisticsCollector) -> None:
        self._statistics = statistics
        self._prediction_rules: list[dict[str, Any]] = []

    def add_prediction_rule(
        self,
        trigger_patterns: list[str],
        predicted_error: str,
        confidence: PredictionConfidence,
        prevention: list[str],
    ) -> None:
        """添加预测规则"""
        self._prediction_rules.append({
            "triggers": trigger_patterns,
            "predicted_error": predicted_error,
            "confidence": confidence,
            "prevention": prevention,
        })

    def predict(self, code_context: str, recent_errors: list[str]) -> list[ErrorPrediction]:
        """预测可能的错误"""
        predictions = []
        
        # 基于代码模式预测
        code_lower = code_context.lower()
        
        # 规则1: 使用未定义变量风险
        if "import" not in code_lower and any(api in code_lower for api in ["serverapi", "clientapi"]):
            predictions.append(ErrorPrediction(
                predicted_error_type="ImportError",
                confidence=PredictionConfidence.MEDIUM,
                probability=0.6,
                triggers=["ModSDK API 调用但没有导入语句"],
                prevention_suggestions=["确保正确导入 mod.server.extraServerApi 或 mod.client.extraClientApi"],
                related_patterns=["modsdk_api_not_found"],
            ))
        
        # 规则2: 字典访问风险
        if "[" in code_context and "]" in code_context and "get(" not in code_lower:
            predictions.append(ErrorPrediction(
                predicted_error_type="KeyError",
                confidence=PredictionConfidence.LOW,
                probability=0.4,
                triggers=["使用方括号访问字典而非 get 方法"],
                prevention_suggestions=["考虑使用 dict.get(key, default) 方法"],
                related_patterns=["runtime_key"],
            ))
        
        # 规则3: 基于历史错误
        stats = self._statistics.get_statistics()
        for error_type, count in stats.most_common_patterns[:3]:
            if count > 5:
                predictions.append(ErrorPrediction(
                    predicted_error_type=error_type,
                    confidence=PredictionConfidence.MEDIUM,
                    probability=min(count / 10, 0.8),
                    triggers=[f"历史错误频率高: {count} 次"],
                    prevention_suggestions=["检查代码中的常见错误模式"],
                    related_patterns=[],
                ))
        
        return predictions


class EnhancedErrorDiagnoser:
    """
    增强错误诊断器

    集成模式识别、知识库、统计和预测功能。
    """

    def __init__(self) -> None:
        self.pattern_recognizer = ErrorPatternRecognizer()
        self.knowledge_base = ErrorKnowledgeBase()
        self.statistics = ErrorStatisticsCollector()
        self.predictor = ErrorPredictor(self.statistics)

    def diagnose(
        self,
        error_text: str,
        code_context: str | None = None,
        file_path: str | None = None,
    ) -> EnhancedDiagnosisResult:
        """
        诊断错误

        Args:
            error_text: 错误文本
            code_context: 相关代码上下文
            file_path: 文件路径

        Returns:
            EnhancedDiagnosisResult: 增强诊断结果
        """
        # 识别错误模式
        patterns = self.pattern_recognizer.recognize(error_text)
        matched_pattern = patterns[0] if patterns else None
        
        # 确定错误类型和严重程度
        if matched_pattern:
            error_type = matched_pattern.pattern_type.value
            severity = matched_pattern.severity
        else:
            error_type = "unknown"
            severity = ErrorSeverity.MEDIUM
        
        # 提取错误消息
        error_message = self._extract_error_message(error_text)
        
        # 搜索知识库
        knowledge_entries = self.knowledge_base.search(error_text)
        
        # 生成自动修复建议
        auto_fix_suggestions = self._generate_fix_suggestions(
            matched_pattern,
            knowledge_entries,
            error_text,
        )
        
        # 记录统计
        self.statistics.record_error(error_type, error_message, file_path)
        
        # 预测
        predictions = []
        if code_context:
            predictions = self.predictor.predict(code_context, [error_text])
        
        return EnhancedDiagnosisResult(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            pattern_match=matched_pattern.id if matched_pattern else None,
            knowledge_entries=knowledge_entries,
            auto_fix_suggestions=auto_fix_suggestions,
            statistics=None,  # 不在单次诊断中返回完整统计
            predictions=predictions,
            raw_error=error_text,
        )

    def _extract_error_message(self, error_text: str) -> str:
        """提取主要错误消息"""
        lines = error_text.strip().split("\n")
        for line in reversed(lines):
            if "Error:" in line or "Exception:" in line:
                return line.strip()
        return lines[-1] if lines else error_text

    def _generate_fix_suggestions(
        self,
        pattern: ErrorPattern | None,
        knowledge: list[ErrorKnowledgeEntry],
        error_text: str,
    ) -> list[dict[str, Any]]:
        """生成修复建议"""
        suggestions = []
        
        if pattern:
            for i, suggestion in enumerate(pattern.fix_suggestions):
                suggestions.append({
                    "id": f"fix_{i}",
                    "description": suggestion,
                    "confidence": "high" if i == 0 else "medium",
                    "source": "pattern",
                })
        
        for entry in knowledge[:3]:
            for i, solution in enumerate(entry.solutions):
                suggestions.append({
                    "id": f"kb_{entry.id}_{i}",
                    "description": solution,
                    "confidence": "medium",
                    "source": "knowledge_base",
                    "code_example": entry.code_examples[i] if i < len(entry.code_examples) else None,
                })
        
        return suggestions

    def get_statistics_report(self) -> dict[str, Any]:
        """获取统计报告"""
        return self.statistics.get_statistics().to_dict()

    def add_custom_pattern(self, pattern: ErrorPattern) -> None:
        """添加自定义错误模式"""
        self.pattern_recognizer.add_pattern(pattern)

    def add_knowledge_entry(self, entry: ErrorKnowledgeEntry) -> None:
        """添加知识库条目"""
        self.knowledge_base.add_entry(entry)


# 便捷函数
def create_enhanced_diagnoser() -> EnhancedErrorDiagnoser:
    """创建增强诊断器"""
    return EnhancedErrorDiagnoser()


def diagnose_error(
    error_text: str,
    code_context: str | None = None,
) -> EnhancedDiagnosisResult:
    """便捷诊断错误"""
    diagnoser = EnhancedErrorDiagnoser()
    return diagnoser.diagnose(error_text, code_context)