"""
增强代码生成模块

提供多文件代码生成、代码审查、风格统一和质量评分功能。
"""

from __future__ import annotations

import ast
import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class CodeStyleType(Enum):
    """代码风格类型"""
    PEP8 = "pep8"
    GOOGLE = "google"
    NUMPY = "numpy"
    MODSDK = "modsdk"


class QualityDimension(Enum):
    """质量维度"""
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MODSDK_COMPLIANCE = "modsdk_compliance"


@dataclass
class GeneratedFile:
    """生成的文件"""
    path: str
    content: str
    language: str = "python"
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "language": self.language,
            "description": self.description,
            "dependencies": self.dependencies,
            "imports": self.imports,
        }


@dataclass
class MultiFileGenerationResult:
    """多文件生成结果"""
    files: list[GeneratedFile]
    success: bool
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": [f.to_dict() for f in self.files],
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class CodeReviewIssue:
    """代码审查问题"""
    file_path: str
    line_number: int
    column: int
    severity: str  # error, warning, info
    message: str
    rule_id: str
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
        }


@dataclass
class CodeReviewResult:
    """代码审查结果"""
    issues: list[CodeReviewIssue]
    score: float
    passed: bool
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "score": round(self.score, 2),
            "passed": self.passed,
            "summary": self.summary,
        }


@dataclass
class RefactorSuggestion:
    """重构建议"""
    file_path: str
    start_line: int
    end_line: int
    original_code: str
    suggested_code: str
    reason: str
    impact: str  # low, medium, high
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "original_code": self.original_code,
            "suggested_code": self.suggested_code,
            "reason": self.reason,
            "impact": self.impact,
            "category": self.category,
        }


@dataclass
class QualityScore:
    """质量评分"""
    overall: float
    dimensions: dict[str, float]
    grade: str  # A, B, C, D, F
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": round(self.overall, 2),
            "dimensions": {k: round(v, 2) for k, v in self.dimensions.items()},
            "grade": self.grade,
            "recommendations": self.recommendations,
        }


class MultiFileGenerator:
    """
    多文件代码生成器

    支持同时生成多个相关文件，保持一致性。
    """

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}
        self._lock = threading.Lock()

    def generate_project_files(
        self,
        project_name: str,
        project_type: str = "empty",
        output_dir: str = ".",
        variables: dict[str, Any] | None = None,
    ) -> MultiFileGenerationResult:
        """
        生成项目文件

        Args:
            project_name: 项目名称
            project_type: 项目类型 (empty, entity, item, block, full)
            output_dir: 输出目录
            variables: 变量

        Returns:
            MultiFileGenerationResult: 生成结果
        """
        files: list[GeneratedFile] = []
        vars_dict = variables or {}
        vars_dict["project_name"] = project_name

        try:
            # 生成 manifest 文件
            files.append(self._generate_manifest(project_name, vars_dict))
            
            # 生成主脚本
            files.append(self._generate_main_script(project_name, vars_dict))

            # 根据项目类型添加额外文件
            if project_type in ("entity", "full"):
                files.extend(self._generate_entity_files(project_name, vars_dict))
            
            if project_type in ("item", "full"):
                files.extend(self._generate_item_files(project_name, vars_dict))
            
            if project_type in ("block", "full"):
                files.extend(self._generate_block_files(project_name, vars_dict))

            return MultiFileGenerationResult(
                files=files,
                success=True,
                metadata={"project_type": project_type, "output_dir": output_dir},
            )

        except Exception as e:
            return MultiFileGenerationResult(
                files=files,
                success=False,
                error=str(e),
            )

    def _generate_manifest(self, name: str, variables: dict[str, Any]) -> GeneratedFile:
        """生成 manifest.json"""
        content = f'''{{
    "format_version": 1,
    "header": {{
        "name": "{name}",
        "description": "{variables.get('description', 'A ModSDK Addon')}",
        "version": [1, 0, 0],
        "min_engine_version": [1, 0, 0]
    }},
    "modules": [
        {{
            "type": "python",
            "version": [1, 0, 0],
            "entry": "main.py"
        }}
    ]
}}'''
        return GeneratedFile(
            path="manifest.json",
            content=content,
            language="json",
            description="ModSDK manifest file",
        )

    def _generate_main_script(self, name: str, variables: dict[str, Any]) -> GeneratedFile:
        """生成主脚本"""
        content = f'''# -*- coding: utf-8 -*-
"""
{name} - Main Script
{variables.get('description', 'A ModSDK Addon')}
"""

import mod.server.extraServerApi as serverApi

# 获取引擎组件工厂
comp_factory = serverApi.GetEngineCompFactory()

def Main():
    """主入口函数"""
    print("[{name}] Addon loaded successfully!")
    
    # 在这里添加你的初始化代码
    # 例如：注册事件监听、创建实体等

# 模块入口
Main()
'''
        return GeneratedFile(
            path="main.py",
            content=content,
            language="python",
            description="Main entry script",
            imports=["mod.server.extraServerApi"],
        )

    def _generate_entity_files(
        self,
        project_name: str,
        variables: dict[str, Any],
    ) -> list[GeneratedFile]:
        """生成实体相关文件"""
        entity_name = variables.get("entity_name", "custom_entity")
        
        # 实体配置
        entity_json = f'''{{
    "format_version": "1.10.0",
    "minecraft:entity": {{
        "description": {{
            "identifier": "{project_name}:{entity_name}",
            "is_spawnable": true,
            "is_summonable": true
        }},
        "components": {{
            "minecraft:type_family": {{
                "family": ["mob"]
            }},
            "minecraft:health": {{
                "value": 20,
                "max": 20
            }},
            "minecraft:movement": {{
                "value": 0.25
            }}
        }}
    }}
}}'''
        
        # 实体脚本
        entity_py = f'''# -*- coding: utf-8 -*-
"""
{entity_name} Entity Script
"""

import mod.server.extraServerApi as serverApi

comp_factory = serverApi.GetEngineCompFactory()

class {entity_name.title().replace("_", "")}Entity:
    """自定义实体类"""
    
    def __init__(self, entity_id):
        self.entity_id = entity_id
        self._setup_components()
    
    def _setup_components(self):
        """设置组件"""
        pass
    
    def on_tick(self):
        """每帧更新"""
        pass

def create_entity(pos):
    """创建实体"""
    # 实体创建逻辑
    pass
'''
        
        return [
            GeneratedFile(
                path=f"entities/{entity_name}.json",
                content=entity_json,
                language="json",
                description=f"Entity configuration for {entity_name}",
            ),
            GeneratedFile(
                path=f"scripts/{entity_name}.py",
                content=entity_py,
                language="python",
                description=f"Entity script for {entity_name}",
            ),
        ]

    def _generate_item_files(
        self,
        project_name: str,
        variables: dict[str, Any],
    ) -> list[GeneratedFile]:
        """生成物品相关文件"""
        item_name = variables.get("item_name", "custom_item")
        
        item_json = f'''{{
    "format_version": "1.10.0",
    "minecraft:item": {{
        "description": {{
            "identifier": "{project_name}:{item_name}",
            "category": "Equipment"
        }},
        "components": {{
            "minecraft:icon": "{item_name}",
            "minecraft:max_stack_size": 64
        }}
    }}
}}'''
        
        item_py = f'''# -*- coding: utf-8 -*-
"""
{item_name} Item Script
"""

import mod.server.extraServerApi as serverApi

def register_item():
    """注册物品"""
    pass

def on_use(player_id, item_data):
    """物品使用回调"""
    pass
'''
        
        return [
            GeneratedFile(
                path=f"items/{item_name}.json",
                content=item_json,
                language="json",
                description=f"Item configuration for {item_name}",
            ),
            GeneratedFile(
                path=f"scripts/{item_name}_item.py",
                content=item_py,
                language="python",
                description=f"Item script for {item_name}",
            ),
        ]

    def _generate_block_files(
        self,
        project_name: str,
        variables: dict[str, Any],
    ) -> list[GeneratedFile]:
        """生成方块相关文件"""
        block_name = variables.get("block_name", "custom_block")
        
        block_json = f'''{{
    "format_version": "1.10.0",
    "minecraft:block": {{
        "description": {{
            "identifier": "{project_name}:{block_name}",
            "register_to_creative_menu": true
        }},
        "components": {{
            "minecraft:destroy_time": 1.0,
            "minecraft:explosion_resistance": 1.0
        }}
    }}
}}'''
        
        block_py = f'''# -*- coding: utf-8 -*-
"""
{block_name} Block Script
"""

import mod.server.extraServerApi as serverApi

def register_block():
    """注册方块"""
    pass

def on_place(player_id, pos):
    """方块放置回调"""
    pass

def on_destroy(player_id, pos):
    """方块破坏回调"""
    pass
'''
        
        return [
            GeneratedFile(
                path=f"blocks/{block_name}.json",
                content=block_json,
                language="json",
                description=f"Block configuration for {block_name}",
            ),
            GeneratedFile(
                path=f"scripts/{block_name}_block.py",
                content=block_py,
                language="python",
                description=f"Block script for {block_name}",
            ),
        ]


class CodeReviewer:
    """
    代码审查器

    检查代码质量，发现问题并提供改进建议。
    """

    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = []
        self._load_builtin_rules()

    def _load_builtin_rules(self) -> None:
        """加载内置审查规则"""
        self._rules = [
            {
                "id": "missing_docstring",
                "check": self._check_docstring,
                "severity": "info",
                "message": "Function missing docstring",
            },
            {
                "id": "long_function",
                "check": self._check_long_function,
                "severity": "warning",
                "message": "Function is too long",
            },
            {
                "id": "too_many_params",
                "check": self._check_too_many_params,
                "severity": "warning",
                "message": "Function has too many parameters",
            },
            {
                "id": "bare_except",
                "check": self._check_bare_except,
                "severity": "error",
                "message": "Bare except clause",
            },
            {
                "id": "unused_import",
                "check": self._check_unused_import,
                "severity": "warning",
                "message": "Potentially unused import",
            },
            {
                "id": "hardcoded_path",
                "check": self._check_hardcoded_path,
                "severity": "info",
                "message": "Hardcoded file path",
            },
            {
                "id": "modsdk_import",
                "check": self._check_modsdk_import,
                "severity": "error",
                "message": "Incorrect ModSDK import",
            },
        ]

    def review(self, code: str, file_path: str = "") -> CodeReviewResult:
        """
        审查代码

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            CodeReviewResult: 审查结果
        """
        issues: list[CodeReviewIssue] = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return CodeReviewResult(
                issues=[CodeReviewIssue(
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    column=e.offset or 0,
                    severity="error",
                    message=f"Syntax error: {e.msg}",
                    rule_id="syntax_error",
                )],
                score=0,
                passed=False,
                summary={"error": 1},
            )

        # 运行所有规则
        for rule in self._rules:
            rule_issues = rule["check"](tree, code, file_path)
            for issue in rule_issues:
                issue.rule_id = rule["id"]
                issue.severity = rule["severity"]
                issue.message = rule["message"]
                issues.append(issue)

        # 计算分数
        score = self._calculate_score(issues)
        passed = score >= 60 and not any(i.severity == "error" for i in issues)
        
        # 统计
        summary: dict[str, int] = defaultdict(int)
        for issue in issues:
            summary[issue.severity] += 1

        return CodeReviewResult(
            issues=issues,
            score=score,
            passed=passed,
            summary=dict(summary),
        )

    def _check_docstring(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查文档字符串"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append(CodeReviewIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        severity="info",
                        message="",
                        rule_id="",
                        suggestion=f"Add docstring to {node.name}",
                    ))
        return issues

    def _check_long_function(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查过长函数"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = node.end_lineno or node.lineno
                length = end_line - node.lineno + 1
                if length > 50:
                    issues.append(CodeReviewIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        severity="warning",
                        message="",
                        rule_id="",
                        suggestion=f"Consider breaking down {node.name} ({length} lines)",
                    ))
        return issues

    def _check_too_many_params(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查参数过多"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1
                if param_count > 5:
                    issues.append(CodeReviewIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        severity="warning",
                        message="",
                        rule_id="",
                        suggestion=f"Consider reducing parameters in {node.name} ({param_count} params)",
                    ))
        return issues

    def _check_bare_except(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查裸 except"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(CodeReviewIssue(
                    file_path=file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    severity="error",
                    message="",
                    rule_id="",
                    suggestion="Use 'except Exception as e:' instead",
                ))
        return issues

    def _check_unused_import(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查未使用的导入"""
        issues = []
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.add(name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.add(name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = imports - used_names
        for name in unused:
            # 找到导入行号
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if (alias.asname or alias.name) == name:
                            issues.append(CodeReviewIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                column=node.col_offset,
                                severity="warning",
                                message="",
                                rule_id="",
                                suggestion=f"Remove unused import: {name}",
                            ))
        return issues

    def _check_hardcoded_path(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查硬编码路径"""
        issues = []
        path_pattern = re.compile(r'["\'](/[a-zA-Z0-9_/.-]+|[A-Z]:\\[a-zA-Z0-9_\\.-]+)["\']')
        
        for i, line in enumerate(code.split("\n"), 1):
            if path_pattern.search(line):
                issues.append(CodeReviewIssue(
                    file_path=file_path,
                    line_number=i,
                    column=0,
                    severity="info",
                    message="",
                    rule_id="",
                    suggestion="Consider using configuration for file paths",
                ))
        return issues

    def _check_modsdk_import(self, tree: ast.AST, code: str, file_path: str) -> list[CodeReviewIssue]:
        """检查 ModSDK 导入"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "mod.server" in alias.name or "mod.client" in alias.name:
                        # 检查是否有 as 别名
                        if not alias.asname:
                            issues.append(CodeReviewIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                column=node.col_offset,
                                severity="info",
                                message="",
                                rule_id="",
                                suggestion="Consider using alias for ModSDK imports",
                            ))
        return issues

    def _calculate_score(self, issues: list[CodeReviewIssue]) -> float:
        """计算质量分数"""
        if not issues:
            return 100.0
        
        penalties = {"error": 20, "warning": 5, "info": 1}
        total_penalty = sum(penalties.get(i.severity, 1) for i in issues)
        
        return max(0, 100 - total_penalty)


class CodeStyleUnifier:
    """
    代码风格统一器

    统一代码风格，支持多种风格规范。
    """

    def __init__(self, style: CodeStyleType = CodeStyleType.PEP8) -> None:
        self.style = style
        self._rules: dict[str, Callable[[str], str]] = {}
        self._load_rules()

    def _load_rules(self) -> None:
        """加载风格规则"""
        self._rules = {
            "trailing_whitespace": self._fix_trailing_whitespace,
            "blank_lines": self._fix_blank_lines,
            "indentation": self._fix_indentation,
            "line_length": self._fix_line_length,
            "imports": self._fix_imports,
        }

    def unify(self, code: str) -> str:
        """
        统一代码风格

        Args:
            code: 原始代码

        Returns:
            str: 统一风格后的代码
        """
        result = code
        for rule_name, rule_func in self._rules.items():
            result = rule_func(result)
        return result

    def _fix_trailing_whitespace(self, code: str) -> str:
        """移除行尾空白"""
        lines = code.split("\n")
        return "\n".join(line.rstrip() for line in lines)

    def _fix_blank_lines(self, code: str) -> str:
        """修复多余空行"""
        # 最多允许两个连续空行
        lines = code.split("\n")
        result: list[str] = []
        blank_count = 0
        
        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        return "\n".join(result)

    def _fix_indentation(self, code: str) -> str:
        """修复缩进（使用 4 空格）"""
        lines = code.split("\n")
        result: list[str] = []
        
        for line in lines:
            if line.strip() == "":
                result.append(line)
            else:
                # 将制表符转换为空格
                new_line = line.replace("\t", "    ")
                result.append(new_line)
        
        return "\n".join(result)

    def _fix_line_length(self, code: str) -> str:
        """处理长行（仅标记，不自动拆分）"""
        # 这里只做标记，实际拆分需要更复杂的处理
        return code

    def _fix_imports(self, code: str) -> str:
        """整理导入顺序"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code
        
        # 提取导入
        imports: list[str] = []
        from_imports: list[str] = []
        other_lines: list[str] = []
        
        lines = code.split("\n")
        import_section = True
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import "):
                imports.append(line)
            elif stripped.startswith("from "):
                from_imports.append(line)
            elif import_section and stripped == "":
                continue
            else:
                import_section = False
                other_lines.append(line)
        
        # 排序并重组
        sorted_imports = sorted(set(imports))
        sorted_from_imports = sorted(set(from_imports))
        
        new_imports = sorted_imports + sorted_from_imports
        if new_imports:
            new_imports.append("")  # 导入后空行
        
        return "\n".join(new_imports + other_lines)


class QualityScorer:
    """
    代码质量评分器

    从多个维度评估代码质量。
    """

    def __init__(self) -> None:
        self.reviewer = CodeReviewer()

    def score(self, code: str) -> QualityScore:
        """
        评估代码质量

        Args:
            code: 代码内容

        Returns:
            QualityScore: 质量评分
        """
        dimensions: dict[str, float] = {}
        recommendations: list[str] = []

        # 可读性
        dimensions["readability"] = self._score_readability(code)
        if dimensions["readability"] < 70:
            recommendations.append("Add more docstrings and comments")

        # 可维护性
        review_result = self.reviewer.review(code)
        dimensions["maintainability"] = review_result.score
        if dimensions["maintainability"] < 70:
            recommendations.append("Refactor long functions and reduce complexity")

        # 性能
        dimensions["performance"] = self._score_performance(code)
        if dimensions["performance"] < 70:
            recommendations.append("Optimize performance-critical sections")

        # 安全性
        dimensions["security"] = self._score_security(code)
        if dimensions["security"] < 70:
            recommendations.append("Review security vulnerabilities")

        # ModSDK 合规性
        dimensions["modsdk_compliance"] = self._score_modsdk_compliance(code)
        if dimensions["modsdk_compliance"] < 70:
            recommendations.append("Follow ModSDK best practices")

        # 计算总分
        overall = sum(dimensions.values()) / len(dimensions)

        # 等级
        if overall >= 90:
            grade = "A"
        elif overall >= 80:
            grade = "B"
        elif overall >= 70:
            grade = "C"
        elif overall >= 60:
            grade = "D"
        else:
            grade = "F"

        return QualityScore(
            overall=overall,
            dimensions=dimensions,
            grade=grade,
            recommendations=recommendations,
        )

    def _score_readability(self, code: str) -> float:
        """评估可读性"""
        score = 100.0
        lines = code.split("\n")
        
        # 检查注释率
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        comment_ratio = comment_lines / len(lines) if lines else 0
        if comment_ratio < 0.1:
            score -= 10
        
        # 检查文档字符串
        if '"""' not in code and "'''" not in code:
            score -= 10
        
        return max(0, score)

    def _score_performance(self, code: str) -> float:
        """评估性能"""
        score = 100.0
        
        # 检查常见性能问题
        if "for i in range(len(" in code:
            score -= 5
        if "while True:" in code and "break" not in code:
            score -= 10
        if code.count("for ") > 5 and "yield" not in code:
            score -= 5
        
        return max(0, score)

    def _score_security(self, code: str) -> float:
        """评估安全性"""
        score = 100.0
        
        dangerous_patterns = [
            (r"eval\s*\(", "eval() usage"),
            (r"exec\s*\(", "exec() usage"),
            (r"__import__\s*\(", "__import__() usage"),
            (r"subprocess", "subprocess usage"),
            (r"os\.system", "os.system usage"),
        ]
        
        for pattern, _ in dangerous_patterns:
            if re.search(pattern, code):
                score -= 20
        
        return max(0, score)

    def _score_modsdk_compliance(self, code: str) -> float:
        """评估 ModSDK 合规性"""
        score = 100.0
        
        # 检查是否使用正确的 API
        if "serverApi" in code or "clientApi" in code:
            # 使用了 ModSDK API
            score += 0  # 基础分
        else:
            # 没有使用 ModSDK API，可能是普通 Python 代码
            return 100.0  # 不扣分
        
        # 检查是否有事件监听
        if "ListenEvent" not in code and "监听" not in code:
            score -= 5
        
        # 检查是否有错误处理
        if "try:" not in code and "except" not in code:
            score -= 10
        
        return max(0, score)


class RefactorEngine:
    """
    重构建议引擎

    分析代码并提供重构建议。
    """

    def __init__(self) -> None:
        self.reviewer = CodeReviewer()

    def analyze(self, code: str, file_path: str = "") -> list[RefactorSuggestion]:
        """
        分析代码并提供重构建议

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            list[RefactorSuggestion]: 重构建议列表
        """
        suggestions: list[RefactorSuggestion] = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return suggestions

        # 分析重复代码
        suggestions.extend(self._find_duplicate_code(code, file_path))
        
        # 分析复杂条件
        suggestions.extend(self._find_complex_conditions(tree, file_path))
        
        # 分析长函数
        suggestions.extend(self._find_long_functions(tree, file_path))

        return suggestions

    def _find_duplicate_code(self, code: str, file_path: str) -> list[RefactorSuggestion]:
        """查找重复代码"""
        suggestions = []
        lines = code.split("\n")
        
        # 简单的重复检测（连续相同行）
        seen_blocks: dict[str, list[int]] = {}
        current_block: list[str] = []
        block_start = 0
        
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#"):
                if not current_block:
                    block_start = i
                current_block.append(line)
            else:
                if len(current_block) >= 3:
                    block_key = "\n".join(current_block)
                    if block_key in seen_blocks:
                        for start in seen_blocks[block_key]:
                            suggestions.append(RefactorSuggestion(
                                file_path=file_path,
                                start_line=start + 1,
                                end_line=start + len(current_block),
                                original_code=block_key,
                                suggested_code="# Consider extracting to a function",
                                reason="Duplicate code block detected",
                                impact="medium",
                                category="duplicate",
                            ))
                        seen_blocks[block_key].append(block_start)
                    else:
                        seen_blocks[block_key] = [block_start]
                current_block = []
        
        return suggestions

    def _find_complex_conditions(
        self,
        tree: ast.AST,
        file_path: str,
    ) -> list[RefactorSuggestion]:
        """查找复杂条件"""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # 计算条件复杂度
                complexity = self._count_conditions(node.test)
                if complexity > 3:
                    suggestions.append(RefactorSuggestion(
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        original_code="complex if condition",
                        suggested_code="# Consider extracting to a separate function",
                        reason=f"Complex condition (complexity: {complexity})",
                        impact="low",
                        category="complexity",
                    ))
        
        return suggestions

    def _find_long_functions(
        self,
        tree: ast.AST,
        file_path: str,
    ) -> list[RefactorSuggestion]:
        """查找长函数"""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = node.end_lineno or node.lineno
                length = end_line - node.lineno + 1
                if length > 30:
                    suggestions.append(RefactorSuggestion(
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=end_line,
                        original_code=f"def {node.name}(...):",
                        suggested_code="# Consider breaking into smaller functions",
                        reason=f"Function too long ({length} lines)",
                        impact="medium",
                        category="length",
                    ))
        
        return suggestions

    def _count_conditions(self, node: ast.expr) -> int:
        """计算条件复杂度"""
        if isinstance(node, ast.BoolOp):
            return sum(self._count_conditions(v) for v in node.values)
        elif isinstance(node, ast.Compare):
            return 1
        elif isinstance(node, ast.UnaryOp):
            return self._count_conditions(node.operand)
        else:
            return 1


# 便捷函数
def generate_project_files(
    project_name: str,
    project_type: str = "empty",
    variables: dict[str, Any] | None = None,
) -> MultiFileGenerationResult:
    """生成项目文件"""
    generator = MultiFileGenerator()
    return generator.generate_project_files(project_name, project_type, ".", variables)


def review_code(code: str, file_path: str = "") -> CodeReviewResult:
    """审查代码"""
    reviewer = CodeReviewer()
    return reviewer.review(code, file_path)


def unify_code_style(code: str, style: CodeStyleType = CodeStyleType.PEP8) -> str:
    """统一代码风格"""
    unifier = CodeStyleUnifier(style)
    return unifier.unify(code)


def score_code_quality(code: str) -> QualityScore:
    """评估代码质量"""
    scorer = QualityScorer()
    return scorer.score(code)


def analyze_refactor_opportunities(code: str, file_path: str = "") -> list[RefactorSuggestion]:
    """分析重构机会"""
    engine = RefactorEngine()
    return engine.analyze(code, file_path)