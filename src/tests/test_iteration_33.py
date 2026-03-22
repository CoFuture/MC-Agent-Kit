"""
迭代 #33 测试

测试 CLI 工具增强、API 使用统计和新功能。
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.stats import ApiUsageStats, ApiUsageTracker, UsageRecord
from mc_agent_kit.stats.tracker import ApiCategory
from mc_agent_kit.launcher.auto_fixer import (
    FixSeverity,
    FixSuggestion,
    FixType,
    MemoryFixReport,
    get_memory_optimization_tips,
)


class TestUsageRecord:
    """UsageRecord 测试"""

    def test_create_usage_record(self) -> None:
        """测试创建使用记录"""
        record = UsageRecord(
            api_name="CreateEngineEntity",
            timestamp="2026-03-22T10:00:00",
            success=True,
            module="entity",
            scope="server",
        )
        assert record.api_name == "CreateEngineEntity"
        assert record.success is True
        assert record.error_message is None

    def test_usage_record_to_dict(self) -> None:
        """测试使用记录序列化"""
        record = UsageRecord(
            api_name="GetEngineTime",
            timestamp="2026-03-22T10:00:00",
            success=False,
            error_message="API not found",
            duration_ms=10.5,
        )
        data = record.to_dict()
        assert data["api_name"] == "GetEngineTime"
        assert data["success"] is False
        assert data["error_message"] == "API not found"
        assert data["duration_ms"] == 10.5

    def test_usage_record_from_dict(self) -> None:
        """测试使用记录反序列化"""
        data = {
            "api_name": "SetEntityPos",
            "timestamp": "2026-03-22T10:00:00",
            "success": True,
            "module": "entity",
        }
        record = UsageRecord.from_dict(data)
        assert record.api_name == "SetEntityPos"
        assert record.success is True
        assert record.module == "entity"


class TestApiUsageStats:
    """ApiUsageStats 测试"""

    def test_create_stats(self) -> None:
        """测试创建统计数据"""
        stats = ApiUsageStats(api_name="CreateEngineEntity")
        assert stats.api_name == "CreateEngineEntity"
        assert stats.total_calls == 0
        assert stats.success_rate == 0.0

    def test_success_rate_calculation(self) -> None:
        """测试成功率计算"""
        stats = ApiUsageStats(
            api_name="TestAPI",
            total_calls=100,
            success_count=80,
            error_count=20,
        )
        assert stats.success_rate == 0.8
        assert stats.error_rate == 0.2

    def test_stats_to_dict(self) -> None:
        """测试统计数据序列化"""
        stats = ApiUsageStats(
            api_name="TestAPI",
            total_calls=50,
            success_count=45,
            error_count=5,
            last_used="2026-03-22T10:00:00",
            common_errors=["TypeError", "ValueError"],
            category=ApiCategory.ENTITY,
        )
        data = stats.to_dict()
        assert data["api_name"] == "TestAPI"
        assert data["total_calls"] == 50
        assert data["success_rate"] == 0.9
        assert data["error_rate"] == 0.1
        assert data["category"] == "entity"

    def test_stats_from_dict(self) -> None:
        """测试统计数据反序列化"""
        data = {
            "api_name": "TestAPI",
            "total_calls": 100,
            "success_count": 90,
            "error_count": 10,
            "common_errors": ["KeyError"],
            "category": "item",
        }
        stats = ApiUsageStats.from_dict(data)
        assert stats.api_name == "TestAPI"
        assert stats.total_calls == 100
        assert stats.category == ApiCategory.ITEM


class TestApiUsageTracker:
    """ApiUsageTracker 测试"""

    def test_create_tracker(self) -> None:
        """测试创建追踪器"""
        tracker = ApiUsageTracker()
        assert tracker.get_all_stats() == {}

    def test_record_api_call(self) -> None:
        """测试记录 API 调用"""
        tracker = ApiUsageTracker()

        tracker.record("CreateEngineEntity", success=True, module="entity")
        tracker.record("CreateEngineEntity", success=True, module="entity")
        tracker.record("CreateEngineEntity", success=False, error_message="TypeError")

        stats = tracker.get_stats("CreateEngineEntity")
        assert stats is not None
        assert stats.total_calls == 3
        assert stats.success_count == 2
        assert stats.error_count == 1
        assert stats.error_rate == pytest.approx(1 / 3)

    def test_get_hot_apis(self) -> None:
        """测试获取热门 API"""
        tracker = ApiUsageTracker()

        # 记录多个 API
        for i in range(10):
            tracker.record("HotAPI1", success=True)
        for i in range(5):
            tracker.record("HotAPI2", success=True)
        for i in range(2):
            tracker.record("HotAPI3", success=True)

        hot = tracker.get_hot_apis(limit=2)
        assert len(hot) == 2
        assert hot[0].api_name == "HotAPI1"
        assert hot[0].total_calls == 10
        assert hot[1].api_name == "HotAPI2"

    def test_get_problematic_apis(self) -> None:
        """测试获取问题 API"""
        tracker = ApiUsageTracker()

        # 创建问题 API（高错误率）
        for i in range(10):
            tracker.record("ProblemAPI", success=False, error_message="Error")

        # 创建正常 API
        for i in range(10):
            tracker.record("GoodAPI", success=True)

        problematic = tracker.get_problematic_apis(min_calls=5, error_rate_threshold=0.3)
        assert len(problematic) == 1
        assert problematic[0].api_name == "ProblemAPI"
        assert problematic[0].error_rate == 1.0

    def test_get_stats_by_module(self) -> None:
        """测试按模块分组统计"""
        tracker = ApiUsageTracker()

        tracker.record("API1", success=True, module="entity")
        tracker.record("API2", success=True, module="entity")
        tracker.record("API3", success=True, module="item")

        by_module = tracker.get_stats_by_module()
        assert "entity" in by_module
        assert "item" in by_module
        assert len(by_module["entity"]) == 2
        assert len(by_module["item"]) == 1

    def test_get_summary(self) -> None:
        """测试获取统计摘要"""
        tracker = ApiUsageTracker()

        tracker.record("API1", success=True)
        tracker.record("API1", success=False, error_message="Error")
        tracker.record("API2", success=True)

        summary = tracker.get_summary()
        assert summary["total_apis"] == 2
        assert summary["total_calls"] == 3
        assert summary["total_success"] == 2
        assert summary["total_errors"] == 1
        assert summary["success_rate"] == pytest.approx(2 / 3)

    def test_save_and_load(self) -> None:
        """测试保存和加载统计数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "stats.json")

            # 创建并保存
            tracker = ApiUsageTracker()
            tracker.record("API1", success=True, module="test")
            tracker.save(path)

            # 加载到新追踪器
            tracker2 = ApiUsageTracker(path)
            stats = tracker2.get_stats("API1")
            assert stats is not None
            assert stats.total_calls == 1

    def test_clear(self) -> None:
        """测试清空统计数据"""
        tracker = ApiUsageTracker()
        tracker.record("API1", success=True)
        tracker.clear()
        assert len(tracker.get_all_stats()) == 0


class TestFixSuggestion:
    """FixSuggestion 测试"""

    def test_create_suggestion(self) -> None:
        """测试创建修复建议"""
        suggestion = FixSuggestion(
            fix_type=FixType.TEXTURE_COMPRESS,
            severity=FixSeverity.HIGH,
            title="大纹理文件",
            description="纹理尺寸过大",
            location="/path/to/texture.png",
            auto_fixable=False,
        )
        assert suggestion.fix_type == FixType.TEXTURE_COMPRESS
        assert suggestion.severity == FixSeverity.HIGH

    def test_suggestion_to_dict(self) -> None:
        """测试修复建议序列化"""
        suggestion = FixSuggestion(
            fix_type=FixType.MODEL_SIMPLIFY,
            severity=FixSeverity.MEDIUM,
            title="复杂模型",
            description="模型顶点数过多",
            location="/path/to/model.geo.json",
            current_value="5000 顶点",
            suggested_value="1000 顶点",
        )
        data = suggestion.to_dict()
        assert data["fix_type"] == "model_simplify"
        assert data["severity"] == "medium"
        assert data["current_value"] == "5000 顶点"


class TestMemoryFixReport:
    """MemoryFixReport 测试"""

    def test_create_report(self) -> None:
        """测试创建修复报告"""
        report = MemoryFixReport(addon_path="/path/to/addon")
        assert report.addon_path == "/path/to/addon"
        assert report.total_issues == 0
        assert not report.has_critical_issues

    def test_report_properties(self) -> None:
        """测试报告属性"""
        report = MemoryFixReport(
            addon_path="/path/to/addon",
            total_issues=10,
            critical_issues=3,
            auto_fixable_issues=5,
        )
        assert report.has_critical_issues is True
        assert report.has_auto_fixable is True

    def test_report_to_dict(self) -> None:
        """测试报告序列化"""
        suggestion = FixSuggestion(
            fix_type=FixType.SCRIPT_OPTIMIZE,
            severity=FixSeverity.LOW,
            title="大脚本文件",
            description="脚本行数过多",
            location="/path/to/script.py",
        )
        report = MemoryFixReport(
            addon_path="/path/to/addon",
            suggestions=[suggestion],
        )
        data = report.to_dict()
        assert data["addon_path"] == "/path/to/addon"
        assert len(data["suggestions"]) == 1


class TestGetMemoryOptimizationTips:
    """get_memory_optimization_tips 测试"""

    def test_get_tips(self) -> None:
        """测试获取优化技巧"""
        tips = get_memory_optimization_tips()
        assert len(tips) > 0

        # 检查技巧结构
        for tip in tips:
            assert "category" in tip
            assert "tip" in tip
            assert "reason" in tip

    def test_tips_categories(self) -> None:
        """测试技巧类别"""
        tips = get_memory_optimization_tips()
        categories = {tip["category"] for tip in tips}
        assert "纹理" in categories
        assert "模型" in categories
        assert "脚本" in categories


class TestApiCategory:
    """ApiCategory 测试"""

    def test_category_values(self) -> None:
        """测试类别值"""
        assert ApiCategory.ENTITY.value == "entity"
        assert ApiCategory.ITEM.value == "item"
        assert ApiCategory.BLOCK.value == "block"
        assert ApiCategory.PLAYER.value == "player"


class TestFixTypeEnum:
    """FixType 枚举测试"""

    def test_fix_type_values(self) -> None:
        """测试修复类型值"""
        assert FixType.TEXTURE_COMPRESS.value == "texture_compress"
        assert FixType.MODEL_SIMPLIFY.value == "model_simplify"
        assert FixType.SCRIPT_OPTIMIZE.value == "script_optimize"
        assert FixType.CONFIG_FIX.value == "config_fix"


class TestFixSeverityEnum:
    """FixSeverity 枚举测试"""

    def test_severity_values(self) -> None:
        """测试严重程度值"""
        assert FixSeverity.CRITICAL.value == "critical"
        assert FixSeverity.HIGH.value == "high"
        assert FixSeverity.MEDIUM.value == "medium"
        assert FixSeverity.LOW.value == "low"


class TestIteration33Integration:
    """迭代 #33 集成测试"""

    def test_stats_workflow(self) -> None:
        """测试统计工作流"""
        tracker = ApiUsageTracker()

        # 模拟 API 调用
        apis = [
            ("CreateEngineEntity", True, "entity"),
            ("GetEngineTime", True, "world"),
            ("SetEntityPos", True, "entity"),
            ("CreateEngineEntity", False, "entity"),
            ("GetEngineTime", True, "world"),
        ]

        for api, success, module in apis:
            tracker.record(api, success=success, module=module)

        # 验证统计
        summary = tracker.get_summary()
        assert summary["total_apis"] == 3
        assert summary["total_calls"] == 5

        # 验证热门 API
        hot = tracker.get_hot_apis(limit=1)
        assert hot[0].api_name in ["CreateEngineEntity", "GetEngineTime"]

    def test_memory_analysis_workflow(self) -> None:
        """测试内存分析工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建模拟 Addon 结构
            addon_path = Path(tmpdir) / "test_addon"
            addon_path.mkdir()

            # 创建脚本目录
            scripts_dir = addon_path / "behavior_pack" / "scripts"
            scripts_dir.mkdir(parents=True)

            # 创建一个大脚本文件
            script_file = scripts_dir / "main.py"
            script_file.write_text("\n".join([f"# Line {i}" for i in range(600)]))

            # 分析
            from mc_agent_kit.launcher.auto_fixer import MemoryAutoFixer

            fixer = MemoryAutoFixer(str(addon_path))
            report = fixer.analyze()

            # 应该检测到脚本文件过大
            assert report.total_issues >= 1

    def test_cli_integration(self) -> None:
        """测试 CLI 集成"""
        # 测试统计命令不抛出异常
        from mc_agent_kit.cli import cmd_stats
        import argparse

        args = argparse.Namespace(
            action="summary",
            limit=10,
            min_calls=5,
            error_rate=0.3,
            api_name=None,
            module=None,
            data_path=None,
            format="json",
        )

        # 应该能正常执行
        result = cmd_stats(args)
        assert result == 0