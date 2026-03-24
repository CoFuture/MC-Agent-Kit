"""
TCP 日志服务器

接收游戏进程发送的日志数据。
"""

from __future__ import annotations
import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from queue import Queue


@dataclass
class LogServer:
    """
    TCP 日志服务器。

    接收游戏进程发送的日志数据，并放入队列供消费者处理。
    """
    host: str = "127.0.0.1"
    port: int = 0
    running: bool = False
    server_socket: socket.socket | None = None
    _thread: threading.Thread | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _log_queue: Queue = field(default_factory=Queue)
    _on_log: Callable[[str], None] | None = None

    def start(self) -> None:
        """启动日志服务器"""
        if self.running:
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)

        # 获取实际绑定的端口
        self.port = self.server_socket.getsockname()[1]

        self.running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self) -> None:
        """接受连接循环"""
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                t = threading.Thread(
                    target=self._handle_client,
                    args=(client, addr),
                    daemon=True
                )
                t.start()
            except TimeoutError:
                continue
            except OSError:
                break

    def _handle_client(self, client: socket.socket, addr: tuple) -> None:
        """处理客户端连接"""
        try:
            while self.running:
                data = client.recv(4096)
                if not data:
                    break
                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = data.hex()

                # 放入队列
                self._log_queue.put(text)

                # 调用回调
                if self._on_log:
                    self._on_log(text)
        except (ConnectionResetError, OSError):
            pass
        finally:
            client.close()

    def stop(self) -> None:
        """停止日志服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self._thread:
            self._thread.join(timeout=3)

    def get_log(self, timeout: float | None = None) -> str | None:
        """
        从队列获取一条日志。

        Args:
            timeout: 超时时间（秒）

        Returns:
            日志文本，如果超时返回 None
        """
        try:
            return self._log_queue.get(timeout=timeout)
        except Exception:
            return None

    def get_all_logs(self) -> list[str]:
        """获取队列中所有日志"""
        logs = []
        while not self._log_queue.empty():
            try:
                logs.append(self._log_queue.get_nowait())
            except Exception:
                break
        return logs

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """设置日志回调函数"""
        self._on_log = callback


def start_log_server(
    host: str = "127.0.0.1",
    port: int = 0,
    on_log: Callable[[str], None] | None = None,
) -> LogServer:
    """
    快速启动一个日志服务器。

    Args:
        host: 绑定的 IP 地址
        port: 绑定的端口，0 表示自动分配
        on_log: 日志回调函数

    Returns:
        LogServer 实例
    """
    server = LogServer(host=host, port=port)
    if on_log:
        server.set_log_callback(on_log)
    server.start()
    return server
