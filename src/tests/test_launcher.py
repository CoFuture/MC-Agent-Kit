"""
测试 addon_scanner 模块
"""

import json
import os
import tempfile

from mc_agent_kit.launcher.addon_scanner import (
    list_addons,
    scan_addon,
)


class TestScanAddon:
    """测试 scan_addon 函数"""

    def test_scan_nonexistent_directory(self):
        """测试扫描不存在的目录"""
        result = scan_addon("/nonexistent/path")
        assert result is None

    def test_scan_empty_directory(self):
        """测试扫描空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_addon(tmpdir)
            assert result is not None
            assert result.id == os.path.basename(tmpdir)
            assert result.name == result.id
            assert len(result.behavior_packs) == 0
            assert len(result.resource_packs) == 0

    def test_scan_with_mcscfg(self):
        """测试扫描包含 work.mcscfg 的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 mcscfg 文件
            mcscfg = {"Name": "Test Addon"}
            with open(os.path.join(tmpdir, "work.mcscfg"), "w", encoding="utf-8") as f:
                json.dump(mcscfg, f)

            result = scan_addon(tmpdir)
            assert result is not None
            assert result.name == "Test Addon"

    def test_scan_with_behavior_pack(self):
        """测试扫描包含 behavior_pack 的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 behavior_pack 目录
            bp_dir = os.path.join(tmpdir, "behavior_pack_TestMod")
            os.makedirs(bp_dir)

            # 创建 manifest
            manifest = {
                "header": {
                    "uuid": "test-uuid-bp",
                    "version": [1, 0, 0]
                }
            }
            with open(os.path.join(bp_dir, "pack_manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            result = scan_addon(tmpdir)
            assert result is not None
            assert len(result.behavior_packs) == 1
            assert result.behavior_packs[0].uuid == "test-uuid-bp"
            assert result.behavior_packs[0].version == [1, 0, 0]

    def test_scan_with_resource_pack(self):
        """测试扫描包含 resource_pack 的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 resource_pack 目录
            rp_dir = os.path.join(tmpdir, "resource_pack_TestMod")
            os.makedirs(rp_dir)

            # 创建 manifest
            manifest = {
                "header": {
                    "uuid": "test-uuid-rp",
                    "version": [1, 0, 0]
                }
            }
            with open(os.path.join(rp_dir, "pack_manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            result = scan_addon(tmpdir)
            assert result is not None
            assert len(result.resource_packs) == 1
            assert result.resource_packs[0].uuid == "test-uuid-rp"


class TestListAddons:
    """测试 list_addons 函数"""

    def test_list_empty_directory(self):
        """测试列出空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_addons(tmpdir)
            assert result == []

    def test_list_nonexistent_directory(self):
        """测试列出不存在的目录"""
        result = list_addons("/nonexistent/path")
        assert result == []

    def test_list_multiple_addons(self):
        """测试列出多个 Addon"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建两个 Addon 目录
            for i in range(2):
                addon_dir = os.path.join(tmpdir, f"addon_{i}")
                os.makedirs(addon_dir)

            result = list_addons(tmpdir)
            assert len(result) == 2
