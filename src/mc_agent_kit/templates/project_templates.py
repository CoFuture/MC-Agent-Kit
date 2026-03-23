"""
项目模板系统模块

提供实体开发模板、物品开发模板、方块开发模板、UI 开发模板、网络同步模板等。

迭代 #57: Agent 技能增强与 ModSDK 深度集成
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TemplateType(Enum):
    """模板类型枚举"""

    # 实体模板
    ENTITY_BASIC = "entity_basic"  # 基础实体模板
    ENTITY_COMPLEX = "entity_complex"  # 复杂实体模板（带 AI）
    ENTITY_NPC = "entity_npc"  # NPC 实体模板

    # 物品模板
    ITEM_CONSUMABLE = "item_consumable"  # 消耗品模板
    ITEM_TOOL = "item_tool"  # 工具模板
    ITEM_WEAPON = "item_weapon"  # 武器模板
    ITEM_ARMOR = "item_armor"  # 护甲模板

    # 方块模板
    BLOCK_BASIC = "block_basic"  # 基础方块模板
    BLOCK_INTERACTIVE = "block_interactive"  # 交互方块模板
    BLOCK_FUNCTIONAL = "block_functional"  # 功能方块模板

    # UI 模板
    UI_FORM = "ui_form"  # UI 表单模板
    UI_DIALOG = "ui_dialog"  # UI 对话框模板
    UI_HUD = "ui_hud"  # UI HUD 模板

    # 网络模板
    NET_SYNC = "net_sync"  # 网络同步模板
    NET_EVENT = "net_event"  # 网络事件模板

    # 项目模板
    PROJECT_EMPTY = "project_empty"  # 空项目模板
    PROJECT_FULL = "project_full"  # 完整项目模板


@dataclass
class TemplateFile:
    """模板文件"""

    path: str  # 相对路径
    content: str
    description: str = ""
    is_template: bool = False  # 是否需要渲染


@dataclass
class TemplateConfig:
    """模板配置"""

    template_type: TemplateType
    name: str
    description: str
    files: list[TemplateFile]
    variables: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class GeneratedProject:
    """生成的项目"""

    name: str
    template_type: TemplateType
    files: dict[str, str]  # path -> content
    structure: dict[str, Any]  # 目录结构
    notes: list[str] = field(default_factory=list)


class ProjectTemplates:
    """
    项目模板系统

    管理和生成各种项目模板。
    """

    # 模板注册表
    TEMPLATES: dict[TemplateType, TemplateConfig] = {}

    def __init__(self):
        """初始化项目模板系统"""
        self._register_builtin_templates()

    def get_template(self, template_type: TemplateType) -> Optional[TemplateConfig]:
        """
        获取模板配置

        Args:
            template_type: 模板类型

        Returns:
            模板配置，不存在返回 None
        """
        return self.TEMPLATES.get(template_type)

    def list_templates(self) -> list[TemplateConfig]:
        """
        列出所有模板

        Returns:
            模板配置列表
        """
        return list(self.TEMPLATES.values())

    def generate(
        self,
        template_type: TemplateType,
        name: str,
        variables: Optional[dict[str, Any]] = None,
        output_dir: Optional[str] = None,
    ) -> Optional[GeneratedProject]:
        """
        生成项目

        Args:
            template_type: 模板类型
            name: 项目名称
            variables: 模板变量
            output_dir: 输出目录

        Returns:
            生成的项目
        """
        template = self.get_template(template_type)
        if not template:
            return None

        variables = variables or {}
        variables["PROJECT_NAME"] = name
        variables["PROJECT_ID"] = name.lower().replace(" ", "_")

        files: dict[str, str] = {}
        structure: dict[str, Any] = {}

        for template_file in template.files:
            # 渲染内容
            content = template_file.content
            if template_file.is_template:
                content = self._render_template(content, variables)

            # 解析路径
            file_path = self._render_template(template_file.path, variables)
            files[file_path] = content

            # 构建目录结构
            self._add_to_structure(structure, file_path)

        # 生成目录结构
        generated = GeneratedProject(
            name=name,
            template_type=template_type,
            files=files,
            structure=structure,
            notes=template.notes.copy(),
        )

        # 如果指定了输出目录，写入文件
        if output_dir:
            self._write_files(output_dir, files)

        return generated

    # ==================== 私有方法 ====================

    def _register_builtin_templates(self) -> None:
        """注册内置模板"""

        # 注册空项目模板
        self.TEMPLATES[TemplateType.PROJECT_EMPTY] = self._create_empty_project_template()

        # 注册完整项目模板
        self.TEMPLATES[TemplateType.PROJECT_FULL] = self._create_full_project_template()

        # 注册实体模板
        self.TEMPLATES[TemplateType.ENTITY_BASIC] = self._create_basic_entity_template()
        self.TEMPLATES[TemplateType.ENTITY_COMPLEX] = self._create_complex_entity_template()
        self.TEMPLATES[TemplateType.ENTITY_NPC] = self._create_npc_entity_template()

        # 注册物品模板
        self.TEMPLATES[TemplateType.ITEM_CONSUMABLE] = self._create_consumable_item_template()
        self.TEMPLATES[TemplateType.ITEM_TOOL] = self._create_tool_item_template()
        self.TEMPLATES[TemplateType.ITEM_WEAPON] = self._create_weapon_item_template()
        self.TEMPLATES[TemplateType.ITEM_ARMOR] = self._create_armor_item_template()

        # 注册方块模板
        self.TEMPLATES[TemplateType.BLOCK_BASIC] = self._create_basic_block_template()
        self.TEMPLATES[TemplateType.BLOCK_INTERACTIVE] = self._create_interactive_block_template()
        self.TEMPLATES[TemplateType.BLOCK_FUNCTIONAL] = self._create_functional_block_template()

        # 注册 UI 模板
        self.TEMPLATES[TemplateType.UI_FORM] = self._create_form_ui_template()
        self.TEMPLATES[TemplateType.UI_DIALOG] = self._create_dialog_ui_template()
        self.TEMPLATES[TemplateType.UI_HUD] = self._create_hud_ui_template()

        # 注册网络模板
        self.TEMPLATES[TemplateType.NET_SYNC] = self._create_net_sync_template()
        self.TEMPLATES[TemplateType.NET_EVENT] = self._create_net_event_template()

    def _render_template(self, template: str, variables: dict[str, Any]) -> str:
        """渲染模板"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def _add_to_structure(self, structure: dict[str, Any], path: str) -> None:
        """添加文件到目录结构"""
        parts = path.split("/")
        current = structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = None  # 文件
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

    def _write_files(self, output_dir: str, files: dict[str, str]) -> None:
        """写入文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for file_path, content in files.items():
            full_path = output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

    # ==================== 模板创建方法 ====================

    def _create_empty_project_template(self) -> TemplateConfig:
        """创建空项目模板"""
        return TemplateConfig(
            template_type=TemplateType.PROJECT_EMPTY,
            name="空项目",
            description="创建一个空的 Addon 项目结构",
            files=[
                TemplateFile(
                    path="{{PROJECT_ID}}/behavior_pack/manifest.json",
                    content='''{
    "format_version": 2,
    "header": {
        "name": "{{PROJECT_NAME}}",
        "description": "{{PROJECT_NAME}} Addon",
        "uuid": "00000000-0000-0000-0000-000000000001",
        "version": [1, 0, 0],
        "min_engine_version": [1, 16, 0]
    },
    "modules": [
        {
            "type": "data",
            "uuid": "00000000-0000-0000-0000-000000000002",
            "version": [1, 0, 0]
        }
    ]
}''',
                    description="Behavior Pack 清单文件",
                ),
                TemplateFile(
                    path="{{PROJECT_ID}}/resource_pack/manifest.json",
                    content='''{
    "format_version": 2,
    "header": {
        "name": "{{PROJECT_NAME}} Resources",
        "description": "{{PROJECT_NAME}} Resource Pack",
        "uuid": "00000000-0000-0000-0000-000000000003",
        "version": [1, 0, 0],
        "min_engine_version": [1, 16, 0]
    },
    "modules": [
        {
            "type": "resources",
            "uuid": "00000000-0000-0000-0000-000000000004",
            "version": [1, 0, 0]
        }
    ]
}''',
                    description="Resource Pack 清单文件",
                ),
                TemplateFile(
                    path="{{PROJECT_ID}}/behavior_pack/scripts/main.py",
                    content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} - Main Script
"""

from mod.common.mod import Mod
from mod.common.system.modEvent import ModEvent


class MainMod:
    """主模块类"""
    
    def __init__(self, system):
        self.system = system
        print("{{PROJECT_NAME}} loaded!")
    
    def destroy(self):
        """清理资源"""
        pass


def create(system):
    """创建模块实例"""
    return MainMod(system)
''',
                    description="主脚本文件",
                ),
            ],
            notes=[
                "请修改 manifest.json 中的 UUID",
                "在 behavior_pack 中添加实体、物品、方块等配置",
                "在 resource_pack 中添加纹理、模型等资源",
            ],
        )

    def _create_full_project_template(self) -> TemplateConfig:
        """创建完整项目模板"""
        template = self._create_empty_project_template()
        template.template_type = TemplateType.PROJECT_FULL
        template.name = "完整项目"
        template.description = "创建一个包含示例代码的完整 Addon 项目"

        # 添加额外文件
        template.files.extend([
            TemplateFile(
                path="{{PROJECT_ID}}/behavior_pack/scripts/events.py",
                content='''# -*- coding: utf-8 -*-
"""
事件处理模块
"""

from mod.common.system.modEvent import ModEvent


class EventHandler:
    """事件处理器"""
    
    def __init__(self, system):
        self.system = system
    
    def on_player_joined(self, args):
        """玩家加入事件"""
        player_id = args.get("id")
        print(f"Player joined: {player_id}")
    
    def on_player_left(self, args):
        """玩家离开事件"""
        player_id = args.get("id")
        print(f"Player left: {player_id}")
    
    def on_server_chat(self, args):
        """服务器聊天事件"""
        message = args.get("message")
        player_id = args.get("playerId")
        print(f"Chat: {message}")
    
    def register(self):
        """注册事件监听器"""
        self.system.DefineEvent("OnPlayerJoined", self.on_player_joined)
        self.system.DefineEvent("OnPlayerLeft", self.on_player_left)
        self.system.DefineEvent("OnServerChat", self.on_server_chat)


def create(system):
    """创建事件处理器实例"""
    handler = EventHandler(system)
    handler.register()
    return handler
''',
                description="事件处理模块",
            ),
            TemplateFile(
                path="{{PROJECT_ID}}/behavior_pack/scripts/utils.py",
                content='''# -*- coding: utf-8 -*-
"""
工具函数模块
"""


def get_distance(pos1, pos2):
    """计算两点距离"""
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    dz = pos1[2] - pos2[2]
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def format_pos(pos):
    """格式化坐标"""
    return f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})"


def clamp(value, min_val, max_val):
    """限制值范围"""
    return max(min_val, min(max_val, value))
''',
                description="工具函数模块",
            ),
        ])
        return template

    def _create_basic_entity_template(self) -> TemplateConfig:
        """创建基础实体模板"""
        return TemplateConfig(
            template_type=TemplateType.ENTITY_BASIC,
            name="基础实体",
            description="创建一个基础的实体模板",
            files=[
                TemplateFile(
                    path="entities/{{PROJECT_ID}}.json",
                    content='''{
    "format_version": "1.16.0",
    "minecraft:entity": {
        "description": {
            "identifier": "custom:{{PROJECT_ID}}",
            "is_spawnable": true,
            "is_summonable": true
        },
        "component_groups": {},
        "components": {
            "minecraft:type_family": {
                "family": ["mob"]
            },
            "minecraft:health": {
                "value": 20,
                "max": 20
            },
            "minecraft:movement": {
                "value": 0.25
            },
            "minecraft:collision_box": {
                "width": 0.6,
                "height": 1.8
            },
            "minecraft:physics": {}
        },
        "events": {}
    }
}''',
                    description="实体配置文件",
                ),
                TemplateFile(
                    path="scripts/{{PROJECT_ID}}.py",
                    content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} 实体脚本
"""

from mod.common.mod import Mod


class {{PROJECT_NAME}}Entity:
    """实体管理类"""
    
    ENTITY_TYPE = "custom:{{PROJECT_ID}}"
    
    def __init__(self, system):
        self.system = system
    
    def on_entity_added(self, args):
        """实体添加时调用"""
        entity_id = args.get("id")
        # 初始化逻辑
        pass
    
    def on_entity_removed(self, args):
        """实体移除时调用"""
        entity_id = args.get("id")
        # 清理逻辑
        pass


def create(system):
    return {{PROJECT_NAME}}Entity(system)
''',
                    description="实体脚本",
                    is_template=True,
                ),
            ],
            notes=[
                "修改实体属性（生命值、速度等）",
                "添加更多组件以增强实体功能",
                "创建纹理和模型文件",
            ],
        )

    def _create_complex_entity_template(self) -> TemplateConfig:
        """创建复杂实体模板"""
        template = self._create_basic_entity_template()
        template.template_type = TemplateType.ENTITY_COMPLEX
        template.name = "复杂实体"
        template.description = "创建一个带 AI 行为的复杂实体模板"

        # 添加 AI 行为脚本
        template.files.append(
            TemplateFile(
                path="scripts/{{PROJECT_ID}}_ai.py",
                content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} AI 行为模块
"""

import random


class {{PROJECT_NAME}}AI:
    """AI 行为控制器"""
    
    def __init__(self, system, entity_id):
        self.system = system
        self.entity_id = entity_id
        self.state = "idle"
        self.target = None
    
    def update(self):
        """更新 AI 状态"""
        if self.state == "idle":
            self._on_idle()
        elif self.state == "wander":
            self._on_wander()
        elif self.state == "chase":
            self._on_chase()
        elif self.state == "attack":
            self._on_attack()
    
    def _on_idle(self):
        """闲置状态"""
        if random.random() < 0.1:
            self.state = "wander"
    
    def _on_wander(self):
        """漫游状态"""
        # 实现漫游逻辑
        pass
    
    def _on_chase(self):
        """追逐状态"""
        if self.target is None:
            self.state = "idle"
            return
        # 实现追逐逻辑
        pass
    
    def _on_attack(self):
        """攻击状态"""
        # 实现攻击逻辑
        pass
    
    def set_target(self, target_id):
        """设置目标"""
        self.target = target_id
        self.state = "chase"
''',
                description="AI 行为模块",
                is_template=True,
            )
        )
        return template

    def _create_npc_entity_template(self) -> TemplateConfig:
        """创建 NPC 实体模板"""
        template = self._create_basic_entity_template()
        template.template_type = TemplateType.ENTITY_NPC
        template.name = "NPC 实体"
        template.description = "创建一个可交互的 NPC 实体模板"

        template.files.append(
            TemplateFile(
                path="scripts/{{PROJECT_ID}}_dialog.py",
                content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} NPC 对话模块
"""


class {{PROJECT_NAME}}Dialog:
    """NPC 对话管理"""
    
    def __init__(self, system, entity_id):
        self.system = system
        self.entity_id = entity_id
        self.dialog_tree = {
            "greeting": {
                "text": "你好，旅行者！",
                "options": [
                    {"text": "你好", "next": "intro"},
                    {"text": "再见", "next": "goodbye"}
                ]
            },
            "intro": {
                "text": "我是这个村庄的守卫。",
                "options": [
                    {"text": "村庄有什么有趣的地方吗？", "next": "village_info"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "village_info": {
                "text": "村东有个神秘的洞穴，你可以去看看。",
                "options": [
                    {"text": "谢谢", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "text": "再见！",
                "options": []
            }
        }
        self.current_node = "greeting"
    
    def get_current_dialog(self):
        """获取当前对话"""
        return self.dialog_tree.get(self.current_node, {})
    
    def select_option(self, option_index):
        """选择对话选项"""
        dialog = self.get_current_dialog()
        options = dialog.get("options", [])
        if option_index < len(options):
            self.current_node = options[option_index].get("next", "greeting")
        return self.get_current_dialog()
    
    def reset(self):
        """重置对话"""
        self.current_node = "greeting"
''',
                description="NPC 对话模块",
                is_template=True,
            )
        )
        return template

    def _create_consumable_item_template(self) -> TemplateConfig:
        """创建消耗品物品模板"""
        return TemplateConfig(
            template_type=TemplateType.ITEM_CONSUMABLE,
            name="消耗品",
            description="创建一个可消耗的物品模板",
            files=[
                TemplateFile(
                    path="items/{{PROJECT_ID}}.json",
                    content='''{
    "format_version": "1.16.0",
    "minecraft:item": {
        "description": {
            "identifier": "custom:{{PROJECT_ID}}",
            "category": "Items"
        },
        "components": {
            "minecraft:food": {
                "nutrition": 4,
                "saturation_modifier": "normal",
                "can_always_eat": false
            },
            "minecraft:use_duration": 32,
            "minecraft:max_stack_size": 64
        }
    }
}''',
                    description="物品配置文件",
                ),
                TemplateFile(
                    path="scripts/{{PROJECT_ID}}.py",
                    content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} 消耗品脚本
"""

from mod.common.mod import Mod


class {{PROJECT_NAME}}Item:
    """消耗品管理类"""
    
    ITEM_ID = "custom:{{PROJECT_ID}}"
    
    def __init__(self, system):
        self.system = system
    
    def on_use_item(self, args):
        """使用物品时调用"""
        player_id = args.get("playerId")
        # 添加使用效果
        pass
    
    def register(self):
        """注册事件"""
        self.system.DefineEvent("OnUseItem", self.on_use_item)


def create(system):
    return {{PROJECT_NAME}}Item(system)
''',
                    description="物品脚本",
                    is_template=True,
                ),
            ],
        )

    def _create_tool_item_template(self) -> TemplateConfig:
        """创建工具物品模板"""
        return TemplateConfig(
            template_type=TemplateType.ITEM_TOOL,
            name="工具",
            description="创建一个工具物品模板",
            files=[
                TemplateFile(
                    path="items/{{PROJECT_ID}}.json",
                    content='''{
    "format_version": "1.16.0",
    "minecraft:item": {
        "description": {
            "identifier": "custom:{{PROJECT_ID}}",
            "category": "Items"
        },
        "components": {
            "minecraft:max_damage": 250,
            "minecraft:hand_equipped": true,
            "minecraft:max_stack_size": 1
        }
    }
}''',
                    description="工具配置文件",
                ),
            ],
        )

    def _create_weapon_item_template(self) -> TemplateConfig:
        """创建武器物品模板"""
        template = self._create_tool_item_template()
        template.template_type = TemplateType.ITEM_WEAPON
        template.name = "武器"
        template.description = "创建一个武器物品模板"
        return template

    def _create_armor_item_template(self) -> TemplateConfig:
        """创建护甲物品模板"""
        return TemplateConfig(
            template_type=TemplateType.ITEM_ARMOR,
            name="护甲",
            description="创建一个护甲物品模板",
            files=[
                TemplateFile(
                    path="items/{{PROJECT_ID}}_helmet.json",
                    content='''{
    "format_version": "1.16.0",
    "minecraft:item": {
        "description": {
            "identifier": "custom:{{PROJECT_ID}}_helmet",
            "category": "Items"
        },
        "components": {
            "minecraft:armor": {
                "protection": 4
            },
            "minecraft:wearable": {
                "slot": "slot.armor.head"
            },
            "minecraft:max_damage": 250,
            "minecraft:max_stack_size": 1
        }
    }
}''',
                    description="头盔配置文件",
                ),
            ],
        )

    def _create_basic_block_template(self) -> TemplateConfig:
        """创建基础方块模板"""
        return TemplateConfig(
            template_type=TemplateType.BLOCK_BASIC,
            name="基础方块",
            description="创建一个基础方块模板",
            files=[
                TemplateFile(
                    path="blocks/{{PROJECT_ID}}.json",
                    content='''{
    "format_version": "1.16.0",
    "minecraft:block": {
        "description": {
            "identifier": "custom:{{PROJECT_ID}}"
        },
        "components": {
            "minecraft:destroy_time": 1.0,
            "minecraft:explosion_resistance": 1.0,
            "minecraft:material_instances": {
                "*": {
                    "texture": "{{PROJECT_ID}}",
                    "render_method": "opaque"
                }
            }
        }
    }
}''',
                    description="方块配置文件",
                ),
            ],
        )

    def _create_interactive_block_template(self) -> TemplateConfig:
        """创建交互方块模板"""
        template = self._create_basic_block_template()
        template.template_type = TemplateType.BLOCK_INTERACTIVE
        template.name = "交互方块"
        template.description = "创建一个可交互的方块模板"

        template.files.append(
            TemplateFile(
                path="scripts/{{PROJECT_ID}}.py",
                content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} 交互方块脚本
"""

from mod.common.mod import Mod


class {{PROJECT_NAME}}Block:
    """交互方块管理类"""
    
    BLOCK_ID = "custom:{{PROJECT_ID}}"
    
    def __init__(self, system):
        self.system = system
    
    def on_use_block(self, args):
        """使用方块时调用"""
        player_id = args.get("playerId")
        block_pos = args.get("blockPos")
        # 交互逻辑
        pass
    
    def register(self):
        """注册事件"""
        self.system.DefineEvent("OnUseBlock", self.on_use_block)


def create(system):
    return {{PROJECT_NAME}}Block(system)
''',
                description="交互方块脚本",
                is_template=True,
            )
        )
        return template

    def _create_functional_block_template(self) -> TemplateConfig:
        """创建功能方块模板"""
        template = self._create_interactive_block_template()
        template.template_type = TemplateType.BLOCK_FUNCTIONAL
        template.name = "功能方块"
        template.description = "创建一个功能性方块模板"
        return template

    def _create_form_ui_template(self) -> TemplateConfig:
        """创建 UI 表单模板"""
        return TemplateConfig(
            template_type=TemplateType.UI_FORM,
            name="UI 表单",
            description="创建一个 UI 表单模板",
            files=[
                TemplateFile(
                    path="ui/{{PROJECT_ID}}_form.py",
                    content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} UI 表单模块
"""

from mod.common.mod import Mod


class {{PROJECT_NAME}}Form:
    """表单管理类"""
    
    def __init__(self, system):
        self.system = system
        self.ui_id = None
    
    def create(self, player_id):
        """创建表单"""
        # 创建 UI
        pass
    
    def on_button_click(self, args):
        """按钮点击事件"""
        button_name = args.get("buttonName")
        # 处理按钮点击
        pass
    
    def on_text_input(self, args):
        """文本输入事件"""
        text = args.get("text")
        # 处理文本输入
        pass
    
    def destroy(self):
        """销毁表单"""
        if self.ui_id:
            # 销毁 UI
            pass


def create(system):
    return {{PROJECT_NAME}}Form(system)
''',
                    description="UI 表单脚本",
                    is_template=True,
                ),
            ],
        )

    def _create_dialog_ui_template(self) -> TemplateConfig:
        """创建 UI 对话框模板"""
        template = self._create_form_ui_template()
        template.template_type = TemplateType.UI_DIALOG
        template.name = "UI 对话框"
        template.description = "创建一个 UI 对话框模板"
        return template

    def _create_hud_ui_template(self) -> TemplateConfig:
        """创建 HUD UI 模板"""
        return TemplateConfig(
            template_type=TemplateType.UI_HUD,
            name="UI HUD",
            description="创建一个 HUD UI 模板",
            files=[
                TemplateFile(
                    path="ui/{{PROJECT_ID}}_hud.py",
                    content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} HUD 模块
"""

from mod.common.mod import Mod


class {{PROJECT_NAME}}HUD:
    """HUD 管理类"""
    
    def __init__(self, system):
        self.system = system
        self.visible = True
    
    def show(self, player_id):
        """显示 HUD"""
        self.visible = True
        # 显示 UI
    
    def hide(self, player_id):
        """隐藏 HUD"""
        self.visible = False
        # 隐藏 UI
    
    def update(self, data):
        """更新 HUD 数据"""
        # 更新显示内容
        pass


def create(system):
    return {{PROJECT_NAME}}HUD(system)
''',
                    description="HUD 脚本",
                    is_template=True,
                ),
            ],
        )

    def _create_net_sync_template(self) -> TemplateConfig:
        """创建网络同步模板"""
        return TemplateConfig(
            template_type=TemplateType.NET_SYNC,
            name="网络同步",
            description="创建一个网络同步模板",
            files=[
                TemplateFile(
                    path="net/{{PROJECT_ID}}_sync.py",
                    content='''# -*- coding: utf-8 -*-
"""
{{PROJECT_NAME}} 网络同步模块
"""

from mod.common.mod import Mod


class {{PROJECT_NAME}}Sync:
    """网络同步管理类"""
    
    def __init__(self, system):
        self.system = system
    
    def sync_to_client(self, player_id, data):
        """同步数据到客户端"""
        # 发送数据到客户端
        pass
    
    def sync_to_server(self, data):
        """同步数据到服务器"""
        # 发送数据到服务器
        pass
    
    def on_client_receive(self, args):
        """客户端接收数据"""
        data = args.get("data")
        # 处理接收的数据
        pass
    
    def on_server_receive(self, args):
        """服务器接收数据"""
        player_id = args.get("playerId")
        data = args.get("data")
        # 处理接收的数据
        pass


def create(system):
    return {{PROJECT_NAME}}Sync(system)
''',
                    description="网络同步脚本",
                    is_template=True,
                ),
            ],
        )

    def _create_net_event_template(self) -> TemplateConfig:
        """创建网络事件模板"""
        template = self._create_net_sync_template()
        template.template_type = TemplateType.NET_EVENT
        template.name = "网络事件"
        template.description = "创建一个网络事件模板"
        return template


def create_project_templates() -> ProjectTemplates:
    """创建项目模板系统实例"""
    return ProjectTemplates()