"""
TCP 日志服务器测试

测试 TCP 日志服务器的启动、接收、停止等功能。
"""

import socket
import threading
import time
from unittest import mock

import pytest

from mc_agent_kit.log_capture.tcp_server import LogServer, start_log_server


class TestLogServer:
    """测试 LogServer 类"""

    def test_create_server(self):
        """测试创建服务器"""
        server = LogServer(host="127.0.0.1", port=0)
        assert server.host == "127.0.0.1"
        assert server.port == 0
        assert not server.running

    def test_start_server(self):
        """测试启动服务器"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        assert server.running
        assert server.port > 0  # 自动分配端口
        assert server.server_socket is not None

        server.stop()

    def test_start_already_running(self):
        """测试重复启动"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()
        port = server.port

        # 再次启动应该无效
        server.start()
        assert server.port == port

        server.stop()

    def test_stop_server(self):
        """测试停止服务器"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()
        server.stop()

        assert not server.running

    def test_get_log_empty(self):
        """测试空队列获取日志"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        log = server.get_log(timeout=0.1)
        assert log is None

        server.stop()

    def test_get_all_logs_empty(self):
        """测试空队列获取所有日志"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        logs = server.get_all_logs()
        assert logs == []

        server.stop()

    def test_set_log_callback(self):
        """测试设置日志回调"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        callback_calls = []

        def callback(log: str):
            callback_calls.append(log)

        server.set_log_callback(callback)

        # 发送测试数据
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall(b"test log message")
        client.close()

        time.sleep(0.2)

        assert len(callback_calls) > 0
        assert "test log message" in callback_calls[0]

        server.stop()

    def test_receive_log(self):
        """测试接收日志"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        # 发送测试数据
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall(b"hello world")
        client.close()

        time.sleep(0.2)

        log = server.get_log(timeout=1.0)
        assert log is not None
        assert "hello world" in log

        server.stop()

    def test_receive_multiple_logs(self):
        """测试接收多条日志"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        # 发送多条日志
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall(b"log1\n")
        time.sleep(0.1)
        client.sendall(b"log2\n")
        time.sleep(0.1)
        client.sendall(b"log3\n")
        client.close()

        time.sleep(0.3)

        logs = server.get_all_logs()
        # 日志可能合并，至少应该有内容
        assert len(logs) >= 1
        total_content = "".join(logs)
        assert "log1" in total_content or "log2" in total_content or "log3" in total_content

        server.stop()

    def test_unicode_log(self):
        """测试 Unicode 日志"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        # 发送中文日志
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall("中文日志测试".encode("utf-8"))
        client.close()

        time.sleep(0.2)

        log = server.get_log(timeout=1.0)
        assert log is not None
        assert "中文" in log

        server.stop()

    def test_get_port_after_start(self):
        """测试启动后获取端口"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        # 端口应该已更新
        actual_port = server.port
        assert actual_port > 0
        assert actual_port < 65536

        server.stop()


class TestStartLogServer:
    """测试 start_log_server 函数"""

    def test_start_log_server_basic(self):
        """测试基本启动"""
        server = start_log_server()
        assert server.running
        assert server.port > 0
        server.stop()

    def test_start_log_server_with_callback(self):
        """测试带回调启动"""
        callback_calls = []

        def callback(log: str):
            callback_calls.append(log)

        server = start_log_server(on_log=callback)
        assert server.running
        assert server._on_log is callback
        server.stop()

    def test_start_log_server_specific_port(self):
        """测试指定端口"""
        server = start_log_server(port=0)  # 0 = auto
        assert server.running
        server.stop()


class TestLogServerConcurrency:
    """测试并发场景"""

    def test_multiple_clients(self):
        """测试多客户端连接"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        # 多个客户端同时发送
        clients = []
        for i in range(3):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", server.port))
            client.sendall(f"client {i}".encode())
            clients.append(client)

        time.sleep(0.3)

        logs = server.get_all_logs()
        assert len(logs) >= 3

        for client in clients:
            client.close()

        server.stop()

    def test_start_stop_multiple_times(self):
        """测试多次启动停止"""
        server = LogServer(host="127.0.0.1", port=0)

        for _ in range(3):
            server.start()
            assert server.running
            server.stop()
            assert not server.running


class TestLogServerEdgeCases:
    """测试边界情况"""

    def test_stop_without_start(self):
        """测试未启动时停止"""
        server = LogServer(host="127.0.0.1", port=0)
        # 应该不会报错
        server.stop()

    def test_empty_data(self):
        """测试空数据"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall(b"")
        client.close()

        time.sleep(0.2)

        # 空数据不应产生日志
        log = server.get_log(timeout=0.1)
        assert log is None

        server.stop()

    def test_large_data(self):
        """测试大数据"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        # 发送大数据
        large_data = b"x" * 10000
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall(large_data)
        client.close()

        time.sleep(0.3)

        logs = server.get_all_logs()
        total_size = sum(len(log) for log in logs)
        assert total_size >= 10000

        server.stop()

    def test_client_disconnect(self):
        """测试客户端断开"""
        server = LogServer(host="127.0.0.1", port=0)
        server.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", server.port))
        client.sendall(b"test")
        client.close()

        time.sleep(0.2)

        # 服务器应该仍在运行
        assert server.running

        server.stop()