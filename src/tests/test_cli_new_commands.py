"""
CLI 新命令测试

测试 mc-create 和 mc-kb 命令。
"""

import json
import os
import tempfile
from unittest import mock

import pytest

from mc_agent_kit.cli import main


class TestCLICreate:
    """测试 mc-create 命令"""

    def test_create_project(self, tmp_path):
        """测试创建项目"""
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            result = main()
            assert result == 0
            assert (tmp_path / "test-addon").exists()
            assert (tmp_path / "test-addon" / "behavior_pack").exists()
            assert (tmp_path / "test-addon" / "resource_pack").exists()

    def test_create_project_json_output(self, tmp_path):
        """测试创建项目（JSON 输出）"""
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path), "--format", "json"]):
            result = main()
            assert result == 0
            assert (tmp_path / "test-addon").exists()

    def test_create_project_already_exists(self, tmp_path):
        """测试创建已存在的项目"""
        # 先创建项目
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            main()

        # 再次创建（不使用 --force）
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            result = main()
            assert result == 1  # 应该失败

    def test_create_project_force(self, tmp_path):
        """测试使用 --force 创建项目"""
        # 先创建项目
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            main()

        # 使用 --force 再次创建
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path), "--force"]):
            result = main()
            assert result == 0

    def test_create_entity(self, tmp_path):
        """测试添加实体"""
        # 先创建项目
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            main()

        # 添加实体
        with mock.patch("sys.argv", ["mc-agent", "create", "entity", "Dragon", "-p", str(tmp_path / "test-addon")]):
            result = main()
            assert result == 0
            entities_dir = tmp_path / "test-addon" / "behavior_pack" / "entities"
            assert entities_dir.exists()
            assert (entities_dir / "dragon.json").exists()

    def test_create_item(self, tmp_path):
        """测试添加物品"""
        # 先创建项目
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            main()

        # 添加物品
        with mock.patch("sys.argv", ["mc-agent", "create", "item", "Sword", "-p", str(tmp_path / "test-addon")]):
            result = main()
            assert result == 0
            items_dir = tmp_path / "test-addon" / "behavior_pack" / "items"
            assert items_dir.exists()
            assert (items_dir / "sword.json").exists()

    def test_create_block(self, tmp_path):
        """测试添加方块"""
        # 先创建项目
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "test-addon", "-p", str(tmp_path)]):
            main()

        # 添加方块
        with mock.patch("sys.argv", ["mc-agent", "create", "block", "Stone", "-p", str(tmp_path / "test-addon")]):
            result = main()
            assert result == 0
            blocks_dir = tmp_path / "test-addon" / "behavior_pack" / "blocks"
            assert blocks_dir.exists()
            assert (blocks_dir / "stone.json").exists()


class TestCLIKB:
    """测试 mc-kb 命令"""

    def test_kb_status(self):
        """测试知识库状态"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "status"]):
            result = main()
            assert result == 0

    def test_kb_status_json(self):
        """测试知识库状态（JSON 输出）"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "status", "--format", "json"]):
            result = main()
            assert result == 0

    def test_kb_search_no_results(self):
        """测试搜索（无索引时）"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "search", "-q", "test"]):
            result = main()
            # 即使没有索引，命令也应该成功执行
            assert result == 0

    def test_kb_api_not_found(self):
        """测试查询不存在的 API"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "api", "-n", "NonExistentAPI"]):
            result = main()
            assert result == 0  # 命令执行成功，但 API 未找到

    def test_kb_event_not_found(self):
        """测试查询不存在的事件"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "event", "-n", "NonExistentEvent"]):
            result = main()
            assert result == 0  # 命令执行成功，但事件未找到

    def test_kb_api_json(self):
        """测试查询 API（JSON 输出）"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "api", "-n", "GetEngineType", "--format", "json"]):
            result = main()
            assert result == 0

    def test_kb_search_json(self):
        """测试搜索（JSON 输出）"""
        with mock.patch("sys.argv", ["mc-agent", "kb", "search", "-q", "entity", "--format", "json"]):
            result = main()
            assert result == 0


class TestCLIScaffoldIntegration:
    """集成测试"""

    def test_full_project_workflow(self, tmp_path):
        """测试完整的项目创建流程"""
        # 1. 创建项目
        with mock.patch("sys.argv", ["mc-agent", "create", "project", "my-addon", "-p", str(tmp_path)]):
            result = main()
            assert result == 0

        # 2. 添加实体
        project_path = tmp_path / "my-addon"
        with mock.patch("sys.argv", ["mc-agent", "create", "entity", "Zombie", "-p", str(project_path)]):
            result = main()
            assert result == 0

        # 3. 验证项目结构
        assert (project_path / "behavior_pack" / "manifest.json").exists()
        assert (project_path / "resource_pack" / "manifest.json").exists()
        assert (project_path / "behavior_pack" / "entities" / "zombie.json").exists()
