"""
迭代 #29 测试

测试游戏启动器诊断、CLI 增强和知识检索集成功能。
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ============================================================
# Launcher Diagnoser Tests
# ============================================================

class TestDiagnosticSeverity:
    """诊断严重程度测试"""

    def test_severity_values(self):
        """测试严重程度枚举值"""
        from mc_agent_kit.launcher.diagnoser import DiagnosticSeverity

        assert DiagnosticSeverity.ERROR.value == "error"
        assert DiagnosticSeverity.WARNING.value == "warning"
        assert DiagnosticSeverity.INFO.value == "info"


class TestDiagnosticCategory:
    """诊断类别测试"""

    def test_category_values(self):
        """测试类别枚举值"""
        from mc_agent_kit.launcher.diagnoser import DiagnosticCategory

        assert DiagnosticCategory.PATH.value == "path"
        assert DiagnosticCategory.CONFIG.value == "config"
        assert DiagnosticCategory.VERSION.value == "version"
        assert DiagnosticCategory.ADDON.value == "addon"
        assert DiagnosticCategory.SYSTEM.value == "system"


class TestDiagnosticIssue:
    """诊断问题测试"""

    def test_create_issue(self):
        """测试创建诊断问题"""
        from mc_agent_kit.launcher.diagnoser import (
            DiagnosticCategory,
            DiagnosticIssue,
            DiagnosticSeverity,
        )

        issue = DiagnosticIssue(
            category=DiagnosticCategory.PATH,
            severity=DiagnosticSeverity.ERROR,
            code="TEST_ERROR",
            message="Test error message",
            details="Test details",
            suggestion="Test suggestion",
        )

        assert issue.category == DiagnosticCategory.PATH
        assert issue.severity == DiagnosticSeverity.ERROR
        assert issue.code == "TEST_ERROR"
        assert issue.message == "Test error message"


class TestDiagnosticReport:
    """诊断报告测试"""

    def test_create_report(self):
        """测试创建诊断报告"""
        from mc_agent_kit.launcher.diagnoser import (
            DiagnosticCategory,
            DiagnosticIssue,
            DiagnosticReport,
            DiagnosticSeverity,
        )

        report = DiagnosticReport(success=True)
        assert report.success is True
        assert report.issues == []
        assert report.checks_passed == 0

    def test_has_errors(self):
        """测试 has_errors 属性"""
        from mc_agent_kit.launcher.diagnoser import (
            DiagnosticCategory,
            DiagnosticIssue,
            DiagnosticReport,
            DiagnosticSeverity,
        )

        report = DiagnosticReport(success=True)
        assert report.has_errors is False

        report.issues.append(DiagnosticIssue(
            category=DiagnosticCategory.PATH,
            severity=DiagnosticSeverity.ERROR,
            code="TEST",
            message="Test",
        ))
        assert report.has_errors is True

    def test_has_warnings(self):
        """测试 has_warnings 属性"""
        from mc_agent_kit.launcher.diagnoser import (
            DiagnosticCategory,
            DiagnosticIssue,
            DiagnosticReport,
            DiagnosticSeverity,
        )

        report = DiagnosticReport(success=True)
        assert report.has_warnings is False

        report.issues.append(DiagnosticIssue(
            category=DiagnosticCategory.PATH,
            severity=DiagnosticSeverity.WARNING,
            code="TEST",
            message="Test",
        ))
        assert report.has_warnings is True

    def test_to_dict(self):
        """测试转换为字典"""
        from mc_agent_kit.launcher.diagnoser import (
            DiagnosticCategory,
            DiagnosticIssue,
            DiagnosticReport,
            DiagnosticSeverity,
        )

        report = DiagnosticReport(
            success=True,
            game_path="/path/to/game",
            checks_passed=5,
        )
        report.issues.append(DiagnosticIssue(
            category=DiagnosticCategory.PATH,
            severity=DiagnosticSeverity.WARNING,
            code="TEST",
            message="Test message",
        ))

        data = report.to_dict()

        assert data["success"] is True
        assert data["game_path"] == "/path/to/game"
        assert data["checks_passed"] == 5
        assert len(data["issues"]) == 1
        assert data["issues"][0]["code"] == "TEST"


class TestLauncherDiagnoser:
    """启动器诊断器测试"""

    def test_create_diagnoser(self):
        """测试创建诊断器"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        assert diagnoser.game_path is None

        diagnoser = LauncherDiagnoser(game_path="/path/to/game")
        assert diagnoser.game_path == "/path/to/game"

    def test_diagnose_game_path_not_found(self):
        """测试游戏路径未找到"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        # Mock _detect_game_path to return None
        diagnoser._detect_game_path = lambda: None

        report = diagnoser.diagnose()

        assert report.success is False
        assert report.has_errors is True
        assert any(i.code == "GAME_PATH_NOT_FOUND" for i in report.issues)

    def test_diagnose_invalid_game_path(self):
        """测试无效游戏路径"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser(game_path="/nonexistent/path/game.exe")
        report = diagnoser.diagnose()

        assert report.has_errors is True
        assert any(i.code == "GAME_PATH_INVALID" for i in report.issues)

    def test_diagnose_addon_not_found(self):
        """测试 Addon 目录不存在"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        diagnoser._detect_game_path = lambda: "/path/to/game"

        report = diagnoser.diagnose(addon_path="/nonexistent/addon")

        assert any(i.code == "ADDON_PATH_NOT_FOUND" for i in report.issues)

    def test_diagnose_config_not_found(self):
        """测试配置文件不存在"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        diagnoser._detect_game_path = lambda: "/path/to/game"

        report = diagnoser.diagnose(config_path="/nonexistent/config.json")

        assert any(i.code == "CONFIG_NOT_FOUND" for i in report.issues)

    def test_quick_check(self):
        """测试快速检查"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        diagnoser._detect_game_path = lambda: "/path/to/game"

        report = diagnoser.quick_check("/nonexistent/addon")

        assert report.addon_path == "/nonexistent/addon"

    def test_collect_system_info(self):
        """测试收集系统信息"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        info = diagnoser._collect_system_info()

        assert "os" in info
        assert "python_version" in info
        assert "architecture" in info


class TestDiagnoseLauncher:
    """便捷函数测试"""

    def test_diagnose_launcher_function(self):
        """测试 diagnose_launcher 函数"""
        from mc_agent_kit.launcher.diagnoser import diagnose_launcher

        report = diagnose_launcher()

        assert report is not None
        assert hasattr(report, "success")


# ============================================================
# Knowledge Retrieval Tests
# ============================================================

class TestSearchResult:
    """搜索结果测试"""

    def test_create_search_result(self):
        """测试创建搜索结果"""
        from mc_agent_kit.knowledge.retrieval import SearchResult

        result = SearchResult(
            type="api",
            name="CreateEntity",
            description="创建实体",
            content="API content",
            score=0.9,
        )

        assert result.type == "api"
        assert result.name == "CreateEntity"
        assert result.score == 0.9


class TestCodeExampleSearchResult:
    """代码示例搜索结果测试"""

    def test_create_code_example_result(self):
        """测试创建代码示例搜索结果"""
        from mc_agent_kit.knowledge.parsers import CodeExample
        from mc_agent_kit.knowledge.retrieval import CodeExampleSearchResult

        example = CodeExample(
            id="test-1",
            code="print('hello')",
            language="python",
            source="test",
        )
        result = CodeExampleSearchResult(
            example=example,
            score=0.8,
        )

        assert result.example == example
        assert result.score == 0.8


class TestKnowledgeRetrieval:
    """知识检索测试"""

    def test_create_retrieval(self):
        """测试创建知识检索实例"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        retrieval = KnowledgeRetrieval()
        assert retrieval.knowledge_base_path is None
        assert retrieval._loaded is False

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        retrieval = KnowledgeRetrieval("/nonexistent/path.json")
        with pytest.raises(FileNotFoundError):
            retrieval.load()

    def test_search_without_load(self):
        """测试未加载时搜索"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        retrieval = KnowledgeRetrieval()
        with pytest.raises(RuntimeError):
            retrieval.search("test")

    def test_load_and_search(self):
        """测试加载并搜索"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        # 创建临时知识库文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "apis": [
                    {
                        "name": "CreateEntity",
                        "description": "创建实体",
                        "module": "entity",
                        "scope": "server",
                        "parameters": [],
                    }
                ],
                "events": [
                    {
                        "name": "OnServerChat",
                        "description": "服务器聊天事件",
                        "module": "chat",
                        "scope": "server",
                        "parameters": [],
                    }
                ],
                "examples": [],
            }, f)
            temp_path = f.name

        try:
            retrieval = KnowledgeRetrieval(temp_path)
            retrieval.load()

            results = retrieval.search("CreateEntity")
            assert len(results) > 0
            assert results[0].name == "CreateEntity"
            assert results[0].type == "api"

        finally:
            os.unlink(temp_path)

    def test_get_api(self):
        """测试获取 API"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "apis": [{"name": "TestAPI", "description": "Test"}],
                "events": [],
                "examples": [],
            }, f)
            temp_path = f.name

        try:
            retrieval = KnowledgeRetrieval(temp_path)
            retrieval.load()

            api = retrieval.get_api("TestAPI")
            assert api is not None
            assert api["name"] == "TestAPI"

            api = retrieval.get_api("NonExistent")
            assert api is None

        finally:
            os.unlink(temp_path)

    def test_get_event(self):
        """测试获取事件"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "apis": [],
                "events": [{"name": "TestEvent", "description": "Test"}],
                "examples": [],
            }, f)
            temp_path = f.name

        try:
            retrieval = KnowledgeRetrieval(temp_path)
            retrieval.load()

            event = retrieval.get_event("TestEvent")
            assert event is not None
            assert event["name"] == "TestEvent"

        finally:
            os.unlink(temp_path)

    def test_search_code_examples(self):
        """测试搜索代码示例"""
        from mc_agent_kit.knowledge.parsers import CodeExample
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "apis": [],
                "events": [],
                "examples": [
                    {
                        "id": "ex-1",
                        "code": "CreateEntity('zombie')",
                        "language": "python",
                        "api_calls": ["CreateEntity"],
                        "event_names": [],
                        "tags": ["entity"],
                    }
                ],
            }, f)
            temp_path = f.name

        try:
            retrieval = KnowledgeRetrieval(temp_path)
            retrieval.load()

            results = retrieval.search_code_examples("CreateEntity")
            assert len(results) > 0

        finally:
            os.unlink(temp_path)

    def test_stats(self):
        """测试统计信息"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "apis": [{"name": "API1"}, {"name": "API2"}],
                "events": [{"name": "Event1"}],
                "examples": [{"id": "ex1"}],
            }, f)
            temp_path = f.name

        try:
            retrieval = KnowledgeRetrieval(temp_path)
            retrieval.load()

            stats = retrieval.stats
            assert stats["apis"] == 2
            assert stats["events"] == 1
            assert stats["examples"] == 1

        finally:
            os.unlink(temp_path)

    def test_save(self):
        """测试保存知识库"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        retrieval = KnowledgeRetrieval()
        retrieval._api_index["TestAPI"] = {"name": "TestAPI"}
        retrieval._event_index["TestEvent"] = {"name": "TestEvent"}
        retrieval._loaded = True

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            retrieval.save(temp_path)

            with open(temp_path) as f:
                data = json.load(f)

            assert "apis" in data
            assert "events" in data
            assert len(data["apis"]) == 1
            assert data["apis"][0]["name"] == "TestAPI"

        finally:
            os.unlink(temp_path)


class TestCreateRetrieval:
    """便捷函数测试"""

    def test_create_retrieval_function(self):
        """测试 create_retrieval 函数"""
        from mc_agent_kit.knowledge.retrieval import create_retrieval

        # 测试不存在的文件
        retrieval = create_retrieval("/nonexistent/path.json")
        assert retrieval is not None
        assert retrieval._loaded is False


# ============================================================
# CLI Tests
# ============================================================

class TestCLIRunCommand:
    """CLI run 命令测试"""

    def test_run_addon_not_found(self):
        """测试 Addon 不存在"""
        from mc_agent_kit.cli import cmd_run
        import argparse

        args = argparse.Namespace(
            addon_path="/nonexistent/addon",
            game_path=None,
            version=None,
            output_dir=None,
            log_port=0,
            no_logs=True,
            wait=False,
            verbose=False,
            format="json",
        )

        # Should return error code
        result = cmd_run(args)
        assert result == 1


class TestCLILogsCommand:
    """CLI logs 命令测试"""

    def test_logs_analyze(self):
        """测试日志分析"""
        from mc_agent_kit.cli import cmd_logs
        import argparse

        args = argparse.Namespace(
            action="analyze",
            log="[INFO] Test log message",
            file=None,
            limit=10,
            format="json",
        )

        result = cmd_logs(args)
        assert result == 0

    def test_logs_errors(self):
        """测试错误提取"""
        from mc_agent_kit.cli import cmd_logs
        import argparse

        args = argparse.Namespace(
            action="errors",
            log="[ERROR] Test error message\n[INFO] Info message",
            file=None,
            limit=10,
            format="json",
        )

        result = cmd_logs(args)
        assert result == 0

    def test_logs_patterns(self):
        """测试模式列表"""
        from mc_agent_kit.cli import cmd_logs
        import argparse

        args = argparse.Namespace(
            action="patterns",
            log="[ERROR] test error message",
            file=None,
            limit=10,
            format="json",
        )

        result = cmd_logs(args)
        assert result == 0


class TestCLILauncherCommand:
    """CLI launcher 命令测试"""

    def test_launcher_diagnose(self):
        """测试启动器诊断"""
        from mc_agent_kit.cli import cmd_launcher
        import argparse

        args = argparse.Namespace(
            action="diagnose",
            addon_path=None,
            config_path=None,
            game_path=None,
            mc_studio_config=None,
            format="json",
        )

        result = cmd_launcher(args)
        # May return 1 if errors found, which is expected
        assert result in [0, 1]


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    """集成测试"""

    def test_diagnoser_and_cli_integration(self):
        """测试诊断器与 CLI 集成"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()
        diagnoser._detect_game_path = lambda: "/mock/game/path"

        report = diagnoser.diagnose()

        # Should have at least some checks
        assert report.checks_passed + report.checks_failed + report.checks_warning > 0

    def test_knowledge_retrieval_full_flow(self):
        """测试知识检索完整流程"""
        from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时知识库
            kb_path = os.path.join(tmpdir, "kb.json")
            with open(kb_path, "w") as f:
                json.dump({
                    "apis": [
                        {"name": "GetPlayer", "description": "获取玩家", "module": "player"},
                        {"name": "SetPos", "description": "设置位置", "module": "entity"},
                    ],
                    "events": [
                        {"name": "OnJoin", "description": "加入事件", "module": "player"},
                    ],
                    "examples": [],
                }, f)

            retrieval = KnowledgeRetrieval(kb_path)
            retrieval.load()

            # 测试搜索
            results = retrieval.search("player")
            assert len(results) > 0

            # 测试 API 获取
            api = retrieval.get_api("GetPlayer")
            assert api is not None

            # 测试事件获取
            event = retrieval.get_event("OnJoin")
            assert event is not None

            # 测试统计
            stats = retrieval.stats
            assert stats["apis"] == 2
            assert stats["events"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])