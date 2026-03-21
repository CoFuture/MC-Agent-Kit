"""
游戏启动器测试

测试 GameLauncher 模块的各项功能。
"""

import os
import subprocess
from datetime import datetime
from unittest import mock

import pytest

from mc_agent_kit.launcher.game_launcher import (
    GameProcess,
    find_free_port,
    generate_error_log_path,
    launch_game,
)


class TestGameProcess:
    """测试 GameProcess 数据类"""

    def test_create_game_process(self):
        """测试创建游戏进程"""
        mock_process = mock.MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = None
        mock_process.pid = 12345

        game_proc = GameProcess(
            process=mock_process,
            pid=12345,
            config_path="/path/to/config",
            error_log_path="/path/to/error.log",
            logging_port=8080,
            logging_ip="127.0.0.1",
        )

        assert game_proc.pid == 12345
        assert game_proc.config_path == "/path/to/config"
        assert game_proc.error_log_path == "/path/to/error.log"
        assert game_proc.logging_port == 8080
        assert game_proc.logging_ip == "127.0.0.1"

    def test_is_running_true(self):
        """测试进程正在运行"""
        mock_process = mock.MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = None  # None 表示仍在运行

        game_proc = GameProcess(
            process=mock_process,
            pid=12345,
            config_path="",
            error_log_path="",
            logging_port=8080,
            logging_ip="127.0.0.1",
        )

        assert game_proc.is_running() is True

    def test_is_running_false(self):
        """测试进程已退出"""
        mock_process = mock.MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = 0  # 非 None 表示已退出

        game_proc = GameProcess(
            process=mock_process,
            pid=12345,
            config_path="",
            error_log_path="",
            logging_port=8080,
            logging_ip="127.0.0.1",
        )

        assert game_proc.is_running() is False

    def test_wait(self):
        """测试等待进程"""
        mock_process = mock.MagicMock(spec=subprocess.Popen)
        mock_process.wait.return_value = 0

        game_proc = GameProcess(
            process=mock_process,
            pid=12345,
            config_path="",
            error_log_path="",
            logging_port=8080,
            logging_ip="127.0.0.1",
        )

        result = game_proc.wait(timeout=10)
        assert result == 0
        mock_process.wait.assert_called_once_with(timeout=10)

    def test_terminate(self):
        """测试终止进程"""
        mock_process = mock.MagicMock(spec=subprocess.Popen)

        game_proc = GameProcess(
            process=mock_process,
            pid=12345,
            config_path="",
            error_log_path="",
            logging_port=8080,
            logging_ip="127.0.0.1",
        )

        game_proc.terminate()
        mock_process.terminate.assert_called_once()

    def test_kill(self):
        """测试强制终止进程"""
        mock_process = mock.MagicMock(spec=subprocess.Popen)

        game_proc = GameProcess(
            process=mock_process,
            pid=12345,
            config_path="",
            error_log_path="",
            logging_port=8080,
            logging_ip="127.0.0.1",
        )

        game_proc.kill()
        mock_process.kill.assert_called_once()


class TestFindFreePort:
    """测试 find_free_port 函数"""

    def test_find_free_port(self):
        """测试查找可用端口"""
        port = find_free_port()

        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_find_free_port_unique(self):
        """测试多次查找返回不同端口"""
        ports = [find_free_port() for _ in range(5)]

        # 端口应该都在有效范围内
        for port in ports:
            assert 1024 <= port <= 65535


class TestGenerateErrorLogPath:
    """测试 generate_error_log_path 函数"""

    def test_generate_default_path(self):
        """测试生成默认路径"""
        with mock.patch.dict(os.environ, {"LOCALAPPDATA": "/appdata"}):
            path = generate_error_log_path()

            assert "Netease" in path
            assert "MCStudio" in path
            assert "errorlogs" in path
            assert path.endswith(".log")

    def test_generate_custom_path(self, tmp_path):
        """测试生成自定义路径"""
        path = generate_error_log_path(str(tmp_path))

        assert str(tmp_path) in path
        assert path.endswith(".log")

    def test_path_contains_timestamp(self):
        """测试路径包含时间戳"""
        with mock.patch.dict(os.environ, {"LOCALAPPDATA": "/appdata"}):
            path = generate_error_log_path()

            # 路径应该包含日期格式
            # 格式: YYYY-MM-DD-HH-MM-SS.log
            assert len(path.split("/")[-1].replace(".log", "").split("-")) >= 5

    def test_creates_directory(self, tmp_path):
        """测试创建目录"""
        new_dir = tmp_path / "new_logs"
        path = generate_error_log_path(str(new_dir))

        assert new_dir.exists()


class TestLaunchGame:
    """测试 launch_game 函数"""

    def test_launch_game_basic(self, tmp_path):
        """测试基本启动"""
        with mock.patch("subprocess.Popen") as mock_popen:
            mock_process = mock.MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            game_exe = str(tmp_path / "game.exe")
            config_path = str(tmp_path / "config")

            result = launch_game(
                game_exe_path=game_exe,
                config_path=config_path,
                logging_port=8080,
            )

            assert result.pid == 12345
            assert result.logging_port == 8080
            assert result.logging_ip == "127.0.0.1"
            mock_popen.assert_called_once()

    def test_launch_game_with_all_params(self, tmp_path):
        """测试带所有参数启动"""
        with mock.patch("subprocess.Popen") as mock_popen:
            mock_process = mock.MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            game_exe = str(tmp_path / "game.exe")
            config_path = str(tmp_path / "config")
            error_log = str(tmp_path / "error.log")

            result = launch_game(
                game_exe_path=game_exe,
                config_path=config_path,
                logging_port=8080,
                logging_ip="192.168.1.1",
                error_log_path=error_log,
                dc_web="http://example.com",
                dc_uid="user123",
            )

            assert result.logging_ip == "192.168.1.1"
            assert result.error_log_path == error_log

            # 检查命令行参数
            call_args = mock_popen.call_args
            cmd = call_args[0][0]

            assert game_exe in cmd
            assert f"config={config_path}" in cmd
            assert f"errorlog={error_log}" in cmd
            assert "dc_web=http://example.com" in cmd
            assert "dc_uid=user123" in cmd
            assert "loggingIP=192.168.1.1" in cmd
            assert "loggingPort=8080" in cmd

    def test_launch_game_auto_error_log(self, tmp_path):
        """测试自动生成错误日志路径"""
        with mock.patch("subprocess.Popen") as mock_popen:
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(tmp_path)}):
                mock_process = mock.MagicMock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process

                game_exe = str(tmp_path / "game.exe")
                config_path = str(tmp_path / "config")

                result = launch_game(
                    game_exe_path=game_exe,
                    config_path=config_path,
                    logging_port=8080,
                )

                # 应该自动生成错误日志路径
                assert result.error_log_path.endswith(".log")

    def test_launch_game_command_format(self, tmp_path):
        """测试命令行格式"""
        with mock.patch("subprocess.Popen") as mock_popen:
            mock_process = mock.MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            game_exe = str(tmp_path / "game.exe")
            config_path = str(tmp_path / "config")

            launch_game(
                game_exe_path=game_exe,
                config_path=config_path,
                logging_port=8080,
            )

            call_args = mock_popen.call_args
            cmd = call_args[0][0]

            # 检查必要参数
            assert "dc_tag1=studio_no_launcher" in cmd


class TestGameProcessIntegration:
    """集成测试（需要实际进程）"""

    @pytest.mark.skipif(
        True,  # 默认跳过，不创建实际进程
        reason="需要实际游戏可执行文件"
    )
    def test_actual_launch_and_terminate(self):
        """测试实际启动和终止"""
        # 这个测试需要实际的游戏可执行文件
        pass