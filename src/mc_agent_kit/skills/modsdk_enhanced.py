"""
ModSDK 增强技能模块

提供 ModSDK API 智能补全、事件监听器生成、实体/物品/方块模板生成等功能。

迭代 #57: Agent 技能增强与 ModSDK 深度集成
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ModSDKVersion(Enum):
    """ModSDK 版本枚举"""

    V1_0 = "1.0"
    V1_5 = "1.5"
    V2_0 = "2.0"
    V2_5 = "2.5"
    V3_0 = "3.0"
    LATEST = "latest"


class EntityType(Enum):
    """实体类型枚举"""

    PASSIVE = "passive"  # 被动生物
    HOSTILE = "hostile"  # 敌对生物
    NEUTRAL = "neutral"  # 中立生物
    BOSS = "boss"  # Boss
    NPC = "npc"  # NPC


class ItemType(Enum):
    """物品类型枚举"""

    CONSUMABLE = "consumable"  # 消耗品
    TOOL = "tool"  # 工具
    WEAPON = "weapon"  # 武器
    ARMOR = "armor"  # 护甲
    BLOCK_ITEM = "block_item"  # 方块物品
    SPECIAL = "special"  # 特殊物品


class BlockType(Enum):
    """方块类型枚举"""

    BASIC = "basic"  # 基础方块
    INTERACTIVE = "interactive"  # 交互方块
    FUNCTIONAL = "functional"  # 功能方块
    DECORATION = "decoration"  # 装饰方块


@dataclass
class BehaviorConfig:
    """行为配置"""

    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True


@dataclass
class ComponentConfig:
    """组件配置"""

    name: str
    namespace: str = "minecraft"
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedEntity:
    """生成的实体"""

    name: str
    identifier: str
    entity_type: EntityType
    behaviors: list[BehaviorConfig]
    components: list[ComponentConfig]
    entity_json: dict[str, Any]
    script_code: str
    resource_files: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class GeneratedItem:
    """生成的物品"""

    name: str
    identifier: str
    item_type: ItemType
    components: list[ComponentConfig]
    item_json: dict[str, Any]
    script_code: str
    resource_files: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class GeneratedBlock:
    """生成的方块"""

    name: str
    identifier: str
    block_type: BlockType
    components: list[ComponentConfig]
    block_json: dict[str, Any]
    script_code: str
    resource_files: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class EventListener:
    """事件监听器"""

    event_name: str
    namespace: str
    scope: str  # client/server
    callback_name: str
    parameters: list[str]
    code: str
    imports: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class APISuggestion:
    """API 建议"""

    api_name: str
    module: str
    description: str
    parameters: list[dict[str, Any]]
    return_type: str
    example_code: str
    relevance_score: float = 0.0


@dataclass
class ValidationResult:
    """验证结果"""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class ModSDKSkill:
    """
    ModSDK 增强技能

    提供 ModSDK API 智能补全、代码生成、配置验证等功能。
    """

    # 常用行为列表
    COMMON_BEHAVIORS = {
        "movement": {
            "description": "移动行为",
            "parameters": {
                "speed": {"type": "float", "default": 1.0, "description": "移动速度"},
                "jump_height": {"type": "float", "default": 1.0, "description": "跳跃高度"},
            },
        },
        "navigation": {
            "description": "导航行为",
            "parameters": {
                "can_walk": {"type": "bool", "default": True},
                "can_swim": {"type": "bool", "default": False},
                "can_fly": {"type": "bool", "default": False},
            },
        },
        "attack": {
            "description": "攻击行为",
            "parameters": {
                "damage": {"type": "float", "default": 1.0},
                "range": {"type": "float", "default": 1.0},
                "cooldown": {"type": "float", "default": 1.0},
            },
        },
        "target": {
            "description": "目标追踪行为",
            "parameters": {
                "target_types": {"type": "list", "default": ["player"]},
                "range": {"type": "float", "default": 16.0},
            },
        },
        "spawn": {
            "description": "生成行为",
            "parameters": {
                "spawn_weight": {"type": "int", "default": 100},
                "spawn_radius": {"type": "int", "default": 128},
            },
        },
    }

    # 常用组件列表
    COMMON_COMPONENTS = {
        "minecraft:type_family": {
            "description": "类型家族",
            "parameters": {"family": {"type": "list", "default": ["mob"]}},
        },
        "minecraft:health": {
            "description": "生命值",
            "parameters": {"value": {"type": "int", "default": 20}, "max": {"type": "int", "default": 20}},
        },
        "minecraft:movement": {
            "description": "移动速度",
            "parameters": {"value": {"type": "float", "default": 0.25}},
        },
        "minecraft:collision_box": {
            "description": "碰撞箱",
            "parameters": {
                "width": {"type": "float", "default": 0.6},
                "height": {"type": "float", "default": 1.8},
            },
        },
        "minecraft:physics": {
            "description": "物理属性",
            "parameters": {"has_gravity": {"type": "bool", "default": True}},
        },
        "minecraft:pushable": {
            "description": "可推动",
            "parameters": {
                "is_pushable": {"type": "bool", "default": True},
                "is_pushable_by_piston": {"type": "bool", "default": True},
            },
        },
        "minecraft:navigation.walk": {
            "description": "步行导航",
            "parameters": {"can_walk": {"type": "bool", "default": True}},
        },
        "minecraft:navigation.fly": {
            "description": "飞行导航",
            "parameters": {"can_fly": {"type": "bool", "default": True}},
        },
        "minecraft:navigation.swim": {
            "description": "游泳导航",
            "parameters": {"can_swim": {"type": "bool", "default": True}},
        },
    }

    # 常用事件列表
    COMMON_EVENTS = {
        "OnServerChat": {
            "scope": "server",
            "description": "服务器聊天事件",
            "parameters": ["args"],
        },
        "OnClientChat": {
            "scope": "client",
            "description": "客户端聊天事件",
            "parameters": ["args"],
        },
        "OnEntityAdded": {
            "scope": "server",
            "description": "实体添加事件",
            "parameters": ["args"],
        },
        "OnEntityRemoved": {
            "scope": "server",
            "description": "实体移除事件",
            "parameters": ["args"],
        },
        "OnPlayerJoined": {
            "scope": "server",
            "description": "玩家加入事件",
            "parameters": ["args"],
        },
        "OnPlayerLeft": {
            "scope": "server",
            "description": "玩家离开事件",
            "parameters": ["args"],
        },
        "OnDamage": {
            "scope": "server",
            "description": "伤害事件",
            "parameters": ["args"],
        },
        "OnDeath": {
            "scope": "server",
            "description": "死亡事件",
            "parameters": ["args"],
        },
        "OnAttack": {
            "scope": "server",
            "description": "攻击事件",
            "parameters": ["args"],
        },
        "OnUseItem": {
            "scope": "server",
            "description": "使用物品事件",
            "parameters": ["args"],
        },
        "OnUseItemOn": {
            "scope": "server",
            "description": "对方块使用物品事件",
            "parameters": ["args"],
        },
        "OnPlaceBlock": {
            "scope": "server",
            "description": "放置方块事件",
            "parameters": ["args"],
        },
        "OnDestroyBlock": {
            "scope": "server",
            "description": "破坏方块事件",
            "parameters": ["args"],
        },
        "OnUpdate": {
            "scope": "both",
            "description": "更新事件",
            "parameters": ["args"],
        },
        "OnTick": {
            "scope": "both",
            "description": "Tick 事件",
            "parameters": ["args"],
        },
        "OnFrame": {
            "scope": "client",
            "description": "帧更新事件",
            "parameters": ["args"],
        },
        "OnKeyDown": {
            "scope": "client",
            "description": "按键按下事件",
            "parameters": ["args"],
        },
        "OnKeyUp": {
            "scope": "client",
            "description": "按键抬起事件",
            "parameters": ["args"],
        },
    }

    def __init__(self, version: ModSDKVersion = ModSDKVersion.LATEST):
        """
        初始化 ModSDK 技能

        Args:
            version: ModSDK 版本
        """
        self.version = version
        self._api_cache: dict[str, APISuggestion] = {}

    def generate_entity(
        self,
        name: str,
        entity_type: EntityType = EntityType.PASSIVE,
        behaviors: Optional[list[dict[str, Any]]] = None,
        components: Optional[list[dict[str, Any]]] = None,
        namespace: str = "custom",
    ) -> GeneratedEntity:
        """
        生成实体配置

        Args:
            name: 实体名称
            entity_type: 实体类型
            behaviors: 行为配置列表
            components: 组件配置列表
            namespace: 命名空间

        Returns:
            生成的实体配置
        """
        identifier = f"{namespace}:{name.lower().replace(' ', '_')}"
        behavior_configs: list[BehaviorConfig] = []
        component_configs: list[ComponentConfig] = []
        notes: list[str] = []

        # 处理行为
        if behaviors:
            for b in behaviors:
                behavior_name = b.get("name", "")
                if behavior_name in self.COMMON_BEHAVIORS:
                    behavior_configs.append(
                        BehaviorConfig(
                            name=behavior_name,
                            parameters=b.get("parameters", {}),
                            priority=b.get("priority", 0),
                            enabled=b.get("enabled", True),
                        )
                    )
                else:
                    notes.append(f"未知行为: {behavior_name}")

        # 处理组件
        if components:
            for c in components:
                comp_name = c.get("name", "")
                if comp_name in self.COMMON_COMPONENTS:
                    component_configs.append(
                        ComponentConfig(
                            name=comp_name,
                            namespace=c.get("namespace", "minecraft"),
                            parameters=c.get("parameters", {}),
                        )
                    )
                else:
                    notes.append(f"未知组件: {comp_name}")

        # 根据实体类型添加默认组件
        if not any(c.name == "minecraft:type_family" for c in component_configs):
            default_families = self._get_default_families(entity_type)
            component_configs.append(
                ComponentConfig(
                    name="minecraft:type_family",
                    parameters={"family": default_families},
                )
            )

        # 生成 JSON 配置
        entity_json = self._generate_entity_json(
            identifier, entity_type, behavior_configs, component_configs
        )

        # 生成脚本代码
        script_code = self._generate_entity_script(identifier, entity_type)

        # 生成资源文件
        resource_files = self._generate_entity_resources(name, identifier)

        return GeneratedEntity(
            name=name,
            identifier=identifier,
            entity_type=entity_type,
            behaviors=behavior_configs,
            components=component_configs,
            entity_json=entity_json,
            script_code=script_code,
            resource_files=resource_files,
            notes=notes,
        )

    def generate_item(
        self,
        name: str,
        item_type: ItemType = ItemType.CONSUMABLE,
        components: Optional[list[dict[str, Any]]] = None,
        namespace: str = "custom",
    ) -> GeneratedItem:
        """
        生成物品配置

        Args:
            name: 物品名称
            item_type: 物品类型
            components: 组件配置列表
            namespace: 命名空间

        Returns:
            生成的物品配置
        """
        identifier = f"{namespace}:{name.lower().replace(' ', '_')}"
        component_configs: list[ComponentConfig] = []
        notes: list[str] = []

        # 处理组件
        if components:
            for c in components:
                comp_name = c.get("name", "")
                component_configs.append(
                    ComponentConfig(
                        name=comp_name,
                        namespace=c.get("namespace", "minecraft"),
                        parameters=c.get("parameters", {}),
                    )
                )

        # 根据物品类型添加默认组件
        default_components = self._get_default_item_components(item_type)
        for comp_name, comp_params in default_components.items():
            if not any(c.name == comp_name for c in component_configs):
                component_configs.append(
                    ComponentConfig(name=comp_name, parameters=comp_params)
                )

        # 生成 JSON 配置
        item_json = self._generate_item_json(identifier, item_type, component_configs)

        # 生成脚本代码
        script_code = self._generate_item_script(identifier, item_type)

        # 生成资源文件
        resource_files = self._generate_item_resources(name, identifier)

        return GeneratedItem(
            name=name,
            identifier=identifier,
            item_type=item_type,
            components=component_configs,
            item_json=item_json,
            script_code=script_code,
            resource_files=resource_files,
            notes=notes,
        )

    def generate_block(
        self,
        name: str,
        block_type: BlockType = BlockType.BASIC,
        components: Optional[list[dict[str, Any]]] = None,
        namespace: str = "custom",
    ) -> GeneratedBlock:
        """
        生成方块配置

        Args:
            name: 方块名称
            block_type: 方块类型
            components: 组件配置列表
            namespace: 命名空间

        Returns:
            生成的方块配置
        """
        identifier = f"{namespace}:{name.lower().replace(' ', '_')}"
        component_configs: list[ComponentConfig] = []
        notes: list[str] = []

        # 处理组件
        if components:
            for c in components:
                comp_name = c.get("name", "")
                component_configs.append(
                    ComponentConfig(
                        name=comp_name,
                        namespace=c.get("namespace", "minecraft"),
                        parameters=c.get("parameters", {}),
                    )
                )

        # 根据方块类型添加默认组件
        default_components = self._get_default_block_components(block_type)
        for comp_name, comp_params in default_components.items():
            if not any(c.name == comp_name for c in component_configs):
                component_configs.append(
                    ComponentConfig(name=comp_name, parameters=comp_params)
                )

        # 生成 JSON 配置
        block_json = self._generate_block_json(identifier, block_type, component_configs)

        # 生成脚本代码
        script_code = self._generate_block_script(identifier, block_type)

        # 生成资源文件
        resource_files = self._generate_block_resources(name, identifier)

        return GeneratedBlock(
            name=name,
            identifier=identifier,
            block_type=block_type,
            components=component_configs,
            block_json=block_json,
            script_code=script_code,
            resource_files=resource_files,
            notes=notes,
        )

    def generate_event_listener(
        self,
        event_name: str,
        callback_name: Optional[str] = None,
        scope: str = "server",
        custom_code: Optional[str] = None,
    ) -> EventListener:
        """
        生成事件监听器

        Args:
            event_name: 事件名称
            callback_name: 回调函数名称
            scope: 作用域 (client/server)
            custom_code: 自定义代码

        Returns:
            事件监听器配置
        """
        event_info = self.COMMON_EVENTS.get(event_name, {})
        callback_name = callback_name or f"on_{event_name.lower()}"

        # 生成代码
        code = self._generate_event_listener_code(
            event_name, callback_name, scope, event_info, custom_code
        )

        # 导入语句
        imports = self._get_event_imports(event_name, scope)

        # 备注
        notes = []
        if not event_info:
            notes.append(f"未知事件: {event_name}，请确认事件名称是否正确")

        return EventListener(
            event_name=event_name,
            namespace=event_info.get("namespace", "MinecraftEvents"),
            scope=event_info.get("scope", scope),
            callback_name=callback_name,
            parameters=event_info.get("parameters", ["args"]),
            code=code,
            imports=imports,
            notes=notes,
        )

    def get_api_suggestions(
        self,
        context: str,
        top_k: int = 5,
    ) -> list[APISuggestion]:
        """
        获取 API 建议

        Args:
            context: 上下文（当前代码或需求描述）
            top_k: 返回数量

        Returns:
            API 建议列表
        """
        # 基于上下文的简单匹配
        suggestions: list[APISuggestion] = []

        # 关键词映射
        keywords_map = {
            "实体": ["CreateEngineEntity", "DestroyEntity", "GetEngineEntity", "SetEntityPos"],
            "创建实体": ["CreateEngineEntity"],
            "销毁实体": ["DestroyEntity"],
            "位置": ["GetPos", "SetPos", "GetEntityPos", "SetEntityPos"],
            "移动": ["MoveEntity", "SetEntityMotion"],
            "物品": ["CreateEngineItemEntity", "GetContainer", "SetInvItemNum"],
            "背包": ["GetContainer", "GetContainerItem", "SetInvItemNum"],
            "方块": ["CreateEngineBlock", "DestroyBlock", "GetBlock", "SetBlock"],
            "放置": ["SetBlock", "PlaceBlock"],
            "破坏": ["DestroyBlock", "BreakBlock"],
            "玩家": ["GetPlayerName", "GetPlayerUID", "GetPlayerPos"],
            "聊天": ["BroadcastToClient", "NotifyToClient", "SetTipMessage"],
            "消息": ["BroadcastToClient", "NotifyToClient"],
            "UI": ["CreateUI", "DestroyUI", "GetUI"],
            "界面": ["CreateUI", "DestroyUI"],
            "伤害": ["DamageEntity", "HurtEntity"],
            "血量": ["GetEntityHealth", "SetEntityHealth"],
            "生命": ["GetEntityHealth", "SetEntityHealth"],
        }

        context_lower = context.lower()
        matched_apis: set[str] = set()

        for keyword, apis in keywords_map.items():
            if keyword in context_lower or keyword in context:
                matched_apis.update(apis)

        # 转换为建议对象
        for api_name in list(matched_apis)[:top_k]:
            suggestion = self._create_api_suggestion(api_name)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    def validate_config(
        self,
        config: dict[str, Any],
        config_type: str = "entity",
    ) -> ValidationResult:
        """
        验证配置

        Args:
            config: 配置字典
            config_type: 配置类型 (entity/item/block)

        Returns:
            验证结果
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        if config_type == "entity":
            return self._validate_entity_config(config)
        elif config_type == "item":
            return self._validate_item_config(config)
        elif config_type == "block":
            return self._validate_block_config(config)
        else:
            errors.append(f"未知配置类型: {config_type}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    # ==================== 私有辅助方法 ====================

    def _get_default_families(self, entity_type: EntityType) -> list[str]:
        """根据实体类型获取默认家族"""
        families_map = {
            EntityType.PASSIVE: ["mob", "passive"],
            EntityType.HOSTILE: ["mob", "hostile", "monster"],
            EntityType.NEUTRAL: ["mob", "neutral"],
            EntityType.BOSS: ["mob", "boss", "hostile"],
            EntityType.NPC: ["mob", "npc"],
        }
        return families_map.get(entity_type, ["mob"])

    def _get_default_item_components(self, item_type: ItemType) -> dict[str, dict[str, Any]]:
        """根据物品类型获取默认组件"""
        defaults = {
            ItemType.CONSUMABLE: {
                "minecraft:food": {"nutrition": 4, "saturation_modifier": "normal"},
                "minecraft:use_duration": 32,
            },
            ItemType.TOOL: {
                "minecraft:max_damage": 250,
                "minecraft:hand_equipped": True,
            },
            ItemType.WEAPON: {
                "minecraft:max_damage": 500,
                "minecraft:hand_equipped": True,
            },
            ItemType.ARMOR: {
                "minecraft:armor": {"protection": 4},
                "minecraft:max_damage": 250,
            },
            ItemType.BLOCK_ITEM: {},
            ItemType.SPECIAL: {},
        }
        return defaults.get(item_type, {})

    def _get_default_block_components(self, block_type: BlockType) -> dict[str, dict[str, Any]]:
        """根据方块类型获取默认组件"""
        defaults = {
            BlockType.BASIC: {
                "minecraft:destroy_time": 1.0,
                "minecraft:explosion_resistance": 1.0,
            },
            BlockType.INTERACTIVE: {
                "minecraft:destroy_time": 1.0,
                "minecraft:explosion_resistance": 1.0,
            },
            BlockType.FUNCTIONAL: {
                "minecraft:destroy_time": 1.0,
                "minecraft:explosion_resistance": 2.0,
            },
            BlockType.DECORATION: {
                "minecraft:destroy_time": 0.5,
                "minecraft:explosion_resistance": 0.5,
            },
        }
        return defaults.get(block_type, {})

    def _generate_entity_json(
        self,
        identifier: str,
        entity_type: EntityType,
        behaviors: list[BehaviorConfig],
        components: list[ComponentConfig],
    ) -> dict[str, Any]:
        """生成实体 JSON 配置"""
        entity_json = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {
                    "identifier": identifier,
                    "is_spawnable": True,
                    "is_summonable": True,
                },
                "component_groups": {},
                "components": {},
                "events": {},
            },
        }

        # 添加组件
        for comp in components:
            entity_json["minecraft:entity"]["components"][comp.name] = comp.parameters

        return entity_json

    def _generate_entity_script(self, identifier: str, entity_type: EntityType) -> str:
        """生成实体脚本代码"""
        return f'''# -*- coding: utf-8 -*-
"""
实体脚本: {identifier}
类型: {entity_type.value}
"""

from mod.common.mod import Mod
from mod.common.system.modEvent import ModEvent
from mod.common.minecraft import GetMinecraft


class {identifier.split(":")[-1].title().replace("_", "")}Entity:
    """实体管理类"""
    
    def __init__(self, system):
        self.system = system
        self.config = {{
            "identifier": "{identifier}",
            "entity_type": "{entity_type.value}",
        }}
    
    def on_entity_added(self, args):
        """实体添加时调用"""
        entity_id = args.get("id")
        # 在这里添加实体初始化逻辑
        pass
    
    def on_entity_removed(self, args):
        """实体移除时调用"""
        entity_id = args.get("id")
        # 在这里添加清理逻辑
        pass
    
    def register_handlers(self):
        """注册事件处理器"""
        self.system.DefineEvent("OnEntityAdded", self.on_entity_added)
        self.system.DefineEvent("OnEntityRemoved", self.on_entity_removed)


def create(system):
    """创建实体实例"""
    return {identifier.split(":")[-1].title().replace("_", "")}Entity(system)
'''

    def _generate_entity_resources(self, name: str, identifier: str) -> dict[str, str]:
        """生成实体资源文件"""
        entity_name = identifier.split(":")[-1]
        return {
            f"textures/entity/{entity_name}.png": f"# 占位纹理文件: {name}",
            f"models/entity/{entity_name}.geo.json": f"# 占位几何文件: {name}",
            f"animations/entity/{entity_name}.anim.json": f"# 占位动画文件: {name}",
        }

    def _generate_item_json(
        self,
        identifier: str,
        item_type: ItemType,
        components: list[ComponentConfig],
    ) -> dict[str, Any]:
        """生成物品 JSON 配置"""
        item_json = {
            "format_version": "1.16.0",
            "minecraft:item": {
                "description": {
                    "identifier": identifier,
                    "category": "Items",
                },
                "components": {},
            },
        }

        # 添加组件
        for comp in components:
            item_json["minecraft:item"]["components"][comp.name] = comp.parameters

        return item_json

    def _generate_item_script(self, identifier: str, item_type: ItemType) -> str:
        """生成物品脚本代码"""
        return f'''# -*- coding: utf-8 -*-
"""
物品脚本: {identifier}
类型: {item_type.value}
"""

from mod.common.mod import Mod
from mod.common.system.modEvent import ModEvent


class {identifier.split(":")[-1].title().replace("_", "")}Item:
    """物品管理类"""
    
    def __init__(self, system):
        self.system = system
        self.config = {{
            "identifier": "{identifier}",
            "item_type": "{item_type.value}",
        }}
    
    def on_use_item(self, args):
        """使用物品时调用"""
        player_id = args.get("playerId")
        item_stack = args.get("itemStack")
        # 在这里添加使用逻辑
        pass
    
    def on_use_item_on(self, args):
        """对方块使用物品时调用"""
        player_id = args.get("playerId")
        item_stack = args.get("itemStack")
        block_pos = args.get("blockPos")
        # 在这里添加使用逻辑
        pass
    
    def register_handlers(self):
        """注册事件处理器"""
        self.system.DefineEvent("OnUseItem", self.on_use_item)
        self.system.DefineEvent("OnUseItemOn", self.on_use_item_on)


def create(system):
    """创建物品实例"""
    return {identifier.split(":")[-1].title().replace("_", "")}Item(system)
'''

    def _generate_item_resources(self, name: str, identifier: str) -> dict[str, str]:
        """生成物品资源文件"""
        item_name = identifier.split(":")[-1]
        return {
            f"textures/items/{item_name}.png": f"# 占位纹理文件: {name}",
        }

    def _generate_block_json(
        self,
        identifier: str,
        block_type: BlockType,
        components: list[ComponentConfig],
    ) -> dict[str, Any]:
        """生成方块 JSON 配置"""
        block_json = {
            "format_version": "1.16.0",
            "minecraft:block": {
                "description": {
                    "identifier": identifier,
                },
                "components": {},
            },
        }

        # 添加组件
        for comp in components:
            block_json["minecraft:block"]["components"][comp.name] = comp.parameters

        return block_json

    def _generate_block_script(self, identifier: str, block_type: BlockType) -> str:
        """生成方块脚本代码"""
        return f'''# -*- coding: utf-8 -*-
"""
方块脚本: {identifier}
类型: {block_type.value}
"""

from mod.common.mod import Mod
from mod.common.system.modEvent import ModEvent


class {identifier.split(":")[-1].title().replace("_", "")}Block:
    """方块管理类"""
    
    def __init__(self, system):
        self.system = system
        self.config = {{
            "identifier": "{identifier}",
            "block_type": "{block_type.value}",
        }}
    
    def on_place_block(self, args):
        """放置方块时调用"""
        player_id = args.get("playerId")
        block_pos = args.get("blockPos")
        # 在这里添加放置逻辑
        pass
    
    def on_destroy_block(self, args):
        """破坏方块时调用"""
        player_id = args.get("playerId")
        block_pos = args.get("blockPos")
        # 在这里添加破坏逻辑
        pass
    
    def on_use_block(self, args):
        """使用方块时调用（交互方块）"""
        player_id = args.get("playerId")
        block_pos = args.get("blockPos")
        # 在这里添加交互逻辑
        pass
    
    def register_handlers(self):
        """注册事件处理器"""
        self.system.DefineEvent("OnPlaceBlock", self.on_place_block)
        self.system.DefineEvent("OnDestroyBlock", self.on_destroy_block)
        if self.config["block_type"] == "interactive":
            self.system.DefineEvent("OnUseBlock", self.on_use_block)


def create(system):
    """创建方块实例"""
    return {identifier.split(":")[-1].title().replace("_", "")}Block(system)
'''

    def _generate_block_resources(self, name: str, identifier: str) -> dict[str, str]:
        """生成方块资源文件"""
        block_name = identifier.split(":")[-1]
        return {
            f"textures/blocks/{block_name}.png": f"# 占位纹理文件: {name}",
        }

    def _generate_event_listener_code(
        self,
        event_name: str,
        callback_name: str,
        scope: str,
        event_info: dict[str, Any],
        custom_code: Optional[str],
    ) -> str:
        """生成事件监听器代码"""
        params = event_info.get("parameters", ["args"])
        params_str = ", ".join(params)

        if custom_code:
            handler_code = custom_code
        else:
            handler_code = f'''        # TODO: 实现事件处理逻辑
        print("{event_name} triggered")'''

        return f'''def {callback_name}({params_str}):
    """处理 {event_name} 事件"""
{handler_code}


def register_{callback_name}(system):
    """注册事件监听器"""
    system.DefineEvent("{event_name}", {callback_name})
'''

    def _get_event_imports(self, event_name: str, scope: str) -> list[str]:
        """获取事件所需的导入"""
        imports = ["from mod.common.system.modEvent import ModEvent"]
        if scope == "client":
            imports.append("from mod.client.mod import Mod")
        else:
            imports.append("from mod.common.mod import Mod")
        return imports

    def _create_api_suggestion(self, api_name: str) -> Optional[APISuggestion]:
        """创建 API 建议对象"""
        # API 信息映射（简化版）
        api_info = {
            "CreateEngineEntity": {
                "module": "实体",
                "description": "创建引擎实体",
                "return_type": "int",
                "example": "entity_id = CreateEngineEntity(entity_type, pos)",
            },
            "DestroyEntity": {
                "module": "实体",
                "description": "销毁实体",
                "return_type": "bool",
                "example": "success = DestroyEntity(entity_id)",
            },
            "GetEngineEntity": {
                "module": "实体",
                "description": "获取引擎实体",
                "return_type": "EngineEntity",
                "example": "entity = GetEngineEntity(entity_id)",
            },
            "SetEntityPos": {
                "module": "实体",
                "description": "设置实体位置",
                "return_type": "bool",
                "example": "SetEntityPos(entity_id, x, y, z)",
            },
            "GetEntityHealth": {
                "module": "实体",
                "description": "获取实体生命值",
                "return_type": "int",
                "example": "health = GetEntityHealth(entity_id)",
            },
            "SetEntityHealth": {
                "module": "实体",
                "description": "设置实体生命值",
                "return_type": "bool",
                "example": "SetEntityHealth(entity_id, health)",
            },
            "BroadcastToClient": {
                "module": "聊天",
                "description": "广播消息给所有客户端",
                "return_type": "bool",
                "example": 'BroadcastToClient("消息内容")',
            },
            "NotifyToClient": {
                "module": "聊天",
                "description": "发送消息给指定客户端",
                "return_type": "bool",
                "example": 'NotifyToClient(player_id, "消息内容")',
            },
            "GetPlayerName": {
                "module": "玩家",
                "description": "获取玩家名称",
                "return_type": "str",
                "example": "name = GetPlayerName(player_id)",
            },
            "GetPlayerUID": {
                "module": "玩家",
                "description": "获取玩家 UID",
                "return_type": "str",
                "example": "uid = GetPlayerUID(player_id)",
            },
        }

        info = api_info.get(api_name)
        if not info:
            return None

        return APISuggestion(
            api_name=api_name,
            module=info["module"],
            description=info["description"],
            parameters=[],
            return_type=info["return_type"],
            example_code=info["example"],
            relevance_score=1.0,
        )

    def _validate_entity_config(self, config: dict[str, Any]) -> ValidationResult:
        """验证实体配置"""
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # 检查必需字段
        if "minecraft:entity" not in config:
            errors.append("缺少 minecraft:entity 根节点")
        else:
            entity = config["minecraft:entity"]
            if "description" not in entity:
                errors.append("缺少 description 字段")
            else:
                desc = entity["description"]
                if "identifier" not in desc:
                    errors.append("缺少 identifier 字段")

        # 检查组件
        if "minecraft:entity" in config:
            components = config["minecraft:entity"].get("components", {})
            if "minecraft:health" not in components:
                suggestions.append("建议添加 minecraft:health 组件")
            if "minecraft:type_family" not in components:
                suggestions.append("建议添加 minecraft:type_family 组件")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _validate_item_config(self, config: dict[str, Any]) -> ValidationResult:
        """验证物品配置"""
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        if "minecraft:item" not in config:
            errors.append("缺少 minecraft:item 根节点")
        else:
            item = config["minecraft:item"]
            if "description" not in item:
                errors.append("缺少 description 字段")
            else:
                desc = item["description"]
                if "identifier" not in desc:
                    errors.append("缺少 identifier 字段")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _validate_block_config(self, config: dict[str, Any]) -> ValidationResult:
        """验证方块配置"""
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        if "minecraft:block" not in config:
            errors.append("缺少 minecraft:block 根节点")
        else:
            block = config["minecraft:block"]
            if "description" not in block:
                errors.append("缺少 description 字段")
            else:
                desc = block["description"]
                if "identifier" not in desc:
                    errors.append("缺少 identifier 字段")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )


def create_modsdk_skill(version: ModSDKVersion = ModSDKVersion.LATEST) -> ModSDKSkill:
    """创建 ModSDK 技能实例"""
    return ModSDKSkill(version)