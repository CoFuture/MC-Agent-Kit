"""
代码执行器模块

执行 Python 代码并捕获结果，支持错误反馈和超时控制。
"""

import ast
import asyncio
import logging
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import StringIO
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""

    SUCCESS = "success"  # 执行成功
    ERROR = "error"  # 执行出错
    TIMEOUT = "timeout"  # 执行超时
    CANCELLED = "cancelled"  # 执行取消


@dataclass
class ExecutionConfig:
    """执行配置"""

    timeout: float = 30.0  # 超时时间（秒）
    capture_output: bool = True  # 是否捕获输出
    capture_locals: bool = True  # 是否捕获局部变量
    allowed_modules: list[str] | None = None  # 允许的模块（None 表示不限制）
    forbidden_modules: list[str] = field(
        default_factory=lambda: [
            "os",
            "subprocess",
            "sys",
            "importlib",
            "ctypes",
        ]
    )  # 禁止的模块
    max_output_size: int = 10000  # 最大输出大小（字符）
    sandbox_mode: bool = True  # 沙箱模式


@dataclass
class ExecutionResult:
    """执行结果"""

    status: ExecutionStatus
    code: str  # 执行的代码
    output: str = ""  # 标准输出
    error: str = ""  # 错误信息
    return_value: Any = None  # 返回值
    locals: dict[str, Any] = field(default_factory=dict)  # 局部变量
    globals: dict[str, Any] = field(default_factory=dict)  # 全局变量
    execution_time: float = 0.0  # 执行时间（秒）
    timestamp: datetime = field(default_factory=datetime.now)  # 执行时间戳
    traceback: str | None = None  # 完整 traceback
    suggestions: list[str] = field(default_factory=list)  # 错误修复建议


class CodeValidator:
    """代码验证器"""

    # 危险的 AST 节点
    DANGEROUS_NODES = {
        ast.Import,
        ast.ImportFrom,
        ast.Global,
        ast.AsyncFunctionDef,
    }

    # 危险的函数调用
    DANGEROUS_CALLS = {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "globals",
        "locals",
        "vars",
    }

    def __init__(self, config: ExecutionConfig):
        self.config = config

    def validate(self, code: str) -> tuple[bool, str]:
        """
        验证代码安全性。

        Args:
            code: 要验证的代码

        Returns:
            (是否安全, 错误消息)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"语法错误: {e}"

        # 检查危险节点
        for node in ast.walk(tree):
            # 检查导入
            if isinstance(node, ast.Import):
                if self.config.sandbox_mode:
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        if module_name in self.config.forbidden_modules:
                            return False, f"禁止导入模块: {module_name}"

            if isinstance(node, ast.ImportFrom):
                if self.config.sandbox_mode and node.module:
                    module_name = node.module.split(".")[0]
                    if module_name in self.config.forbidden_modules:
                        return False, f"禁止导入模块: {module_name}"

            # 检查危险调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_CALLS:
                        return False, f"禁止调用函数: {node.func.id}"

                # 检查属性调用
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.DANGEROUS_CALLS:
                        return False, f"禁止调用方法: {node.func.attr}"

        return True, ""

    def check_syntax(self, code: str) -> tuple[bool, str]:
        """
        检查代码语法。

        Args:
            code: 要检查的代码

        Returns:
            (语法是否正确, 错误消息)
        """
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"语法错误 (行 {e.lineno}): {e.msg}"


class CodeExecutor:
    """
    代码执行器。

    支持执行 Python 代码并捕获结果，提供：
    - 超时控制
    - 输出捕获
    - 错误反馈
    - 安全检查

    使用示例:
        executor = CodeExecutor()
        
        # 执行代码
        result = executor.execute("print('Hello, World!')")
        
        # 执行并获取返回值
        result = executor.execute("x = 1 + 2; x")
        print(result.return_value)  # 3
    """

    def __init__(self, config: ExecutionConfig | None = None):
        """
        初始化执行器。

        Args:
            config: 执行配置
        """
        self.config = config or ExecutionConfig()
        self.validator = CodeValidator(self.config)
        self._execution_count = 0
        self._last_result: ExecutionResult | None = None

    def execute(self, code: str, context: dict[str, Any] | None = None) -> ExecutionResult:
        """
        执行代码。

        Args:
            code: 要执行的代码
            context: 执行上下文（全局变量）

        Returns:
            ExecutionResult: 执行结果
        """
        self._execution_count += 1
        start_time = datetime.now()

        # 验证代码
        if self.config.sandbox_mode:
            is_valid, error_msg = self.validator.validate(code)
            if not is_valid:
                return ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    code=code,
                    error=error_msg,
                    suggestions=["移除危险代码", "在非沙箱模式下执行"],
                )

        # 检查语法
        is_valid, error_msg = self.validator.check_syntax(code)
        if not is_valid:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                code=code,
                error=error_msg,
                suggestions=["检查语法错误", "确保括号和引号匹配"],
            )

        # 准备执行环境
        execution_globals = self._prepare_globals(context)
        execution_locals: dict[str, Any] = {}

        # 捕获输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        if self.config.capture_output:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

        try:
            # 执行代码
            return_value = self._execute_code(
                code, execution_globals, execution_locals
            )

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 获取输出
            output = stdout_capture.getvalue()
            error_output = stderr_capture.getvalue()

            # 截断输出
            if len(output) > self.config.max_output_size:
                output = output[: self.config.max_output_size] + "\n... (输出已截断)"

            result = ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                code=code,
                output=output,
                error=error_output,
                return_value=return_value,
                locals=execution_locals if self.config.capture_locals else {},
                globals=execution_globals,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            tb = traceback.format_exc()

            result = ExecutionResult(
                status=ExecutionStatus.ERROR,
                code=code,
                error=str(e),
                traceback=tb,
                execution_time=execution_time,
                suggestions=self._generate_suggestions(e),
            )

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        self._last_result = result
        return result

    def execute_async(
        self, code: str, context: dict[str, Any] | None = None
    ) -> ExecutionResult:
        """
        异步执行代码（带超时控制）。

        Args:
            code: 要执行的代码
            context: 执行上下文

        Returns:
            ExecutionResult: 执行结果
        """
        # 在实际实现中，这里应该使用线程或进程来执行代码
        # 这里简化为同步执行
        return self.execute(code, context)

    def execute_file(self, file_path: str) -> ExecutionResult:
        """
        执行文件中的代码。

        Args:
            file_path: 文件路径

        Returns:
            ExecutionResult: 执行结果
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                code="",
                error=f"文件不存在: {file_path}",
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                code="",
                error=f"读取文件失败: {e}",
            )

        return self.execute(code)

    def execute_with_timeout(
        self, code: str, timeout: float, context: dict[str, Any] | None = None
    ) -> ExecutionResult:
        """
        带超时控制的执行。

        Args:
            code: 要执行的代码
            timeout: 超时时间（秒）
            context: 执行上下文

        Returns:
            ExecutionResult: 执行结果
        """
        # 保存原配置
        original_timeout = self.config.timeout
        self.config.timeout = timeout

        try:
            # 使用线程池执行（简化版本）
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.execute, code, context)
                try:
                    return future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    return ExecutionResult(
                        status=ExecutionStatus.TIMEOUT,
                        code=code,
                        error=f"执行超时（{timeout}秒）",
                        suggestions=[
                            "检查代码是否存在无限循环",
                            "增加超时时间",
                            "优化代码性能",
                        ],
                    )
        finally:
            self.config.timeout = original_timeout

    def _prepare_globals(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """准备全局执行环境"""
        globals_dict: dict[str, Any] = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
            "__doc__": None,
        }

        if context:
            globals_dict.update(context)

        return globals_dict

    def _execute_code(
        self, code: str, globals_dict: dict[str, Any], locals_dict: dict[str, Any]
    ) -> Any:
        """
        执行代码并返回最后一个表达式的值。

        Args:
            code: 代码
            globals_dict: 全局变量字典
            locals_dict: 局部变量字典

        Returns:
            最后一个表达式的值
        """
        # 尝试解析为表达式
        try:
            tree = ast.parse(code, mode="eval")
            return eval(compile(tree, "<string>", "eval"), globals_dict, locals_dict)
        except SyntaxError:
            # 不是表达式，作为语句执行
            pass

        # 解析为语句
        tree = ast.parse(code, mode="exec")

        # 如果最后一个节点是表达式，提取它
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            # 执行除最后一个表达式外的所有语句
            if len(tree.body) > 1:
                exec(
                    compile(ast.Module(body=tree.body[:-1], type_ignores=[]), "<string>", "exec"),
                    globals_dict,
                    locals_dict,
                )
            # 返回最后一个表达式的值
            last_expr = tree.body[-1]
            return eval(
                compile(ast.Expression(last_expr.value), "<string>", "eval"),
                globals_dict,
                locals_dict,
            )
        else:
            # 执行所有语句
            exec(compile(tree, "<string>", "exec"), globals_dict, locals_dict)
            return None

    def _generate_suggestions(self, error: Exception) -> list[str]:
        """生成错误修复建议"""
        suggestions = []
        error_type = type(error).__name__

        if error_type == "NameError":
            suggestions.append("检查变量名是否拼写正确")
            suggestions.append("确保变量在使用前已定义")
        elif error_type == "TypeError":
            suggestions.append("检查参数类型是否正确")
            suggestions.append("确认操作支持该类型")
        elif error_type == "IndexError":
            suggestions.append("检查索引是否在有效范围内")
        elif error_type == "KeyError":
            suggestions.append("检查键是否存在")
            suggestions.append("使用 .get() 方法安全获取")
        elif error_type == "AttributeError":
            suggestions.append("检查属性名是否正确")
            suggestions.append("确认对象类型")
        else:
            suggestions.append("检查错误消息了解详情")
            suggestions.append("使用调试工具定位问题")

        return suggestions

    def get_last_result(self) -> ExecutionResult | None:
        """获取最后一次执行结果"""
        return self._last_result

    def get_execution_count(self) -> int:
        """获取执行次数"""
        return self._execution_count

    def reset(self) -> None:
        """重置执行器状态"""
        self._execution_count = 0
        self._last_result = None


class ExecutionManager:
    """
    执行管理器。

    管理多个执行器实例，支持：
    - 执行器池
    - 执行历史
    - 执行统计
    """

    def __init__(self, max_pool_size: int = 5):
        """
        初始化执行管理器。

        Args:
            max_pool_size: 最大池大小
        """
        self.max_pool_size = max_pool_size
        self._executors: list[CodeExecutor] = []
        self._history: list[ExecutionResult] = []
        self._callbacks: list[Callable[[ExecutionResult], None]] = []

    def get_executor(self) -> CodeExecutor:
        """获取一个执行器"""
        if self._executors:
            return self._executors.pop()

        return CodeExecutor()

    def return_executor(self, executor: CodeExecutor) -> None:
        """归还执行器"""
        if len(self._executors) < self.max_pool_size:
            executor.reset()
            self._executors.append(executor)

    def execute(self, code: str, context: dict[str, Any] | None = None) -> ExecutionResult:
        """
        执行代码并记录历史。

        Args:
            code: 要执行的代码
            context: 执行上下文

        Returns:
            ExecutionResult: 执行结果
        """
        executor = self.get_executor()
        try:
            result = executor.execute(code, context)
            self._history.append(result)
            self._notify_callbacks(result)
            return result
        finally:
            self.return_executor(executor)

    def add_callback(self, callback: Callable[[ExecutionResult], None]) -> None:
        """添加执行回调"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ExecutionResult], None]) -> None:
        """移除执行回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, result: ExecutionResult) -> None:
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    def get_history(self, limit: int = 100) -> list[ExecutionResult]:
        """获取执行历史"""
        return self._history[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """获取执行统计"""
        if not self._history:
            return {
                "total_executions": 0,
                "success_count": 0,
                "error_count": 0,
                "timeout_count": 0,
                "avg_execution_time": 0.0,
            }

        success_count = sum(1 for r in self._history if r.status == ExecutionStatus.SUCCESS)
        error_count = sum(1 for r in self._history if r.status == ExecutionStatus.ERROR)
        timeout_count = sum(1 for r in self._history if r.status == ExecutionStatus.TIMEOUT)
        avg_time = sum(r.execution_time for r in self._history) / len(self._history)

        return {
            "total_executions": len(self._history),
            "success_count": success_count,
            "error_count": error_count,
            "timeout_count": timeout_count,
            "avg_execution_time": avg_time,
        }

    def clear_history(self) -> None:
        """清除执行历史"""
        self._history.clear()