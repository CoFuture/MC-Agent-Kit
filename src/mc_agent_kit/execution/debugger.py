"""
调试器模块

提供断点调试、变量监视、调用栈追踪和条件断点功能。
"""

import ast
import inspect
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class DebuggerState(Enum):
    """调试器状态"""

    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停（命中断点）
    STEPPING = "stepping"  # 单步执行
    STOPPED = "stopped"  # 已停止


@dataclass
class BreakpointCondition:
    """断点条件"""

    expression: str  # 条件表达式
    language: str = "python"  # 条件语言

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        评估条件。

        Args:
            context: 评估上下文

        Returns:
            条件是否满足
        """
        try:
            return bool(eval(self.expression, {"__builtins__": {}}, context))
        except Exception as e:
            logger.warning(f"条件评估失败: {e}")
            return False


@dataclass
class Breakpoint:
    """断点定义"""

    id: str  # 断点 ID
    file: str  # 文件路径
    line: int  # 行号
    enabled: bool = True  # 是否启用
    condition: BreakpointCondition | None = None  # 条件
    hit_count: int = 0  # 命中次数
    ignore_count: int = 0  # 忽略次数（前 N 次不暂停）
    log_message: str | None = None  # 日志消息（不暂停，只输出日志）
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间

    def should_pause(self, context: dict[str, Any]) -> bool:
        """
        判断是否应该暂停。

        Args:
            context: 当前上下文

        Returns:
            是否暂停
        """
        if not self.enabled:
            return False

        if self.ignore_count > 0 and self.hit_count < self.ignore_count:
            return False

        if self.condition:
            return self.condition.evaluate(context)

        return True

    def hit(self) -> None:
        """记录命中"""
        self.hit_count += 1


@dataclass
class CallFrame:
    """调用栈帧"""

    index: int  # 帧索引（0 为当前帧）
    function: str  # 函数名
    file: str  # 文件路径
    line: int  # 行号
    code_context: list[str] | None = None  # 代码上下文
    locals: dict[str, Any] = field(default_factory=dict)  # 局部变量
    globals: dict[str, Any] = field(default_factory=dict)  # 全局变量

    def get_source_line(self) -> str | None:
        """获取当前行源代码"""
        if self.code_context:
            return self.code_context[0] if self.code_context else None
        return None


@dataclass
class VariableWatch:
    """变量监视"""

    name: str  # 变量名
    expression: str | None = None  # 表达式（如果不是简单变量）
    last_value: Any = None  # 上次值
    value_type: str | None = None  # 值类型
    changed: bool = False  # 是否发生变化
    watch_count: int = 0  # 监视次数

    def update(self, context: dict[str, Any]) -> Any:
        """
        更新变量值。

        Args:
            context: 评估上下文

        Returns:
            当前值
        """
        old_value = self.last_value
        self.watch_count += 1

        try:
            if self.expression:
                self.last_value = eval(self.expression, {"__builtins__": {}}, context)
            else:
                self.last_value = context.get(self.name)

            self.value_type = type(self.last_value).__name__
            self.changed = old_value != self.last_value

        except Exception as e:
            self.last_value = f"<error: {e}>"
            self.value_type = "error"
            self.changed = False

        return self.last_value


@dataclass
class DebugSession:
    """调试会话"""

    id: str  # 会话 ID
    state: DebuggerState = DebuggerState.IDLE
    current_file: str | None = None
    current_line: int = 0
    call_stack: list[CallFrame] = field(default_factory=list)
    breakpoints: dict[str, list[Breakpoint]] = field(default_factory=dict)
    watches: dict[str, VariableWatch] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def add_breakpoint(self, breakpoint: Breakpoint) -> None:
        """添加断点"""
        if breakpoint.file not in self.breakpoints:
            self.breakpoints[breakpoint.file] = []
        self.breakpoints[breakpoint.file].append(breakpoint)

    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点"""
        for file, bps in self.breakpoints.items():
            for i, bp in enumerate(bps):
                if bp.id == breakpoint_id:
                    bps.pop(i)
                    return True
        return False

    def get_breakpoints_for_file(self, file: str) -> list[Breakpoint]:
        """获取文件的所有断点"""
        return self.breakpoints.get(file, [])

    def add_watch(self, watch: VariableWatch) -> None:
        """添加变量监视"""
        self.watches[watch.name] = watch

    def remove_watch(self, name: str) -> bool:
        """移除变量监视"""
        if name in self.watches:
            del self.watches[name]
            return True
        return False

    def update_watches(self, context: dict[str, Any]) -> dict[str, Any]:
        """更新所有监视变量"""
        result = {}
        for name, watch in self.watches.items():
            result[name] = watch.update(context)
        return result


class Debugger:
    """
    调试器。

    提供断点调试、变量监视、调用栈追踪功能。

    使用示例:
        debugger = Debugger()
        
        # 设置断点
        bp = debugger.set_breakpoint("main.py", 10)
        
        # 添加条件断点
        bp = debugger.set_breakpoint(
            "main.py", 20,
            condition="x > 10"
        )
        
        # 监视变量
        debugger.watch_variable("x")
        
        # 开始调试
        debugger.start()
    """

    def __init__(self):
        """初始化调试器"""
        self._session: DebugSession | None = None
        self._breakpoint_counter = 0
        self._on_breakpoint_hit: Callable[[Breakpoint, dict[str, Any]], None] | None = None
        self._on_step: Callable[[int, str, dict[str, Any]], None] | None = None
        self._step_mode: str | None = None  # "into", "over", "out"

    def create_session(self) -> DebugSession:
        """创建调试会话"""
        self._session = DebugSession(id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        return self._session

    def get_session(self) -> DebugSession | None:
        """获取当前会话"""
        return self._session

    def start(self) -> None:
        """开始调试"""
        if not self._session:
            self.create_session()
        self._session.state = DebuggerState.RUNNING
        self._session.last_activity = datetime.now()

    def pause(self) -> None:
        """暂停执行"""
        if self._session:
            self._session.state = DebuggerState.PAUSED
            self._session.last_activity = datetime.now()

    def resume(self) -> None:
        """继续执行"""
        if self._session:
            self._session.state = DebuggerState.RUNNING
            self._session.last_activity = datetime.now()
            self._step_mode = None

    def stop(self) -> None:
        """停止调试"""
        if self._session:
            self._session.state = DebuggerState.STOPPED
            self._session.last_activity = datetime.now()

    def set_breakpoint(
        self,
        file: str,
        line: int,
        condition: str | None = None,
        ignore_count: int = 0,
        log_message: str | None = None,
    ) -> Breakpoint:
        """
        设置断点。

        Args:
            file: 文件路径
            line: 行号
            condition: 条件表达式
            ignore_count: 忽略次数
            log_message: 日志消息

        Returns:
            创建的断点
        """
        if not self._session:
            self.create_session()

        self._breakpoint_counter += 1
        bp_id = f"bp_{self._breakpoint_counter}"

        bp_condition = None
        if condition:
            bp_condition = BreakpointCondition(expression=condition)

        breakpoint = Breakpoint(
            id=bp_id,
            file=file,
            line=line,
            condition=bp_condition,
            ignore_count=ignore_count,
            log_message=log_message,
        )

        self._session.add_breakpoint(breakpoint)
        return breakpoint

    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """
        移除断点。

        Args:
            breakpoint_id: 断点 ID

        Returns:
            是否成功
        """
        if self._session:
            return self._session.remove_breakpoint(breakpoint_id)
        return False

    def toggle_breakpoint(self, breakpoint_id: str) -> bool | None:
        """
        切换断点启用状态。

        Args:
            breakpoint_id: 断点 ID

        Returns:
            新的启用状态，如果断点不存在则返回 None
        """
        if not self._session:
            return None

        for bps in self._session.breakpoints.values():
            for bp in bps:
                if bp.id == breakpoint_id:
                    bp.enabled = not bp.enabled
                    return bp.enabled
        return None

    def list_breakpoints(self) -> list[Breakpoint]:
        """列出所有断点"""
        if not self._session:
            return []

        result = []
        for bps in self._session.breakpoints.values():
            result.extend(bps)
        return result

    def watch_variable(self, name: str, expression: str | None = None) -> VariableWatch:
        """
        添加变量监视。

        Args:
            name: 变量名
            expression: 表达式（可选）

        Returns:
            创建的监视
        """
        if not self._session:
            self.create_session()

        watch = VariableWatch(name=name, expression=expression)
        self._session.add_watch(watch)
        return watch

    def remove_watch(self, name: str) -> bool:
        """
        移除变量监视。

        Args:
            name: 变量名

        Returns:
            是否成功
        """
        if self._session:
            return self._session.remove_watch(name)
        return False

    def list_watches(self) -> list[VariableWatch]:
        """列出所有监视变量"""
        if not self._session:
            return []
        return list(self._session.watches.values())

    def get_watch_values(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        获取所有监视变量的当前值。

        Args:
            context: 执行上下文

        Returns:
            变量名到值的映射
        """
        if not self._session:
            return {}
        return self._session.update_watches(context)

    def check_breakpoint(self, file: str, line: int, context: dict[str, Any]) -> Breakpoint | None:
        """
        检查是否命中断点。

        Args:
            file: 当前文件
            line: 当前行号
            context: 执行上下文

        Returns:
            命中的断点，如果没有则返回 None
        """
        if not self._session or self._session.state != DebuggerState.RUNNING:
            return None

        breakpoints = self._session.get_breakpoints_for_file(file)
        for bp in breakpoints:
            if bp.line == line:
                bp.hit()
                if bp.should_pause(context):
                    self._session.state = DebuggerState.PAUSED
                    self._session.current_file = file
                    self._session.current_line = line
                    return bp

        return None

    def update_call_stack(self, frames: list[CallFrame]) -> None:
        """
        更新调用栈。

        Args:
            frames: 调用栈帧列表
        """
        if self._session:
            self._session.call_stack = frames

    def get_call_stack(self) -> list[CallFrame]:
        """获取调用栈"""
        if self._session:
            return self._session.call_stack
        return []

    def step_into(self) -> None:
        """单步进入"""
        if self._session:
            self._session.state = DebuggerState.STEPPING
            self._step_mode = "into"
            self._session.last_activity = datetime.now()

    def step_over(self) -> None:
        """单步跳过"""
        if self._session:
            self._session.state = DebuggerState.STEPPING
            self._step_mode = "over"
            self._session.last_activity = datetime.now()

    def step_out(self) -> None:
        """单步跳出"""
        if self._session:
            self._session.state = DebuggerState.STEPPING
            self._step_mode = "out"
            self._session.last_activity = datetime.now()

    def get_state(self) -> DebuggerState:
        """获取调试器状态"""
        if self._session:
            return self._session.state
        return DebuggerState.IDLE

    def get_current_position(self) -> tuple[str | None, int]:
        """
        获取当前位置。

        Returns:
            (文件路径, 行号)
        """
        if self._session:
            return self._session.current_file, self._session.current_line
        return None, 0

    def set_on_breakpoint_hit(self, callback: Callable[[Breakpoint, dict[str, Any]], None]) -> None:
        """设置断点命中回调"""
        self._on_breakpoint_hit = callback

    def set_on_step(self, callback: Callable[[int, str, dict[str, Any]], None]) -> None:
        """设置单步回调"""
        self._on_step = callback

    def get_status(self) -> dict[str, Any]:
        """获取调试器状态摘要"""
        if not self._session:
            return {
                "state": "no_session",
                "breakpoints": 0,
                "watches": 0,
                "call_stack_depth": 0,
            }

        return {
            "state": self._session.state.value,
            "current_file": self._session.current_file,
            "current_line": self._session.current_line,
            "breakpoints": len(self.list_breakpoints()),
            "watches": len(self.list_watches()),
            "call_stack_depth": len(self._session.call_stack),
            "started_at": self._session.started_at.isoformat(),
            "last_activity": self._session.last_activity.isoformat(),
        }


class DebugCodeAnalyzer:
    """
    调试代码分析器。

    分析代码结构，支持：
    - 函数/类定义提取
    - 可执行行检测
    - 变量使用分析
    """

    def __init__(self):
        self._cache: dict[str, ast.AST] = {}

    def parse_file(self, file_path: str) -> ast.AST | None:
        """解析文件"""
        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()
            return ast.parse(code)
        except Exception as e:
            logger.error(f"解析文件失败: {e}")
            return None

    def get_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """获取所有函数定义"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                    }
                )
        return functions

    def get_classes(self, tree: ast.AST) -> list[dict[str, Any]]:
        """获取所有类定义"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in node.body if isinstance(n, ast.FunctionDef)
                ]
                classes.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno,
                        "methods": methods,
                        "docstring": ast.get_docstring(node),
                    }
                )
        return classes

    def get_executable_lines(self, tree: ast.AST) -> set[int]:
        """获取所有可执行行号"""
        lines = set()
        for node in ast.walk(tree):
            if hasattr(node, "lineno"):
                # 过滤掉非执行节点
                if isinstance(
                    node,
                    (
                        ast.Expr,
                        ast.Assign,
                        ast.AugAssign,
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.With,
                        ast.Return,
                        ast.Raise,
                        ast.Call,
                        ast.FunctionDef,
                    ),
                ):
                    lines.add(node.lineno)
        return lines

    def get_variable_uses(self, tree: ast.AST, var_name: str) -> list[int]:
        """获取变量使用的行号"""
        uses = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == var_name:
                uses.append(node.lineno)
        return uses

    def find_function_containing_line(self, tree: ast.AST, line: int) -> dict[str, Any] | None:
        """找到包含指定行的函数"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno <= line <= (node.end_lineno or node.lineno):
                    return {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno,
                    }
        return None