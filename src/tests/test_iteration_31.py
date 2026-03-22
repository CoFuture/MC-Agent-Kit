"""
迭代 #31 测试

测试启动器内存问题诊断、知识库增强和测试覆盖率提升功能。
"""

import json
import os
import tempfile
from pathlib import Path

import pytest


# ============================================================
# Memory Issue Diagnosis Tests
# ============================================================

class TestMemoryDiagnosticReport:
    """内存诊断报告测试"""

    def test_create_memory_report(self):
        """测试创建内存诊断报告"""
        from mc_agent_kit.launcher.diagnoser import MemoryDiagnosticReport

        report = MemoryDiagnosticReport(
            addon_path="/test/addon",
            config_path="/test/config.json",
            has_memory_issues=False,
            issues=[],
            suggestions=[],
        )

        assert report.addon_path == "/test/addon"
        assert report.has_memory_issues is False
        assert len(report.issues) == 0

    def test_memory_report_to_dict(self):
        """测试内存诊断报告转字典"""
        from mc_agent_kit.launcher.diagnoser import MemoryDiagnosticReport

        report = MemoryDiagnosticReport(
            addon_path="/test/addon",
            config_path="/test/config.json",
            has_memory_issues=True,
            issues=[{"type": "large_texture", "message": "纹理过大"}],
            suggestions=["压缩纹理"],
        )

        data = report.to_dict()

        assert data["addon_path"] == "/test/addon"
        assert data["has_memory_issues"] is True
        assert len(data["issues"]) == 1
        assert len(data["suggestions"]) == 1


class TestAddonResourceAnalyzer:
    """Addon 资源分析器测试"""

    def test_analyze_texture_files(self):
        """测试分析纹理文件"""
        from mc_agent_kit.launcher.diagnoser import AddonResourceAnalyzer

        analyzer = AddonResourceAnalyzer()

        # 创建临时目录和纹理文件
        with tempfile.TemporaryDirectory() as tmpdir:
            textures_dir = os.path.join(tmpdir, "textures")
            os.makedirs(textures_dir)

            # 创建一个大纹理文件（模拟）
            large_texture = os.path.join(textures_dir, "large.png")
            with open(large_texture, "wb") as f:
                f.write(b"x" * (5 * 1024 * 1024))  # 5MB

            # 创建一个小纹理文件
            small_texture = os.path.join(textures_dir, "small.png")
            with open(small_texture, "wb") as f:
                f.write(b"x" * 1024)  # 1KB

            result = analyzer.analyze_texture_sizes(textures_dir)

            assert "large_files" in result
            assert len(result["large_files"]) >= 1

    def test_analyze_model_files(self):
        """测试分析模型文件"""
        from mc_agent_kit.launcher.diagnoser import AddonResourceAnalyzer

        analyzer = AddonResourceAnalyzer()

        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = os.path.join(tmpdir, "models")
            os.makedirs(models_dir)

            # 创建模型文件
            model_file = os.path.join(models_dir, "entity.geo.json")
            model_data = {
                "format_version": "1.12.0",
                "minecraft:geometry": [
                    {
                        "description": {"identifier": "geometry.test"},
                        "bones": [{"name": "bone1", "cubes": []}]
                    }
                ]
            }

            with open(model_file, "w") as f:
                json.dump(model_data, f)

            result = analyzer.analyze_model_files(models_dir)

            assert "total_models" in result
            assert result["total_models"] >= 1

    def test_analyze_scripts(self):
        """测试分析脚本文件"""
        from mc_agent_kit.launcher.diagnoser import AddonResourceAnalyzer

        analyzer = AddonResourceAnalyzer()

        with tempfile.TemporaryDirectory() as tmpdir:
            scripts_dir = os.path.join(tmpdir, "scripts")
            os.makedirs(scripts_dir)

            # 创建脚本文件
            script_file = os.path.join(scripts_dir, "main.py")
            with open(script_file, "w") as f:
                f.write("""
# Test script
def main():
    print("Hello")

if __name__ == "__main__":
    main()
""")

            result = analyzer.analyze_scripts(scripts_dir)

            assert "total_scripts" in result
            assert result["total_scripts"] >= 1


class TestGameVersionChecker:
    """游戏版本检查器测试"""

    def test_parse_version_string(self):
        """测试解析版本字符串"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker

        checker = GameVersionChecker()

        # 测试标准版本格式
        version = checker.parse_version("1.21.0")
        assert version is not None
        assert version["major"] == 1
        assert version["minor"] == 21
        assert version["patch"] == 0

        # 测试带后缀版本
        version = checker.parse_version("1.20.50.20")
        assert version is not None
        assert version["major"] == 1

    def test_check_compatibility(self):
        """测试兼容性检查"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker

        checker = GameVersionChecker()

        # 测试版本比较 - 游戏版本高于 addon 版本则兼容
        result = checker.check_compatibility("1.20.0", "1.21.0")
        assert result["compatible"] is True  # 游戏版本高，兼容

        result = checker.check_compatibility("1.21.0", "1.20.0")
        assert result["compatible"] is False  # 游戏版本低，不兼容

    def test_get_version_features(self):
        """测试获取版本特性"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker

        checker = GameVersionChecker()

        features = checker.get_version_features("1.21.0")
        assert isinstance(features, list)


# ============================================================
# Knowledge Base Enhancement Tests
# ============================================================

class TestApiVersionTag:
    """API 版本标记测试"""

    def test_create_version_tag(self):
        """测试创建版本标记"""
        from mc_agent_kit.knowledge_base.models import ApiVersionTag

        tag = ApiVersionTag(
            api_name="CreateEntity",
            introduced_in="1.16.0",
            deprecated_in=None,
            removed_in=None,
            notes=[],
        )

        assert tag.api_name == "CreateEntity"
        assert tag.introduced_in == "1.16.0"
        assert tag.is_deprecated() is False

    def test_is_deprecated(self):
        """测试废弃检测"""
        from mc_agent_kit.knowledge_base.models import ApiVersionTag

        tag = ApiVersionTag(
            api_name="OldAPI",
            introduced_in="1.10.0",
            deprecated_in="1.18.0",
            removed_in=None,
            notes=["请使用 NewAPI 替代"],
        )

        assert tag.is_deprecated() is True
        assert tag.is_removed() is False

    def test_is_removed(self):
        """测试移除检测"""
        from mc_agent_kit.knowledge_base.models import ApiVersionTag

        tag = ApiVersionTag(
            api_name="RemovedAPI",
            introduced_in="1.10.0",
            deprecated_in="1.15.0",
            removed_in="1.20.0",
            notes=[],
        )

        assert tag.is_removed() is True


class TestEnhancedSearchRelevance:
    """增强搜索相关性测试"""

    def test_search_with_version_filter(self):
        """测试带版本过滤的搜索"""
        from mc_agent_kit.knowledge.retrieval import EnhancedKnowledgeRetrieval

        retrieval = EnhancedKnowledgeRetrieval()

        # 添加带版本的 API
        retrieval._api_index["NewAPI"] = {
            "name": "NewAPI",
            "description": "新 API",
            "version": "1.21.0",
        }

        retrieval._api_index["OldAPI"] = {
            "name": "OldAPI",
            "description": "旧 API",
            "version": "1.16.0",
        }

        retrieval._loaded = True

        # 搜索最新版本 API
        results = retrieval.search("API", target_version="1.21.0")
        assert len(results) > 0

    def test_search_boost_exact_match(self):
        """测试精确匹配加分"""
        from mc_agent_kit.knowledge.retrieval import EnhancedKnowledgeRetrieval

        retrieval = EnhancedKnowledgeRetrieval()

        retrieval._api_index["CreateEntity"] = {
            "name": "CreateEntity",
            "description": "创建实体",
        }

        retrieval._api_index["EntityBehavior"] = {
            "name": "EntityBehavior",
            "description": "实体行为",
        }

        retrieval._loaded = True

        results = retrieval.search("CreateEntity")

        # CreateEntity 应该排在前面
        assert results[0].name == "CreateEntity"


class TestCodeExampleEnhancement:
    """代码示例增强测试"""

    def test_code_example_with_difficulty(self):
        """测试带难度标记的代码示例"""
        from mc_agent_kit.knowledge.parsers.code_extractor import EnhancedCodeExample

        example = EnhancedCodeExample(
            id="example-1",
            code="print('hello')",
            language="python",
            source="test.md",
            description="简单示例",
            difficulty="beginner",
            estimated_time_minutes=5,
        )

        assert example.difficulty == "beginner"
        assert example.estimated_time_minutes == 5

    def test_code_example_categorization(self):
        """测试代码示例分类"""
        from mc_agent_kit.knowledge.parsers.code_extractor import CodeExampleCategory

        assert CodeExampleCategory.BASIC.value == "basic"
        assert CodeExampleCategory.ADVANCED.value == "advanced"
        assert CodeExampleCategory.COMPLETE.value == "complete"


# ============================================================
# Configuration Generation Boundary Tests
# ============================================================

class TestConfigGeneratorBoundaries:
    """配置生成边界测试"""

    def test_generate_config_with_special_characters(self):
        """测试特殊字符"""
        from mc_agent_kit.launcher.config_generator import GameConfig, WorldInfo, PlayerInfo, ServerInfo
        from mc_agent_kit.launcher.addon_scanner import AddonInfo, PackInfo

        addon_info = AddonInfo(
            id="test_addon_123",
            name="测试 Addon 中文",
            path="/test/path",
            behavior_packs=[],
            resource_packs=[],
        )

        game_config = GameConfig(
            addon_id="test_addon_123",
            addon_name="测试 Addon 中文",
            addon_path="/test/path",
            game_version="1.21.0",
            game_exe_path="/game/exe",
            world_info=WorldInfo(),
            player_info=PlayerInfo(),
            server_info=ServerInfo(),
        )

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            from mc_agent_kit.launcher.config_generator import generate_config
            result, config_path = generate_config(addon_info, game_config, tmpdir)
            assert result is not None


# ============================================================
# Error Handling Tests
# ============================================================

class TestErrorHandling:
    """错误处理测试"""

    def test_diagnose_with_invalid_config(self):
        """测试无效配置诊断"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json {")
            temp_path = f.name

        try:
            report = diagnoser.diagnose(config_path=temp_path)
            assert report is not None
        finally:
            os.unlink(temp_path)

    def test_diagnose_with_missing_fields(self):
        """测试缺失字段诊断"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser

        diagnoser = LauncherDiagnoser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"version": "1.0.0"}, f)  # 缺少必要字段
            temp_path = f.name

        try:
            report = diagnoser.diagnose(config_path=temp_path)
            assert report is not None
        finally:
            os.unlink(temp_path)

    def test_autofix_with_corrupted_config(self):
        """测试损坏配置自动修复"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer

        fixer = ConfigAutoFixer()

        # 部分损坏的配置
        corrupted_config = {
            "version": "1.0.0",
            # 缺少 MainComponentId
            "world_info": {
                # 缺少必要字段
            },
        }

        report = fixer.analyze(corrupted_config)
        assert len(report.fixes) > 0

        fixed_config, fix_report = fixer.fix(corrupted_config)
        assert "MainComponentId" in fixed_config


# ============================================================
# Integration Tests
# ============================================================

class TestIteration31Integration:
    """迭代 #31 集成测试"""

    def test_full_memory_diagnosis_workflow(self):
        """测试完整内存诊断工作流"""
        from mc_agent_kit.launcher.diagnoser import (
            AddonResourceAnalyzer,
            GameVersionChecker,
            MemoryDiagnosticReport,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 Addon 结构
            textures_dir = os.path.join(tmpdir, "textures")
            os.makedirs(textures_dir)

            # 创建纹理文件
            with open(os.path.join(textures_dir, "test.png"), "wb") as f:
                f.write(b"x" * 1024)

            # 分析资源
            analyzer = AddonResourceAnalyzer()
            texture_result = analyzer.analyze_texture_sizes(textures_dir)

            assert "total_size_bytes" in texture_result

            # 检查版本兼容性
            checker = GameVersionChecker()
            compat_result = checker.check_compatibility("1.21.0", "1.20.0")

            assert "compatible" in compat_result

            # 生成诊断报告
            report = MemoryDiagnosticReport(
                addon_path=tmpdir,
                config_path="",
                has_memory_issues=False,
                issues=[],
                suggestions=[],
            )

            assert report.to_dict() is not None

    def test_enhanced_knowledge_search_workflow(self):
        """测试增强知识搜索工作流"""
        from mc_agent_kit.knowledge.retrieval import EnhancedKnowledgeRetrieval

        retrieval = EnhancedKnowledgeRetrieval()

        # 添加测试数据
        retrieval._api_index["CreateEntity"] = {
            "name": "CreateEntity",
            "description": "创建实体 API",
            "version": "1.16.0",
            "module": "实体",
        }

        retrieval._api_index["DestroyEntity"] = {
            "name": "DestroyEntity",
            "description": "销毁实体 API",
            "version": "1.16.0",
            "module": "实体",
        }

        retrieval._loaded = True

        # 搜索
        results = retrieval.search("实体")
        assert len(results) > 0

        # 获取统计
        stats = retrieval.stats
        assert stats["apis"] == 2
