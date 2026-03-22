"""
迭代 #32 测试：内存问题自动修复与知识库增强

测试内容：
1. 内存问题自动修复功能
2. API 使用统计
3. 增强代码示例
4. 性能优化
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# ============================================================
# FixType and FixSeverity Tests
# ============================================================


class TestFixType:
    """测试 FixType 枚举"""

    def test_fix_type_values(self):
        """测试修复类型值"""
        from mc_agent_kit.launcher.auto_fixer import FixType

        assert FixType.TEXTURE_COMPRESS.value == "texture_compress"
        assert FixType.MODEL_SIMPLIFY.value == "model_simplify"
        assert FixType.SCRIPT_OPTIMIZE.value == "script_optimize"
        assert FixType.CONFIG_FIX.value == "config_fix"
        assert FixType.MEMORY_SETTING.value == "memory_setting"

    def test_fix_type_count(self):
        """测试修复类型数量"""
        from mc_agent_kit.launcher.auto_fixer import FixType

        assert len(list(FixType)) == 5


class TestFixSeverity:
    """测试 FixSeverity 枚举"""

    def test_severity_values(self):
        """测试严重程度值"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity

        assert FixSeverity.CRITICAL.value == "critical"
        assert FixSeverity.HIGH.value == "high"
        assert FixSeverity.MEDIUM.value == "medium"
        assert FixSeverity.LOW.value == "low"

    def test_severity_count(self):
        """测试严重程度数量"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity

        assert len(list(FixSeverity)) == 4


# ============================================================
# FixSuggestion Tests
# ============================================================


class TestFixSuggestion:
    """测试 FixSuggestion 数据结构"""

    def test_create_fix_suggestion(self):
        """测试创建修复建议"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity, FixSuggestion, FixType

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
        assert suggestion.title == "大纹理文件"
        assert suggestion.auto_fixable is False

    def test_fix_suggestion_to_dict(self):
        """测试修复建议转字典"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity, FixSuggestion, FixType

        suggestion = FixSuggestion(
            fix_type=FixType.TEXTURE_COMPRESS,
            severity=FixSeverity.HIGH,
            title="大纹理文件",
            description="纹理尺寸过大",
            location="/path/to/texture.png",
            current_value="2048x2048",
            suggested_value="512x512",
            auto_fixable=False,
        )

        result = suggestion.to_dict()

        assert result["fix_type"] == "texture_compress"
        assert result["severity"] == "high"
        assert result["title"] == "大纹理文件"
        assert result["current_value"] == "2048x2048"
        assert result["suggested_value"] == "512x512"


# ============================================================
# MemoryFixReport Tests
# ============================================================


class TestMemoryFixReport:
    """测试 MemoryFixReport 数据结构"""

    def test_create_report(self):
        """测试创建修复报告"""
        from mc_agent_kit.launcher.auto_fixer import MemoryFixReport

        report = MemoryFixReport(addon_path="/path/to/addon")

        assert report.addon_path == "/path/to/addon"
        assert report.total_issues == 0
        assert report.critical_issues == 0
        assert report.suggestions == []

    def test_report_properties(self):
        """测试报告属性"""
        from mc_agent_kit.launcher.auto_fixer import (
            FixSeverity,
            FixSuggestion,
            FixType,
            MemoryFixReport,
        )

        report = MemoryFixReport(
            addon_path="/path/to/addon",
            total_issues=5,
            critical_issues=2,
            auto_fixable_issues=1,
        )

        assert report.has_critical_issues is True
        assert report.has_auto_fixable is True

    def test_report_to_dict(self):
        """测试报告转字典"""
        from mc_agent_kit.launcher.auto_fixer import (
            FixSeverity,
            FixSuggestion,
            FixType,
            MemoryFixReport,
        )

        suggestion = FixSuggestion(
            fix_type=FixType.TEXTURE_COMPRESS,
            severity=FixSeverity.HIGH,
            title="大纹理文件",
            description="纹理尺寸过大",
            location="/path/to/texture.png",
        )

        report = MemoryFixReport(
            addon_path="/path/to/addon",
            total_issues=1,
            suggestions=[suggestion],
        )

        result = report.to_dict()

        assert result["addon_path"] == "/path/to/addon"
        assert result["total_issues"] == 1
        assert len(result["suggestions"]) == 1


# ============================================================
# TextureAnalyzer Tests
# ============================================================


class TestTextureAnalyzer:
    """测试纹理分析器"""

    def test_analyze_empty_dir(self):
        """测试分析空目录"""
        from mc_agent_kit.launcher.auto_fixer import TextureAnalyzer

        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = TextureAnalyzer()
            suggestions = analyzer.analyze(tmpdir)

            assert suggestions == []

    def test_analyze_nonexistent_dir(self):
        """测试分析不存在的目录"""
        from mc_agent_kit.launcher.auto_fixer import TextureAnalyzer

        analyzer = TextureAnalyzer()
        suggestions = analyzer.analyze("/nonexistent/path")

        assert suggestions == []


# ============================================================
# ModelAnalyzer Tests
# ============================================================


class TestModelAnalyzer:
    """测试模型分析器"""

    def test_analyze_simple_model(self):
        """测试分析简单模型"""
        from mc_agent_kit.launcher.auto_fixer import ModelAnalyzer

        model_data = {
            "minecraft:geometry": [
                {
                    "bones": [
                        {"name": "root", "cubes": [{"size": [1, 1, 1]}]}
                    ]
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test.geo.json")
            with open(model_path, "w", encoding="utf-8") as f:
                json.dump(model_data, f)

            analyzer = ModelAnalyzer()
            suggestions = analyzer.analyze(tmpdir)

            # 简单模型不应该有问题
            assert all(s.severity.value != "high" for s in suggestions)

    def test_analyze_complex_model(self):
        """测试分析复杂模型"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity, ModelAnalyzer

        # 创建一个复杂模型（超过 1000 个顶点）
        bones = []
        for i in range(50):
            cubes = [{"size": [1, 1, 1]} for _ in range(50)]
            bones.append({"name": f"bone_{i}", "cubes": cubes})

        model_data = {
            "minecraft:geometry": [{"bones": bones}]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "complex.geo.json")
            with open(model_path, "w", encoding="utf-8") as f:
                json.dump(model_data, f)

            analyzer = ModelAnalyzer()
            suggestions = analyzer.analyze(tmpdir)

            # 应该检测到复杂模型
            assert any(s.severity in (FixSeverity.HIGH, FixSeverity.MEDIUM) for s in suggestions)

    def test_analyze_empty_dir(self):
        """测试分析空目录"""
        from mc_agent_kit.launcher.auto_fixer import ModelAnalyzer

        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = ModelAnalyzer()
            suggestions = analyzer.analyze(tmpdir)

            assert suggestions == []


# ============================================================
# ScriptAnalyzer Tests
# ============================================================


class TestScriptAnalyzer:
    """测试脚本分析器"""

    def test_analyze_simple_script(self):
        """测试分析简单脚本"""
        from mc_agent_kit.launcher.auto_fixer import ScriptAnalyzer

        script_content = """
# Simple script
def hello():
    print("Hello, World!")
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "simple.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            analyzer = ScriptAnalyzer()
            suggestions = analyzer.analyze(tmpdir)

            # 简单脚本不应该有高严重度问题
            assert all(s.severity.value not in ("critical", "high") for s in suggestions)

    def test_analyze_large_script(self):
        """测试分析大脚本"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity, ScriptAnalyzer

        # 创建一个大脚本
        lines = ["# Large script"] + ["x = 1"] * 600
        script_content = "\n".join(lines)

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "large.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            analyzer = ScriptAnalyzer()
            suggestions = analyzer.analyze(tmpdir)

            # 应该检测到大脚本
            assert any(s.severity == FixSeverity.MEDIUM for s in suggestions)


# ============================================================
# MemoryAutoFixer Tests
# ============================================================


class TestMemoryAutoFixer:
    """测试内存自动修复器"""

    def test_analyze_nonexistent_addon(self):
        """测试分析不存在的 Addon"""
        from mc_agent_kit.launcher.auto_fixer import MemoryAutoFixer

        fixer = MemoryAutoFixer("/nonexistent/addon")
        report = fixer.analyze()

        assert len(report.errors) > 0
        assert "不存在" in report.errors[0]

    def test_analyze_empty_addon(self):
        """测试分析空 Addon"""
        from mc_agent_kit.launcher.auto_fixer import MemoryAutoFixer

        with tempfile.TemporaryDirectory() as tmpdir:
            fixer = MemoryAutoFixer(tmpdir)
            report = fixer.analyze()

            # 空 Addon 应该没有问题
            assert report.total_issues == 0


# ============================================================
# EnhancedCodeExample Tests
# ============================================================


class TestEnhancedCodeExample:
    """测试增强代码示例"""

    def test_create_enhanced_example(self):
        """测试创建增强代码示例"""
        from mc_agent_kit.knowledge_base.models import (
            DifficultyLevel,
            EnhancedCodeExample,
            ExampleCategory,
        )

        example = EnhancedCodeExample(
            id="ex_001",
            code="print('Hello')",
            title="Hello World",
            description="简单的 Hello World 示例",
            difficulty=DifficultyLevel.BEGINNER,
            category=ExampleCategory.BASIC,
        )

        assert example.id == "ex_001"
        assert example.difficulty == DifficultyLevel.BEGINNER
        assert example.category == ExampleCategory.BASIC

    def test_enhanced_example_to_dict(self):
        """测试增强代码示例转字典"""
        from mc_agent_kit.knowledge_base.models import (
            DifficultyLevel,
            EnhancedCodeExample,
            ExampleCategory,
        )

        example = EnhancedCodeExample(
            id="ex_001",
            code="print('Hello')",
            title="Hello World",
            description="简单的 Hello World 示例",
            difficulty=DifficultyLevel.BEGINNER,
            category=ExampleCategory.BASIC,
            estimated_time_minutes=5,
            api_names=["print"],
        )

        result = example.to_dict()

        assert result["id"] == "ex_001"
        assert result["difficulty"] == "beginner"
        assert result["category"] == "basic"
        assert result["estimated_time_minutes"] == 5
        assert "print" in result["api_names"]

    def test_enhanced_example_from_dict(self):
        """测试从字典创建增强代码示例"""
        from mc_agent_kit.knowledge_base.models import (
            DifficultyLevel,
            EnhancedCodeExample,
            ExampleCategory,
        )

        data = {
            "id": "ex_002",
            "code": "CreateEngineEntity()",
            "title": "Create Entity",
            "description": "创建实体示例",
            "difficulty": "intermediate",
            "category": "entity",
            "estimated_time_minutes": 15,
            "api_names": ["CreateEngineEntity"],
        }

        example = EnhancedCodeExample.from_dict(data)

        assert example.id == "ex_002"
        assert example.difficulty == DifficultyLevel.INTERMEDIATE
        assert example.category == ExampleCategory.ENTITY


# ============================================================
# DifficultyLevel Tests
# ============================================================


class TestDifficultyLevel:
    """测试难度等级枚举"""

    def test_difficulty_values(self):
        """测试难度等级值"""
        from mc_agent_kit.knowledge_base.models import DifficultyLevel

        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
        assert DifficultyLevel.EXPERT.value == "expert"


# ============================================================
# ExampleCategory Tests
# ============================================================


class TestExampleCategory:
    """测试示例类别枚举"""

    def test_category_values(self):
        """测试类别值"""
        from mc_agent_kit.knowledge_base.models import ExampleCategory

        assert ExampleCategory.BASIC.value == "basic"
        assert ExampleCategory.ENTITY.value == "entity"
        assert ExampleCategory.ITEM.value == "item"
        assert ExampleCategory.BLOCK.value == "block"
        assert ExampleCategory.UI.value == "ui"
        assert ExampleCategory.NETWORK.value == "network"
        assert ExampleCategory.PERFORMANCE.value == "performance"
        assert ExampleCategory.ADVANCED.value == "advanced"


# ============================================================
# ApiUsageStats Tests
# ============================================================


class TestApiUsageStats:
    """测试 API 使用统计"""

    def test_create_usage_stats(self):
        """测试创建使用统计"""
        from mc_agent_kit.knowledge_base.models import ApiUsageStats

        stats = ApiUsageStats(
            api_name="CreateEngineEntity",
            usage_count=100,
            success_count=95,
            error_count=5,
        )

        assert stats.api_name == "CreateEngineEntity"
        assert stats.usage_count == 100
        assert stats.success_count == 95
        assert stats.error_count == 5

    def test_success_rate(self):
        """测试成功率计算"""
        from mc_agent_kit.knowledge_base.models import ApiUsageStats

        stats = ApiUsageStats(
            api_name="TestAPI",
            usage_count=100,
            success_count=80,
            error_count=20,
        )

        assert stats.success_rate == 0.8

    def test_zero_usage_success_rate(self):
        """测试零使用次数的成功率"""
        from mc_agent_kit.knowledge_base.models import ApiUsageStats

        stats = ApiUsageStats(api_name="UnusedAPI")

        assert stats.success_rate == 0.0

    def test_usage_stats_to_dict(self):
        """测试使用统计转字典"""
        from mc_agent_kit.knowledge_base.models import ApiUsageStats

        stats = ApiUsageStats(
            api_name="TestAPI",
            usage_count=50,
            success_count=45,
            error_count=5,
            last_used="2026-03-22T10:00:00",
        )

        result = stats.to_dict()

        assert result["api_name"] == "TestAPI"
        assert result["usage_count"] == 50
        assert result["success_rate"] == 0.9


# ============================================================
# ApiUsageTracker Tests
# ============================================================


class TestApiUsageTracker:
    """测试 API 使用追踪器"""

    def test_create_tracker(self):
        """测试创建追踪器"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()

        assert tracker.total_queries == 0
        assert tracker.tracked_apis == 0

    def test_record_usage(self):
        """测试记录使用"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()
        tracker.record_usage("TestAPI", success=True)
        tracker.record_usage("TestAPI", success=True)
        tracker.record_usage("TestAPI", success=False, error="Test error")

        assert tracker.total_queries == 3
        assert tracker.tracked_apis == 1

        stats = tracker.get_stats("TestAPI")
        assert stats is not None
        assert stats.usage_count == 3
        assert stats.success_count == 2
        assert stats.error_count == 1

    def test_get_popular_apis(self):
        """测试获取热门 API"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()
        tracker.record_usage("API1", success=True)
        tracker.record_usage("API1", success=True)
        tracker.record_usage("API2", success=True)

        popular = tracker.get_popular_apis(limit=10)

        assert len(popular) == 2
        assert popular[0] == ("API1", 2)
        assert popular[1] == ("API2", 1)

    def test_get_problematic_apis(self):
        """测试获取问题 API"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()
        # 创建一个成功率高和一个成功率低的 API
        for _ in range(10):
            tracker.record_usage("GoodAPI", success=True)

        for _ in range(5):
            tracker.record_usage("BadAPI", success=False, error="Error")

        problematic = tracker.get_problematic_apis(limit=10)

        # BadAPI 应该在问题列表中
        assert any(api == "BadAPI" for api, _ in problematic)

    def test_get_recommendations(self):
        """测试获取推荐"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()
        tracker.record_usage("API1", success=True)
        tracker.record_related_apis("API1", ["API2", "API3"])

        recommendations = tracker.get_recommendations("API1")

        assert "API2" in recommendations
        assert "API3" in recommendations

    def test_save_and_load(self):
        """测试保存和加载"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()
        tracker.record_usage("API1", success=True)
        tracker.record_usage("API2", success=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "usage_stats.json")
            tracker.save(path)

            new_tracker = ApiUsageTracker()
            new_tracker.load(path)

            assert new_tracker.total_queries == 2
            assert new_tracker.tracked_apis == 2


# ============================================================
# get_memory_optimization_tips Tests
# ============================================================


class TestMemoryOptimizationTips:
    """测试内存优化技巧"""

    def test_get_tips(self):
        """测试获取优化技巧"""
        from mc_agent_kit.launcher.auto_fixer import get_memory_optimization_tips

        tips = get_memory_optimization_tips()

        assert len(tips) > 0
        assert all("category" in tip for tip in tips)
        assert all("tip" in tip for tip in tips)
        assert all("reason" in tip for tip in tips)

    def test_tips_categories(self):
        """测试技巧类别"""
        from mc_agent_kit.launcher.auto_fixer import get_memory_optimization_tips

        tips = get_memory_optimization_tips()
        categories = set(tip["category"] for tip in tips)

        assert "纹理" in categories
        assert "模型" in categories
        assert "脚本" in categories


# ============================================================
# analyze_addon_memory Function Tests
# ============================================================


class TestAnalyzeAddonMemory:
    """测试分析 Addon 内存便捷函数"""

    def test_analyze_nonexistent(self):
        """测试分析不存在的 Addon"""
        from mc_agent_kit.launcher.auto_fixer import analyze_addon_memory

        report = analyze_addon_memory("/nonexistent/path")

        assert len(report.errors) > 0

    def test_analyze_empty(self):
        """测试分析空 Addon"""
        from mc_agent_kit.launcher.auto_fixer import analyze_addon_memory

        with tempfile.TemporaryDirectory() as tmpdir:
            report = analyze_addon_memory(tmpdir)

            # 空 Addon 应该没有问题
            assert report.total_issues == 0


# ============================================================
# Integration Tests
# ============================================================


class TestIteration32Integration:
    """迭代 #32 集成测试"""

    def test_full_addon_analysis(self):
        """测试完整 Addon 分析"""
        from mc_agent_kit.launcher.auto_fixer import MemoryAutoFixer

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建模拟 Addon 结构
            addon_path = Path(tmpdir) / "test_addon"
            addon_path.mkdir()

            # 创建 behavior_pack
            bp_path = addon_path / "behavior_pack"
            bp_path.mkdir()

            # 创建脚本
            scripts_path = bp_path / "scripts"
            scripts_path.mkdir()

            script_content = "\n".join(["x = 1"] * 600)
            (scripts_path / "main.py").write_text(script_content, encoding="utf-8")

            # 创建 resource_pack
            rp_path = addon_path / "resource_pack"
            rp_path.mkdir()

            # 创建模型
            models_path = rp_path / "models"
            models_path.mkdir()

            model_data = {
                "minecraft:geometry": [
                    {"bones": [{"name": "root", "cubes": [{"size": [1, 1, 1]}]}]}
                ]
            }
            with open(models_path / "test.geo.json", "w", encoding="utf-8") as f:
                json.dump(model_data, f)

            # 分析
            fixer = MemoryAutoFixer(str(addon_path))
            report = fixer.analyze()

            # 应该检测到大脚本
            assert any("脚本" in s.title for s in report.suggestions)

    def test_api_usage_tracking_workflow(self):
        """测试 API 使用追踪工作流"""
        from mc_agent_kit.knowledge_base.models import ApiUsageTracker

        tracker = ApiUsageTracker()

        # 模拟使用场景
        apis_used = [
            ("CreateEngineEntity", True),
            ("GetEngineEntity", True),
            ("CreateEngineEntity", True),
            ("DestroyEngineEntity", True),
            ("CreateEngineEntity", False),
        ]

        for api, success in apis_used:
            tracker.record_usage(api, success=success)

        # 检查统计
        stats = tracker.get_stats("CreateEngineEntity")
        assert stats is not None
        assert stats.usage_count == 3
        assert stats.success_count == 2
        assert stats.error_count == 1

        # 获取热门 API
        popular = tracker.get_popular_apis()
        assert popular[0][0] == "CreateEngineEntity"