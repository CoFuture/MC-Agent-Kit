"""
测试 log_capture.parser 模块
"""

from datetime import datetime

import pytest

from mc_agent_kit.log_capture.parser import (
    LogLevel,
    LogParser,
)


class TestLogParser:
    """测试 LogParser 类"""

    @pytest.fixture
    def parser(self):
        return LogParser()

    def test_parse_standard_format(self, parser):
        """测试解析标准格式日志"""
        log = "[2026-03-22 01:00:00][INFO][Server] Server started"
        entry = parser.parse(log)

        assert entry.level == LogLevel.INFO
        assert entry.timestamp == datetime(2026, 3, 22, 1, 0, 0)
        assert entry.source == "Server"
        assert entry.message == "Server started"
        assert not entry.is_error

    def test_parse_error_log(self, parser):
        """测试解析错误日志"""
        log = "[2026-03-22 01:00:00][ERROR][Mod] Failed to load mod"
        entry = parser.parse(log)

        assert entry.level == LogLevel.ERROR
        assert entry.is_error

    def test_parse_warning_log(self, parser):
        """测试解析警告日志"""
        log = "[2026-03-22 01:00:00][WARNING][System] Memory low"
        entry = parser.parse(log)

        assert entry.level == LogLevel.WARNING

    def test_parse_simple_format(self, parser):
        """测试解析简单格式日志"""
        log = "[INFO] Simple log message"
        entry = parser.parse(log)

        assert entry.level == LogLevel.INFO
        assert entry.message == "Simple log message"

    def test_parse_python_traceback(self, parser):
        """测试识别 Python traceback"""
        log = "Traceback (most recent call last):\n  File \"test.py\", line 1\n    pass"
        entry = parser.parse(log)

        assert entry.is_python_traceback
        assert entry.is_error
        assert entry.level == LogLevel.ERROR

    def test_parse_python_error(self, parser):
        """测试识别 Python 错误"""
        log = "ValueError: invalid value"
        entry = parser.parse(log)

        assert entry.is_error
        assert "ValueError" in entry.message

    def test_detect_error_by_keyword(self, parser):
        """测试通过关键词检测错误"""
        log = "Something went wrong, error occurred"
        entry = parser.parse(log)

        assert entry.level == LogLevel.ERROR

    def test_detect_warning_by_keyword(self, parser):
        """测试通过关键词检测警告"""
        log = "This is a warning message"
        entry = parser.parse(log)

        assert entry.level == LogLevel.WARNING

    def test_parse_batch(self, parser):
        """测试批量解析"""
        logs = [
            "[INFO] Message 1",
            "[ERROR] Message 2",
            "[WARNING] Message 3",
        ]
        entries = parser.parse_batch(logs)

        assert len(entries) == 3
        assert entries[0].level == LogLevel.INFO
        assert entries[1].level == LogLevel.ERROR
        assert entries[2].level == LogLevel.WARNING

    def test_extract_errors(self, parser):
        """测试提取错误日志"""
        logs = [
            "[INFO] Normal message",
            "[ERROR] Error message",
            "[WARNING] Warning message",
            "Traceback (most recent call last):",
        ]
        errors = parser.extract_errors(logs)

        assert len(errors) == 2
        assert all(e.is_error for e in errors)
