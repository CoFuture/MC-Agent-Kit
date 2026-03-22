"""
增强代码模板

提供实体行为、物品逻辑、方块逻辑等更多模板。
"""

from dataclasses import dataclass, field
from typing import Any

from .templates import CodeTemplate, TemplateParameter, TemplateType


# 实体行为模板
ENTITY_BEHAVIOR_TEMPLATE = CodeTemplate(
    name="entity_behavior",
    template_type=TemplateType.ENTITY,
    description="生成实体行为逻辑代码",
    template="""# 实体行为逻辑
# 实体类型: {{ entity_type | default('custom_entity') }}
# 行为类型: {{ behavior_type | default('passive') }}

import mod.server.extraServerApi as serverApi

# 获取游戏组件工厂
compFactory = serverApi.GetEngineCompFactory()

class {{ entity_class | default('CustomEntity') }}Behavior:
    \"\"\"
    {{ entity_type | default('custom_entity') }} 实体行为类
    行为类型: {{ behavior_type | default('passive') }}
    \"\"\"

    def __init__(self, entityId):
        self.entityId = entityId
        self.state = "idle"
        self.targetId = None
        self.tickCount = 0

    def on_spawn(self):
        \"\"\"实体生成时调用\"\"\"
        print("[{{ entity_class | default('CustomEntity') }}] 实体生成:", self.entityId)
        {% if init_health %}
        # 设置初始生命值
        comp = compFactory.CreateActorAttribute(self.entityId)
        if comp:
            comp.SetAttrMaxHealth({{ init_health }})
            comp.SetAttrHealth({{ init_health }})
        {% endif %}

    def on_tick(self):
        \"\"\"每 tick 调用\"\"\"
        self.tickCount += 1

        {% if behavior_type == 'hostile' %}
        # 敌对行为
        self._update_hostile_behavior()
        {% elif behavior_type == 'neutral' %}
        # 中立行为
        self._update_neutral_behavior()
        {% else %}
        # 被动行为
        self._update_passive_behavior()
        {% endif %}

    def _update_passive_behavior(self):
        \"\"\"被动行为更新\"\"\"
        if self.tickCount % 100 == 0:
            # 每 5 秒随机移动
            self._random_walk()

    def _update_neutral_behavior(self):
        \"\"\"中立行为更新\"\"\"
        # 检测附近玩家
        nearby_players = self._get_nearby_players({{ detection_range | default(16) }})

        if nearby_players and not self.targetId:
            # 被攻击时才反击
            pass

        if self.targetId:
            self._chase_target()

    def _update_hostile_behavior(self):
        \"\"\"敌对行为更新\"\"\"
        # 检测附近玩家
        nearby_players = self._get_nearby_players({{ detection_range | default(16) }})

        if nearby_players:
            # 追踪最近的玩家
            self.targetId = nearby_players[0]
            self._chase_target()
        else:
            self.targetId = None
            self._random_walk()

    def _random_walk(self):
        \"\"\"随机行走\"\"\"
        import random
        comp = compFactory.CreateActorMotion(self.entityId)
        if comp:
            dx = random.uniform(-1, 1)
            dz = random.uniform(-1, 1)
            comp.SetEntityMotion((dx * 0.5, 0, dz * 0.5))

    def _get_nearby_players(self, radius):
        \"\"\"获取附近玩家\"\"\"
        comp = compFactory.CreateGame()
        pos = self._get_entity_pos()
        if not pos:
            return []

        # 获取附近实体
        entities = comp.GetEntitiesInSquare(pos, radius, radius, radius)
        players = []
        for entityId in entities:
            # 检查是否为玩家
            entityType = self._get_entity_type(entityId)
            if entityType == "minecraft:player":
                players.append(entityId)
        return players

    def _chase_target(self):
        \"\"\"追踪目标\"\"\"
        if not self.targetId:
            return

        targetPos = self._get_entity_pos(self.targetId)
        myPos = self._get_entity_pos()

        if not targetPos or not myPos:
            return

        # 计算方向
        dx = targetPos[0] - myPos[0]
        dz = targetPos[2] - myPos[2]
        distance = (dx * dx + dz * dz) ** 0.5

        if distance > 2:
            # 移动向目标
            comp = compFactory.CreateActorMotion(self.entityId)
            if comp:
                speed = {{ chase_speed | default(0.3) }}
                comp.SetEntityMotion((dx / distance * speed, 0, dz / distance * speed))
        else:
            # 攻击目标
            self._attack_target()

    def _attack_target(self):
        \"\"\"攻击目标\"\"\"
        comp = compFactory.CreateGame()
        damage = {{ attack_damage | default(2) }}
        comp.DamageEntity(self.targetId, self.entityId, damage)

    def _get_entity_pos(self, entityId=None):
        \"\"\"获取实体位置\"\"\"
        eid = entityId or self.entityId
        comp = compFactory.CreatePos(eid)
        if comp:
            return comp.GetPos()
        return None

    def _get_entity_type(self, entityId):
        \"\"\"获取实体类型\"\"\"
        comp = compFactory.CreateType(entityId)
        if comp:
            return comp.GetEngineType()
        return None

    def on_death(self):
        \"\"\"实体死亡时调用\"\"\"
        print("[{{ entity_class | default('CustomEntity') }}] 实体死亡:", self.entityId)
        {% if drop_items %}
        # 掉落物品
        self._drop_loot()
        {% endif %}

    def _drop_loot(self):
        \"\"\"掉落战利品\"\"\"
        comp = compFactory.CreateGame()
        pos = self._get_entity_pos()
        if pos:
            {% for drop in drop_items %}
            # 掉落 {{ drop }}
            comp.SpawnEngineItemEntity("{{ drop }}", pos, (0, 0.5, 0))
            {% endfor %}

# 注册事件
def OnEntityCreated(args):
    entityId = args.get('id')
    entityType = args.get('engineType')
    if entityType == '{{ entity_type | default('custom_entity') }}':
        behavior = {{ entity_class | default('CustomEntity') }}Behavior(entityId)
        # 存储 behavior 实例以便后续使用

serverApi.ListenForEvent('Minecraft', 'OnEntityCreated', OnEntityCreated)
""",
    parameters=[
        TemplateParameter(
            name="entity_type",
            description="实体类型标识符",
            param_type="str",
            required=True,
        ),
        TemplateParameter(
            name="entity_class",
            description="实体行为类名",
            param_type="str",
            required=False,
        ),
        TemplateParameter(
            name="behavior_type",
            description="行为类型 (passive/neutral/hostile)",
            param_type="str",
            required=False,
            default="passive",
            choices=["passive", "neutral", "hostile"],
        ),
        TemplateParameter(
            name="init_health",
            description="初始生命值",
            param_type="int",
            required=False,
            default=20,
        ),
        TemplateParameter(
            name="detection_range",
            description="检测范围",
            param_type="int",
            required=False,
            default=16,
        ),
        TemplateParameter(
            name="chase_speed",
            description="追踪速度",
            param_type="float",
            required=False,
            default=0.3,
        ),
        TemplateParameter(
            name="attack_damage",
            description="攻击伤害",
            param_type="int",
            required=False,
            default=2,
        ),
        TemplateParameter(
            name="drop_items",
            description="掉落物品列表",
            param_type="list",
            required=False,
            default=[],
        ),
    ],
    tags=["entity", "behavior", "ai"],
    examples=[
        "entity_behavior(entity_type='my_mod:custom_mob', behavior_type='hostile')",
    ],
    scope="server",
)


# 物品逻辑模板
ITEM_LOGIC_TEMPLATE = CodeTemplate(
    name="item_logic",
    template_type=TemplateType.ITEM,
    description="生成物品使用逻辑代码",
    template="""# 物品使用逻辑
# 物品标识符: {{ item_identifier | default('my_mod:custom_item') }}
# 物品类型: {{ item_type | default('consumable') }}

import mod.server.extraServerApi as serverApi
import mod.client.extraClientApi as clientApi

compFactory = serverApi.GetEngineCompFactory()

class {{ item_class | default('CustomItem') }}Logic:
    \"\"\"
    {{ item_identifier | default('my_mod:custom_item') }} 物品逻辑
    物品类型: {{ item_type | default('consumable') }}
    \"\"\"

    ITEM_ID = "{{ item_identifier | default('my_mod:custom_item') }}"
    COOLDOWN = {{ cooldown | default(0) }}  # 冷却时间 (秒)

    @staticmethod
    def on_use(entityId, itemStack):
        \"\"\"
        物品使用时调用

        Args:
            entityId: 使用物品的实体 ID
            itemStack: 物品堆叠信息

        Returns:
            bool: 是否消耗物品
        \"\"\"
        print("[{{ item_class | default('CustomItem') }}] 物品被使用")

        {% if item_type == 'consumable' %}
        # 消耗品逻辑
        return {{ item_class | default('CustomItem') }}Logic._consumable_effect(entityId)
        {% elif item_type == 'tool' %}
        # 工具逻辑
        return {{ item_class | default('CustomItem') }}Logic._tool_effect(entityId)
        {% elif item_type == 'weapon' %}
        # 武器逻辑
        return {{ item_class | default('CustomItem') }}Logic._weapon_effect(entityId)
        {% else %}
        # 通用逻辑
        return {{ item_class | default('CustomItem') }}Logic._generic_effect(entityId)
        {% endif %}

    @staticmethod
    def _consumable_effect(entityId):
        \"\"\"消耗品效果\"\"\"
        comp = compFactory.CreateActorAttribute(entityId)
        if comp:
            # 恢复生命值
            currentHealth = comp.GetAttrHealth()
            maxHealth = comp.GetAttrMaxHealth()
            newHealth = min(currentHealth + {{ heal_amount | default(10) }}, maxHealth)
            comp.SetAttrHealth(newHealth)
            print(f"[Item] 恢复生命值: {newHealth - currentHealth}")

        # 添加效果
        {% if effects %}
        {{ item_class | default('CustomItem') }}Logic._apply_effects(entityId)
        {% endif %}

        return True  # 消耗物品

    @staticmethod
    def _tool_effect(entityId):
        \"\"\"工具效果\"\"\"
        # 获取玩家看向的目标
        comp = compFactory.CreateGame(entityId)
        target = comp.GetEntityLookingAt(entityId, {{ max_distance | default(5) }})

        if target:
            print(f"[Item] 对目标使用工具: {target}")
            # TODO: 实现工具效果

        return False  # 不消耗物品

    @staticmethod
    def _weapon_effect(entityId):
        \"\"\"武器效果\"\"\"
        # 武器在攻击时处理，这里返回 False
        return False

    @staticmethod
    def _generic_effect(entityId):
        \"\"\"通用效果\"\"\"
        # TODO: 实现自定义效果
        return False

    @staticmethod
    def _apply_effects(entityId):
        \"\"\"添加药水效果\"\"\"
        comp = compFactory.CreateEffect(entityId)
        if comp:
            {% for effect in effects %}
            # 添加 {{ effect.name }} 效果
            comp.AddEffect(
                "{{ effect.name }}",
                {{ effect.duration | default(100) }},
                {{ effect.level | default(0) }},
                {{ effect.show_particles | default(True)|lower }}
            )
            {% endfor %}

    @staticmethod
    def on_attack(attackerId, targetId, damage):
        \"\"\"
        攻击时调用 (武器类型)

        Args:
            attackerId: 攻击者实体 ID
            targetId: 目标实体 ID
            damage: 基础伤害

        Returns:
            float: 实际伤害
        \"\"\"
        {% if item_type == 'weapon' %}
        # 武器额外伤害
        extra_damage = {{ extra_damage | default(0) }}
        total_damage = damage + extra_damage

        print(f"[Weapon] 攻击伤害: {total_damage}")

        {% if on_hit_effects %}
        # 攻击命中效果
        {{ item_class | default('CustomItem') }}Logic._on_hit_effect(targetId)
        {% endif %}

        return total_damage
        {% else %}
        return damage
        {% endif %}

    @staticmethod
    def _on_hit_effect(targetId):
        \"\"\"命中效果\"\"\"
        {% if on_hit_effects %}
        comp = compFactory.CreateEffect(targetId)
        if comp:
            {% for effect in on_hit_effects %}
            comp.AddEffect("{{ effect.name }}", {{ effect.duration }}, {{ effect.level }}, True)
            {% endfor %}
        {% endif %}

# 注册事件
def OnItemUse(args):
    entityId = args.get('entityId')
    itemStack = args.get('itemStack')
    if itemStack and itemStack.get('newItemName') == {{ item_class | default('CustomItem') }}Logic.ITEM_ID:
        {{ item_class | default('CustomItem') }}Logic.on_use(entityId, itemStack)

serverApi.ListenForEvent('Minecraft', 'OnItemUse', OnItemUse)

{% if item_type == 'weapon' %}
def OnAttack(args):
    attackerId = args.get('attackerId')
    targetId = args.get('targetId')
    damage = args.get('damage', 0)
    # 检查攻击者是否持有此武器
    comp = compFactory.CreateContainer(attackerId)
    if comp:
        mainHand = comp.GetEntityMainHandItem(attackerId)
        if mainHand and mainHand.get('newItemName') == {{ item_class | default('CustomItem') }}Logic.ITEM_ID:
            args['damage'] = {{ item_class | default('CustomItem') }}Logic.on_attack(attackerId, targetId, damage)

serverApi.ListenForEvent('Minecraft', 'OnAttack', OnAttack)
{% endif %}
""",
    parameters=[
        TemplateParameter(
            name="item_identifier",
            description="物品标识符 (namespace:item_name)",
            param_type="str",
            required=True,
        ),
        TemplateParameter(
            name="item_class",
            description="物品逻辑类名",
            param_type="str",
            required=False,
        ),
        TemplateParameter(
            name="item_type",
            description="物品类型 (consumable/tool/weapon)",
            param_type="str",
            required=False,
            default="consumable",
            choices=["consumable", "tool", "weapon"],
        ),
        TemplateParameter(
            name="cooldown",
            description="冷却时间 (秒)",
            param_type="int",
            required=False,
            default=0,
        ),
        TemplateParameter(
            name="heal_amount",
            description="治疗量 (消耗品)",
            param_type="int",
            required=False,
            default=10,
        ),
        TemplateParameter(
            name="effects",
            description="药水效果列表",
            param_type="list",
            required=False,
            default=[],
        ),
        TemplateParameter(
            name="extra_damage",
            description="额外伤害 (武器)",
            param_type="int",
            required=False,
            default=0,
        ),
        TemplateParameter(
            name="on_hit_effects",
            description="命中效果列表 (武器)",
            param_type="list",
            required=False,
            default=[],
        ),
        TemplateParameter(
            name="max_distance",
            description="最大交互距离 (工具)",
            param_type="int",
            required=False,
            default=5,
        ),
    ],
    tags=["item", "logic", "use"],
    examples=[
        "item_logic(item_identifier='my_mod:health_potion', item_type='consumable', heal_amount=20)",
        "item_logic(item_identifier='my_mod:magic_sword', item_type='weapon', extra_damage=5)",
    ],
    scope="server",
)


# 方块逻辑模板
BLOCK_LOGIC_TEMPLATE = CodeTemplate(
    name="block_logic",
    template_type=TemplateType.BLOCK,
    description="生成方块交互逻辑代码",
    template="""# 方块交互逻辑
# 方块标识符: {{ block_identifier | default('my_mod:custom_block') }}
# 方块类型: {{ block_type | default('solid') }}

import mod.server.extraServerApi as serverApi

compFactory = serverApi.GetEngineCompFactory()

class {{ block_class | default('CustomBlock') }}Logic:
    \"\"\"
    {{ block_identifier | default('my_mod:custom_block') }} 方块逻辑
    方块类型: {{ block_type | default('solid') }}
    \"\"\"

    BLOCK_ID = "{{ block_identifier | default('my_mod:custom_block') }}"

    @staticmethod
    def on_placed(pos, dimensionId, playerId):
        \"\"\"
        方块放置时调用

        Args:
            pos: 放置位置 (x, y, z)
            dimensionId: 维度 ID
            playerId: 放置玩家 ID
        \"\"\"
        print(f"[{{ block_class | default('CustomBlock') }}] 方块放置于: {pos}")

        {% if block_type == 'interactive' %}
        # 交互方块初始化
        {{ block_class | default('CustomBlock') }}Logic._init_interactive_block(pos, dimensionId)
        {% elif block_type == 'redstone' %}
        # 红石方块初始化
        {{ block_class | default('CustomBlock') }}Logic._init_redstone_block(pos, dimensionId)
        {% elif block_type == 'functional' %}
        # 功能方块初始化
        {{ block_class | default('CustomBlock') }}Logic._init_functional_block(pos, dimensionId)
        {% endif %}

    @staticmethod
    def on_destroyed(pos, dimensionId, playerId):
        \"\"\"
        方块破坏时调用

        Args:
            pos: 破坏位置 (x, y, z)
            dimensionId: 维度 ID
            playerId: 破坏玩家 ID
        \"\"\"
        print(f"[{{ block_class | default('CustomBlock') }}] 方块破坏于: {pos}")

        {% if drop_self == False %}
        # 掉落特定物品
        {{ block_class | default('CustomBlock') }}Logic._drop_loot(pos, dimensionId)
        {% endif %}

    @staticmethod
    def on_interact(pos, dimensionId, playerId, itemStack):
        \"\"\"
        玩家交互时调用

        Args:
            pos: 方块位置 (x, y, z)
            dimensionId: 维度 ID
            playerId: 交互玩家 ID
            itemStack: 玩家手持物品

        Returns:
            bool: 是否拦截默认行为
        \"\"\"
        {% if block_type == 'interactive' %}
        print(f"[{{ block_class | default('CustomBlock') }}] 玩家 {playerId} 交互方块")

        # 检查手持物品
        if itemStack:
            itemName = itemStack.get('newItemName', '')
            print(f"[Block] 手持物品: {itemName}")

            {% if interact_items %}
            if itemName in {{ interact_items }}:
                return {{ block_class | default('CustomBlock') }}Logic._special_interact(pos, dimensionId, playerId, itemName)
            {% endif %}

        # 默认交互
        return {{ block_class | default('CustomBlock') }}Logic._default_interact(pos, dimensionId, playerId)
        {% else %}
        return False  # 不拦截
        {% endif %}

    @staticmethod
    def _init_interactive_block(pos, dimensionId):
        \"\"\"初始化交互方块\"\"\"
        # 存储方块状态
        # TODO: 实现状态存储
        pass

    @staticmethod
    def _init_redstone_block(pos, dimensionId):
        \"\"\"初始化红石方块\"\"\"
        # 设置红石信号
        comp = compFactory.CreateRedStone(pos, dimensionId)
        if comp:
            comp.SetBlockRedstonePower({{ redstone_power | default(15) }})

    @staticmethod
    def _init_functional_block(pos, dimensionId):
        \"\"\"初始化功能方块\"\"\"
        # TODO: 实现功能初始化
        pass

    @staticmethod
    def _default_interact(pos, dimensionId, playerId):
        \"\"\"默认交互行为\"\"\"
        # 发送消息
        comp = compFactory.CreateGame(playerId)
        comp.NotifyToClient(playerId, {
            'type': 'block_interact',
            'blockId': {{ block_class | default('CustomBlock') }}Logic.BLOCK_ID,
            'pos': pos
        })
        return False

    @staticmethod
    def _special_interact(pos, dimensionId, playerId, itemName):
        \"\"\"特殊交互行为\"\"\"
        print(f"[Block] 特殊交互: {itemName}")
        return True  # 拦截默认行为

    @staticmethod
    def _drop_loot(pos, dimensionId):
        \"\"\"掉落物品\"\"\"
        comp = compFactory.CreateGame()
        {% if custom_drops %}
        {% for drop in custom_drops %}
        comp.SpawnEngineItemEntity("{{ drop.item }}", pos, (0, 0.5, 0), {{ drop.count | default(1) }})
        {% endfor %}
        {% else %}
        # 默认掉落自身
        comp.SpawnEngineItemEntity({{ block_class | default('CustomBlock') }}Logic.BLOCK_ID, pos, (0, 0.5, 0))
        {% endif %}

    @staticmethod
    def on_neighbor_changed(pos, dimensionId, neighborPos):
        \"\"\"
        邻居方块变化时调用 (红石方块)

        Args:
            pos: 当前方块位置
            dimensionId: 维度 ID
            neighborPos: 变化的邻居位置
        \"\"\"
        {% if block_type == 'redstone' %}
        # 检查红石信号
        comp = compFactory.CreateRedStone(pos, dimensionId)
        if comp:
            power = comp.GetBlockRedstonePower()
            print(f"[Redstone] 方块信号强度: {power}")
            # TODO: 根据信号执行逻辑
        {% endif %}

    @staticmethod
    def on_tick(pos, dimensionId):
        \"\"\"
        每 tick 调用 (如果注册了 tick)

        Args:
            pos: 方块位置
            dimensionId: 维度 ID
        \"\"\"
        {% if has_tick_logic %}
        # 自定义 tick 逻辑
        pass
        {% endif %}

# 注册事件
def OnBlockPlaced(args):
    blockName = args.get('blockName')
    if blockName == {{ block_class | default('CustomBlock') }}Logic.BLOCK_ID:
        pos = args.get('pos')
        dimensionId = args.get('dimensionId', 0)
        playerId = args.get('entityId')
        {{ block_class | default('CustomBlock') }}Logic.on_placed(pos, dimensionId, playerId)

def OnBlockDestroyed(args):
    blockName = args.get('blockName')
    if blockName == {{ block_class | default('CustomBlock') }}Logic.BLOCK_ID:
        pos = args.get('pos')
        dimensionId = args.get('dimensionId', 0)
        playerId = args.get('entityId')
        {{ block_class | default('CustomBlock') }}Logic.on_destroyed(pos, dimensionId, playerId)

def OnBlockInteract(args):
    blockName = args.get('blockName')
    if blockName == {{ block_class | default('CustomBlock') }}Logic.BLOCK_ID:
        pos = args.get('pos')
        dimensionId = args.get('dimensionId', 0)
        playerId = args.get('entityId')
        itemStack = args.get('itemStack')
        args['returnValue'] = {{ block_class | default('CustomBlock') }}Logic.on_interact(pos, dimensionId, playerId, itemStack)

serverApi.ListenForEvent('Minecraft', 'OnBlockPlaced', OnBlockPlaced)
serverApi.ListenForEvent('Minecraft', 'OnBlockDestroyed', OnBlockDestroyed)
serverApi.ListenForEvent('Minecraft', 'OnBlockInteract', OnBlockInteract)
""",
    parameters=[
        TemplateParameter(
            name="block_identifier",
            description="方块标识符 (namespace:block_name)",
            param_type="str",
            required=True,
        ),
        TemplateParameter(
            name="block_class",
            description="方块逻辑类名",
            param_type="str",
            required=False,
        ),
        TemplateParameter(
            name="block_type",
            description="方块类型 (solid/interactive/redstone/functional)",
            param_type="str",
            required=False,
            default="solid",
            choices=["solid", "interactive", "redstone", "functional"],
        ),
        TemplateParameter(
            name="drop_self",
            description="破坏时是否掉落自身",
            param_type="bool",
            required=False,
            default=True,
        ),
        TemplateParameter(
            name="custom_drops",
            description="自定义掉落列表",
            param_type="list",
            required=False,
            default=[],
        ),
        TemplateParameter(
            name="interact_items",
            description="可交互物品列表",
            param_type="list",
            required=False,
            default=[],
        ),
        TemplateParameter(
            name="redstone_power",
            description="红石信号强度 (红石方块)",
            param_type="int",
            required=False,
            default=15,
        ),
        TemplateParameter(
            name="has_tick_logic",
            description="是否有 tick 逻辑",
            param_type="bool",
            required=False,
            default=False,
        ),
    ],
    tags=["block", "logic", "interact"],
    examples=[
        "block_logic(block_identifier='my_mod:chest', block_type='interactive')",
        "block_logic(block_identifier='my_mod:lever', block_type='redstone')",
    ],
    scope="server",
)


# 数据同步模板
DATA_SYNC_TEMPLATE = CodeTemplate(
    name="data_sync",
    template_type=TemplateType.CUSTOM,
    description="生成客户端-服务端数据同步代码",
    template="""# 客户端-服务端数据同步
# 同步名称: {{ sync_name | default('custom_data') }}

# 服务端代码
import mod.server.extraServerApi as serverApi

# 客户端代码
import mod.client.extraClientApi as clientApi

# 同步事件名称
SYNC_EVENT = "{{ sync_name | default('custom_data') }}_sync"

# 服务端同步管理器
class {{ sync_class | default('CustomData') }}SyncServer:
    \"\"\"服务端数据同步管理器\"\"\"

    def __init__(self):
        self.data = {}
        self.playerCallbacks = {}

    def set_data(self, playerId, key, value):
        \"\"\"
        设置玩家数据并同步

        Args:
            playerId: 玩家 ID
            key: 数据键
            value: 数据值
        \"\"\"
        if playerId not in self.data:
            self.data[playerId] = {}
        self.data[playerId][key] = value

        # 同步到客户端
        self._sync_to_client(playerId, {key: value})

    def get_data(self, playerId, key=None):
        \"\"\"
        获取玩家数据

        Args:
            playerId: 玩家 ID
            key: 数据键 (可选)

        Returns:
            数据值或整个数据字典
        \"\"\"
        if playerId not in self.data:
            return None
        if key:
            return self.data[playerId].get(key)
        return self.data[playerId].copy()

    def _sync_to_client(self, playerId, data):
        \"\"\"同步数据到客户端\"\"\"
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.NotifyToClient(playerId, {
            'type': SYNC_EVENT,
            'data': data
        })

    def sync_all(self, playerId):
        \"\"\"同步所有数据到客户端\"\"\"
        if playerId in self.data:
            self._sync_to_client(playerId, self.data[playerId])

# 客户端数据管理器
class {{ sync_class | default('CustomData') }}SyncClient:
    \"\"\"客户端数据管理器\"\"\"

    def __init__(self):
        self.data = {}

    def on_sync(self, data):
        \"\"\"
        接收同步数据

        Args:
            data: 同步的数据字典
        \"\"\"
        self.data.update(data)
        print(f"[Client] 收到同步数据: {data}")

    def get_data(self, key=None):
        \"\"\"
        获取本地数据

        Args:
            key: 数据键 (可选)

        Returns:
            数据值或整个数据字典
        \"\"\"
        if key:
            return self.data.get(key)
        return self.data.copy()

# 创建实例
serverSync = {{ sync_class | default('CustomData') }}SyncServer()
clientSync = {{ sync_class | default('CustomData') }}SyncClient()

# 客户端注册监听
def OnClientNotify(args):
    if args.get('type') == SYNC_EVENT:
        clientSync.on_sync(args.get('data', {}))

clientApi.ListenForEvent('Minecraft', 'OnClientNotify', OnClientNotify)
""",
    parameters=[
        TemplateParameter(
            name="sync_name",
            description="同步名称",
            param_type="str",
            required=True,
        ),
        TemplateParameter(
            name="sync_class",
            description="同步类名",
            param_type="str",
            required=False,
        ),
    ],
    tags=["sync", "network", "client-server"],
    examples=[
        "data_sync(sync_name='player_stats')",
    ],
    scope="both",
)


# 增强模板列表
ENHANCED_TEMPLATES: list[CodeTemplate] = [
    ENTITY_BEHAVIOR_TEMPLATE,
    ITEM_LOGIC_TEMPLATE,
    BLOCK_LOGIC_TEMPLATE,
    DATA_SYNC_TEMPLATE,
]