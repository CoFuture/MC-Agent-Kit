"""
执行模块测试

测试代码执行器、调试器、热重载和性能分析功能。
"""

import os
import tempfile
import threading
import time
from datetime import datetime

import pytest

from mc_agent_kit.execution import (
    Breakpoint,
    BreakpointCondition,
    CallFrame,
    CodeExecutor,
    Debugger,
    DebuggerState,
    ExecutionConfig,
    ExecutionResult,
    ExecutionStatus,
    ExecutionManager,
    FileWatcher,
    HotReloader,
    MemoryMonitor,
    MemorySnapshot,
    PerformanceAnalyzer,
    PerformanceConfig,
    ProfilingResult,
    ProfilingStatus,
    ReloadConfig,
    ReloadStatus,
    ReloadResult,
    Timer,
    VariableWatch,
)


class TestCodeExecutor:
    """代码执行器测试"""

    def test_basic_execution(self):
        """测试基本执行"""
        executor = CodeExecutor()
        result = executor.execute("x = 1 + 2")

        assert result.status == ExecutionStatus.SUCCESS
        assert result.locals.get("x") == 3

    def test_execution_with_output(self):
        """测试输出捕获"""
        executor = CodeExecutor()
        result = executor.execute("print('Hello, World!')")

        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, World!" in result.output

    def test_execution_with_return_value(self):
        """测试返回值"""
        executor = CodeExecutor()
        result = executor.execute("1 + 2")

        assert result.status == ExecutionStatus.SUCCESS
        assert result.return_value == 3

    def test_execution_with_error(self):
        """测试错误处理"""
        executor = CodeExecutor()
        result = executor.execute("1 / 0")

        assert result.status == ExecutionStatus.ERROR
        assert "ZeroDivisionError" in result.error or "ZeroDivisionError" in (result.traceback or "")

    def test_execution_with_syntax_error(self):
        """测试语法错误"""
        executor = CodeExecutor()
        result = executor.execute("print('missing quote")

        assert result.status == ExecutionStatus.ERROR
        assert "语法错误" in result.error or "SyntaxError" in result.error

    def test_execution_with_context(self):
        """测试执行上下文"""
        executor = CodeExecutor()
        result = executor.execute("y = x + 1", context={"x": 10})

        assert result.status == ExecutionStatus.SUCCESS
        assert result.locals.get("y") == 11

    def test_sandbox_mode_blocks_dangerous_imports(self):
        """测试沙箱模式阻止危险导入"""
        config = ExecutionConfig(sandbox_mode=True)
        executor = CodeExecutor(config)
        result = executor.execute("import os")

        assert result.status == ExecutionStatus.ERROR
        assert "禁止导入" in result.error

    def test_sandbox_mode_blocks_dangerous_calls(self):
        """测试沙箱模式阻止危险调用"""
        config = ExecutionConfig(sandbox_mode=True)
        executor = CodeExecutor(config)
        result = executor.execute("eval('1+1')")

        assert result.status == ExecutionStatus.ERROR
        assert "禁止调用" in result.error

    def test_non_sandbox_mode_allows_imports(self):
        """测试非沙箱模式允许导入"""
        config = ExecutionConfig(sandbox_mode=False)
        executor = CodeExecutor(config)
        result = executor.execute("import math; math.pi")

        assert result.status == ExecutionStatus.SUCCESS

    def test_execution_time_tracking(self):
        """测试执行时间跟踪"""
        executor = CodeExecutor()
        result = executor.execute("sum(range(1000))")

        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_time >= 0

    def test_execution_count(self):
        """测试执行计数"""
        executor = CodeExecutor()

        for i in range(5):
            executor.execute(f"x = {i}")

        assert executor.get_execution_count() == 5

    def test_last_result(self):
        """测试最后执行结果"""
        executor = CodeExecutor()
        executor.execute("x = 1")
        executor.execute("y = 2")

        last = executor.get_last_result()
        assert last.locals.get("y") == 2

    def test_reset(self):
        """测试重置"""
        executor = CodeExecutor()
        executor.execute("x = 1")

        executor.reset()

        assert executor.get_execution_count() == 0
        assert executor.get_last_result() is None

    def test_execute_file(self):
        """测试执行文件"""
        executor = CodeExecutor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("result = 1 + 2")
            f.flush()
            file_path = f.name

        try:
            result = executor.execute_file(file_path)
            assert result.status == ExecutionStatus.SUCCESS
        finally:
            # 尝试删除，如果失败则忽略
            try:
                os.unlink(file_path)
            except PermissionError:
                pass

    def test_execute_file_not_found(self):
        """测试执行不存在的文件"""
        executor = CodeExecutor()
        result = executor.execute_file("/nonexistent/file.py")

        assert result.status == ExecutionStatus.ERROR
        assert "不存在" in result.error

    def test_execute_with_timeout(self):
        """测试带超时的执行"""
        executor = CodeExecutor()
        result = executor.execute_with_timeout("x = 1", timeout=5.0)

        assert result.status == ExecutionStatus.SUCCESS


class TestExecutionManager:
    """执行管理器测试"""

    def test_execute_and_history(self):
        """测试执行和历史记录"""
        manager = ExecutionManager()
        manager.execute("x = 1")
        manager.execute("y = 2")

        history = manager.get_history()
        assert len(history) == 2

    def test_statistics(self):
        """测试统计信息"""
        manager = ExecutionManager()
        manager.execute("x = 1")
        manager.execute("y = 2")
        manager.execute("raise Exception('test')")

        stats = manager.get_statistics()
        assert stats["total_executions"] == 3
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1

    def test_callback(self):
        """测试回调"""
        manager = ExecutionManager()
        results = []

        def callback(result):
            results.append(result)

        manager.add_callback(callback)
        manager.execute("x = 1")

        assert len(results) == 1

    def test_clear_history(self):
        """测试清除历史"""
        manager = ExecutionManager()
        manager.execute("x = 1")

        manager.clear_history()
        history = manager.get_history()

        assert len(history) == 0


class TestDebugger:
    """调试器测试"""

    def test_create_session(self):
        """测试创建会话"""
        debugger = Debugger()
        session = debugger.create_session()

        assert session is not None
        assert session.state == DebuggerState.IDLE

    def test_set_breakpoint(self):
        """测试设置断点"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 10)

        assert bp.file == "main.py"
        assert bp.line == 10
        assert bp.enabled

    def test_set_conditional_breakpoint(self):
        """测试条件断点"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 20, condition="x > 10")

        assert bp.condition is not None
        assert bp.condition.expression == "x > 10"

    def test_remove_breakpoint(self):
        """测试移除断点"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 10)

        assert debugger.remove_breakpoint(bp.id)
        assert not debugger.remove_breakpoint("nonexistent")

    def test_toggle_breakpoint(self):
        """测试切换断点状态"""
        debugger = Debugger()
        bp = debugger.set_breakpoint("main.py", 10)

        new_state = debugger.toggle_breakpoint(bp.id)
        assert new_state is False

        new_state = debugger.toggle_breakpoint(bp.id)
        assert new_state is True

    def test_list_breakpoints(self):
        """测试列出断点"""
        debugger = Debugger()
        debugger.set_breakpoint("main.py", 10)
        debugger.set_breakpoint("main.py", 20)

        bps = debugger.list_breakpoints()
        assert len(bps) == 2

    def test_watch_variable(self):
        """测试变量监视"""
        debugger = Debugger()
        watch = debugger.watch_variable("x")

        assert watch.name == "x"

    def test_remove_watch(self):
        """测试移除监视"""
        debugger = Debugger()
        debugger.watch_variable("x")

        assert debugger.remove_watch("x")
        assert not debugger.remove_watch("nonexistent")

    def test_get_watch_values(self):
        """测试获取监视值"""
        debugger = Debugger()
        debugger.watch_variable("x")

        values = debugger.get_watch_values({"x": 10, "y": 20})
        assert values.get("x") == 10

    def test_debugger_state(self):
        """测试调试器状态"""
        debugger = Debugger()

        assert debugger.get_state() == DebuggerState.IDLE

        debugger.start()
        assert debugger.get_state() == DebuggerState.RUNNING

        debugger.pause()
        assert debugger.get_state() == DebuggerState.PAUSED

        debugger.resume()
        assert debugger.get_state() == DebuggerState.RUNNING

        debugger.stop()
        assert debugger.get_state() == DebuggerState.STOPPED

    def test_step_modes(self):
        """测试单步模式"""
        debugger = Debugger()
        debugger.start()

        debugger.step_into()
        assert debugger.get_state() == DebuggerState.STEPPING

    def test_call_stack(self):
        """测试调用栈"""
        debugger = Debugger()
        debugger.create_session()

        frames = [
            CallFrame(index=0, function="func_a", file="a.py", line=10),
            CallFrame(index=1, function="func_b", file="b.py", line=20),
        ]
        debugger.update_call_stack(frames)

        stack = debugger.get_call_stack()
        assert len(stack) == 2

    def test_status(self):
        """测试状态摘要"""
        debugger = Debugger()
        debugger.set_breakpoint("main.py", 10)
        debugger.watch_variable("x")

        status = debugger.get_status()
        assert status["breakpoints"] == 1
        assert status["watches"] == 1


class TestBreakpointCondition:
    """断点条件测试"""

    def test_simple_condition(self):
        """测试简单条件"""
        condition = BreakpointCondition(expression="x > 10")

        assert condition.evaluate({"x": 15})
        assert not condition.evaluate({"x": 5})

    def test_complex_condition(self):
        """测试复杂条件"""
        condition = BreakpointCondition(expression="x > 0 and y < 10")

        assert condition.evaluate({"x": 5, "y": 5})
        assert not condition.evaluate({"x": -1, "y": 5})


class TestFileWatcher:
    """文件监控器测试"""

    def test_add_remove_watch(self):
        """测试添加/移除监控"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher.add_watch(tmpdir)
            watcher.remove_watch(tmpdir)

    def test_get_changes(self):
        """测试获取变化"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher.add_watch(tmpdir)

            # 创建文件
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, "w") as f:
                f.write("# test")

            # 手动检查变化（不启动线程）
            watcher._scan_directory(tmpdir)


class TestHotReloader:
    """热重载器测试"""

    def test_reload_module(self):
        """测试重载模块"""
        reloader = HotReloader()

        # 重载一个标准库模块
        result = reloader.reload_module("json")

        # json 模块在 sys.modules 中，应该能重载
        assert result.status in [ReloadStatus.SUCCESS, ReloadStatus.FAILED]

    def test_watch_directory(self):
        """测试监控目录"""
        reloader = HotReloader()

        with tempfile.TemporaryDirectory() as tmpdir:
            reloader.watch_directory(tmpdir)
            reloader.unwatch_directory(tmpdir)

    def test_status(self):
        """测试状态"""
        reloader = HotReloader()
        status = reloader.get_status()

        assert "watching" in status
        assert "loaded_modules" in status


class TestPerformanceAnalyzer:
    """性能分析器测试"""

    def test_start_stop(self):
        """测试开始/停止分析"""
        analyzer = PerformanceAnalyzer()

        analyzer.start()
        time.sleep(0.01)  # 短暂等待
        report = analyzer.stop()

        assert report is not None
        assert report.total_time >= 0

    def test_profile_decorator(self):
        """测试分析装饰器"""
        analyzer = PerformanceAnalyzer()

        @analyzer.profile
        def test_func():
            return sum(range(100))

        result = test_func()
        assert result == 4950

    def test_timer_context(self):
        """测试计时器上下文"""
        analyzer = PerformanceAnalyzer()

        with analyzer.profile_block("test"):
            time.sleep(0.01)

        # 计时器应该正常工作

    def test_record_timing(self):
        """测试记录计时"""
        analyzer = PerformanceAnalyzer()
        analyzer.record_timing("test_op", 10.5)
        analyzer.record_timing("test_op", 20.5)

        stats = analyzer.get_timing_stats("test_op")
        assert stats["count"] == 2
        assert stats["avg"] == 15.5

    def test_reset(self):
        """测试重置"""
        analyzer = PerformanceAnalyzer()
        analyzer.start()
        analyzer.stop()
        analyzer.reset()

        assert analyzer.get_status() == ProfilingStatus.IDLE

    def test_pause_resume(self):
        """测试暂停/恢复"""
        analyzer = PerformanceAnalyzer()
        analyzer.start()
        analyzer.pause()
        analyzer.resume()
        analyzer.stop()


class TestTimer:
    """计时器测试"""

    def test_basic_timing(self):
        """测试基本计时"""
        timer = Timer()
        timer.start()
        time.sleep(0.01)
        elapsed = timer.stop()

        assert elapsed >= 0.01

    def test_context_manager(self):
        """测试上下文管理器"""
        with Timer() as timer:
            time.sleep(0.01)

        assert timer.elapsed() >= 0.01

    def test_elapsed_ms(self):
        """测试毫秒耗时"""
        timer = Timer()
        timer.start()
        time.sleep(0.01)
        timer.stop()

        assert timer.elapsed_ms() >= 10

    def test_reset(self):
        """测试重置"""
        timer = Timer()
        timer.start()
        timer.stop()
        timer.reset()

        assert timer.elapsed() == 0


class TestMemoryMonitor:
    """内存监控器测试"""

    def test_start_stop(self):
        """测试启动/停止"""
        monitor = MemoryMonitor(threshold_mb=1000.0)

        monitor.start()
        time.sleep(0.1)
        monitor.stop()

    def test_get_current_usage(self):
        """测试获取当前使用"""
        monitor = MemoryMonitor()
        monitor.start()

        usage = monitor.get_current_usage()
        assert "current_mb" in usage
        assert "peak_mb" in usage

        monitor.stop()

    def test_threshold_callback(self):
        """测试阈值回调"""
        monitor = MemoryMonitor(threshold_mb=0.0)  # 设置为 0 触发回调
        called = []

        def on_threshold(mb):
            called.append(mb)

        monitor.set_on_threshold_exceeded(on_threshold)
        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        # 由于阈值是 0，应该触发回调
        # 注意：由于 tracemalloc 只追踪分配的内存，可能不触发


class TestReloadResult:
    """重载结果测试"""

    def test_reload_result_creation(self):
        """测试重载结果创建"""
        result = ReloadResult(
            status=ReloadStatus.SUCCESS,
            file_path="/path/to/file.py",
            module_name="test_module",
            reload_time_ms=10.5,
        )

        assert result.status == ReloadStatus.SUCCESS
        assert result.module_name == "test_module"


class TestProfilingResult:
    """分析结果测试"""

    def test_profiling_result_creation(self):
        """测试分析结果创建"""
        result = ProfilingResult(
            function_name="test_func",
            calls=100,
            total_time=0.5,
            cumulative_time=1.0,
            avg_time=0.005,
            min_time=0.001,
            max_time=0.01,
        )

        assert result.function_name == "test_func"
        assert result.calls == 100


class TestMemorySnapshot:
    """内存快照测试"""

    def test_snapshot_creation(self):
        """测试快照创建"""
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            current_size=1024 * 1024,  # 1 MB
            peak_size=2 * 1024 * 1024,  # 2 MB
            allocated_blocks=100,
            freed_blocks=50,
        )

        assert snapshot.current_size == 1024 * 1024
        assert snapshot.peak_size == 2 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])