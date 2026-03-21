"""
增量更新模块测试 (v0.5.0)

测试文档变更检测和增量更新功能。
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mc_agent_kit.knowledge.incremental import (
    ChangeReport,
    DocumentChange,
    IncrementalUpdater,
)


class TestDocumentChange:
    """测试 DocumentChange"""

    def test_change_creation(self):
        """测试变更记录创建"""
        change = DocumentChange(
            path="test.md",
            change_type="modified",
            old_hash="abc123",
            new_hash="def456",
        )

        assert change.path == "test.md"
        assert change.change_type == "modified"
        assert change.old_hash == "abc123"
        assert change.new_hash == "def456"

    def test_added_change(self):
        """测试新增变更"""
        change = DocumentChange(
            path="new.md",
            change_type="added",
            new_hash="hash123",
        )

        assert change.change_type == "added"
        assert change.old_hash is None

    def test_deleted_change(self):
        """测试删除变更"""
        change = DocumentChange(
            path="old.md",
            change_type="deleted",
            old_hash="old_hash",
        )

        assert change.change_type == "deleted"
        assert change.new_hash is None


class TestChangeReport:
    """测试 ChangeReport"""

    def test_empty_report(self):
        """测试空报告"""
        report = ChangeReport()

        assert report.total_changes == 0
        assert not report.has_changes

    def test_report_with_changes(self):
        """测试有变更的报告"""
        report = ChangeReport()
        report.added.append(DocumentChange(path="a.md", change_type="added", new_hash="h1"))
        report.modified.append(DocumentChange(path="b.md", change_type="modified", old_hash="h2", new_hash="h3"))
        report.deleted.append(DocumentChange(path="c.md", change_type="deleted", old_hash="h4"))

        assert report.total_changes == 3
        assert report.has_changes

    def test_report_to_dict(self):
        """测试报告转字典"""
        report = ChangeReport()
        report.added.append(DocumentChange(path="a.md", change_type="added", new_hash="h1"))

        d = report.to_dict()

        assert d["total_changes"] == 1
        assert len(d["added"]) == 1
        assert d["added"][0]["path"] == "a.md"


class TestIncrementalUpdater:
    """测试 IncrementalUpdater"""

    @pytest.fixture
    def temp_dirs(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as state_dir:
            with tempfile.TemporaryDirectory() as docs_dir:
                yield state_dir, docs_dir

    def test_updater_init(self, temp_dirs):
        """测试更新器初始化"""
        state_dir, _ = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        assert updater.state_dir == Path(state_dir)
        assert updater._state == {}

    def test_compute_hash(self, temp_dirs):
        """测试哈希计算"""
        state_dir, _ = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        hash1 = updater._compute_hash("测试内容")
        hash2 = updater._compute_hash("测试内容")
        hash3 = updater._compute_hash("不同内容")

        assert hash1 == hash2
        assert hash1 != hash3

    def test_detect_changes_empty(self, temp_dirs):
        """测试检测空目录变更"""
        state_dir, docs_dir = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        changes = updater.detect_changes(docs_dir)

        assert not changes.has_changes

    def test_detect_changes_new_files(self, temp_dirs):
        """测试检测新文件"""
        state_dir, docs_dir = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        # 创建测试文件
        (Path(docs_dir) / "test1.md").write_text("内容1", encoding="utf-8")
        (Path(docs_dir) / "test2.txt").write_text("内容2", encoding="utf-8")

        changes = updater.detect_changes(docs_dir)

        assert changes.has_changes
        assert len(changes.added) == 2
        assert len(changes.modified) == 0
        assert len(changes.deleted) == 0

    def test_detect_changes_modified(self, temp_dirs):
        """测试检测修改的文件"""
        state_dir, docs_dir = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        # 创建并索引文件
        test_file = Path(docs_dir) / "test.md"
        test_file.write_text("原始内容", encoding="utf-8")

        # 首次检测
        changes1 = updater.detect_changes(docs_dir)
        assert len(changes1.added) == 1

        # 应用状态
        updater._state[test_file.name] = updater._compute_hash("原始内容")

        # 修改文件
        test_file.write_text("修改后的内容", encoding="utf-8")

        # 再次检测
        changes2 = updater.detect_changes(docs_dir)

        assert len(changes2.modified) == 1

    def test_detect_changes_deleted(self, temp_dirs):
        """测试检测删除的文件"""
        state_dir, docs_dir = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        # 创建文件并记录状态
        updater._state["deleted.md"] = "some_hash"

        # 检测（文件不存在）
        changes = updater.detect_changes(docs_dir)

        assert len(changes.deleted) == 1
        assert changes.deleted[0].path == "deleted.md"

    def test_save_and_load_state(self, temp_dirs):
        """测试状态保存和加载"""
        state_dir, docs_dir = temp_dirs

        # 创建更新器并设置状态
        updater1 = IncrementalUpdater(state_dir=state_dir)
        updater1._state["file1.md"] = "hash1"
        updater1._state["file2.md"] = "hash2"
        updater1._save_state()

        # 创建新更新器加载状态
        updater2 = IncrementalUpdater(state_dir=state_dir)

        assert updater2._state["file1.md"] == "hash1"
        assert updater2._state["file2.md"] == "hash2"

    def test_get_document_state(self, temp_dirs):
        """测试获取文档状态"""
        state_dir, _ = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)
        updater._state["test.md"] = "test_hash"

        assert updater.get_document_state("test.md") == "test_hash"
        assert updater.get_document_state("not_exist.md") is None

    def test_get_all_states(self, temp_dirs):
        """测试获取所有状态"""
        state_dir, _ = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)
        updater._state["a.md"] = "hash_a"
        updater._state["b.md"] = "hash_b"

        states = updater.get_all_states()

        assert states["a.md"] == "hash_a"
        assert states["b.md"] == "hash_b"
        # 确保是副本
        states["c.md"] = "hash_c"
        assert "c.md" not in updater._state

    def test_clear_state(self, temp_dirs):
        """测试清空状态"""
        state_dir, _ = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)
        updater._state["test.md"] = "hash"
        updater.clear_state()

        assert updater._state == {}

    def test_rebuild_state(self, temp_dirs):
        """测试重建状态"""
        state_dir, docs_dir = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        # 创建测试文件
        (Path(docs_dir) / "a.md").write_text("内容A", encoding="utf-8")
        (Path(docs_dir) / "b.txt").write_text("内容B", encoding="utf-8")

        count = updater.rebuild_state(docs_dir)

        assert count == 2
        assert len(updater._state) == 2

    def test_extensions_filter(self, temp_dirs):
        """测试扩展名过滤"""
        state_dir, docs_dir = temp_dirs
        updater = IncrementalUpdater(state_dir=state_dir)

        # 创建不同扩展名的文件
        (Path(docs_dir) / "a.md").write_text("MD", encoding="utf-8")
        (Path(docs_dir) / "b.txt").write_text("TXT", encoding="utf-8")
        (Path(docs_dir) / "c.py").write_text("PY", encoding="utf-8")

        # 只检测 .md 文件
        changes = updater.detect_changes(docs_dir, extensions=[".md"])

        assert len(changes.added) == 1
        assert changes.added[0].path == "a.md"


class TestConvenienceFunction:
    """测试便捷函数"""

    def test_create_incremental_updater(self):
        """测试创建增量更新器"""
        from mc_agent_kit.knowledge.incremental import create_incremental_updater

        with tempfile.TemporaryDirectory() as state_dir:
            updater = create_incremental_updater(state_dir=state_dir)

            assert isinstance(updater, IncrementalUpdater)
            assert updater.state_dir == Path(state_dir)