"""
调试器模块测试

测试 Debugger、Breakpoint、VariableWatch 等功能。
"""

import ast
import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.execution.debugger import (
    Breakpoint,
    BreakpointCondition,
    CallFrame,
    DebugCodeAnalyzer,
    DebugSession,
    Debugger,
    DebuggerState,
    VariableWatch,
)


class TestBreakpointCondition:
    """测试断点条件"""

    def test_simple_condition(self):
        """测试简单条件"""
        condition = BreakpointCondition(expression="x > 10")
        context = {"x": 15}

        assert condition.evaluate(context) is True

    def test_false_condition(self):
        """测试假条件"""
        condition = BreakpointCondition(expression="x < 5")
        context = {"x": 10}

        assert condition.evaluate(context) is False

    def test_complex_condition(self):
        """测试复杂条件"""
        condition = BreakpointCondition(expression="x > 0 and y == 'test'")
        context = {"x": 5, "y": "test"}

        assert condition.evaluate(context) is True

    def test_invalid_condition(self):
        """测试无效条件"""
        condition = BreakpointCondition(expression="undefined_var > 10")
        context = {"x": 5}

        # 无效条件应该返回 False
        assert condition.evaluate(context) is False

    def test_equality_condition(self):
        """测试相等条件"""
        condition = BreakpointCondition(expression="name == 'test'")
        context = {"name": "test"}

        assert condition.evaluate(context) is True

    def test_comparison_condition(self):
        """测试比较条件"""
        condition = BreakpointCondition(expression="value >= 100")
        context = {"value": 100}

        assert condition.evaluate(context) is True


class TestBreakpoint:
    """测试断点"""

    def test_basic_breakpoint(self):
        """测试基本断点"""
        bp = Breakpoint(id="bp_1", file="main.py", line=10)

        assert bp.id == "bp_1"
        assert bp.file == "main.py"
        assert bp.line == 10
        assert bp.enabled is True
        assert bp.hit_count == 0

    def test_breakpoint_with_condition(self):
        """测试带条件的断点"""
        condition = BreakpointCondition(expression="x > 5")
        bp = Breakpoint(id="bp_2", file="main.py", line=20, condition=condition)

        assert bp.condition is not None
        assert bp.condition.expression == "x > 5"

    def test_breakpoint_ignore_count(self):
        """测试忽略次数"""
        bp = Breakpoint(id="bp_3", file="main.py", line=30, ignore_count=3)

        # 前三次命中不应该暂停
        bp.hit()
        assert bp.hit_count == 1
        assert bp.should_pause({}) is False

        bp.hit()
        bp.hit()
        assert bp.hit_count == 3

        # 第四次应该暂停
        bp.hit()
        assert bp.should_pause({}) is True

    def test_breakpoint_disabled(self):
        """测试禁用断点"""
        bp = Breakpoint(id="bp_4", file="main.py", line=40, enabled=False)

        assert bp.should_pause({}) is False

    def test_breakpoint_hit(self):
        """测试命中计数"""
        bp = Breakpoint(id="bp_5", file="main.py", line=50)

        for _ in range(5):
            bp.hit()

        assert bp.hit_count == 5

    def test_log_message_breakpoint(self):
        """测试日志断点"""
        bp = Breakpoint(
            id="bp_6",
            file="main.py",
            line=60,
            log_message="Variable x = {x}",
        )

        assert bp.log_message == "Variable x = {x}"
        # 日志断点也应该能暂停
        assert bp.should_pause({}) is True

    def test_should_pause_with_condition(self):
        """测试条件断点暂停逻辑"""
        condition = BreakpointCondition(expression="count > 3")
        bp = Breakpoint(id="bp_7", file="main.py", line=70, condition=condition)

        # 条件不满足
        assert bp.should_pause({"count": 2}) is False

        # 条件满足
        assert bp.should_pause({"count": 5}) is True


class TestCallFrame:
    """测试调用栈帧"""

    def test_basic_frame(self):
        """测试基本栈帧"""
        frame = CallFrame(
            index=0,
            function="main",
            file="main.py",
            line=10,
        )

        assert frame.index == 0
        assert frame.function == "main"
        assert frame.file == "main.py"
        assert frame.line == 10

    def test_frame_with_variables(self):
        """测试带变量的栈帧"""
        frame = CallFrame(
            index=1,
            function="helper",
            file="utils.py",
            line=25,
            locals={"x": 10, "y": "test"},
            globals={"config": {"debug": True}},
        )

        assert frame.locals == {"x": 10, "y": "test"}
        assert frame.globals["config"]["debug"] is True

    def test_frame_code_context(self):
        """测试代码上下文"""
        frame = CallFrame(
            index=0,
            function="main",
            file="main.py",
            line=5,
            code_context=["x = 1", "y = 2"],
        )

        assert frame.get_source_line() == "x = 1"

    def test_frame_no_code_context(self):
        """测试无代码上下文"""
        frame = CallFrame(
            index=0,
            function="main",
            file="main.py",
            line=5,
        )

        assert frame.get_source_line() is None


class TestVariableWatch:
    """测试变量监视"""

    def test_basic_watch(self):
        """测试基本监视"""
        watch = VariableWatch(name="x")

        assert watch.name == "x"
        assert watch.last_value is None
        assert watch.watch_count == 0

    def test_watch_update(self):
        """测试更新监视值"""
        watch = VariableWatch(name="x")
        context = {"x": 42}

        value = watch.update(context)

        assert value == 42
        assert watch.last_value == 42
        assert watch.watch_count == 1
        assert watch.value_type == "int"

    def test_watch_change_detection(self):
        """测试变化检测"""
        watch = VariableWatch(name="x")
        context = {"x": 1}

        watch.update(context)
        assert watch.changed is True  # 第一次更新，从 None 变为 1

        watch.update(context)
        assert watch.changed is False  # 第二次更新，值没有变化

        context["x"] = 2
        watch.update(context)
        assert watch.changed is True  # 值变化了

    def test_watch_expression(self):
        """测试表达式监视"""
        watch = VariableWatch(name="sum", expression="x + y")
        context = {"x": 10, "y": 20}

        value = watch.update(context)

        assert value == 30
        assert watch.last_value == 30

    def test_watch_error_handling(self):
        """测试错误处理"""
        watch = VariableWatch(name="z")
        context = {}  # 没有 z 变量

        value = watch.update(context)

        # 变量不存在时，值为 None
        assert value is None
        assert watch.value_type == "NoneType"


class TestDebugSession:
    """测试调试会话"""

    def test_session_creation(self):
        """测试会话创建"""
        session = DebugSession(id="session_1")

        assert session.id == "session_1"
        assert session.state == DebuggerState.IDLE
        assert len(session.breakpoints) == 0

    def test_add_breakpoint(self):
        """测试添加断点"""
        session = DebugSession(id="session_2")
        bp = Breakpoint(id="bp_1", file="main.py", line=10)

        session.add_breakpoint(bp)

        assert "main.py" in session.breakpoints
        assert len(session.breakpoints["main.py"]) == 1

    def test_remove_breakpoint(self):
        """测试移除断点"""
        session = DebugSession(id="session_3")
        bp = Breakpoint(id="bp_1", file="main.py", line=10)

        session.add_breakpoint(bp)
        result = session.remove_breakpoint("bp_1")

        assert result is True
        assert len(session.breakpoints["main.py"]) == 0

    def test_remove_nonexistent_breakpoint(self):
        """测试移除不存在的断点"""
        session = DebugSession(id="session_4")

        result = session.remove_breakpoint("nonexistent")

        assert result is False

    def test_get_breakpoints_for_file(self):
        """测试获取文件的断点"""
        session = DebugSession(id="session_5")

        bp1 = Breakpoint(id="bp_1", file="main.py", line=10)
        bp2 = Breakpoint(id="bp_2", file="main.py", line=20)
        bp3 = Breakpoint(id="bp_3", file="utils.py", line=5)

        session.add_breakpoint(bp1)
        session.add_breakpoint(bp2)
        session.add_breakpoint(bp3)

        main_bps = session.get_breakpoints_for_file("main.py")

        assert len(main_bps) == 2

    def test_add_watch(self):
        """测试添加监视"""
        session = DebugSession(id="session_6")
        watch = VariableWatch(name="x")

        session.add_watch(watch)

        assert "x" in session.watches

    def test_remove_watch(self):
        """测试移除监视"""
        session = DebugSession(id="session_7")
        watch = VariableWatch(name="x")

        session.add_watch(watch)
        result = session.remove_watch("x")

        assert result is True
        assert "x" not in session.watches

    def test_update_watches(self):
        """测试更新所有监视"""
        session = DebugSession(id="session_8")

        watch1 = VariableWatch(name="x")
        watch2 = VariableWatch(name="y")

        session.add_watch(watch1)
        session.add_watch(watch2)

        context = {"x": 10, "y": 20}
        values = session.update_watches(context)

        assert values["x"] == 10
        assert values["y"] == 20


class TestDebugger:
    """测试调试器"""

    def test_debugger_creation(self):
        """测试调试器创建"""
        debugger = Debugger()

        assert debugger._session is None
        assert debugger._breakpoint_counter == 0

    def test_create_session(self):
        """测试创建会话"""
        debugger = Debugger()
        session = debugger.create_session()

        assert session is not None
        assert session.id.startswith("session_")

    def test_start_debugging(self):
        """测试开始调试"""
        debugger = Debugger()
        debugger.start()

        assert debugger.get_state() == DebuggerState.RUNNING

    def test_pause_debugging(self):
        """测试暂停调试"""
        debugger = Debugger()
        debugger.start()
        debugger.pause()

        assert debugger.get_state() == DebuggerState.PAUSED

    def test_resume_debugging(self):
        """测试继续调试"""
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.resume()

        assert debugger.get_state() == DebuggerState.RUNNING

    def test_stop_debugging(self):
        """测试停止调试"""
        debugger = Debugger()
        debugger.start()
        debugger.stop()

        assert debugger.get_state() == DebuggerState.STOPPED

    def test_set_breakpoint(self):
        """测试设置断点"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 10)

        assert bp.id == "bp_1"
        assert bp.file == "main.py"
        assert bp.line == 10

    def test_set_conditional_breakpoint(self):
        """测试设置条件断点"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 20, condition="x > 5")

        assert bp.condition is not None
        assert bp.condition.expression == "x > 5"

    def test_remove_breakpoint(self):
        """测试移除断点"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 10)

        result = debugger.remove_breakpoint(bp.id)

        assert result is True
        assert len(debugger.list_breakpoints()) == 0

    def test_toggle_breakpoint(self):
        """测试切换断点状态"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 10)

        # 禁用
        new_state = debugger.toggle_breakpoint(bp.id)
        assert new_state is False

        # 启用
        new_state = debugger.toggle_breakpoint(bp.id)
        assert new_state is True

    def test_toggle_nonexistent_breakpoint(self):
        """测试切换不存在的断点"""
        debugger = Debugger()

        result = debugger.toggle_breakpoint("nonexistent")

        assert result is None

    def test_watch_variable(self):
        """测试监视变量"""
        debugger = Debugger()
        watch = debugger.watch_variable("x")

        assert watch.name == "x"
        assert len(debugger.list_watches()) == 1

    def test_remove_watch(self):
        """测试移除监视"""
        debugger = Debugger()
        debugger.watch_variable("x")

        result = debugger.remove_watch("x")

        assert result is True
        assert len(debugger.list_watches()) == 0

    def test_get_watch_values(self):
        """测试获取监视值"""
        debugger = Debugger()
        debugger.watch_variable("x")
        debugger.watch_variable("y")

        values = debugger.get_watch_values({"x": 10, "y": 20})

        assert values["x"] == 10
        assert values["y"] == 20

    def test_check_breakpoint_hit(self):
        """测试断点命中检测"""
        debugger = Debugger()
        debugger.start()
        debugger.set_breakpoint("main.py", 10)

        # 命中断点
        bp = debugger.check_breakpoint("main.py", 10, {"x": 5})

        assert bp is not None
        assert debugger.get_state() == DebuggerState.PAUSED

    def test_check_breakpoint_miss(self):
        """测试断点未命中"""
        debugger = Debugger()
        debugger.start()
        debugger.set_breakpoint("main.py", 10)

        # 不同行号
        bp = debugger.check_breakpoint("main.py", 20, {"x": 5})

        assert bp is None

    def test_check_breakpoint_condition(self):
        """测试条件断点命中"""
        debugger = Debugger()
        debugger.start()
        debugger.set_breakpoint("main.py", 10, condition="x > 5")

        # 条件不满足
        debugger._session.state = DebuggerState.RUNNING
        bp = debugger.check_breakpoint("main.py", 10, {"x": 3})

        assert bp is None  # 不应该暂停

        # 条件满足
        debugger._session.state = DebuggerState.RUNNING
        bp = debugger.check_breakpoint("main.py", 10, {"x": 10})

        assert bp is not None  # 应该暂停

    def test_update_call_stack(self):
        """测试更新调用栈"""
        debugger = Debugger()
        debugger.create_session()  # 先创建会话

        frames = [
            CallFrame(index=0, function="main", file="main.py", line=10),
            CallFrame(index=1, function="helper", file="utils.py", line=5),
        ]

        debugger.update_call_stack(frames)

        assert len(debugger.get_call_stack()) == 2

    def test_step_into(self):
        """测试单步进入"""
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.step_into()

        assert debugger.get_state() == DebuggerState.STEPPING
        assert debugger._step_mode == "into"

    def test_step_over(self):
        """测试单步跳过"""
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.step_over()

        assert debugger.get_state() == DebuggerState.STEPPING
        assert debugger._step_mode == "over"

    def test_step_out(self):
        """测试单步跳出"""
        debugger = Debugger()
        debugger.start()
        debugger.pause()
        debugger.step_out()

        assert debugger.get_state() == DebuggerState.STEPPING
        assert debugger._step_mode == "out"

    def test_get_current_position(self):
        """测试获取当前位置"""
        debugger = Debugger()
        debugger.start()
        debugger.set_breakpoint("main.py", 10)
        debugger.check_breakpoint("main.py", 10, {})

        file, line = debugger.get_current_position()

        assert file == "main.py"
        assert line == 10

    def test_set_callbacks(self):
        """测试设置回调"""
        debugger = Debugger()

        def on_bp(bp, ctx):
            pass

        def on_step(line, file, ctx):
            pass

        debugger.set_on_breakpoint_hit(on_bp)
        debugger.set_on_step(on_step)

        assert debugger._on_breakpoint_hit == on_bp
        assert debugger._on_step == on_step

    def test_get_status(self):
        """测试获取状态摘要"""
        debugger = Debugger()
        debugger.start()
        debugger.set_breakpoint("main.py", 10)
        debugger.watch_variable("x")

        status = debugger.get_status()

        assert status["state"] == "running"
        assert status["breakpoints"] == 1
        assert status["watches"] == 1


class TestDebugCodeAnalyzer:
    """测试调试代码分析器"""

    def test_parse_file(self):
        """测试解析文件"""
        analyzer = DebugCodeAnalyzer()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def hello():\n    print('world')\n")
            f.flush()

            tree = analyzer.parse_file(f.name)

        assert tree is not None

    def test_parse_invalid_file(self):
        """测试解析无效文件"""
        analyzer = DebugCodeAnalyzer()

        tree = analyzer.parse_file("/nonexistent/file.py")

        assert tree is None

    def test_get_functions(self):
        """测试获取函数列表"""
        analyzer = DebugCodeAnalyzer()
        code = """
def func1():
    pass

def func2(x, y):
    return x + y
"""
        tree = ast.parse(code)
        functions = analyzer.get_functions(tree)

        assert len(functions) == 2
        assert functions[0]["name"] == "func1"
        assert functions[1]["args"] == ["x", "y"]

    def test_get_classes(self):
        """测试获取类列表"""
        analyzer = DebugCodeAnalyzer()
        code = """
class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass
"""
        tree = ast.parse(code)
        classes = analyzer.get_classes(tree)

        assert len(classes) == 1
        assert classes[0]["name"] == "MyClass"
        assert "method1" in classes[0]["methods"]
        assert "method2" in classes[0]["methods"]

    def test_get_executable_lines(self):
        """测试获取可执行行"""
        analyzer = DebugCodeAnalyzer()
        code = """
x = 1
y = 2
if x > 0:
    print(y)
"""
        tree = ast.parse(code)
        lines = analyzer.get_executable_lines(tree)

        # 应该包含一些可执行行
        assert len(lines) > 0

    def test_get_variable_uses(self):
        """测试获取变量使用"""
        analyzer = DebugCodeAnalyzer()
        code = """
x = 1
y = x + 1
print(x)
"""
        tree = ast.parse(code)
        uses = analyzer.get_variable_uses(tree, "x")

        # x 在第2、3、4行使用
        assert len(uses) >= 2

    def test_find_function_containing_line(self):
        """测试查找包含指定行的函数"""
        analyzer = DebugCodeAnalyzer()
        code = """
def func1():
    x = 1  # line 3
    y = 2

def func2():
    pass
"""
        tree = ast.parse(code)

        # 查找第3行所在的函数
        func = analyzer.find_function_containing_line(tree, 3)

        assert func is not None
        assert func["name"] == "func1"

    def test_find_function_no_match(self):
        """测试找不到函数"""
        analyzer = DebugCodeAnalyzer()
        code = """
x = 1
y = 2
"""
        tree = ast.parse(code)

        func = analyzer.find_function_containing_line(tree, 1)

        assert func is None


class TestIntegration:
    """集成测试"""

    def test_full_debug_session(self):
        """测试完整调试会话"""
        debugger = Debugger()

        # 创建会话
        debugger.create_session()

        # 设置断点
        bp1 = debugger.set_breakpoint("main.py", 10)
        bp2 = debugger.set_breakpoint("main.py", 20, condition="x > 5")

        # 添加监视
        debugger.watch_variable("x")
        debugger.watch_variable("y")

        # 开始调试
        debugger.start()
        assert debugger.get_state() == DebuggerState.RUNNING

        # 模拟命中断点
        debugger.check_breakpoint("main.py", 10, {"x": 3})
        assert debugger.get_state() == DebuggerState.PAUSED

        # 检查监视值
        values = debugger.get_watch_values({"x": 3, "y": 5})
        assert values["x"] == 3

        # 继续执行
        debugger.resume()
        assert debugger.get_state() == DebuggerState.RUNNING

        # 停止调试
        debugger.stop()
        assert debugger.get_state() == DebuggerState.STOPPED

    def test_multiple_breakpoints(self):
        """测试多个断点"""
        debugger = Debugger()
        debugger.start()

        # 设置多个断点
        bp1 = debugger.set_breakpoint("main.py", 10)
        bp2 = debugger.set_breakpoint("main.py", 20)
        bp3 = debugger.set_breakpoint("utils.py", 5)

        assert len(debugger.list_breakpoints()) == 3

        # 禁用一个
        debugger.toggle_breakpoint(bp1.id)

        # 移除一个
        debugger.remove_breakpoint(bp2.id)

        assert len(debugger.list_breakpoints()) == 2

    def test_call_stack_tracking(self):
        """测试调用栈追踪"""
        debugger = Debugger()
        debugger.create_session()  # 先创建会话

        # 模拟调用栈
        frames = [
            CallFrame(
                index=0,
                function="current_func",
                file="main.py",
                line=50,
                locals={"x": 1},
            ),
            CallFrame(
                index=1,
                function="caller_func",
                file="main.py",
                line=30,
                locals={"y": 2},
            ),
            CallFrame(
                index=2,
                function="main",
                file="main.py",
                line=10,
                locals={},
            ),
        ]

        debugger.update_call_stack(frames)

        stack = debugger.get_call_stack()
        assert len(stack) == 3
        assert stack[0].function == "current_func"


class TestEdgeCases:
    """边界条件测试"""

    def test_breakpoint_same_line_different_files(self):
        """测试不同文件同一行断点"""
        debugger = Debugger()

        bp1 = debugger.set_breakpoint("main.py", 10)
        bp2 = debugger.set_breakpoint("utils.py", 10)

        assert bp1.id != bp2.id
        assert len(debugger.list_breakpoints()) == 2

    def test_condition_with_empty_context(self):
        """测试空上下文条件"""
        condition = BreakpointCondition(expression="x > 5")
        result = condition.evaluate({})

        assert result is False

    def test_watch_without_variable(self):
        """测试监视不存在的变量"""
        watch = VariableWatch(name="nonexistent")
        value = watch.update({})

        # 变量不存在时返回 None
        assert value is None

    def test_debugger_without_session(self):
        """测试无会话调试器操作"""
        debugger = Debugger()

        # 这些操作不应该崩溃
        assert debugger.get_state() == DebuggerState.IDLE
        assert debugger.list_breakpoints() == []
        assert debugger.list_watches() == []
        assert debugger.get_call_stack() == []
        assert debugger.get_current_position() == (None, 0)

    def test_session_id_uniqueness(self):
        """测试会话 ID 唯一性"""
        import time
        
        debugger1 = Debugger()
        session1 = debugger1.create_session()

        # 等待一秒确保时间戳不同
        time.sleep(1)

        debugger2 = Debugger()
        session2 = debugger2.create_session()

        assert session1.id != session2.id

    def test_breakpoint_ignore_count_zero(self):
        """测试忽略次数为零"""
        bp = Breakpoint(id="bp_1", file="main.py", line=10, ignore_count=0)

        # 应该立即暂停
        assert bp.should_pause({}) is True

    def test_frame_with_empty_code_context(self):
        """测试空代码上下文"""
        frame = CallFrame(
            index=0,
            function="main",
            file="main.py",
            line=10,
            code_context=[],
        )

        # 空列表应该返回 None
        assert frame.get_source_line() is None

    def test_debugger_state_transitions(self):
        """测试调试器状态转换"""
        debugger = Debugger()

        # IDLE -> RUNNING
        debugger.start()
        assert debugger.get_state() == DebuggerState.RUNNING

        # RUNNING -> PAUSED
        debugger.pause()
        assert debugger.get_state() == DebuggerState.PAUSED

        # PAUSED -> RUNNING
        debugger.resume()
        assert debugger.get_state() == DebuggerState.RUNNING

        # RUNNING -> STOPPED
        debugger.stop()
        assert debugger.get_state() == DebuggerState.STOPPED

    def test_analyze_complex_code(self):
        """测试分析复杂代码"""
        analyzer = DebugCodeAnalyzer()
        code = """
class Calculator:
    '''A simple calculator'''

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

def main():
    calc = Calculator()
    result = calc.add(1, 2)
    print(result)

if __name__ == "__main__":
    main()
"""
        tree = ast.parse(code)

        functions = analyzer.get_functions(tree)
        classes = analyzer.get_classes(tree)
        lines = analyzer.get_executable_lines(tree)

        assert len(functions) >= 3  # add, multiply, main
        assert len(classes) == 1
        assert classes[0]["name"] == "Calculator"
        assert len(lines) > 0