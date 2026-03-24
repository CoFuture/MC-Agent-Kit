"""
游戏内执行器模块

整合游戏启动器与代码执行器，实现在游戏环境中执行代码。
"""

from __future__ import annotations
import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..launcher.game_launcher import GameProcess, find_free_port, launch_game
from ..log_capture.tcp_server import LogServer
from .executor import CodeExecutor, ExecutionConfig, ExecutionResult

logger = logging.getLogger(__name__)


class GameExecutorState(Enum):
    """游戏执行器状态"""

    IDLE = "idle"  # 空闲
    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    EXECUTING = "executing"  # 执行代码中
    STOPPING = "stopping"  # 停止中
    ERROR = "error"  # 错误


@dataclass
class GameExecutionConfig:
    """游戏执行配置"""

    game_exe_path: str = ""  # 游戏可执行文件路径
    config_path: str = ""  # 启动配置文件路径
    logging_host: str = "127.0.0.1"  # 日志接收 IP
    logging_port: int = 0  # 日志接收端口（0 = 自动分配）
    dc_web: str = ""  # 数据上报网关
    dc_uid: str = ""  # 数据上报用户 ID
    auto_start: bool = False  # 是否自动启动游戏
    auto_stop: bool = True  # 执行完成后是否自动停止游戏
    execution_timeout: float = 30.0  # 执行超时时间
    capture_logs: bool = True  # 是否捕获日志


@dataclass
class GameExecutionResult:
    """游戏执行结果"""

    execution_result: ExecutionResult  # 代码执行结果
    game_logs: list[str] = field(default_factory=list)  # 游戏日志
    game_errors: list[str] = field(default_factory=list)  # 游戏错误
    execution_time: float = 0.0  # 总执行时间
    game_pid: int | None = None  # 游戏进程 ID
    timestamp: datetime = field(default_factory=datetime.now)  # 执行时间戳


@dataclass
class GameSession:
    """游戏会话"""

    process: GameProcess | None = None  # 游戏进程
    log_server: LogServer | None = None  # 日志服务器
    state: GameExecutorState = GameExecutorState.IDLE  # 当前状态
    start_time: datetime | None = None  # 启动时间
    execution_history: list[GameExecutionResult] = field(default_factory=list)  # 执行历史


class GameExecutor:
    """
    游戏内执行器。

    整合游戏启动器和代码执行器，提供：
    - 游戏进程管理
    - 代码执行环境
    - 日志实时捕获
    - 执行历史记录

    使用示例:
        executor = GameExecutor(config)
        await executor.start_game()
        result = await executor.execute("print('Hello from game!')")
        await executor.stop_game()
    """

    def __init__(
        self,
        config: GameExecutionConfig,
        execution_config: ExecutionConfig | None = None,
    ):
        """
        初始化游戏执行器。

        Args:
            config: 游戏执行配置
            execution_config: 代码执行配置
        """
        self.config = config
        self.execution_config = execution_config or ExecutionConfig()
        self.code_executor = CodeExecutor(self.execution_config)
        self.session = GameSession()
        self._log_buffer: list[str] = []
        self._error_buffer: list[str] = []
        self._on_log: Callable[[str], None] | None = None
        self._on_error: Callable[[str], None] | None = None

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """设置日志回调函数"""
        self._on_log = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """设置错误回调函数"""
        self._on_error = callback

    def start_game(self) -> GameSession:
        """
        启动游戏进程。

        Returns:
            GameSession: 游戏会话
        """
        if self.session.state == GameExecutorState.RUNNING:
            logger.warning("游戏已在运行中")
            return self.session

        self.session.state = GameExecutorState.STARTING

        try:
            # 确定日志端口
            port = self.config.logging_port or find_free_port()

            # 启动日志服务器
            if self.config.capture_logs:
                self.session.log_server = LogServer(
                    host=self.config.logging_host,
                    port=port,
                )
                self.session.log_server.set_log_callback(self._handle_log)
                self.session.log_server.start()
                actual_port = self.session.log_server.port
            else:
                actual_port = port

            # 启动游戏进程
            self.session.process = launch_game(
                game_exe_path=self.config.game_exe_path,
                config_path=self.config.config_path,
                logging_port=actual_port,
                logging_ip=self.config.logging_host,
                dc_web=self.config.dc_web,
                dc_uid=self.config.dc_uid,
            )

            self.session.state = GameExecutorState.RUNNING
            self.session.start_time = datetime.now()

            logger.info(f"游戏已启动，PID: {self.session.process.pid}")

        except Exception as e:
            self.session.state = GameExecutorState.ERROR
            logger.error(f"启动游戏失败: {e}")
            raise

        return self.session

    def stop_game(self) -> None:
        """停止游戏进程"""
        if self.session.state != GameExecutorState.RUNNING:
            return

        self.session.state = GameExecutorState.STOPPING

        try:
            if self.session.process:
                self.session.process.terminate()
                try:
                    self.session.process.wait(timeout=5)
                except Exception:
                    if self.session.process:
                        self.session.process.kill()

            if self.session.log_server:
                self.session.log_server.stop()

            self.session.state = GameExecutorState.IDLE
            logger.info("游戏已停止")

        except Exception as e:
            self.session.state = GameExecutorState.ERROR
            logger.error(f"停止游戏失败: {e}")
            raise

    def execute(self, code: str, context: dict[str, Any] | None = None) -> GameExecutionResult:
        """
        在游戏环境中执行代码。

        Args:
            code: 要执行的代码
            context: 执行上下文

        Returns:
            GameExecutionResult: 执行结果
        """
        if self.session.state != GameExecutorState.RUNNING:
            raise RuntimeError("游戏未运行，请先调用 start_game()")

        self.session.state = GameExecutorState.EXECUTING
        start_time = datetime.now()

        # 清空日志缓冲
        self._log_buffer.clear()
        self._error_buffer.clear()

        try:
            # 执行代码
            execution_result = self.code_executor.execute(code, context)

            # 收集执行期间的游戏日志
            game_logs = list(self._log_buffer)
            game_errors = list(self._error_buffer)

            # 构建结果
            result = GameExecutionResult(
                execution_result=execution_result,
                game_logs=game_logs,
                game_errors=game_errors,
                execution_time=(datetime.now() - start_time).total_seconds(),
                game_pid=self.session.process.pid if self.session.process else None,
            )

            # 记录历史
            self.session.execution_history.append(result)

            return result

        finally:
            self.session.state = GameExecutorState.RUNNING

    async def execute_async(
        self, code: str, context: dict[str, Any] | None = None
    ) -> GameExecutionResult:
        """
        异步执行代码。

        Args:
            code: 要执行的代码
            context: 执行上下文

        Returns:
            GameExecutionResult: 执行结果
        """
        # 在线程池中执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.execute(code, context))

    def execute_with_auto_start(
        self, code: str, context: dict[str, Any] | None = None
    ) -> GameExecutionResult:
        """
        自动启动游戏并执行代码。

        Args:
            code: 要执行的代码
            context: 执行上下文

        Returns:
            GameExecutionResult: 执行结果
        """
        auto_started = False

        if self.session.state != GameExecutorState.RUNNING:
            self.start_game()
            auto_started = True

        try:
            result = self.execute(code, context)
            return result
        finally:
            if auto_started and self.config.auto_stop:
                self.stop_game()

    def _handle_log(self, log: str) -> None:
        """处理游戏日志"""
        self._log_buffer.append(log)

        # 检测错误
        if self._is_error_log(log):
            self._error_buffer.append(log)
            if self._on_error:
                self._on_error(log)

        # 调用回调
        if self._on_log:
            self._on_log(log)

    def _is_error_log(self, log: str) -> bool:
        """检测日志是否为错误"""
        error_keywords = ["error", "exception", "failed", "traceback", "错误", "异常"]
        log_lower = log.lower()
        return any(kw in log_lower for kw in error_keywords)

    def get_session_info(self) -> dict[str, Any]:
        """获取会话信息"""
        return {
            "state": self.session.state.value,
            "game_pid": self.session.process.pid if self.session.process else None,
            "start_time": self.session.start_time.isoformat() if self.session.start_time else None,
            "execution_count": len(self.session.execution_history),
            "log_server_port": self.session.log_server.port if self.session.log_server else None,
        }

    def get_execution_history(self, limit: int = 100) -> list[GameExecutionResult]:
        """获取执行历史"""
        return self.session.execution_history[-limit:]

    def is_game_running(self) -> bool:
        """检查游戏是否在运行"""
        return (
            self.session.state == GameExecutorState.RUNNING
            and self.session.process is not None
            and self.session.process.is_running()
        )

    def get_recent_logs(self, count: int = 100) -> list[str]:
        """获取最近的日志"""
        return self._log_buffer[-count:]

    def get_recent_errors(self, count: int = 50) -> list[str]:
        """获取最近的错误日志"""
        return self._error_buffer[-count:]

    def clear_buffers(self) -> None:
        """清空日志缓冲"""
        self._log_buffer.clear()
        self._error_buffer.clear()
