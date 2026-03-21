"""
游戏执行器测试

测试 GameExecutor 模块的各项功能。
"""

import asyncio
from datetime import datetime
from unittest import mock

import pytest

from mc_agent_kit.execution.game_executor import (
    GameExecutionConfig,
    GameExecutionResult,
    GameExecutor,
    GameExecutorState,
    GameSession,
)
from mc_agent_kit.execution.executor import ExecutionResult, ExecutionStatus
from mc_agent_kit.launcher.game_launcher import GameProcess


class TestGameExecutorState:
    """测试 GameExecutorState 枚举"""

    def test_state_values(self):
        """测试状态值"""
        assert GameExecutorState.IDLE.value == "idle"
        assert GameExecutorState.STARTING.value == "starting"
        assert GameExecutorState.RUNNING.value == "running"
        assert GameExecutorState.EXECUTING.value == "executing"
        assert GameExecutorState.STOPPING.value == "stopping"
        assert GameExecutorState.ERROR.value == "error"


class TestGameExecutionConfig:
    """测试 GameExecutionConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = GameExecutionConfig()

        assert config.game_exe_path == ""
        assert config.config_path == ""
        assert config.logging_host == "127.0.0.1"
        assert config.logging_port == 0
        assert config.auto_start is False
        assert config.auto_stop is True
        assert config.execution_timeout == 30.0
        assert config.capture_logs is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = GameExecutionConfig(
            game_exe_path="/path/to/game.exe",
            config_path="/path/to/config",
            logging_host="192.168.1.1",
            logging_port=8080,
            dc_web="http://example.com",
            dc_uid="user123",
            auto_start=True,
            auto_stop=False,
            execution_timeout=60.0,
            capture_logs=False,
        )

        assert config.game_exe_path == "/path/to/game.exe"
        assert config.config_path == "/path/to/config"
        assert config.logging_host == "192.168.1.1"
        assert config.logging_port == 8080
        assert config.dc_web == "http://example.com"
        assert config.dc_uid == "user123"
        assert config.auto_start is True
        assert config.auto_stop is False
        assert config.execution_timeout == 60.0
        assert config.capture_logs is False


class TestGameExecutionResult:
    """测试 GameExecutionResult"""

    def test_create_result(self):
        """测试创建执行结果"""
        execution_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            output="Hello",
            return_value=None,
        )

        result = GameExecutionResult(
            execution_result=execution_result,
            game_logs=["log1", "log2"],
            game_errors=["error1"],
            execution_time=1.5,
            game_pid=12345,
        )

        assert result.execution_result == execution_result
        assert result.game_logs == ["log1", "log2"]
        assert result.game_errors == ["error1"]
        assert result.execution_time == 1.5
        assert result.game_pid == 12345
        assert isinstance(result.timestamp, datetime)


class TestGameSession:
    """测试 GameSession"""

    def test_create_session(self):
        """测试创建会话"""
        session = GameSession()

        assert session.process is None
        assert session.log_server is None
        assert session.state == GameExecutorState.IDLE
        assert session.start_time is None
        assert session.execution_history == []

    def test_session_with_process(self):
        """测试带进程的会话"""
        mock_process = mock.MagicMock(spec=GameProcess)
        mock_process.pid = 12345

        session = GameSession(
            process=mock_process,
            state=GameExecutorState.RUNNING,
            start_time=datetime.now(),
        )

        assert session.process == mock_process
        assert session.state == GameExecutorState.RUNNING
        assert session.start_time is not None


class TestGameExecutor:
    """测试 GameExecutor"""

    def test_create_executor(self):
        """测试创建执行器"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        assert executor.config == config
        assert executor.session.state == GameExecutorState.IDLE
        assert executor.code_executor is not None

    def test_set_log_callback(self):
        """测试设置日志回调"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        callback_calls = []

        def callback(log: str):
            callback_calls.append(log)

        executor.set_log_callback(callback)
        executor._handle_log("test log")

        assert "test log" in callback_calls

    def test_set_error_callback(self):
        """测试设置错误回调"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        error_calls = []

        def callback(error: str):
            error_calls.append(error)

        executor.set_error_callback(callback)
        executor._handle_log("ERROR: something went wrong")

        assert len(error_calls) == 1

    def test_is_error_log(self):
        """测试错误日志检测"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        assert executor._is_error_log("ERROR: test") is True
        assert executor._is_error_log("Exception: test") is True
        assert executor._is_error_log("Failed to load") is True
        assert executor._is_error_log("Traceback...") is True
        assert executor._is_error_log("错误信息") is True
        assert executor._is_error_log("异常发生") is True
        assert executor._is_error_log("Normal log") is False

    def test_get_session_info(self):
        """测试获取会话信息"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        info = executor.get_session_info()

        assert info["state"] == "idle"
        assert info["game_pid"] is None
        assert info["execution_count"] == 0

    def test_get_recent_logs(self):
        """测试获取最近日志"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        executor._log_buffer = ["log1", "log2", "log3"]

        logs = executor.get_recent_logs(2)
        assert logs == ["log2", "log3"]

    def test_get_recent_errors(self):
        """测试获取最近错误"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        executor._error_buffer = ["error1", "error2"]

        errors = executor.get_recent_errors(1)
        assert errors == ["error2"]

    def test_clear_buffers(self):
        """测试清空缓冲"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        executor._log_buffer = ["log1", "log2"]
        executor._error_buffer = ["error1"]

        executor.clear_buffers()

        assert executor._log_buffer == []
        assert executor._error_buffer == []

    def test_is_game_running_false(self):
        """测试游戏未运行"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        assert executor.is_game_running() is False

    def test_stop_game_not_running(self):
        """测试停止未运行的游戏"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        # 应该不会抛异常
        executor.stop_game()

    def test_get_execution_history_empty(self):
        """测试空执行历史"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        history = executor.get_execution_history()
        assert history == []


class TestGameExecutorWithMock:
    """使用 Mock 测试 GameExecutor"""

    def test_start_game(self):
        """测试启动游戏"""
        config = GameExecutionConfig(
            game_exe_path="/path/to/game.exe",
            config_path="/path/to/config",
        )
        executor = GameExecutor(config)

        with mock.patch(
            "mc_agent_kit.execution.game_executor.launch_game"
        ) as mock_launch:
            with mock.patch(
                "mc_agent_kit.execution.game_executor.LogServer"
            ) as mock_server_class:
                # 设置 Mock
                mock_process = mock.MagicMock()
                mock_process.pid = 12345
                mock_launch.return_value = mock_process

                mock_server = mock.MagicMock()
                mock_server.port = 8080
                mock_server_class.return_value = mock_server

                session = executor.start_game()

                assert session.state == GameExecutorState.RUNNING
                assert session.process == mock_process
                mock_launch.assert_called_once()

    def test_start_game_already_running(self):
        """测试游戏已运行时启动"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)
        executor.session.state = GameExecutorState.RUNNING

        session = executor.start_game()

        # 应该返回现有会话，不启动新游戏
        assert session.state == GameExecutorState.RUNNING

    def test_stop_game(self):
        """测试停止游戏"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        # 设置运行状态
        mock_process = mock.MagicMock()
        mock_process.wait.return_value = 0
        executor.session.process = mock_process
        executor.session.state = GameExecutorState.RUNNING

        mock_server = mock.MagicMock()
        executor.session.log_server = mock_server

        executor.stop_game()

        assert executor.session.state == GameExecutorState.IDLE
        mock_process.terminate.assert_called_once()
        mock_server.stop.assert_called_once()

    def test_execute_not_running(self):
        """测试游戏未运行时执行"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        with pytest.raises(RuntimeError, match="游戏未运行"):
            executor.execute("print('test')")

    def test_execute_success(self):
        """测试执行代码"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        # 设置运行状态
        mock_process = mock.MagicMock()
        mock_process.pid = 12345
        executor.session.process = mock_process
        executor.session.state = GameExecutorState.RUNNING

        # Mock 代码执行器
        mock_result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            output="Hello",
            return_value=None,
        )

        with mock.patch.object(
            executor.code_executor, "execute", return_value=mock_result
        ):
            result = executor.execute("print('Hello')")

            assert result.execution_result.status == ExecutionStatus.SUCCESS
            assert result.game_pid == 12345
            assert len(executor.session.execution_history) == 1

    def test_execute_with_auto_start(self):
        """测试自动启动并执行"""
        config = GameExecutionConfig(
            game_exe_path="/path/to/game.exe",
            config_path="/path/to/config",
            auto_stop=True,
        )
        executor = GameExecutor(config)

        with mock.patch.object(executor, "start_game") as mock_start:
            with mock.patch.object(executor, "stop_game") as mock_stop:
                with mock.patch.object(executor, "execute") as mock_execute:
                    mock_execute.return_value = mock.MagicMock(
                        execution_result=mock.MagicMock(),
                        game_logs=[],
                        game_errors=[],
                    )

                    executor.execute_with_auto_start("print('test')")

                    mock_start.assert_called_once()
                    mock_execute.assert_called_once()
                    mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """测试异步执行"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        # 设置运行状态
        mock_process = mock.MagicMock()
        mock_process.pid = 12345
        executor.session.process = mock_process
        executor.session.state = GameExecutorState.RUNNING

        mock_result = GameExecutionResult(
            execution_result=ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                code="print('test')",
                output="test",
                return_value=None,
            ),
        )

        with mock.patch.object(executor, "execute", return_value=mock_result):
            result = await executor.execute_async("print('test')")

            assert result.execution_result.status == ExecutionStatus.SUCCESS


class TestGameExecutorErrorHandling:
    """测试错误处理"""

    def test_start_game_error(self):
        """测试启动游戏失败"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        with mock.patch(
            "mc_agent_kit.execution.game_executor.launch_game",
            side_effect=Exception("Launch failed"),
        ):
            with mock.patch(
                "mc_agent_kit.execution.game_executor.LogServer"
            ) as mock_server_class:
                mock_server = mock.MagicMock()
                mock_server_class.return_value = mock_server

                with pytest.raises(Exception, match="Launch failed"):
                    executor.start_game()

                assert executor.session.state == GameExecutorState.ERROR

    def test_stop_game_error(self):
        """测试停止游戏失败"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        mock_process = mock.MagicMock()
        mock_process.terminate.side_effect = Exception("Terminate failed")
        executor.session.process = mock_process
        executor.session.state = GameExecutorState.RUNNING

        with pytest.raises(Exception, match="Terminate failed"):
            executor.stop_game()

        assert executor.session.state == GameExecutorState.ERROR

    def test_handle_log_with_error_detection(self):
        """测试日志处理和错误检测"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        error_calls = []
        executor.set_error_callback(lambda e: error_calls.append(e))

        executor._handle_log("Normal log message")
        assert len(error_calls) == 0

        executor._handle_log("ERROR: Something failed")
        assert len(error_calls) == 1
        assert executor._error_buffer[-1] == "ERROR: Something failed"