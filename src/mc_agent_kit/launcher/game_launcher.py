"""
游戏启动模块

启动 Minecraft 游戏进程，并管理其生命周期。
"""

import os
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GameProcess:
    """游戏进程信息"""
    process: subprocess.Popen
    pid: int
    config_path: str
    error_log_path: str
    logging_port: int
    logging_ip: str

    def is_running(self) -> bool:
        """检查进程是否仍在运行"""
        return self.process.poll() is None

    def wait(self, timeout: float | None = None) -> int:
        """
        等待游戏进程退出。

        Args:
            timeout: 超时时间（秒）

        Returns:
            进程返回码
        """
        return self.process.wait(timeout=timeout)

    def terminate(self) -> None:
        """终止游戏进程"""
        self.process.terminate()

    def kill(self) -> None:
        """强制终止游戏进程"""
        self.process.kill()


def find_free_port() -> int:
    """
    查找一个可用的端口号。

    Returns:
        可用的端口号
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def generate_error_log_path(base_dir: str | None = None) -> str:
    """
    生成错误日志文件路径。

    Args:
        base_dir: 日志目录基础路径，默认使用 MC Studio 日志目录

    Returns:
        日志文件完整路径
    """
    if base_dir is None:
        base_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Netease",
            "MCStudio",
            "log",
            "x64_mc",
            "errorlogs"
        )

    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return os.path.join(base_dir, f"{timestamp}.log")


def launch_game(
    game_exe_path: str,
    config_path: str,
    logging_port: int,
    logging_ip: str = "127.0.0.1",
    error_log_path: str | None = None,
    dc_web: str = "",
    dc_uid: str = "",
) -> GameProcess:
    """
    启动游戏进程。

    Args:
        game_exe_path: 游戏可执行文件路径
        config_path: 配置文件路径
        logging_port: 日志接收端口
        logging_ip: 日志接收 IP
        error_log_path: 错误日志路径
        dc_web: 数据上报网关
        dc_uid: 数据上报用户 ID

    Returns:
        GameProcess 对象
    """
    if error_log_path is None:
        error_log_path = generate_error_log_path()

    cmd = [
        game_exe_path,
        f"config={config_path}",
        f"errorlog={error_log_path}",
        "dc_tag1=studio_no_launcher",
    ]

    if dc_web:
        cmd.append(f"dc_web={dc_web}")
    if dc_uid:
        cmd.append(f"dc_uid={dc_uid}")

    cmd.append(f"loggingIP={logging_ip}")
    cmd.append(f"loggingPort={logging_port}")

    process = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(game_exe_path),
    )

    return GameProcess(
        process=process,
        pid=process.pid,
        config_path=config_path,
        error_log_path=error_log_path,
        logging_port=logging_port,
        logging_ip=logging_ip,
    )
