"""
迭代 #30 测试

测试配置文件对比工具、自动修复功能等。
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.launcher.diagnoser import (
    ConfigAutoFixer,
    ConfigFix,
    ConfigFixReport,
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    DiagnosticSeverity,
    LauncherDiagnoser,
    diagnose_launcher,
    fix_config,
)


class TestConfigFix:
    """ConfigFix 数据结构测试"""

    def test_config_fix_creation(self):
        """测试 ConfigFix 创建"""
        fix = ConfigFix(
            field="world_info.game_type",
            current_value=None,
            suggested_value=1,
            description="缺少字段",
            auto_fixable=True,
        )
        assert fix.field == "world_info.game_type"
        assert fix.current_value is None
        assert fix.suggested_value == 1
        assert fix.auto_fixable is True

    def test_config_fix_defaults(self):
        """测试 ConfigFix 默认值"""
        fix = ConfigFix(
            field="test",
            current_value=None,
            suggested_value="value",
            description="test",
        )
        assert fix.auto_fixable is True


class TestConfigFixReport:
    """ConfigFixReport 数据结构测试"""

    def test_empty_report(self):
        """测试空报告"""
        report = ConfigFixReport()
        assert report.fixes == []
        assert report.fixed is False
        assert report.errors == []
        assert report.warnings == []

    def test_report_with_fixes(self):
        """测试带修复项的报告"""
        report = ConfigFixReport()
        report.fixes.append(ConfigFix(
            field="test",
            current_value=None,
            suggested_value="value",
            description="test fix",
        ))
        assert len(report.fixes) == 1

    def test_report_to_dict(self):
        """测试报告转换为字典"""
        report = ConfigFixReport()
        report.fixes.append(ConfigFix(
            field="test",
            current_value=None,
            suggested_value="value",
            description="test",
        ))
        report.fixed = True
        report.errors.append("error")

        result = report.to_dict()
        assert result["fixed"] is True
        assert len(result["fixes"]) == 1
        assert len(result["errors"]) == 1


class TestConfigAutoFixer:
    """ConfigAutoFixer 测试"""

    def test_analyze_empty_config(self):
        """测试分析空配置"""
        fixer = ConfigAutoFixer()
        report = fixer.analyze({})

        # 应该报告所有必要字段缺失
        assert len(report.fixes) > 0
        fields = [f.field for f in report.fixes]
        assert "version" in fields
        assert "MainComponentId" in fields
        assert "world_info" in fields

    def test_analyze_complete_config(self):
        """测试分析完整配置"""
        fixer = ConfigAutoFixer()
        config = {
            "version": "1.0.0",
            "client_type": 0,
            "MainComponentId": "test",
            "LocalComponentPathsDict": {},
            "world_info": {
                "level_id": "test",
                "game_type": 1,
                "difficulty": 2,
                "permission_level": 1,
                "cheat": True,
                "cheat_info": {
                    "pvp": True,
                    "show_coordinates": False,
                    "always_day": False,
                    "daylight_cycle": True,
                    "fire_spreads": True,
                    "tnt_explodes": True,
                    "keep_inventory": True,
                    "mob_spawn": True,
                    "natural_regeneration": True,
                    "mob_loot": True,
                    "mob_griefing": True,
                    "tile_drops": True,
                    "entities_drop_loot": True,
                    "weather_cycle": True,
                    "command_blocks_enabled": True,
                    "random_tick_speed": 1,
                    "experimental_holiday": False,
                    "experimental_biomes": False,
                    "fancy_bubbles": False,
                },
                "resource_packs": [],
                "behavior_packs": [],
                "name": "test",
                "world_type": 2,
            },
            "room_info": {
                "ip": "",
                "port": 0,
                "muiltClient": False,
                "room_name": "",
                "token": "",
                "room_id": 0,
                "host_id": 0,
                "allow_pe": True,
                "max_player": 0,
                "visibility_mode": 0,
                "is_pe": True,
            },
            "player_info": {
                "user_id": 0,
                "user_name": "",
                "urs": "",
            },
            "anti_addiction_info": {
                "enable": False,
                "left_time": 0,
                "exp_multiplier": 1.0,
                "block_multplier": 1.0,
                "first_message": "",
            },
            "misc": {
                "multiplayer_game_type": 0,
                "is_store_enabled": 1,
            },
        }

        report = fixer.analyze(config)
        assert len(report.fixes) == 0

    def test_analyze_missing_world_info_fields(self):
        """测试分析缺少 world_info 字段的配置"""
        fixer = ConfigAutoFixer()
        config = {
            "world_info": {
                "game_type": 1,
                # 缺少其他字段
            }
        }

        report = fixer.analyze(config)
        fields = [f.field for f in report.fixes]

        # 应该报告缺失的字段
        assert "world_info.level_id" in fields
        assert "world_info.difficulty" in fields
        assert "world_info.cheat" in fields

    def test_analyze_missing_cheat_info_fields(self):
        """测试分析缺少 cheat_info 字段的配置"""
        fixer = ConfigAutoFixer()
        config = {
            "world_info": {
                "cheat_info": {
                    "pvp": True,
                    # 缺少其他字段
                }
            }
        }

        report = fixer.analyze(config)
        fields = [f.field for f in report.fixes]

        assert "world_info.cheat_info.daylight_cycle" in fields
        assert "world_info.cheat_info.mob_spawn" in fields

    def test_fix_empty_config(self):
        """测试修复空配置"""
        fixer = ConfigAutoFixer()
        fixed_config, report = fixer.fix({})

        assert report.fixed is True
        assert "version" in fixed_config
        assert "world_info" in fixed_config
        assert "room_info" in fixed_config

    def test_fix_preserves_existing_values(self):
        """测试修复保留现有值"""
        fixer = ConfigAutoFixer()
        config = {
            "version": "2.0.0",
            "world_info": {
                "game_type": 2,
            }
        }

        fixed_config, report = fixer.fix(config)

        # 现有值应该被保留
        assert fixed_config["version"] == "2.0.0"
        assert fixed_config["world_info"]["game_type"] == 2

    def test_fix_local_component_paths(self):
        """测试修复 LocalComponentPathsDict"""
        fixer = ConfigAutoFixer()
        config = {
            "LocalComponentPathsDict": {
                "addon_id": {
                    # 缺少 cfg_path 和 work_path
                }
            }
        }

        report = fixer.analyze(config)
        fields = [f.field for f in report.fixes]

        assert any("cfg_path" in f for f in fields)
        assert any("work_path" in f for f in fields)

    def test_fix_from_file(self):
        """测试从文件修复"""
        fixer = ConfigAutoFixer()

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False
        ) as f:
            json.dump({"version": "1.0.0"}, f)
            temp_path = f.name

        try:
            report = fixer.fix_from_file(temp_path)
            assert report.fixed is True

            # 读取修复后的文件
            with open(temp_path, encoding="utf-8") as f:
                fixed = json.load(f)

            assert "world_info" in fixed
        finally:
            os.unlink(temp_path)

    def test_fix_from_invalid_file(self):
        """测试从无效文件修复"""
        fixer = ConfigAutoFixer()

        # 不存在的文件
        report = fixer.fix_from_file("/nonexistent/path.json")
        assert len(report.errors) > 0


class TestLauncherDiagnoserEnhanced:
    """LauncherDiagnoser 增强功能测试"""

    def test_deep_compare_dicts(self):
        """测试深度比较字典"""
        diagnoser = LauncherDiagnoser()
        result = {
            "differences": [],
            "warnings": [],
            "suggestions": [],
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
        }

        diagnoser._deep_compare(
            {"a": 1, "b": 2},
            {"a": 1, "b": 3, "c": 4},
            "",
            result
        )

        # b 的值不同，c 在 reference 中存在但 current 中不存在
        assert len(result["differences"]) >= 1

    def test_deep_compare_lists(self):
        """测试深度比较列表"""
        diagnoser = LauncherDiagnoser()
        result = {
            "differences": [],
            "warnings": [],
            "suggestions": [],
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
        }

        diagnoser._deep_compare(
            [1, 2, 3],
            [1, 2, 4],
            "list",
            result
        )

        # 长度相同但元素不同
        assert len(result["differences"]) >= 1

    def test_deep_compare_type_mismatch(self):
        """测试深度比较类型不匹配"""
        diagnoser = LauncherDiagnoser()
        result = {
            "differences": [],
            "warnings": [],
            "suggestions": [],
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
        }

        diagnoser._deep_compare(
            {"a": "string"},
            {"a": 123},
            "test",
            result
        )

        assert len(result["type_mismatches"]) == 1
        assert result["type_mismatches"][0]["path"] == "test.a"

    def test_compare_with_mc_studio_config(self):
        """测试与 MC Studio 配置对比"""
        diagnoser = LauncherDiagnoser()

        current_config = {
            "version": "1.0.0",
            "MainComponentId": "test",
            "world_info": {
                "game_type": 1,
            }
        }

        mc_config = {
            "version": "2.0.0",
            "MainComponentId": "test",
            "world_info": {
                "game_type": 2,
            }
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False
        ) as f1, tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False
        ) as f2:
            json.dump(current_config, f1)
            json.dump(mc_config, f2)
            current_path = f1.name
            mc_path = f2.name

        try:
            result = diagnoser.compare_with_mc_studio_config(
                current_path, mc_path
            )

            assert len(result["differences"]) >= 1
            assert any(d["field"] in ["version", "world_info.game_type"] for d in result["differences"])
        finally:
            os.unlink(current_path)
            os.unlink(mc_path)


class TestDiagnoseLauncherFunction:
    """diagnose_launcher 便捷函数测试"""

    def test_diagnose_launcher_returns_report(self):
        """测试 diagnose_launcher 返回诊断报告"""
        report = diagnose_launcher()
        assert isinstance(report, DiagnosticReport)

    def test_diagnose_launcher_with_addon_path(self):
        """测试 diagnose_launcher 带 Addon 路径"""
        # 使用不存在的路径测试
        report = diagnose_launcher(addon_path="/nonexistent/path")
        assert report.checks_failed > 0


class TestFixConfigFunction:
    """fix_config 便捷函数测试"""

    def test_fix_config_invalid_path(self):
        """测试 fix_config 无效路径"""
        report = fix_config("/nonexistent/path.json")
        assert len(report.errors) > 0

    def test_fix_config_valid_path(self):
        """测试 fix_config 有效路径"""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False
        ) as f:
            json.dump({"version": "1.0.0"}, f)
            temp_path = f.name

        try:
            report = fix_config(temp_path)
            assert report.fixed is True
        finally:
            os.unlink(temp_path)


class TestDiagnosticReportExtended:
    """DiagnosticReport 扩展测试"""

    def test_report_with_system_info(self):
        """测试报告包含系统信息"""
        report = DiagnosticReport(success=True)
        report.system_info = {"os": "Windows", "memory_total_gb": 16}

        result = report.to_dict()
        assert "system_info" in result
        assert result["system_info"]["os"] == "Windows"


class TestConfigValidationIntegration:
    """配置验证集成测试"""

    def test_full_workflow(self):
        """测试完整工作流：分析 -> 修复 -> 验证"""
        fixer = ConfigAutoFixer()

        # 原始不完整配置
        original = {
            "version": "1.0.0",
            "MainComponentId": "my-addon",
        }

        # 分析
        report = fixer.analyze(original)
        assert len(report.fixes) > 0

        # 修复
        fixed, fix_report = fixer.fix(original)
        assert fix_report.fixed is True

        # 验证修复后的配置
        verify_report = fixer.analyze(fixed)
        assert len(verify_report.fixes) == 0