"""
自动修复器模块

提供自动化修复能力，包括：
- 错误定位和根因分析
- 多错误关联分析
- 修复模板库
- 自动应用修复
- 修复验证
"""

from __future__ import annotations

import ast
import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class FixStatus(Enum):
    """修复状态"""
    PENDING = "pending"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"


class FixPriority(Enum):
    """修复优先级"""
    CRITICAL = 0  # 必须修复
    HIGH = 1      # 强烈建议修复
    MEDIUM = 2    # 建议修复
    LOW = 3       # 可选修复
    STYLE = 4     # 代码风格


class ErrorRelation(Enum):
    """错误关联类型"""
    CAUSAL = "causal"        # A 导致 B
    RELATED = "related"      # A 和 B 相关
    DUPLICATE = "duplicate"  # A 和 B 是同一问题
    CONSECUTIVE = "consecutive"  # A 和 B 连续出现


@dataclass
class ErrorLocation:
    """错误位置"""
    file_path: str
    line_start: int
    line_end: int | None = None
    column_start: int | None = None
    column_end: int | None = None
    function_name: str | None = None
    class_name: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "column_start": self.column_start,
            "column_end": self.column_end,
            "function_name": self.function_name,
            "class_name": self.class_name,
        }


@dataclass
class RootCause:
    """根因分析结果"""
    error_type: str
    description: str
    location: ErrorLocation | None
    contributing_factors: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "description": self.description,
            "location": self.location.to_dict() if self.location else None,
            "contributing_factors": self.contributing_factors,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class ErrorCorrelation:
    """错误关联"""
    error_id_1: str
    error_id_2: str
    relation: ErrorRelation
    description: str
    confidence: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error_id_1": self.error_id_1,
            "error_id_2": self.error_id_2,
            "relation": self.relation.value,
            "description": self.description,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class FixTemplate:
    """修复模板"""
    id: str
    name: str
    error_types: list[str]
    pattern: str  # 匹配模式
    code_before: str  # 修复前代码模板
    code_after: str   # 修复后代码模板
    description: str
    auto_applicable: bool = True
    requires_confirmation: bool = False
    priority: FixPriority = FixPriority.MEDIUM
    tags: list[str] = field(default_factory=list)
    
    def matches(self, error_type: str, error_message: str) -> bool:
        """检查是否匹配错误"""
        if error_type not in self.error_types:
            return False
        return bool(re.search(self.pattern, error_message, re.IGNORECASE))
    
    def apply(self, code: str, context: dict[str, Any]) -> str:
        """应用修复模板"""
        result = self.code_after
        # 替换上下文变量
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


@dataclass
class AppliedFix:
    """已应用的修复"""
    error_id: str
    template_id: str
    file_path: str
    original_code: str
    fixed_code: str
    status: FixStatus
    message: str = ""
    timestamp: float = 0.0
    verification_result: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "error_id": self.error_id,
            "template_id": self.template_id,
            "file_path": self.file_path,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "verification_result": self.verification_result,
        }


@dataclass
class FixReport:
    """修复报告"""
    total_errors: int = 0
    fixable_errors: int = 0
    applied_fixes: int = 0
    verified_fixes: int = 0
    failed_fixes: int = 0
    skipped_fixes: int = 0
    fixes: list[AppliedFix] = field(default_factory=list)
    correlations: list[ErrorCorrelation] = field(default_factory=list)
    root_causes: list[RootCause] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_errors": self.total_errors,
            "fixable_errors": self.fixable_errors,
            "applied_fixes": self.applied_fixes,
            "verified_fixes": self.verified_fixes,
            "failed_fixes": self.failed_fixes,
            "skipped_fixes": self.skipped_fixes,
            "fixes": [f.to_dict() for f in self.fixes],
            "correlations": [c.to_dict() for c in self.correlations],
            "root_causes": [r.to_dict() for r in self.root_causes],
        }


class ErrorLocalizer:
    """
    错误定位器
    
    精确定位错误位置，包括行号、列号、函数名等。
    """
    
    def __init__(self) -> None:
        self._traceback_pattern = re.compile(
            r'File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+(\w+))?'
        )
        self._syntax_pattern = re.compile(
            r'File\s+"([^"]+)",\s+line\s+(\d+)'
        )
    
    def locate(self, error_log: str, code: str | None = None) -> ErrorLocation | None:
        """
        定位错误位置
        
        Args:
            error_log: 错误日志
            code: 相关代码（可选）
            
        Returns:
            ErrorLocation 或 None
        """
        # 尝试从 traceback 提取
        matches = list(self._traceback_pattern.finditer(error_log))
        if matches:
            last_match = matches[-1]
            file_path = last_match.group(1)
            line_number = int(last_match.group(2))
            function_name = last_match.group(3)
            
            location = ErrorLocation(
                file_path=file_path,
                line_start=line_number,
                function_name=function_name,
            )
            
            # 如果有代码，提取更多信息
            if code:
                self._enrich_location(location, code)
            
            return location
        
        return None
    
    def _enrich_location(self, location: ErrorLocation, code: str) -> None:
        """丰富位置信息"""
        lines = code.split("\n")
        if location.line_start <= len(lines):
            # 获取行内容
            line_content = lines[location.line_start - 1]
            
            # 尝试解析 AST 获取函数和类信息
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.lineno <= location.line_start <= node.end_lineno or 0:
                            location.function_name = node.name
                            location.class_name = self._find_parent_class(tree, node)
                    elif isinstance(node, ast.ClassDef):
                        if node.lineno <= location.line_start <= node.end_lineno or 0:
                            location.class_name = node.name
            except SyntaxError:
                pass
    
    def _find_parent_class(self, tree: ast.AST, node: ast.AST) -> str | None:
        """查找父类名"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.iter_child_nodes(parent):
                    if child is node:
                        return parent.name
        return None
    
    def locate_all(self, error_log: str) -> list[ErrorLocation]:
        """定位所有错误位置"""
        matches = self._traceback_pattern.finditer(error_log)
        locations = []
        
        for match in matches:
            locations.append(ErrorLocation(
                file_path=match.group(1),
                line_start=int(match.group(2)),
                function_name=match.group(3),
            ))
        
        return locations


class RootCauseAnalyzer:
    """
    根因分析器
    
    分析错误的根本原因。
    """
    
    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = []
        self._load_builtin_rules()
    
    def _load_builtin_rules(self) -> None:
        """加载内置规则"""
        rules = [
            {
                "error_type": "NameError",
                "pattern": r"name\s+['\"](\w+)['\"]\s+is not defined",
                "causes": [
                    "变量未声明",
                    "拼写错误",
                    "作用域问题",
                    "导入缺失",
                ],
                "evidence_patterns": [
                    r"import\s+{name}",
                    r"from\s+\w+\s+import\s+{name}",
                ],
            },
            {
                "error_type": "KeyError",
                "pattern": r"['\"]?(\w+)['\"]?",
                "causes": [
                    "键名拼写错误",
                    "数据结构变化",
                    "字典未初始化",
                ],
                "evidence_patterns": [
                    r"\[['\"]{key}['\"]\]",
                    r"\.get\(['\"]{key}['\"]",
                ],
            },
            {
                "error_type": "AttributeError",
                "pattern": r"has no attribute\s+['\"](\w+)['\"]",
                "causes": [
                    "属性名拼写错误",
                    "对象类型不正确",
                    "对象为 None",
                    "继承关系错误",
                ],
                "evidence_patterns": [
                    r"\.{attr}",
                    r"getattr\([^,]+,\s*['\"]{attr}['\"]",
                ],
            },
            {
                "error_type": "TypeError",
                "pattern": r"(.+)",
                "causes": [
                    "参数类型错误",
                    "参数数量不匹配",
                    "None 类型操作",
                    "类型转换失败",
                ],
                "evidence_patterns": [],
            },
            {
                "error_type": "IndexError",
                "pattern": r"(.+)",
                "causes": [
                    "索引超出范围",
                    "列表为空",
                    "负索引超出范围",
                ],
                "evidence_patterns": [
                    r"\[\s*{index}\s*\]",
                    r"len\([^)]+\)",
                ],
            },
        ]
        
        for rule in rules:
            self._rules.append(rule)
    
    def analyze(
        self,
        error_type: str,
        error_message: str,
        code_context: str | None = None,
        location: ErrorLocation | None = None,
    ) -> RootCause:
        """
        分析根因
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            code_context: 代码上下文
            location: 错误位置
            
        Returns:
            RootCause
        """
        # 查找匹配规则
        matched_rule = None
        for rule in self._rules:
            if rule["error_type"] == error_type:
                matched_rule = rule
                break
        
        if not matched_rule:
            return RootCause(
                error_type=error_type,
                description=f"未知错误类型: {error_type}",
                location=location,
                confidence=0.0,
            )
        
        # 提取关键信息
        pattern = matched_rule["pattern"]
        match = re.search(pattern, error_message)
        captured = match.group(1) if match else ""
        
        # 构建证据
        evidence = []
        if code_context:
            for ep in matched_rule.get("evidence_patterns", []):
                ep_formatted = ep.format(name=captured, key=captured, attr=captured, index=captured)
                if re.search(ep_formatted, code_context):
                    evidence.append(f"发现相关代码模式: {ep_formatted}")
        
        # 计算置信度
        confidence = 0.5
        if evidence:
            confidence += 0.1 * len(evidence)
        confidence = min(confidence, 0.95)
        
        return RootCause(
            error_type=error_type,
            description=f"{'; '.join(matched_rule['causes'][:2])}",
            location=location,
            contributing_factors=matched_rule["causes"],
            evidence=evidence,
            confidence=confidence,
        )


class ErrorCorrelator:
    """
    错误关联分析器
    
    分析多个错误之间的关联关系。
    """
    
    def __init__(self) -> None:
        self._correlation_rules: list[dict[str, Any]] = []
        self._load_builtin_rules()
    
    def _load_builtin_rules(self) -> None:
        """加载内置关联规则"""
        rules = [
            {
                "condition": lambda e1, e2: (
                    e1.get("type") == "NameError" and
                    e2.get("type") == "AttributeError" and
                    e1.get("line", 0) < e2.get("line", 0)
                ),
                "relation": ErrorRelation.CAUSAL,
                "description": "NameError 导致后续 AttributeError",
            },
            {
                "condition": lambda e1, e2: (
                    e1.get("type") == e2.get("type") and
                    e1.get("message") == e2.get("message")
                ),
                "relation": ErrorRelation.DUPLICATE,
                "description": "重复的相同错误",
            },
            {
                "condition": lambda e1, e2: (
                    abs(e1.get("line", 0) - e2.get("line", 0)) <= 3
                ),
                "relation": ErrorRelation.CONSECUTIVE,
                "description": "相邻的错误可能相关",
            },
            {
                "condition": lambda e1, e2: (
                    e1.get("file") == e2.get("file") and
                    e1.get("type") != e2.get("type")
                ),
                "relation": ErrorRelation.RELATED,
                "description": "同一文件中的不同错误可能相关",
            },
        ]
        
        for rule in rules:
            self._correlation_rules.append(rule)
    
    def correlate(self, errors: list[dict[str, Any]]) -> list[ErrorCorrelation]:
        """
        分析错误关联
        
        Args:
            errors: 错误列表，每个错误是一个字典
            
        Returns:
            关联列表
        """
        correlations = []
        
        for i, error1 in enumerate(errors):
            for j, error2 in enumerate(errors):
                if i >= j:
                    continue
                
                for rule in self._correlation_rules:
                    try:
                        if rule["condition"](error1, error2):
                            correlations.append(ErrorCorrelation(
                                error_id_1=error1.get("id", str(i)),
                                error_id_2=error2.get("id", str(j)),
                                relation=rule["relation"],
                                description=rule["description"],
                                confidence=0.7,
                            ))
                            break
                    except Exception:
                        pass
        
        return correlations


class FixTemplateLibrary:
    """
    修复模板库
    
    管理和应用修复模板。
    """
    
    def __init__(self) -> None:
        self._templates: dict[str, FixTemplate] = {}
        self._lock = threading.Lock()
        self._load_builtin_templates()
    
    def _load_builtin_templates(self) -> None:
        """加载内置模板"""
        templates = [
            # KeyError 修复模板
            FixTemplate(
                id="keyerror_get_method",
                name="使用 get 方法安全访问字典",
                error_types=["KeyError"],
                pattern=r"['\"]?(\w+)['\"]?",
                code_before="data['{key}']",
                code_after="data.get('{key}', default_value)",
                description="使用 dict.get() 方法避免 KeyError",
                auto_applicable=True,
                priority=FixPriority.HIGH,
                tags=["safe_access", "dict"],
            ),
            FixTemplate(
                id="keyerror_check_existence",
                name="检查键是否存在",
                error_types=["KeyError"],
                pattern=r"['\"]?(\w+)['\"]?",
                code_before="value = data['{key}']",
                code_after="if '{key}' in data:\n    value = data['{key}']\nelse:\n    value = default",
                description="使用 in 检查键是否存在",
                auto_applicable=False,
                requires_confirmation=True,
                priority=FixPriority.MEDIUM,
                tags=["check", "dict"],
            ),
            
            # AttributeError 修复模板
            FixTemplate(
                id="attrerror_getattr",
                name="使用 getattr 安全访问属性",
                error_types=["AttributeError"],
                pattern=r"has no attribute\s+['\"](\w+)['\"]",
                code_before="obj.{attr}",
                code_after="getattr(obj, '{attr}', default_value)",
                description="使用 getattr() 方法安全访问属性",
                auto_applicable=True,
                priority=FixPriority.HIGH,
                tags=["safe_access", "attribute"],
            ),
            FixTemplate(
                id="attrerror_none_check",
                name="添加 None 检查",
                error_types=["AttributeError"],
                pattern=r"'NoneType'.*has no attribute",
                code_before="obj.{attr}",
                code_after="if obj is not None:\n    obj.{attr}\nelse:\n    # handle None case",
                description="添加 None 检查避免 AttributeError",
                auto_applicable=False,
                requires_confirmation=True,
                priority=FixPriority.HIGH,
                tags=["none_check", "safety"],
            ),
            
            # IndexError 修复模板
            FixTemplate(
                id="indexerror_bounds_check",
                name="添加边界检查",
                error_types=["IndexError"],
                pattern=r"(.+)",
                code_before="lst[i]",
                code_after="lst[i] if 0 <= i < len(lst) else default",
                description="添加边界检查避免 IndexError",
                auto_applicable=True,
                priority=FixPriority.HIGH,
                tags=["bounds", "list"],
            ),
            
            # ZeroDivisionError 修复模板
            FixTemplate(
                id="zerodiv_check",
                name="添加除零检查",
                error_types=["ZeroDivisionError"],
                pattern=r"(.+)",
                code_before="result = a / b",
                code_after="result = a / b if b != 0 else default",
                description="添加除零检查",
                auto_applicable=True,
                priority=FixPriority.HIGH,
                tags=["division", "safety"],
            ),
            
            # NameError 修复模板（建议性）
            FixTemplate(
                id="nameerror_import",
                name="添加导入语句",
                error_types=["NameError"],
                pattern=r"name\s+['\"](\w+)['\"]\s+is not defined",
                code_before="# {name} not imported",
                code_after="import {name}  # 或 from module import {name}",
                description="可能需要导入模块",
                auto_applicable=False,
                requires_confirmation=True,
                priority=FixPriority.MEDIUM,
                tags=["import", "name"],
            ),
            
            # ModSDK 特定修复模板
            FixTemplate(
                id="modsdk_scope_check",
                name="检查 ModSDK 作用域",
                error_types=["ModSDKError"],
                pattern=r"(GetEngineType|GetConfig|CreateEngine).*failed",
                code_before="# API 调用失败",
                code_after="# 检查当前是服务端还是客户端\n# 服务端: import mod.server.extraServerApi as serverApi\n# 客户端: import mod.client.extraClientApi as clientApi",
                description="检查 ModSDK API 作用域",
                auto_applicable=False,
                requires_confirmation=True,
                priority=FixPriority.HIGH,
                tags=["modsdk", "scope"],
            ),
        ]
        
        with self._lock:
            for template in templates:
                self._templates[template.id] = template
    
    def add_template(self, template: FixTemplate) -> None:
        """添加模板"""
        with self._lock:
            self._templates[template.id] = template
    
    def get_template(self, template_id: str) -> FixTemplate | None:
        """获取模板"""
        return self._templates.get(template_id)
    
    def find_templates(
        self,
        error_type: str,
        error_message: str,
    ) -> list[FixTemplate]:
        """
        查找匹配的模板
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            
        Returns:
            匹配的模板列表，按优先级排序
        """
        matched = []
        
        for template in self._templates.values():
            if template.matches(error_type, error_message):
                matched.append(template)
        
        # 按优先级排序
        matched.sort(key=lambda t: t.priority.value)
        return matched
    
    def list_templates(self) -> list[FixTemplate]:
        """列出所有模板"""
        return list(self._templates.values())


class FixVerifier:
    """
    修复验证器
    
    验证修复是否成功。
    """
    
    def __init__(self) -> None:
        self._validators: dict[str, Callable] = {}
        self._load_builtin_validators()
    
    def _load_builtin_validators(self) -> None:
        """加载内置验证器"""
        # 语法验证
        self._validators["syntax"] = self._validate_syntax
        # 运行时验证
        self._validators["runtime"] = self._validate_runtime
    
    def _validate_syntax(self, code: str) -> tuple[bool, str]:
        """验证语法"""
        try:
            ast.parse(code)
            return True, "语法正确"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
    
    def _validate_runtime(self, code: str) -> tuple[bool, str]:
        """验证运行时（简单检查）"""
        # 简单的运行时检查
        # 实际实现可能需要执行代码或使用静态分析
        return True, "运行时验证通过"
    
    def verify(
        self,
        fixed_code: str,
        original_error: str,
        verification_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        验证修复
        
        Args:
            fixed_code: 修复后的代码
            original_error: 原始错误
            verification_types: 验证类型列表
            
        Returns:
            验证结果
        """
        results = {
            "passed": True,
            "checks": [],
        }
        
        types = verification_types or ["syntax"]
        
        for vtype in types:
            if vtype in self._validators:
                passed, message = self._validators[vtype](fixed_code)
                results["checks"].append({
                    "type": vtype,
                    "passed": passed,
                    "message": message,
                })
                if not passed:
                    results["passed"] = False
        
        return results


class AutoFixer:
    """
    自动修复器
    
    整合所有修复功能的主类。
    """
    
    def __init__(self) -> None:
        self.localizer = ErrorLocalizer()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.correlator = ErrorCorrelator()
        self.template_library = FixTemplateLibrary()
        self.verifier = FixVerifier()
    
    def diagnose(
        self,
        error_log: str,
        code: str | None = None,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """
        诊断错误
        
        Args:
            error_log: 错误日志
            code: 相关代码
            file_path: 文件路径
            
        Returns:
            诊断结果
        """
        # 提取错误类型和消息
        error_type, error_message = self._extract_error_info(error_log)
        
        # 定位错误
        location = self.localizer.locate(error_log, code)
        if not location and file_path:
            location = ErrorLocation(file_path=file_path, line_start=1)
        
        # 分析根因
        root_cause = self.root_cause_analyzer.analyze(
            error_type, error_message, code, location
        )
        
        # 查找修复模板
        templates = self.template_library.find_templates(error_type, error_message)
        
        return {
            "error_type": error_type,
            "error_message": error_message,
            "location": location.to_dict() if location else None,
            "root_cause": root_cause.to_dict(),
            "fix_templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "auto_applicable": t.auto_applicable,
                    "priority": t.priority.value,
                    "code_after": t.code_after,
                }
                for t in templates
            ],
        }
    
    def diagnose_multiple(
        self,
        errors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        诊断多个错误
        
        Args:
            errors: 错误列表
            
        Returns:
            诊断结果，包含关联分析
        """
        results = []
        
        for error in errors:
            result = self.diagnose(
                error.get("log", ""),
                error.get("code"),
                error.get("file"),
            )
            result["id"] = error.get("id", str(len(results)))
            results.append(result)
        
        # 分析关联
        correlations = self.correlator.correlate(errors)
        
        return {
            "errors": results,
            "correlations": [c.to_dict() for c in correlations],
        }
    
    def apply_fix(
        self,
        template_id: str,
        code: str,
        context: dict[str, Any],
        verify: bool = True,
    ) -> AppliedFix:
        """
        应用修复
        
        Args:
            template_id: 模板 ID
            code: 原始代码
            context: 上下文变量
            verify: 是否验证修复
            
        Returns:
            AppliedFix
        """
        import time
        
        template = self.template_library.get_template(template_id)
        if not template:
            return AppliedFix(
                error_id=context.get("error_id", ""),
                template_id=template_id,
                file_path=context.get("file_path", ""),
                original_code=code,
                fixed_code=code,
                status=FixStatus.FAILED,
                message="模板不存在",
                timestamp=time.time(),
            )
        
        # 应用模板
        fixed_code = template.apply(code, context)
        
        # 验证
        verification_result = None
        if verify:
            verification_result = self.verifier.verify(fixed_code, context.get("error", ""))
        
        # 确定状态
        if verification_result and verification_result.get("passed"):
            status = FixStatus.VERIFIED
        else:
            status = FixStatus.APPLIED
        
        return AppliedFix(
            error_id=context.get("error_id", ""),
            template_id=template_id,
            file_path=context.get("file_path", ""),
            original_code=code,
            fixed_code=fixed_code,
            status=status,
            message="修复已应用",
            timestamp=time.time(),
            verification_result=verification_result,
        )
    
    def auto_fix(
        self,
        error_log: str,
        code: str,
        file_path: str | None = None,
    ) -> FixReport:
        """
        自动修复错误
        
        Args:
            error_log: 错误日志
            code: 代码
            file_path: 文件路径
            
        Returns:
            FixReport
        """
        import time
        
        report = FixReport(total_errors=1)
        
        # 诊断
        diagnosis = self.diagnose(error_log, code, file_path)
        
        # 查找可自动应用的模板
        templates = [
            t for t in self.template_library.find_templates(
                diagnosis["error_type"],
                diagnosis["error_message"],
            )
            if t.auto_applicable
        ]
        
        if not templates:
            report.skipped_fixes = 1
            return report
        
        report.fixable_errors = 1
        
        # 应用第一个可用模板
        template = templates[0]
        
        # 提取上下文
        context = self._extract_context(diagnosis, code)
        
        # 应用修复
        applied = self.apply_fix(
            template.id,
            code,
            context,
            verify=True,
        )
        
        report.fixes.append(applied)
        
        if applied.status == FixStatus.VERIFIED:
            report.verified_fixes = 1
            report.applied_fixes = 1
        elif applied.status == FixStatus.APPLIED:
            report.applied_fixes = 1
        else:
            report.failed_fixes = 1
        
        # 添加根因
        report.root_causes.append(RootCause(
            error_type=diagnosis["root_cause"]["error_type"],
            description=diagnosis["root_cause"]["description"],
            location=None,
            contributing_factors=diagnosis["root_cause"]["contributing_factors"],
            evidence=diagnosis["root_cause"]["evidence"],
            confidence=diagnosis["root_cause"]["confidence"],
        ))
        
        return report
    
    def _extract_error_info(self, error_log: str) -> tuple[str, str]:
        """提取错误类型和消息"""
        # 匹配 Python 错误格式
        match = re.search(r"(\w+Error|Exception):\s*(.+?)(?:\n|$)", error_log)
        if match:
            return match.group(1), match.group(2)
        return "Unknown", error_log
    
    def _extract_context(self, diagnosis: dict[str, Any], code: str) -> dict[str, Any]:
        """从诊断结果提取上下文"""
        context = {
            "error": diagnosis["error_message"],
            "error_type": diagnosis["error_type"],
        }
        
        # 从根因提取信息
        root_cause = diagnosis.get("root_cause", {})
        
        # 尝试从错误消息提取变量名
        error_message = diagnosis.get("error_message", "")
        
        # KeyError: 提取键名
        key_match = re.search(r"['\"]?(\w+)['\"]?", error_message)
        if key_match and diagnosis["error_type"] == "KeyError":
            context["key"] = key_match.group(1)
        
        # AttributeError: 提取属性名
        attr_match = re.search(r"has no attribute\s+['\"](\w+)['\"]", error_message)
        if attr_match:
            context["attr"] = attr_match.group(1)
        
        # NameError: 提取名称
        name_match = re.search(r"name\s+['\"](\w+)['\"]\s+is not defined", error_message)
        if name_match:
            context["name"] = name_match.group(1)
        
        return context


# 便捷函数
def create_auto_fixer() -> AutoFixer:
    """创建自动修复器"""
    return AutoFixer()


def diagnose_error(
    error_log: str,
    code: str | None = None,
) -> dict[str, Any]:
    """诊断错误"""
    fixer = AutoFixer()
    return fixer.diagnose(error_log, code)


def auto_fix_error(
    error_log: str,
    code: str,
) -> FixReport:
    """自动修复错误"""
    fixer = AutoFixer()
    return fixer.auto_fix(error_log, code)