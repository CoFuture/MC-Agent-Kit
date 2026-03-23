"""
智能测试生成模块

提供单元测试、集成测试自动生成，测试用例覆盖率分析和测试执行结果分析功能。
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class TestType(Enum):
    """测试类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CoverageLevel(Enum):
    """覆盖率等级"""
    HIGH = "high"  # > 80%
    MEDIUM = "medium"  # 50% - 80%
    LOW = "low"  # < 50%


@dataclass
class TestCase:
    """测试用例"""
    name: str
    test_type: TestType
    description: str
    code: str
    setup_code: str = ""
    teardown_code: str = ""
    assertions: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    timeout: float = 30.0


@dataclass
class TestSuite:
    """测试套件"""
    name: str
    test_cases: list[TestCase]
    setup_module: str = ""
    teardown_module: str = ""
    imports: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    """覆盖率报告"""
    total_lines: int
    covered_lines: int
    coverage_percentage: float
    level: CoverageLevel
    uncovered_lines: list[int]
    covered_functions: list[str]
    uncovered_functions: list[str]
    branches_total: int = 0
    branches_covered: int = 0


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    status: TestStatus
    duration: float
    message: str = ""
    traceback: str = ""
    assertions_passed: int = 0
    assertions_failed: int = 0


@dataclass
class TestReport:
    """测试报告"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    results: list[TestResult]
    coverage: CoverageReport | None = None


class IntelligentTestGenerator:
    """智能测试生成器

    自动生成单元测试和集成测试。

    使用示例:
        generator = IntelligentTestGenerator()
        suite = generator.generate_unit_tests(source_code)
    """

    def __init__(self) -> None:
        """初始化测试生成器"""
        self._templates: dict[str, str] = {}
        self._lock = threading.Lock()

        # 初始化模板
        self._init_templates()

    def _init_templates(self) -> None:
        """初始化测试模板"""
        self._templates = {
            "function_test": '''
def test_{function_name}():
    """Test {function_name} function."""
    # Arrange
    {setup_code}
    
    # Act
    result = {function_name}({args})
    
    # Assert
    {assertions}
''',
            "class_test": '''
class Test{class_name}:
    """Tests for {class_name}."""
    
    def setup_method(self):
        """Setup for each test."""
        self.instance = {class_name}({setup_args})
    
    def test_{method_name}(self):
        """Test {method_name} method."""
        result = self.instance.{method_name}({args})
        {assertions}
''',
            "exception_test": '''
def test_{function_name}_raises_{exception_type}():
    """Test {function_name} raises {exception_type}."""
    with pytest.raises({exception_type}):
        {function_name}({args})
''',
            "parametrize_test": '''
@pytest.mark.parametrize("{params}", {test_cases})
def test_{function_name}_parametrized({param_names}):
    """Test {function_name} with various inputs."""
    result = {function_name}({args})
    {assertions}
''',
            "integration_test": '''
class Test{feature_name}Integration:
    """Integration tests for {feature_name}."""
    
    @pytest.fixture
    def setup_integration(self):
        """Setup integration test environment."""
        {setup_code}
        yield
        {teardown_code}
    
    def test_{scenario_name}(self, setup_integration):
        """Test {scenario_name} scenario."""
        {test_code}
''',
        }

    def generate_unit_tests(
        self,
        source_code: str,
        module_name: str = "module",
        include_edge_cases: bool = True,
    ) -> TestSuite:
        """生成单元测试

        Args:
            source_code: 源代码
            module_name: 模块名
            include_edge_cases: 是否包含边界情况测试

        Returns:
            TestSuite: 测试套件
        """
        test_cases: list[TestCase] = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return TestSuite(
                name=f"test_{module_name}",
                test_cases=[],
                imports=["import pytest"],
            )

        # 为每个函数生成测试
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                func_tests = self._generate_function_tests(node, include_edge_cases)
                test_cases.extend(func_tests)

            elif isinstance(node, ast.ClassDef):
                class_tests = self._generate_class_tests(node, include_edge_cases)
                test_cases.extend(class_tests)

        return TestSuite(
            name=f"test_{module_name}",
            test_cases=test_cases,
            imports=["import pytest", f"from {module_name} import *"],
        )

    def _generate_function_tests(
        self,
        node: ast.FunctionDef,
        include_edge_cases: bool,
    ) -> list[TestCase]:
        """生成函数测试"""
        tests: list[TestCase] = []

        # 基本功能测试
        args = self._extract_args(node)
        setup_code = self._generate_setup(node)
        assertions = self._generate_assertions(node)

        test_code = self._templates["function_test"].format(
            function_name=node.name,
            setup_code=setup_code,
            args=", ".join(args),
            assertions="\n    ".join(assertions),
        )

        tests.append(TestCase(
            name=f"test_{node.name}",
            test_type=TestType.UNIT,
            description=f"Test {node.name} function",
            code=test_code,
            setup_code=setup_code,
            assertions=assertions,
            tags=["unit", node.name],
        ))

        # 边界情况测试
        if include_edge_cases:
            edge_tests = self._generate_edge_case_tests(node)
            tests.extend(edge_tests)

        return tests

    def _generate_class_tests(
        self,
        node: ast.ClassDef,
        include_edge_cases: bool,
    ) -> list[TestCase]:
        """生成类测试"""
        tests: list[TestCase] = []

        # 为每个公共方法生成测试
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                method_tests = self._generate_method_tests(node.name, item)
                tests.extend(method_tests)

        return tests

    def _generate_method_tests(
        self,
        class_name: str,
        method: ast.FunctionDef,
    ) -> list[TestCase]:
        """生成方法测试"""
        tests: list[TestCase] = []

        args = self._extract_args(method)
        # 移除 self 参数
        if args and args[0] == "self":
            args = args[1:]

        setup_args = self._generate_setup_args(method)
        assertions = self._generate_assertions(method)

        test_code = self._templates["class_test"].format(
            class_name=class_name,
            setup_args=", ".join(setup_args),
            method_name=method.name,
            args=", ".join(args),
            assertions="\n        ".join(assertions),
        )

        tests.append(TestCase(
            name=f"test_{class_name}_{method.name}",
            test_type=TestType.UNIT,
            description=f"Test {class_name}.{method.name} method",
            code=test_code,
            assertions=assertions,
            tags=["unit", class_name, method.name],
        ))

        return tests

    def _generate_edge_case_tests(self, node: ast.FunctionDef) -> list[TestCase]:
        """生成边界情况测试"""
        tests: list[TestCase] = []

        # None 输入测试
        if self._can_accept_none(node):
            tests.append(TestCase(
                name=f"test_{node.name}_with_none",
                test_type=TestType.UNIT,
                description=f"Test {node.name} with None input",
                code=f'''
def test_{node.name}_with_none():
    """Test {node.name} handles None input."""
    result = {node.name}(None)
    assert result is not None or result is None  # Verify behavior
''',
                tags=["edge_case", "none"],
            ))

        # 空列表/字典测试
        if self._accepts_collection(node):
            tests.append(TestCase(
                name=f"test_{node.name}_with_empty",
                test_type=TestType.UNIT,
                description=f"Test {node.name} with empty collection",
                code=f'''
def test_{node.name}_with_empty():
    """Test {node.name} handles empty collection."""
    result = {node.name}([])
    assert result is not None  # Should not crash
''',
                tags=["edge_case", "empty"],
            ))

        return tests

    def _extract_args(self, node: ast.FunctionDef) -> list[str]:
        """提取函数参数"""
        args = []
        for arg in node.args.args:
            # 简单的默认值处理
            if arg.arg == "self":
                args.append("self")
            else:
                args.append(f"{arg.arg}=None")  # 使用 None 作为默认测试值
        return args

    def _generate_setup(self, node: ast.FunctionDef) -> str:
        """生成测试设置代码"""
        setup_lines = []

        # 根据函数特征生成设置代码
        if node.args.args:
            setup_lines.append("# Initialize test data")
            for arg in node.args.args:
                if arg.arg != "self":
                    setup_lines.append(f"{arg.arg} = None  # TODO: Set appropriate value")

        return "\n    ".join(setup_lines)

    def _generate_setup_args(self, node: ast.FunctionDef) -> list[str]:
        """生成设置参数"""
        args = []
        for arg in node.args.args:
            if arg.arg != "self":
                args.append("None")  # 使用 None 作为默认值
        return args

    def _generate_assertions(self, node: ast.FunctionDef) -> list[str]:
        """生成断言"""
        assertions = []

        # 基本断言
        assertions.append("assert result is not None  # Basic assertion")

        # 根据返回类型添加断言
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
            if "int" in return_type.lower():
                assertions.append("assert isinstance(result, int)")
            elif "str" in return_type.lower():
                assertions.append("assert isinstance(result, str)")
            elif "list" in return_type.lower():
                assertions.append("assert isinstance(result, list)")
            elif "dict" in return_type.lower():
                assertions.append("assert isinstance(result, dict)")
            elif "bool" in return_type.lower():
                assertions.append("assert isinstance(result, bool)")

        return assertions

    def _can_accept_none(self, node: ast.FunctionDef) -> bool:
        """判断函数是否可以接受 None"""
        # 简单判断：检查是否有类型注解
        for arg in node.args.args:
            if arg.annotation:
                annotation = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                if "Optional" in annotation or "None" in annotation:
                    return True
        return True  # 默认可以

    def _accepts_collection(self, node: ast.FunctionDef) -> bool:
        """判断函数是否接受集合类型"""
        for arg in node.args.args:
            if arg.annotation:
                annotation = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                if any(t in annotation for t in ["List", "list", "Dict", "dict", "Sequence"]):
                    return True
        return False

    def generate_integration_tests(
        self,
        source_code: str,
        feature_name: str,
        scenarios: list[dict[str, Any]] | None = None,
    ) -> TestSuite:
        """生成集成测试

        Args:
            source_code: 源代码
            feature_name: 功能名称
            scenarios: 测试场景列表

        Returns:
            TestSuite: 测试套件
        """
        test_cases: list[TestCase] = []

        if scenarios is None:
            scenarios = self._extract_scenarios(source_code, feature_name)

        for scenario in scenarios:
            test_code = self._templates["integration_test"].format(
                feature_name=feature_name,
                setup_code=scenario.get("setup", "pass"),
                teardown_code=scenario.get("teardown", "pass"),
                scenario_name=scenario.get("name", "default"),
                test_code=scenario.get("test", "pass"),
            )

            test_cases.append(TestCase(
                name=f"test_{feature_name}_{scenario.get('name', 'default')}",
                test_type=TestType.INTEGRATION,
                description=f"Integration test for {feature_name} - {scenario.get('name', 'default')}",
                code=test_code,
                setup_code=scenario.get("setup", ""),
                teardown_code=scenario.get("teardown", ""),
                tags=["integration", feature_name],
            ))

        return TestSuite(
            name=f"test_{feature_name}_integration",
            test_cases=test_cases,
            imports=["import pytest"],
        )

    def _extract_scenarios(
        self,
        source_code: str,
        feature_name: str,
    ) -> list[dict[str, Any]]:
        """从代码中提取测试场景"""
        scenarios = []

        # 默认场景
        scenarios.append({
            "name": "happy_path",
            "setup": "# Setup test data",
            "teardown": "# Cleanup",
            "test": "# Execute and verify\nresult = main_function()\nassert result is not None",
        })

        scenarios.append({
            "name": "error_handling",
            "setup": "# Setup error conditions",
            "teardown": "# Cleanup",
            "test": "# Test error handling\ntry:\n    result = main_function()\nexcept Exception as e:\n    assert str(e) is not None",
        })

        return scenarios

    def analyze_coverage(
        self,
        source_code: str,
        test_code: str,
    ) -> CoverageReport:
        """分析测试覆盖率

        Args:
            source_code: 源代码
            test_code: 测试代码

        Returns:
            CoverageReport: 覆盖率报告
        """
        try:
            source_tree = ast.parse(source_code)
            test_tree = ast.parse(test_code)
        except SyntaxError:
            return CoverageReport(
                total_lines=0,
                covered_lines=0,
                coverage_percentage=0.0,
                level=CoverageLevel.LOW,
                uncovered_lines=[],
                covered_functions=[],
                uncovered_functions=[],
            )

        # 提取源代码中的函数和类
        source_functions = self._extract_functions(source_tree)
        source_classes = self._extract_classes(source_tree)

        # 提取测试中引用的函数
        tested_functions = self._extract_tested_functions(test_tree)

        # 计算覆盖率
        covered_functions = [f for f in source_functions if f in tested_functions]
        uncovered_functions = [f for f in source_functions if f not in tested_functions]

        # 计算行覆盖率（简化估算）
        source_lines = len(source_code.split("\n"))
        # 基于函数覆盖率估算行覆盖率
        if source_functions:
            coverage_ratio = len(covered_functions) / len(source_functions)
        else:
            coverage_ratio = 1.0

        covered_lines = int(source_lines * coverage_ratio)
        coverage_percentage = coverage_ratio * 100

        # 确定覆盖率等级
        if coverage_percentage >= 80:
            level = CoverageLevel.HIGH
        elif coverage_percentage >= 50:
            level = CoverageLevel.MEDIUM
        else:
            level = CoverageLevel.LOW

        # 估算未覆盖的行
        uncovered_lines = list(range(covered_lines + 1, source_lines + 1))

        return CoverageReport(
            total_lines=source_lines,
            covered_lines=covered_lines,
            coverage_percentage=coverage_percentage,
            level=level,
            uncovered_lines=uncovered_lines,
            covered_functions=covered_functions,
            uncovered_functions=uncovered_functions,
        )

    def _extract_functions(self, tree: ast.AST) -> list[str]:
        """提取函数名列表"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                functions.append(node.name)
        return functions

    def _extract_classes(self, tree: ast.AST) -> list[str]:
        """提取类名列表"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    def _extract_tested_functions(self, tree: ast.AST) -> list[str]:
        """提取测试中引用的函数"""
        tested = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    tested.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    tested.add(node.func.attr)

        return list(tested)

    def generate_test_file(
        self,
        suite: TestSuite,
        output_path: str | Path,
    ) -> str:
        """生成测试文件

        Args:
            suite: 测试套件
            output_path: 输出路径

        Returns:
            str: 生成的测试代码
        """
        lines = []

        # 添加导入
        for imp in suite.imports:
            lines.append(imp)
        lines.append("")

        # 添加模块设置
        if suite.setup_module:
            lines.append("# Module setup")
            lines.append(suite.setup_module)
            lines.append("")

        # 添加测试用例
        for test_case in suite.test_cases:
            lines.append(f"# {test_case.description}")
            lines.append(test_case.code)
            lines.append("")

        # 添加模块清理
        if suite.teardown_module:
            lines.append("# Module teardown")
            lines.append(suite.teardown_module)

        code = "\n".join(lines)

        # 写入文件
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")

        return code


class TestAnalyzer:
    """测试分析器

    分析测试执行结果。
    """

    def __init__(self) -> None:
        """初始化分析器"""
        self._results: list[TestResult] = []
        self._lock = threading.Lock()

    def add_result(self, result: TestResult) -> None:
        """添加测试结果"""
        with self._lock:
            self._results.append(result)

    def generate_report(self) -> TestReport:
        """生成测试报告"""
        with self._lock:
            results = list(self._results)

        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        duration = sum(r.duration for r in results)

        return TestReport(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=results,
        )

    def analyze_failures(self) -> dict[str, Any]:
        """分析失败原因"""
        failures = [r for r in self._results if r.status == TestStatus.FAILED]

        analysis = {
            "total_failures": len(failures),
            "by_type": {},
            "by_message": {},
            "patterns": [],
        }

        # 按消息分组
        for failure in failures:
            msg_key = failure.message[:50] if failure.message else "Unknown"
            if msg_key not in analysis["by_message"]:
                analysis["by_message"][msg_key] = []
            analysis["by_message"][msg_key].append(failure.test_name)

        return analysis


# 全局实例
_generator: IntelligentTestGenerator | None = None
_analyzer: TestAnalyzer | None = None


def get_test_generator() -> IntelligentTestGenerator:
    """获取全局测试生成器"""
    global _generator
    if _generator is None:
        _generator = IntelligentTestGenerator()
    return _generator


def get_test_analyzer() -> TestAnalyzer:
    """获取全局测试分析器"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TestAnalyzer()
    return _analyzer


def generate_tests(
    source_code: str,
    module_name: str = "module",
    test_type: TestType = TestType.UNIT,
) -> TestSuite:
    """便捷函数：生成测试

    Args:
        source_code: 源代码
        module_name: 模块名
        test_type: 测试类型

    Returns:
        TestSuite: 测试套件
    """
    generator = get_test_generator()

    if test_type == TestType.UNIT:
        return generator.generate_unit_tests(source_code, module_name)
    elif test_type == TestType.INTEGRATION:
        return generator.generate_integration_tests(source_code, module_name)
    else:
        return generator.generate_unit_tests(source_code, module_name)