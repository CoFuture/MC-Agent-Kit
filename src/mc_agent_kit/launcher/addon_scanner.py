"""
Addon 扫描模块

扫描 MC Studio 的 Addon 目录，提取 Addon 信息。
"""

import json
import os
from dataclasses import dataclass, field


@dataclass
class PackInfo:
    """资源包/行为包信息"""
    dir_name: str
    uuid: str
    version: list[int] = field(default_factory=lambda: [0, 0, 1])


@dataclass
class AddonInfo:
    """Addon 完整信息"""
    id: str
    name: str
    path: str
    behavior_packs: list[PackInfo] = field(default_factory=list)
    resource_packs: list[PackInfo] = field(default_factory=list)


def scan_addon(addon_path: str) -> AddonInfo | None:
    """
    扫描单个 Addon 目录，提取信息。

    Args:
        addon_path: Addon 目录路径

    Returns:
        AddonInfo 对象，如果扫描失败返回 None
    """
    if not os.path.isdir(addon_path):
        return None

    addon_id = os.path.basename(addon_path)
    info = AddonInfo(
        id=addon_id,
        name=addon_id,
        path=addon_path,
    )

    # 读取 work.mcscfg 获取名称
    mcscfg_path = os.path.join(addon_path, "work.mcscfg")
    if os.path.exists(mcscfg_path):
        try:
            with open(mcscfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            info.name = cfg.get("Name", addon_id)
        except (OSError, json.JSONDecodeError):
            pass

    # 扫描子目录
    for entry in os.listdir(addon_path):
        entry_path = os.path.join(addon_path, entry)
        if not os.path.isdir(entry_path):
            continue

        manifest_path = os.path.join(entry_path, "pack_manifest.json")
        if not os.path.exists(manifest_path):
            continue

        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)

            header = manifest.get("header", {})
            pack_uuid = header.get("uuid", "")
            pack_version = header.get("version", [0, 0, 1])

            pack_info = PackInfo(
                dir_name=entry,
                uuid=pack_uuid,
                version=pack_version,
            )

            if entry.startswith("behavior_pack"):
                info.behavior_packs.append(pack_info)
            elif entry.startswith("resource_pack"):
                info.resource_packs.append(pack_info)

        except (OSError, json.JSONDecodeError):
            continue

    return info


def list_addons(addon_dir: str) -> list[AddonInfo]:
    """
    扫描 Addon 目录，返回所有 Addon 信息列表。

    Args:
        addon_dir: Addon 根目录路径 (如 MCStudio/work/{account}/Cpp/AddOn)

    Returns:
        AddonInfo 列表
    """
    addons = []
    if not os.path.exists(addon_dir):
        return addons

    for d in os.listdir(addon_dir):
        addon_path = os.path.join(addon_dir, d)
        if os.path.isdir(addon_path):
            addon_info = scan_addon(addon_path)
            if addon_info:
                addons.append(addon_info)

    return addons
