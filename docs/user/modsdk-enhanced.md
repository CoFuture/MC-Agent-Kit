# ModSDK 增强技能使用指南

> 版本: v1.45.0
> 最后更新: 2026-03-24

---

## 概述

ModSDK 增强技能提供了 Minecraft 网易版 ModSDK 的智能辅助开发功能，包括：

- 实体配置生成
- 物品配置生成
- 方块配置生成
- 事件监听器生成
- API 智能补全
- 配置验证

---

## 快速开始

### 安装

```bash
pip install mc-agent-kit
```

### 基本使用

```python
from mc_agent_kit.skills.modsdk_enhanced import (
    create_modsdk_skill,
    EntityType,
    ItemType,
    BlockType,
)

# 创建技能实例
skill = create_modsdk_skill()

# 生成实体
entity = skill.generate_entity(
    name="CustomZombie",
    entity_type=EntityType.HOSTILE,
    namespace="myaddon",
)

print(entity.entity_json)  # 实体 JSON 配置
print(entity.script_code)  # Python 脚本代码
```

---

## 实体生成

### 基础实体

```python
entity = skill.generate_entity(
    name="SimpleMob",
    entity_type=EntityType.PASSIVE,  # 被动生物
    namespace="myaddon",
)
```

### 带行为的实体

```python
entity = skill.generate_entity(
    name="AggressiveMob",
    entity_type=EntityType.HOSTILE,
    behaviors=[
        {"name": "movement", "parameters": {"speed": 1.5}},
        {"name": "attack", "parameters": {"damage": 5.0, "range": 3.0}},
        {"name": "navigation", "parameters": {"can_path": True}},
    ],
    namespace="myaddon",
)
```

### 带组件的实体

```python
entity = skill.generate_entity(
    name="TankMob",
    entity_type=EntityType.BOSS,
    components=[
        {"name": "minecraft:health", "parameters": {"value": 100, "max": 100}},
        {"name": "minecraft:type_family", "parameters": {"family": ["boss", "mob"]}},
        {"name": "minecraft:attack", "parameters": {"damage": 10}},
    ],
    namespace="myaddon",
)
```

### 实体类型

| 类型 | 描述 |
|------|------|
| `PASSIVE` | 被动生物（如羊、猪） |
| `HOSTILE` | 敌对生物（如僵尸、骷髅） |
| `NEUTRAL` | 中立生物（如狼、末影人） |
| `BOSS` | Boss 生物 |
| `NPC` | NPC 角色 |

---

## 物品生成

### 消耗品

```python
item = skill.generate_item(
    name="HealthPotion",
    item_type=ItemType.CONSUMABLE,
    namespace="myaddon",
)
```

### 武器

```python
item = skill.generate_item(
    name="DiamondSword",
    item_type=ItemType.WEAPON,
    components=[
        {"name": "minecraft:durability", "parameters": {"max_durability": 1561}},
        {"name": "minecraft:damage", "parameters": {"value": 7}},
    ],
    namespace="myaddon",
)
```

### 工具

```python
item = skill.generate_item(
    name="MagicPickaxe",
    item_type=ItemType.TOOL,
    namespace="myaddon",
)
```

### 物品类型

| 类型 | 描述 |
|------|------|
| `CONSUMABLE` | 消耗品（药水、食物） |
| `TOOL` | 工具（镐、斧、锹） |
| `WEAPON` | 武器（剑、弓） |
| `ARMOR` | 护甲（头盔、胸甲） |
| `BLOCK_ITEM` | 方块物品 |
| `SPECIAL` | 特殊物品 |

---

## 方块生成

### 基础方块

```python
block = skill.generate_block(
    name="CustomStone",
    block_type=BlockType.BASIC,
    namespace="myaddon",
)
```

### 交互方块

```python
block = skill.generate_block(
    name="MagicChest",
    block_type=BlockType.INTERACTIVE,
    namespace="myaddon",
)
```

### 功能方块

```python
block = skill.generate_block(
    name="PowerGenerator",
    block_type=BlockType.FUNCTIONAL,
    namespace="myaddon",
)
```

### 方块类型

| 类型 | 描述 |
|------|------|
| `BASIC` | 基础方块（石头、泥土） |
| `INTERACTIVE` | 交互方块（箱子、门） |
| `FUNCTIONAL` | 功能方块（红石设备） |
| `DECORATION` | 装饰方块 |

---

## 事件监听器生成

### 基本事件监听

```python
listener = skill.generate_event_listener(
    event_name="OnServerChat",
    callback_name="on_chat",
    scope="server",
)

print(listener.code)
```

### 自定义处理代码

```python
listener = skill.generate_event_listener(
    event_name="OnPlayerJoined",
    callback_name="on_player_join",
    custom_code="""
    player_name = event["playerName"]
    print(f"Player joined: {player_name}")
    # 自定义欢迎逻辑
    """,
)
```

### 常用事件

| 事件 | 作用域 | 描述 |
|------|--------|------|
| `OnServerChat` | server | 服务器聊天 |
| `OnPlayerJoined` | server | 玩家加入 |
| `OnPlayerLeft` | server | 玩家离开 |
| `OnEntityAdded` | server | 实体添加 |
| `OnEntityRemoved` | server | 实体移除 |
| `OnServerTick` | server | 服务器刻 |
| `OnClientTick` | client | 客户端刻 |

---

## API 智能建议

```python
# 根据上下文获取 API 建议
suggestions = skill.get_api_suggestions(
    context="创建实体并设置位置",
    top_k=5,
)

for suggestion in suggestions:
    print(f"API: {suggestion.name}")
    print(f"描述: {suggestion.description}")
    print(f"示例: {suggestion.example}")
```

---

## 配置验证

### 验证实体配置

```python
entity_config = {
    "minecraft:entity": {
        "description": {"identifier": "myaddon:custom_mob"},
        "components": {
            "minecraft:health": {"value": 20},
        },
    }
}

result = skill.validate_config(entity_config, config_type="entity")

if result.valid:
    print("配置有效")
else:
    for error in result.errors:
        print(f"错误: {error}")
    for warning in result.warnings:
        print(f"警告: {warning}")
```

### 验证物品配置

```python
item_config = {
    "minecraft:item": {
        "description": {"identifier": "myaddon:custom_item"},
    }
}

result = skill.validate_config(item_config, config_type="item")
```

### 验证方块配置

```python
block_config = {
    "minecraft:block": {
        "description": {"identifier": "myaddon:custom_block"},
    }
}

result = skill.validate_config(block_config, config_type="block")
```

---

## 内置模板

### 常用行为

```python
# 查看内置行为
print(skill.COMMON_BEHAVIORS)
# ['movement', 'attack', 'navigation', 'look_at_player', 'random_stroll', ...]
```

### 常用组件

```python
# 查看内置组件
print(skill.COMMON_COMPONENTS)
# ['minecraft:health', 'minecraft:type_family', 'minecraft:collision_box', ...]
```

### 常用事件

```python
# 查看内置事件
print(skill.COMMON_EVENTS)
# ['OnServerChat', 'OnPlayerJoined', 'OnEntityAdded', ...]
```

---

## CLI 命令

### 生成实体

```bash
mc-agent generate entity --name CustomZombie --type hostile --namespace myaddon
```

### 生成物品

```bash
mc-agent generate item --name HealthPotion --type consumable --namespace myaddon
```

### 生成方块

```bash
mc-agent generate block --name MagicChest --type interactive --namespace myaddon
```

### 验证配置

```bash
mc-agent validate entity_config.json --type entity
```

---

## 最佳实践

### 1. 使用命名空间

始终使用明确的命名空间，避免冲突：

```python
entity = skill.generate_entity(
    name="MyMob",
    namespace="my_unique_addon",  # 使用独特的命名空间
)
```

### 2. 组合使用组件

合理组合组件以实现预期行为：

```python
entity = skill.generate_entity(
    name="FlyingMob",
    entity_type=EntityType.HOSTILE,
    components=[
        {"name": "minecraft:health", "parameters": {"value": 30}},
        {"name": "minecraft:flying_speed", "parameters": {"value": 0.5}},
        {"name": "minecraft:navigation.fly", "parameters": {}},
    ],
)
```

### 3. 验证生成的配置

始终验证生成的配置：

```python
entity = skill.generate_entity("TestMob")
result = skill.validate_config(entity.entity_json, "entity")

if not result.valid:
    print("配置有问题，请检查：")
    for error in result.errors:
        print(f"  - {error}")
```

### 4. 检查生成的代码

使用代码分析器检查生成的脚本：

```python
from mc_agent_kit.analysis.code_analyzer import create_code_analyzer

analyzer = create_code_analyzer()
analysis = analyzer.analyze(entity.script_code, "entity.py")

print(f"代码质量分数: {analysis.score}")
```

---

## 常见问题

### Q: 生成的实体无法加载？

检查以下几点：
1. 命名空间是否正确
2. 实体 JSON 是否有效（使用 `validate_config`）
3. 资源文件是否完整

### Q: 事件监听器不触发？

确保：
1. 事件名称正确
2. 作用域匹配（server/client）
3. 已正确注册事件

### Q: 组件参数不正确？

参考官方文档或使用 API 建议功能获取正确参数。

---

## 参考链接

- [MC-Agent-Kit 文档](./getting-started.md)
- [代码分析器使用指南](./code-analysis.md)
- [项目模板使用指南](./templates.md)
- [调试器使用指南](./debugger.md)

---

*文档版本: v1.45.0*
*最后更新: 2026-03-24*