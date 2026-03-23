"""
游戏调试器模块

提供游戏内日志捕获、断点调试、变量监视、热重载支持等功能。

迭代 #57: Agent 技能增强与 ModSDK 深度集成
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class DebugState(Enum):
    """调试状态枚举"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PAUSED = "paused"
    RUNNING = "running"
    ERROR = "error"


class BreakpointType(Enum):
    """断点类型枚举"""

    LINE = "line"  # 行断点
    CONDITIONAL = "conditional"  # 条件断点
    LOG = "log"  # 日志断点
    FUNCTION = "function"  # 函数断点


@dataclass
class Breakpoint:
    """断点配置"""

    id: str
    file: str
    line: int
    enabled: bool = True
    bp_type: BreakpointType = BreakpointType.LINE
    condition: Optional[str] = None
    log_message: Optional[str] = None
    hit_count: int = 0
    max_hits: int = 0  # 0 表示无限制


@dataclass
class WatchVariable:
    """监视变量"""

    name: str
    expression: str
    value: Any = None
    type_name: str = ""
    last_updated: float = 0.0


@dataclass
class DebugFrame:
    """调试栈帧"""

    index: int
    file: str
    line: int
    function: str
    locals: dict[str, Any] = field(default_factory=dict)


@dataclass
class LogEntry:
    """日志条目"""

    timestamp: float
    level: str
    message: str
    source: str = ""
    file: str = ""
    line: int = 0


@dataclass
class DebugSession:
    """调试会话"""

    session_id: str
    game_pid: int
    start_time: float
    state: DebugState
    breakpoints: list[Breakpoint] = field(default_factory=list)
    watches: list[WatchVariable] = field(default_factory=list)
    call_stack: list[DebugFrame] = field(default_factory=list)
    logs: list[LogEntry] = field(default_factory=list)
    current_frame: int = 0


class GameDebugger:
    """
    游戏调试器

    提供游戏内调试支持，包括日志捕获、断点设置、变量监视等功能。
    """

    # 日志级别映射
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # 常见错误模式
    ERROR_PATTERNS = [
        (r"KeyError:\s*['\"](.+?)['\"]", "KeyError"),
        (r"AttributeError:\s*(.+)", "AttributeError"),
        (r"TypeError:\s*(.+)", "TypeError"),
        (r"ValueError:\s*(.+)", "ValueError"),
        (r"ImportError:\s*(.+)", "ImportError"),
        (r"SyntaxError:\s*(.+)", "SyntaxError"),
        (r"NameError:\s*name\s*['\"](.+?)['\"]\s*is not defined", "NameError"),
        (r"IndexError:\s*(.+)", "IndexError"),
        (r"File\s*['\"](.+?)['\"]\s*not found", "FileNotFoundError"),
    ]

    def __init__(
        self,
        log_dir: Optional[str] = None,
        max_logs: int = 10000,
        log_callback: Optional[Callable[[LogEntry], None]] = None,
    ):
        """
        初始化游戏调试器

        Args:
            log_dir: 日志目录
            max_logs: 最大日志条数
            log_callback: 日志回调函数
        """
        self.log_dir = Path(log_dir) if log_dir else None
        self.max_logs = max_logs
        self.log_callback = log_callback

        self._session: Optional[DebugSession] = None
        self._breakpoint_counter = 0
        self._log_file: Optional[Any] = None
        self._log_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def state(self) -> DebugState:
        """获取当前调试状态"""
        if self._session is None:
            return DebugState.DISCONNECTED
        return self._session.state

    @property
    def session(self) -> Optional[DebugSession]:
        """获取当前调试会话"""
        return self._session

    def attach(self, game_pid: int) -> bool:
        """
        附加到游戏进程

        Args:
            game_pid: 游戏进程 ID

        Returns:
            是否成功附加
        """
        if self._session is not None:
            logger.warning("已有活跃的调试会话，请先断开")
            return False

        try:
            # 检查进程是否存在
            # 在 Windows 上使用 tasklist
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {game_pid}"],
                capture_output=True,
                text=True,
            )
            if str(game_pid) not in result.stdout:
                logger.error(f"进程 {game_pid} 不存在")
                return False

            # 创建调试会话
            self._session = DebugSession(
                session_id=f"debug_{game_pid}_{int(time.time())}",
                game_pid=game_pid,
                start_time=time.time(),
                state=DebugState.CONNECTED,
            )

            # 启动日志捕获线程
            self._start_log_capture()

            logger.info(f"已附加到游戏进程 {game_pid}")
            return True

        except Exception as e:
            logger.error(f"附加失败: {e}")
            return False

    def detach(self) -> bool:
        """
        断开与游戏进程的连接

        Returns:
            是否成功断开
        """
        if self._session is None:
            return True

        try:
            # 停止日志捕获
            self._stop_log_capture()

            # 保存日志
            if self.log_dir and self._session.logs:
                self._save_logs()

            self._session.state = DebugState.DISCONNECTED
            self._session = None

            logger.info("已断开调试连接")
            return True

        except Exception as e:
            logger.error(f"断开失败: {e}")
            return False

    def set_breakpoint(
        self,
        file: str,
        line: int,
        condition: Optional[str] = None,
        log_message: Optional[str] = None,
    ) -> Optional[Breakpoint]:
        """
        设置断点

        Args:
            file: 文件路径
            line: 行号
            condition: 条件表达式
            log_message: 日志消息（日志断点）

        Returns:
            创建的断点，失败返回 None
        """
        if self._session is None:
            logger.warning("没有活跃的调试会话")
            return None

        self._breakpoint_counter += 1
        bp_id = f"bp_{self._breakpoint_counter}"

        bp_type = BreakpointType.LINE
        if log_message:
            bp_type = BreakpointType.LOG
        elif condition:
            bp_type = BreakpointType.CONDITIONAL

        breakpoint = Breakpoint(
            id=bp_id,
            file=file,
            line=line,
            bp_type=bp_type,
            condition=condition,
            log_message=log_message,
        )

        self._session.breakpoints.append(breakpoint)
        logger.info(f"已设置断点: {file}:{line}")

        return breakpoint

    def remove_breakpoint(self, bp_id: str) -> bool:
        """
        移除断点

        Args:
            bp_id: 断点 ID

        Returns:
            是否成功移除
        """
        if self._session is None:
            return False

        for i, bp in enumerate(self._session.breakpoints):
            if bp.id == bp_id:
                self._session.breakpoints.pop(i)
                logger.info(f"已移除断点: {bp_id}")
                return True

        return False

    def toggle_breakpoint(self, bp_id: str) -> bool:
        """
        切换断点启用状态

        Args:
            bp_id: 断点 ID

        Returns:
            新的启用状态
        """
        if self._session is None:
            return False

        for bp in self._session.breakpoints:
            if bp.id == bp_id:
                bp.enabled = not bp.enabled
                return bp.enabled

        return False

    def add_watch(self, name: str, expression: str) -> Optional[WatchVariable]:
        """
        添加变量监视

        Args:
            name: 监视名称
            expression: 表达式

        Returns:
            创建的监视变量
        """
        if self._session is None:
            logger.warning("没有活跃的调试会话")
            return None

        watch = WatchVariable(name=name, expression=expression)
        self._session.watches.append(watch)
        return watch

    def remove_watch(self, name: str) -> bool:
        """
        移除变量监视

        Args:
            name: 监视名称

        Returns:
            是否成功移除
        """
        if self._session is None:
            return False

        for i, watch in enumerate(self._session.watches):
            if watch.name == name:
                self._session.watches.pop(i)
                return True

        return False

    def get_variables(self) -> dict[str, Any]:
        """
        获取当前变量

        Returns:
            变量字典
        """
        if self._session is None:
            return {}

        variables = {}
        for watch in self._session.watches:
            variables[watch.name] = {
                "expression": watch.expression,
                "value": watch.value,
                "type": watch.type_name,
            }

        # 如果有调用栈，添加当前帧的局部变量
        if self._session.call_stack and self._session.current_frame < len(
            self._session.call_stack
        ):
            current_frame = self._session.call_stack[self._session.current_frame]
            variables["__locals__"] = current_frame.locals

        return variables

    def get_call_stack(self) -> list[DebugFrame]:
        """
        获取调用栈

        Returns:
            调用栈列表
        """
        if self._session is None:
            return []
        return self._session.call_stack

    def step_over(self) -> bool:
        """
        单步跳过

        Returns:
            是否成功
        """
        if self._session is None or self._session.state != DebugState.PAUSED:
            return False

        # 模拟单步跳过
        self._session.state = DebugState.RUNNING
        logger.info("执行单步跳过")
        return True

    def step_into(self) -> bool:
        """
        单步进入

        Returns:
            是否成功
        """
        if self._session is None or self._session.state != DebugState.PAUSED:
            return False

        # 模拟单步进入
        self._session.state = DebugState.RUNNING
        logger.info("执行单步进入")
        return True

    def step_out(self) -> bool:
        """
        单步跳出

        Returns:
            是否成功
        """
        if self._session is None or self._session.state != DebugState.PAUSED:
            return False

        # 模拟单步跳出
        self._session.state = DebugState.RUNNING
        logger.info("执行单步跳出")
        return True

    def continue_execution(self) -> bool:
        """
        继续执行

        Returns:
            是否成功
        """
        if self._session is None or self._session.state != DebugState.PAUSED:
            return False

        self._session.state = DebugState.RUNNING
        logger.info("继续执行")
        return True

    def pause(self) -> bool:
        """
        暂停执行

        Returns:
            是否成功
        """
        if self._session is None or self._session.state != DebugState.RUNNING:
            return False

        self._session.state = DebugState.PAUSED
        logger.info("已暂停执行")
        return True

    def hot_reload(self, file: str) -> bool:
        """
        热重载文件

        Args:
            file: 要重载的文件路径

        Returns:
            是否成功
        """
        if self._session is None:
            return False

        # 检查文件是否存在
        if not os.path.exists(file):
            logger.error(f"文件不存在: {file}")
            return False

        # 模拟热重载
        logger.info(f"热重载文件: {file}")
        return True

    def get_logs(
        self,
        level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LogEntry]:
        """
        获取日志

        Args:
            level: 日志级别过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            日志条目列表
        """
        if self._session is None:
            return []

        logs = self._session.logs
        if level:
            logs = [log for log in logs if log.level == level]

        return logs[offset : offset + limit]

    def analyze_logs(self) -> dict[str, Any]:
        """
        分析日志

        Returns:
            分析结果
        """
        if self._session is None:
            return {"error": "没有活跃的调试会话"}

        logs = self._session.logs
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        statistics = {
            "total": len(logs),
            "by_level": {},
        }

        # 统计各级别数量
        for log in logs:
            level = log.level
            statistics["by_level"][level] = statistics["by_level"].get(level, 0) + 1

            # 检测错误
            if log.level == "ERROR" or log.level == "CRITICAL":
                error_info = self._parse_error(log.message)
                if error_info:
                    error_info["log_entry"] = log
                    errors.append(error_info)

            # 检测警告
            if log.level == "WARNING":
                warnings.append(
                    {
                        "message": log.message,
                        "source": log.source,
                        "log_entry": log,
                    }
                )

        return {
            "statistics": statistics,
            "errors": errors,
            "warnings": warnings,
            "has_errors": len(errors) > 0,
            "has_warnings": len(warnings) > 0,
        }

    # ==================== 私有方法 ====================

    def _start_log_capture(self) -> None:
        """启动日志捕获线程"""
        if self._session is None:
            return

        self._stop_event.clear()
        self._log_thread = threading.Thread(target=self._capture_logs, daemon=True)
        self._log_thread.start()

    def _stop_log_capture(self) -> None:
        """停止日志捕获线程"""
        self._stop_event.set()
        if self._log_thread:
            self._log_thread.join(timeout=2.0)
            self._log_thread = None

    def _capture_logs(self) -> None:
        """日志捕获循环"""
        while not self._stop_event.is_set() and self._session:
            try:
                # 模拟日志捕获
                # 实际实现需要根据游戏的日志输出方式调整
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"日志捕获错误: {e}")
                break

    def _parse_error(self, message: str) -> Optional[dict[str, Any]]:
        """解析错误消息"""
        for pattern, error_type in self.ERROR_PATTERNS:
            match = re.search(pattern, message)
            if match:
                return {
                    "type": error_type,
                    "message": message,
                    "detail": match.group(1) if match.groups() else "",
                }
        return None

    def _save_logs(self) -> None:
        """保存日志到文件"""
        if not self._session or not self.log_dir:
            return

        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / f"debug_{self._session.session_id}.log"

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                for log in self._session.logs:
                    f.write(f"[{log.level}] {log.message}\n")

            logger.info(f"日志已保存到: {log_file}")

        except Exception as e:
            logger.error(f"保存日志失败: {e}")

    def add_log(self, level: str, message: str, source: str = "") -> None:
        """
        添加日志条目

        Args:
            level: 日志级别
            message: 日志消息
            source: 日志来源
        """
        if self._session is None:
            return

        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            message=message,
            source=source,
        )

        self._session.logs.append(entry)

        # 限制日志数量
        if len(self._session.logs) > self.max_logs:
            self._session.logs = self._session.logs[-self.max_logs :]

        # 回调
        if self.log_callback:
            self.log_callback(entry)


def create_game_debugger(
    log_dir: Optional[str] = None,
    max_logs: int = 10000,
    log_callback: Optional[Callable[[LogEntry], None]] = None,
) -> GameDebugger:
    """创建游戏调试器实例"""
    return GameDebugger(log_dir=log_dir, max_logs=max_logs, log_callback=log_callback)