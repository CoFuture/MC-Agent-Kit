"""
项目创建器

提供 Addon 项目创建和管理功能。
"""

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class AddonProject:
    """Addon 项目信息"""
    name: str
    path: Path
    behavior_pack_path: Path
    resource_pack_path: Path


class ProjectCreator:
    """
    项目创建器

    用于创建标准 Addon 项目结构。

    使用示例:
        creator = ProjectCreator()
        project = creator.create_project("my-addon")
        creator.add_entity("Dragon", project)
    """

    def __init__(self, template_dir: Path | None = None):
        """
        初始化项目创建器

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = template_dir

    def create_project(
        self,
        name: str,
        path: Path | str = ".",
        template: Literal["empty", "entity", "item", "block"] = "empty",
        force: bool = False,
    ) -> AddonProject:
        """
        创建 Addon 项目

        Args:
            name: 项目名称
            path: 项目路径
            template: 项目模板
            force: 是否覆盖已存在的项目

        Returns:
            创建的项目信息

        Raises:
            FileExistsError: 项目已存在且 force=False
        """
        project_path = Path(path) / name

        if project_path.exists() and not force:
            raise FileExistsError(f"项目已存在: {project_path}")

        # 创建目录结构
        behavior_pack_path = project_path / "behavior_pack"
        resource_pack_path = project_path / "resource_pack"

        behavior_pack_path.mkdir(parents=True, exist_ok=True)
        resource_pack_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (behavior_pack_path / "scripts").mkdir(exist_ok=True)
        (resource_pack_path / "textures").mkdir(exist_ok=True)

        # 创建清单文件
        self._create_manifests(name, behavior_pack_path, resource_pack_path)

        return AddonProject(
            name=name,
            path=project_path,
            behavior_pack_path=behavior_pack_path,
            resource_pack_path=resource_pack_path,
        )

    def add_entity(
        self,
        name: str,
        project: AddonProject | Path | str,
        template: str = "default",
    ) -> list[Path]:
        """
        添加实体

        Args:
            name: 实体名称
            project: 项目路径或 AddonProject 对象
            template: 实体模板

        Returns:
            创建的文件路径列表
        """
        if isinstance(project, (str, Path)):
            project_path = Path(project)
            behavior_pack_path = project_path / "behavior_pack"
            project_path / "resource_pack"
        else:
            behavior_pack_path = project.behavior_pack_path

        created_files = []

        # 创建实体定义文件
        entities_dir = behavior_pack_path / "entities"
        entities_dir.mkdir(exist_ok=True)

        entity_file = entities_dir / f"{name.lower()}.json"
        entity_content = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {
                    "identifier": f"custom:{name.lower()}",
                    "is_spawnable": True,
                    "is_summonable": True,
                },
                "component_groups": {},
                "components": {},
            }
        }
        entity_file.write_text(json.dumps(entity_content, indent=2))
        created_files.append(entity_file)

        return created_files

    def add_item(
        self,
        name: str,
        project: AddonProject | Path | str,
        template: str = "default",
    ) -> list[Path]:
        """
        添加物品

        Args:
            name: 物品名称
            project: 项目路径或 AddonProject 对象
            template: 物品模板

        Returns:
            创建的文件路径列表
        """
        if isinstance(project, (str, Path)):
            project_path = Path(project)
            behavior_pack_path = project_path / "behavior_pack"
            resource_pack_path = project_path / "resource_pack"
        else:
            behavior_pack_path = project.behavior_pack_path
            resource_pack_path = project.resource_pack_path

        created_files = []

        # 创建物品定义文件
        items_dir = behavior_pack_path / "items"
        items_dir.mkdir(exist_ok=True)

        item_file = items_dir / f"{name.lower()}.json"
        item_content = {
            "format_version": "1.16.0",
            "minecraft:item": {
                "description": {
                    "identifier": f"custom:{name.lower()}",
                    "category": "Items",
                },
                "components": {
                    "minecraft:icon": f"custom:{name.lower()}",
                    "minecraft:creative_group": "itemGroup.name.items",
                },
            },
        }
        item_file.write_text(json.dumps(item_content, indent=2))
        created_files.append(item_file)

        # 创建物品脚本
        scripts_dir = behavior_pack_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        script_file = scripts_dir / f"{name.lower()}_item.py"
        script_content = self._generate_item_script(name)
        script_file.write_text(script_content)
        created_files.append(script_file)

        # 创建纹理占位符说明
        textures_dir = resource_pack_path / "textures"
        textures_dir.mkdir(exist_ok=True)
        items_textures_dir = textures_dir / "items"
        items_textures_dir.mkdir(exist_ok=True)

        # 创建纹理定义文件
        textures_json = resource_pack_path / "textures" / "item_texture.json"
        if not textures_json.exists():
            texture_def = {
                "resource_pack_name": "pack",
                "texture_name": "atlas.items",
                "texture_data": {
                    name.lower(): {
                        "textures": f"textures/items/{name.lower()}"
                    }
                },
            }
            textures_json.write_text(json.dumps(texture_def, indent=2))
            created_files.append(textures_json)

        return created_files

    def add_block(
        self,
        name: str,
        project: AddonProject | Path | str,
        template: str = "default",
    ) -> list[Path]:
        """
        添加方块

        Args:
            name: 方块名称
            project: 项目路径或 AddonProject 对象
            template: 方块模板

        Returns:
            创建的文件路径列表
        """
        if isinstance(project, (str, Path)):
            project_path = Path(project)
            behavior_pack_path = project_path / "behavior_pack"
            resource_pack_path = project_path / "resource_pack"
        else:
            behavior_pack_path = project.behavior_pack_path
            resource_pack_path = project.resource_pack_path

        created_files = []

        # 创建方块定义文件
        blocks_dir = behavior_pack_path / "blocks"
        blocks_dir.mkdir(exist_ok=True)

        block_file = blocks_dir / f"{name.lower()}.json"
        block_content = {
            "format_version": "1.16.0",
            "minecraft:block": {
                "description": {
                    "identifier": f"custom:{name.lower()}",
                },
                "components": {
                    "minecraft:destroy_time": 1.0,
                    "minecraft:explosion_resistance": 1.0,
                    "minecraft:friction": 0.6,
                    "minecraft:light_emission": 0,
                    "minecraft:light_dampening": 15,
                    "minecraft:map_color": "#FFFFFF",
                    "minecraft:geometry": f"geometry.{name.lower()}",
                },
            },
        }
        block_file.write_text(json.dumps(block_content, indent=2))
        created_files.append(block_file)

        # 创建方块脚本
        scripts_dir = behavior_pack_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        script_file = scripts_dir / f"{name.lower()}_block.py"
        script_content = self._generate_block_script(name)
        script_file.write_text(script_content)
        created_files.append(script_file)

        # 创建几何模型
        models_dir = resource_pack_path / "models"
        models_dir.mkdir(exist_ok=True)
        entity_dir = models_dir / "entity"
        entity_dir.mkdir(exist_ok=True)

        geo_file = entity_dir / f"{name.lower()}.geo.json"
        geo_content = self._generate_block_geometry(name)
        geo_file.write_text(json.dumps(geo_content, indent=2))
        created_files.append(geo_file)

        # 创建纹理占位符
        textures_dir = resource_pack_path / "textures"
        textures_dir.mkdir(exist_ok=True)
        blocks_textures_dir = textures_dir / "blocks"
        blocks_textures_dir.mkdir(exist_ok=True)

        return created_files

    def _generate_item_script(self, name: str) -> str:
        """生成物品脚本"""
        return f'''# -*- coding: utf-8 -*-
"""
{name} 物品逻辑

使用 ModSDK API 实现物品功能。
"""

from mod.common import minecraftEnum
from mod.common.minecraftEnum import ItemUseType


def register_item(system, item_name="{name.lower()}"):
    """
    注册物品事件监听

    Args:
        system: 游戏系统实例
        item_name: 物品名称
    """

    def on_item_use(args):
        """物品使用事件"""
        player_id = args["playerId"]
        item_stack = args["itemStack"]

        # TODO: 实现物品使用逻辑
        print(f"{{item_name}} used by player: {{player_id}}")

    # 注册事件监听
    system.DefineEvent("OnItemUse")
    system.ListenForEvent("OnItemUse", on_item_use)


def on_server_create(system):
    """服务端创建时调用"""
    register_item(system)
'''

    def _generate_block_script(self, name: str) -> str:
        """生成方块脚本"""
        return f'''# -*- coding: utf-8 -*-
"""
{name} 方块逻辑

使用 ModSDK API 实现方块功能。
"""

from mod.common import minecraftEnum


def register_block(system, block_name="{name.lower()}"):
    """
    注册方块事件监听

    Args:
        system: 游戏系统实例
        block_name: 方块名称
    """

    def on_block_placed(args):
        """方块放置事件"""
        block_pos = args["blockPos"]
        player_id = args.get("playerId")

        # TODO: 实现方块放置逻辑
        print(f"{{block_name}} placed at: {{block_pos}}")

    def on_block_destroyed(args):
        """方块破坏事件"""
        block_pos = args["blockPos"]

        # TODO: 实现方块破坏逻辑
        print(f"{{block_name}} destroyed at: {{block_pos}}")

    # 注册事件监听
    system.DefineEvent("OnBlockPlaced")
    system.DefineEvent("OnBlockDestroyed")
    system.ListenForEvent("OnBlockPlaced", on_block_placed)
    system.ListenForEvent("OnBlockDestroyed", on_block_destroyed)


def on_server_create(system):
    """服务端创建时调用"""
    register_block(system)
'''

    def _generate_block_geometry(self, name: str) -> dict:
        """生成方块几何模型"""
        return {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": f"geometry.{name.lower()}",
                        "texture_width": 16,
                        "texture_height": 16,
                    },
                    "bones": [
                        {
                            "name": name.lower(),
                            "pivot": [0, 0, 0],
                            "cubes": [
                                {
                                    "origin": [0, 0, 0],
                                    "size": [16, 16, 16],
                                    "uv": [0, 0],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    def _create_manifests(
        self,
        name: str,
        behavior_pack_path: Path,
        resource_pack_path: Path,
    ) -> None:
        """创建清单文件"""
        bp_uuid = str(uuid.uuid4())
        rp_uuid = str(uuid.uuid4())

        # Behavior Pack manifest
        bp_manifest = {
            "format_version": 2,
            "header": {
                "name": name,
                "description": f"{name} Behavior Pack",
                "uuid": bp_uuid,
                "version": [1, 0, 0],
                "min_engine_version": [1, 16, 0],
            },
            "modules": [
                {
                    "type": "data",
                    "uuid": str(uuid.uuid4()),
                    "version": [1, 0, 0],
                }
            ],
        }

        (behavior_pack_path / "manifest.json").write_text(
            json.dumps(bp_manifest, indent=2)
        )

        # Resource Pack manifest
        rp_manifest = {
            "format_version": 2,
            "header": {
                "name": f"{name} Resources",
                "description": f"{name} Resource Pack",
                "uuid": rp_uuid,
                "version": [1, 0, 0],
                "min_engine_version": [1, 16, 0],
            },
            "modules": [
                {
                    "type": "resources",
                    "uuid": str(uuid.uuid4()),
                    "version": [1, 0, 0],
                }
            ],
        }

        (resource_pack_path / "manifest.json").write_text(
            json.dumps(rp_manifest, indent=2)
        )
