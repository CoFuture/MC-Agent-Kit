"""
项目创建器

提供 Addon 项目创建和管理功能。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import json
import uuid


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
            resource_pack_path = project_path / "resource_pack"
        else:
            behavior_pack_path = project.behavior_pack_path
            resource_pack_path = project.resource_pack_path
        
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
    ) -> list[Path]:
        """添加物品"""
        raise NotImplementedError("物品创建功能将在后续迭代中实现")
    
    def add_block(
        self,
        name: str,
        project: AddonProject | Path | str,
    ) -> list[Path]:
        """添加方块"""
        raise NotImplementedError("方块创建功能将在后续迭代中实现")
    
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