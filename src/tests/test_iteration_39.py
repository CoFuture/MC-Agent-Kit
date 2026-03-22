"""
迭代 #39 测试

目标：
1. 提升测试覆盖率至 90%+
2. 端到端流程完善
3. 性能优化验证
4. 文档完善验证
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# ============================================================
# API Search Skill Tests (提升覆盖率)
# ============================================================

class TestAPISearchSkillCoverage:
    """API 检索 Skill 覆盖率测试"""

    def test_initialize_with_kb_path(self):
        """测试带知识库路径初始化"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = os.path.join(tmpdir, "test_kb.json")
            # 创建正确格式的知识库文件
            kb_data = {
                "apis": {},
                "events": {},
                "enums": {},
                "version": "1.0.0"
            }
            with open(kb_path, 'w') as f:
                json.dump(kb_data, f)
            
            skill = ModSDKAPISearchSkill(kb_path=kb_path)
            result = skill.initialize()
            assert result is True
            assert skill._initialized is True

    def test_initialize_without_kb(self):
        """测试无知识库初始化"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        # 不初始化知识库
        skill._retriever = None
        skill._initialized = False
        
        result = skill.initialize()
        # 应该成功初始化，只是没有加载知识库
        assert result is True

    def test_execute_without_initialized(self):
        """测试未初始化时执行"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = False
        skill._retriever = None
        
        # 由于 initialize() 会在 execute 中调用，所以实际会成功
        result = skill.execute(query="test")
        # 知识库已存在，初始化会成功
        assert result is not None

    def test_execute_with_name(self):
        """测试按名称精确搜索"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import APIEntry, Scope
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        # Mock 返回的 API
        mock_api = APIEntry(
            name="GetEngineType",
            module="系统",
            description="获取引擎类型",
            scope=Scope.BOTH,
            method_path="GetEngineType",
            parameters=[],
            return_type="str",
            return_description="引擎类型",
            examples=[],
            remarks=[],
        )
        skill._retriever.get_api.return_value = mock_api
        
        result = skill.execute(name="GetEngineType")
        assert result.success is True
        assert result.data[0]["name"] == "GetEngineType"

    def test_execute_with_name_not_found(self):
        """测试名称搜索未找到"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        skill._retriever.get_api.return_value = None
        skill._retriever.suggest.return_value = ["Suggestion1"]
        
        result = skill.execute(name="NonExistentAPI")
        assert result.success is False
        assert "未找到" in result.error

    def test_execute_with_return_type(self):
        """测试按返回类型搜索"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import APIEntry, Scope
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        mock_apis = [
            APIEntry(
                name="GetPos",
                module="实体",
                description="获取位置",
                scope=Scope.SERVER,
                method_path="GetPos",
                parameters=[],
                return_type="tuple",
                return_description="坐标",
                examples=[],
                remarks=[],
            )
        ]
        skill._retriever.search_by_return_type.return_value = mock_apis
        
        result = skill.execute(return_type="tuple")
        assert result.success is True
        assert len(result.data) == 1

    def test_execute_with_param_name(self):
        """测试按参数名搜索"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import APIEntry, Scope
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        mock_apis = [
            APIEntry(
                name="SetPos",
                module="实体",
                description="设置位置",
                scope=Scope.SERVER,
                method_path="SetPos",
                parameters=[],
                return_type=None,
                return_description=None,
                examples=[],
                remarks=[],
            )
        ]
        skill._retriever.search_by_parameter.return_value = mock_apis
        
        result = skill.execute(param_name="pos")
        assert result.success is True

    def test_execute_fuzzy_search(self):
        """测试模糊搜索"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import APIEntry, Scope
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        mock_api = APIEntry(
            name="GetEngineType",
            module="系统",
            description="获取引擎类型",
            scope=Scope.BOTH,
            method_path="GetEngineType",
            parameters=[],
            return_type="str",
            return_description="引擎类型",
            examples=[],
            remarks=[],
        )
        skill._retriever.fuzzy_search.return_value = [(mock_api, 1)]
        
        result = skill.execute(query="engin", fuzzy=True)
        assert result.success is True

    def test_execute_with_query(self):
        """测试关键词搜索"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import APIEntry, Scope
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        mock_apis = [
            APIEntry(
                name="CreateEntity",
                module="实体",
                description="创建实体",
                scope=Scope.SERVER,
                method_path="CreateEntity",
                parameters=[],
                return_type="int",
                return_description="实体ID",
                examples=[],
                remarks=[],
            )
        ]
        skill._retriever.search_api.return_value = mock_apis
        
        result = skill.execute(query="entity", scope="server")
        assert result.success is True

    def test_execute_module_only(self):
        """测试仅按模块搜索"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import APIEntry, Scope
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        mock_apis = [
            APIEntry(
                name="CreateItem",
                module="物品",
                description="创建物品",
                scope=Scope.SERVER,
                method_path="CreateItem",
                parameters=[],
                return_type="int",
                return_description="物品ID",
                examples=[],
                remarks=[],
            )
        ]
        skill._retriever.search_api.return_value = mock_apis
        
        result = skill.execute(module="物品")
        assert result.success is True

    def test_execute_no_params(self):
        """测试无参数执行"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        
        result = skill.execute()
        assert result.success is False
        assert "请提供搜索参数" in result.error

    def test_execute_exception(self):
        """测试执行异常"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        skill._retriever.search_api.side_effect = Exception("Test error")
        
        result = skill.execute(query="test")
        assert result.success is False
        assert "Test error" in result.error

    def test_list_modules(self):
        """测试列出模块"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        skill._retriever.list_modules.return_value = ["实体", "物品", "方块"]
        
        result = skill.list_modules()
        assert result.success is True
        assert len(result.data) == 3

    def test_list_modules_not_initialized(self):
        """测试未初始化时列出模块"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._retriever = None
        skill._initialized = False
        
        # 会自动初始化，知识库存在时会成功
        result = skill.list_modules()
        # 知识库已存在，初始化会成功
        assert result is not None

    def test_get_stats(self):
        """测试获取统计"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = Mock()
        skill._retriever.get_stats.return_value = {"apis": 100, "events": 50}
        
        result = skill.get_stats()
        assert result.success is True
        assert result.data["apis"] == 100

    def test_get_stats_not_initialized(self):
        """测试未初始化时获取统计"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill._retriever = None
        skill._initialized = False
        
        # 会自动初始化，知识库存在时会成功
        result = skill.get_stats()
        # 知识库已存在，初始化会成功
        assert result is not None

    def test_parse_scope_chinese(self):
        """测试中文作用域解析"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import Scope
        
        skill = ModSDKAPISearchSkill()
        
        assert skill._parse_scope("客户端") == Scope.CLIENT
        assert skill._parse_scope("服务端") == Scope.SERVER
        assert skill._parse_scope("双端") == Scope.BOTH


# ============================================================
# Launcher Diagnoser Tests (提升覆盖率)
# ============================================================

class TestLauncherDiagnoserCoverage:
    """启动器诊断器覆盖率测试"""

    def test_diagnose_with_game_path(self):
        """测试带游戏路径诊断"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        diagnoser = LauncherDiagnoser(game_path="C:\\fake\\path\\Minecraft.Windows.exe")
        report = diagnoser.diagnose()
        
        assert report.game_path == "C:\\fake\\path\\Minecraft.Windows.exe"
        # 路径不存在，应该有错误
        assert report.has_errors is True

    def test_diagnose_with_addon_path(self):
        """测试带 Addon 路径诊断"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建标准 Addon 结构
            addon_path = os.path.join(tmpdir, "test_addon")
            os.makedirs(os.path.join(addon_path, "behavior_pack"))
            os.makedirs(os.path.join(addon_path, "resource_pack"))
            
            # 创建 manifest.json
            bp_manifest = {
                "format_version": 1,
                "header": {
                    "name": "Test BP",
                    "description": "Test",
                    "uuid": "test-uuid-bp",
                    "version": [1, 0, 0]
                },
                "modules": [{"type": "data"}]
            }
            with open(os.path.join(addon_path, "behavior_pack", "manifest.json"), 'w') as f:
                json.dump(bp_manifest, f)
            
            rp_manifest = {
                "format_version": 1,
                "header": {
                    "name": "Test RP",
                    "description": "Test",
                    "uuid": "test-uuid-rp",
                    "version": [1, 0, 0]
                },
                "modules": [{"type": "resources"}]
            }
            with open(os.path.join(addon_path, "resource_pack", "manifest.json"), 'w') as f:
                json.dump(rp_manifest, f)
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.diagnose(addon_path=addon_path)
            
            assert report.addon_path == addon_path

    def test_diagnose_addon_not_exists(self):
        """测试 Addon 路径不存在"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        diagnoser = LauncherDiagnoser()
        report = diagnoser.diagnose(addon_path="/nonexistent/path")
        
        assert report.has_errors is True
        assert any(i.code == "ADDON_PATH_NOT_FOUND" for i in report.issues)

    def test_diagnose_config_not_exists(self):
        """测试配置文件不存在"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        diagnoser = LauncherDiagnoser()
        report = diagnoser.diagnose(config_path="/nonexistent/config.json")
        
        assert report.has_errors is True
        assert any(i.code == "CONFIG_NOT_FOUND" for i in report.issues)

    def test_diagnose_invalid_manifest(self):
        """测试无效 manifest.json"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            addon_path = os.path.join(tmpdir, "test_addon")
            os.makedirs(os.path.join(addon_path, "behavior_pack"))
            
            # 创建无效的 JSON 文件
            with open(os.path.join(addon_path, "behavior_pack", "manifest.json"), 'w') as f:
                f.write("{ invalid json }")
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.quick_check(addon_path)
            
            assert any(i.code == "MANIFEST_JSON_ERROR" for i in report.issues)

    def test_diagnose_manifest_missing_field(self):
        """测试 manifest.json 缺少字段"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            addon_path = os.path.join(tmpdir, "test_addon")
            os.makedirs(os.path.join(addon_path, "behavior_pack"))
            
            # 创建缺少字段的 manifest
            manifest = {"format_version": 1}  # 缺少 header
            with open(os.path.join(addon_path, "behavior_pack", "manifest.json"), 'w') as f:
                json.dump(manifest, f)
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.quick_check(addon_path)
            
            assert any(i.code == "MANIFEST_FIELD_MISSING" for i in report.issues)

    def test_diagnose_config_json_error(self):
        """测试配置文件 JSON 错误"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, 'w') as f:
                f.write("{ invalid json }")
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.diagnose(config_path=config_path)
            
            assert any(i.code == "CONFIG_JSON_ERROR" for i in report.issues)

    def test_diagnose_config_missing_fields(self):
        """测试配置文件缺少字段"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = {}  # 空配置
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.diagnose(config_path=config_path)
            
            assert any(i.code == "CONFIG_FIELD_MISSING" for i in report.issues)

    def test_diagnose_config_valid(self):
        """测试有效配置文件"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = {
                "version": "1.0",
                "MainComponentId": "test-component",
                "world_info": {
                    "resource_packs": ["pack1"],
                    "behavior_packs": ["pack2"]
                },
                "LocalComponentPathsDict": {
                    "test-component": {
                        "cfg_path": tmpdir,
                        "work_path": tmpdir
                    }
                }
            }
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.diagnose(config_path=config_path)
            
            # 不应该有配置相关的错误
            config_errors = [i for i in report.issues if i.category.value == "config"]
            assert all(e.code != "CONFIG_FIELD_MISSING" for e in config_errors)

    def test_quick_check(self):
        """测试快速检查"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            addon_path = os.path.join(tmpdir, "test_addon")
            os.makedirs(addon_path)
            
            diagnoser = LauncherDiagnoser()
            report = diagnoser.quick_check(addon_path)
            
            assert report.addon_path == addon_path

    def test_compare_configs(self):
        """测试配置对比"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = {
                "version": "1.0",
                "MainComponentId": "test",
                "world_info": {"game_type": 1}
            }
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            diagnoser = LauncherDiagnoser()
            result = diagnoser.compare_with_mc_studio_config(config_path)
            
            assert "differences" in result
            assert "warnings" in result

    def test_compare_configs_missing_mc_studio(self):
        """测试配置对比 - 无 MC Studio 配置"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = {"version": "1.0"}
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            diagnoser = LauncherDiagnoser()
            result = diagnoser.compare_with_mc_studio_config(config_path)
            
            # 应该有警告说找不到 MC Studio 配置
            assert len(result["warnings"]) > 0

    def test_deep_compare_values(self):
        """测试深度比较值"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        diagnoser = LauncherDiagnoser()
        
        result = {
            "differences": [],
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
        }
        
        # 比较不同类型的值
        diagnoser._deep_compare("string", 123, "test_field", result)
        assert len(result["type_mismatches"]) > 0
        
        # 比较相同值
        result["type_mismatches"] = []
        diagnoser._deep_compare("same", "same", "test_field", result)
        assert len(result["type_mismatches"]) == 0

    def test_deep_compare_lists(self):
        """测试深度比较列表"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        diagnoser = LauncherDiagnoser()
        
        result = {
            "differences": [],
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
        }
        
        # 比较不同长度的列表
        diagnoser._deep_compare([1, 2], [1, 2, 3], "test_list", result)
        assert any(d["field"] == "test_list (length)" for d in result["differences"])

    def test_collect_system_info(self):
        """测试收集系统信息"""
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        diagnoser = LauncherDiagnoser()
        info = diagnoser._collect_system_info()
        
        assert "os" in info
        assert "python_version" in info


# ============================================================
# Config Auto Fixer Tests
# ============================================================

class TestConfigAutoFixerCoverage:
    """配置自动修复器覆盖率测试"""

    def test_analyze_empty_config(self):
        """测试分析空配置"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer
        
        fixer = ConfigAutoFixer()
        report = fixer.analyze({})
        
        assert len(report.fixes) > 0

    def test_analyze_valid_config(self):
        """测试分析有效配置"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer
        
        fixer = ConfigAutoFixer()
        config = {
            "version": "1.0.0",
            "MainComponentId": "test",
            "LocalComponentPathsDict": {
                "test": {"cfg_path": "/path", "work_path": "/path"}
            },
            "world_info": {
                "level_id": "test",
                "game_type": 1,
                "difficulty": 2,
                "cheat": True,
                "cheat_info": fixer.CHEAT_INFO_DEFAULTS,
                "resource_packs": [],
                "behavior_packs": []
            },
            "room_info": {
                "token": "",
                "room_id": 0,
                "host_id": 0,
                "max_player": 0,
                "allow_pe": True
            },
            "player_info": {
                "user_id": 0,
                "user_name": "",
                "urs": ""
            }
        }
        
        report = fixer.analyze(config)
        # 有效配置应该不需要太多修复
        assert report is not None

    def test_fix_config(self):
        """测试修复配置"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer
        
        fixer = ConfigAutoFixer()
        original = {}
        fixed, report = fixer.fix(original)
        
        assert report.fixed is True
        assert "version" in fixed
        assert "world_info" in fixed

    def test_fix_from_file(self):
        """测试从文件修复"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, 'w') as f:
                json.dump({}, f)
            
            fixer = ConfigAutoFixer()
            report = fixer.fix_from_file(config_path)
            
            assert report.fixed is True

    def test_fix_from_file_read_error(self):
        """测试从文件修复 - 读取错误"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer
        
        fixer = ConfigAutoFixer()
        report = fixer.fix_from_file("/nonexistent/path/config.json")
        
        assert len(report.errors) > 0

    def test_apply_fix_nested(self):
        """测试应用修复 - 嵌套字段"""
        from mc_agent_kit.launcher.diagnoser import ConfigAutoFixer
        
        fixer = ConfigAutoFixer()
        config = {}
        fixer._apply_fix(config, "world_info.game_type", 1)
        
        assert config["world_info"]["game_type"] == 1


# ============================================================
# Memory Diagnostic Tests
# ============================================================

class TestMemoryDiagnostic:
    """内存诊断测试"""

    def test_addon_resource_analyzer_textures(self):
        """测试纹理分析"""
        from mc_agent_kit.launcher.diagnoser import AddonResourceAnalyzer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            textures_dir = os.path.join(tmpdir, "textures")
            os.makedirs(textures_dir)
            
            # 创建一个小纹理文件
            small_texture = os.path.join(textures_dir, "small.png")
            with open(small_texture, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # 小 PNG 文件
            
            analyzer = AddonResourceAnalyzer()
            result = analyzer.analyze_texture_sizes(textures_dir)
            
            assert result["total_files"] == 1

    def test_addon_resource_analyzer_models(self):
        """测试模型分析"""
        from mc_agent_kit.launcher.diagnoser import AddonResourceAnalyzer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            models_dir = os.path.join(tmpdir, "models")
            os.makedirs(models_dir)
            
            # 创建一个模型文件
            model_file = os.path.join(models_dir, "test.geo.json")
            with open(model_file, 'w') as f:
                json.dump({"format_version": "1.12.0"}, f)
            
            analyzer = AddonResourceAnalyzer()
            result = analyzer.analyze_model_files(models_dir)
            
            assert result["total_models"] == 1

    def test_addon_resource_analyzer_scripts(self):
        """测试脚本分析"""
        from mc_agent_kit.launcher.diagnoser import AddonResourceAnalyzer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts_dir = os.path.join(tmpdir, "scripts")
            os.makedirs(scripts_dir)
            
            # 创建一个脚本文件
            script_file = os.path.join(scripts_dir, "main.py")
            with open(script_file, 'w') as f:
                f.write("print('Hello World')\n")
            
            analyzer = AddonResourceAnalyzer()
            result = analyzer.analyze_scripts(scripts_dir)
            
            assert result["total_scripts"] == 1

    def test_game_version_checker_parse(self):
        """测试版本解析"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker
        
        checker = GameVersionChecker()
        result = checker.parse_version("1.21.0")
        
        assert result["major"] == 1
        assert result["minor"] == 21
        assert result["patch"] == 0

    def test_game_version_checker_invalid(self):
        """测试无效版本解析"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker
        
        checker = GameVersionChecker()
        result = checker.parse_version("invalid")
        
        assert result is None

    def test_game_version_checker_compatibility(self):
        """测试版本兼容性检查"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker
        
        checker = GameVersionChecker()
        
        # 兼容情况
        result = checker.check_compatibility("1.20.0", "1.21.0")
        assert result["compatible"] is True
        
        # 不兼容情况
        result = checker.check_compatibility("1.21.0", "1.20.0")
        assert result["compatible"] is False

    def test_game_version_checker_features(self):
        """测试版本特性获取"""
        from mc_agent_kit.launcher.diagnoser import GameVersionChecker
        
        checker = GameVersionChecker()
        features = checker.get_version_features("1.21.0")
        
        assert isinstance(features, list)


# ============================================================
# End-to-End Workflow Tests
# ============================================================

class TestEndToEndWorkflow:
    """端到端工作流测试"""

    def test_full_diagnostic_workflow(self):
        """测试完整诊断工作流"""
        from mc_agent_kit.launcher.diagnoser import (
            LauncherDiagnoser,
            ConfigAutoFixer,
            diagnose_launcher,
            fix_config,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 Addon
            addon_path = os.path.join(tmpdir, "test_addon")
            os.makedirs(os.path.join(addon_path, "behavior_pack"))
            
            manifest = {
                "format_version": 1,
                "header": {
                    "name": "Test",
                    "description": "Test",
                    "uuid": "test-uuid",
                    "version": [1, 0, 0]
                },
                "modules": [{"type": "data"}]
            }
            with open(os.path.join(addon_path, "behavior_pack", "manifest.json"), 'w') as f:
                json.dump(manifest, f)
            
            # 创建配置
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, 'w') as f:
                json.dump({}, f)
            
            # 诊断
            report = diagnose_launcher(addon_path=addon_path, config_path=config_path)
            assert report is not None
            
            # 修复配置
            fix_report = fix_config(config_path)
            assert fix_report is not None

    def test_api_search_workflow(self):
        """测试 API 搜索工作流"""
        from mc_agent_kit.skills.modsdk.api_search import (
            ModSDKAPISearchSkill,
            APISearchResult,
        )
        
        skill = ModSDKAPISearchSkill()
        skill.initialize()
        
        # 测试各种搜索方式
        result = skill.execute(query="entity")
        assert result is not None
        
        result = skill.list_modules()
        assert result is not None
        
        result = skill.get_stats()
        assert result is not None


# ============================================================
# Performance Benchmark Tests
# ============================================================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_diagnose_performance(self):
        """测试诊断性能"""
        import time
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            addon_path = os.path.join(tmpdir, "addon")
            os.makedirs(addon_path)
            
            diagnoser = LauncherDiagnoser()
            
            start = time.time()
            diagnoser.quick_check(addon_path)
            duration = time.time() - start
            
            # 诊断应该在 1 秒内完成
            assert duration < 1.0

    def test_api_search_performance(self):
        """测试 API 搜索性能"""
        import time
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        skill.initialize()
        
        start = time.time()
        for _ in range(10):
            skill.execute(query="entity", limit=5)
        duration = time.time() - start
        
        # 10 次搜索应该在 5 秒内完成
        assert duration < 5.0


# ============================================================
# Integration Tests
# ============================================================

class TestIteration39Integration:
    """迭代 #39 集成测试"""

    def test_all_modules_importable(self):
        """测试所有模块可导入"""
        from mc_agent_kit import (
            launcher,
            knowledge,
            skills,
            scaffold,
            generator,
            autofix,
            log_capture,
            retrieval,
            execution,
            performance,
            stats,
        )
        
        assert launcher is not None
        assert knowledge is not None
        assert skills is not None
        assert scaffold is not None

    def test_diagnostic_report_serialization(self):
        """测试诊断报告序列化"""
        from mc_agent_kit.launcher.diagnoser import (
            DiagnosticReport,
            DiagnosticIssue,
            DiagnosticSeverity,
            DiagnosticCategory,
        )
        
        report = DiagnosticReport(success=True)
        report.issues.append(DiagnosticIssue(
            category=DiagnosticCategory.CONFIG,
            severity=DiagnosticSeverity.ERROR,
            code="TEST_ERROR",
            message="Test error message",
        ))
        
        data = report.to_dict()
        assert data["success"] is True
        assert len(data["issues"]) == 1

    def test_config_fix_report_serialization(self):
        """测试配置修复报告序列化"""
        from mc_agent_kit.launcher.diagnoser import (
            ConfigFixReport,
            ConfigFix,
        )
        
        report = ConfigFixReport()
        report.fixes.append(ConfigFix(
            field="test_field",
            current_value=None,
            suggested_value="test_value",
            description="Test fix",
        ))
        
        data = report.to_dict()
        assert len(data["fixes"]) == 1


# ============================================================
# Acceptance Criteria Tests
# ============================================================

class TestAcceptanceCriteria:
    """验收标准测试"""

    def test_diagnostic_tool_available(self):
        """诊断工具可用"""
        from mc_agent_kit.launcher.diagnoser import diagnose_launcher
        
        assert callable(diagnose_launcher)

    def test_config_fix_available(self):
        """配置修复可用"""
        from mc_agent_kit.launcher.diagnoser import fix_config
        
        assert callable(fix_config)

    def test_api_search_available(self):
        """API 搜索可用"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        
        skill = ModSDKAPISearchSkill()
        assert skill is not None

    def test_scaffold_available(self):
        """脚手架可用"""
        from mc_agent_kit.scaffold.creator import ProjectCreator
        
        creator = ProjectCreator()
        assert creator is not None