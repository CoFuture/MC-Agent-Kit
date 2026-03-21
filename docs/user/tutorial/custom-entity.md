# 自定义实体教程

本教程将带你创建一个自定义实体（怪物/动物）。

## 目标

创建一个自定义怪物 "冰霜幽灵"，具有以下特性：

- 独特的外观（使用模型和材质）
- 冰霜攻击能力
- 特殊掉落物

## 准备工作

- 完成 [Hello World 教程](hello-world.md)
- 准备实体模型文件（.json）和材质文件（.png）

## 步骤 1：搜索实体相关 API

```bash
# 搜索实体创建 API
mc-agent api -q "CreateEntity" -l 5

# 搜索实体事件
mc-agent event -q "entity" -m "entity" -l 5
```

## 步骤 2：生成实体注册代码

```bash
mc-agent gen -t entity_create -p '{
  "entity_id": "frost_ghost",
  "entity_name": "冰霜幽灵",
  "namespace": "custom",
  "model_path": "models/entity/frost_ghost.json",
  "texture_path": "textures/entity/frost_ghost.png"
}'
```

生成的代码：

```python
# frost_ghost.py
# 冰霜幽灵实体定义

import mod.server.extraServerApi as serverApi
from mod.common.mod import Mod

# 实体 ID
FROST_GHOST_ID = "custom:frost_ghost"

class FrostGhostMod(Mod):
    """冰霜幽灵模组"""
    
    def __init__(self):
        self.comp_factory = serverApi.GetEngineCompFactory()
    
    def on_load(self):
        """模组加载时调用"""
        self._register_entity()
        self._register_events()
        print("[FrostGhost] 冰霜幽灵模组已加载")
    
    def _register_entity(self):
        """注册自定义实体"""
        # 实体定义
        entity_def = {
            "identifier": FROST_GHOST_ID,
            "runtime_identifier": "minecraft:zombie",  # 基于僵尸行为
            "components": {
                "minecraft:type_family": {"family": ["monster", "undead"]},
                "minecraft:health": {"value": 30, "max": 30},
                "minecraft:movement": {"value": 0.25},
                "minecraft:attack": {"damage": 5},
                "minecraft:loot": {"table": "loot_tables/entities/frost_ghost.json"}
            }
        }
        
        # 注册实体
        self.comp_factory.RegisterEntity(entity_def)
    
    def _register_events(self):
        """注册事件监听器"""
        # 实体受伤事件
        self.comp_factory.RegisterOnEntityHurt(self._on_entity_hurt)
        
        # 实体死亡事件
        self.comp_factory.RegisterOnEntityDie(self._on_entity_die)
    
    def _on_entity_hurt(self, args):
        """实体受伤回调"""
        entity_id = args.get('entityId')
        damage = args.get('damage', 0)
        
        if entity_id == FROST_GHOST_ID:
            # 冰霜幽灵受伤时释放冰霜效果
            self._cast_frost_effect(args.get('srcId'))
    
    def _on_entity_die(self, args):
        """实体死亡回调"""
        entity_id = args.get('entityId')
        
        if entity_id == FROST_GHOST_ID:
            print("[FrostGhost] 冰霜幽灵被击败！")
    
    def _cast_frost_effect(self, target_id):
        """对目标施加冰霜效果"""
        if target_id:
            # 减速效果
            self.comp_factory.AddEffectToEntity(
                target_id,
                "slowness",
                3,  # 持续时间（秒）
                1   # 效果等级
            )


# 模组入口
mod = FrostGhostMod()
mod.on_load()
```

## 步骤 3：创建实体配置文件

创建 `entities/frost_ghost.json`：

```json
{
  "format_version": "1.10.0",
  "minecraft:entity": {
    "description": {
      "identifier": "custom:frost_ghost",
      "is_spawnable": true,
      "is_summonable": true,
      "is_experimental": false
    },
    "component_groups": {
      "frost_ghost:spawn": {
        "minecraft:health": {"value": 30, "max": 30},
        "minecraft:movement": {"value": 0.25},
        "minecraft:attack": {"damage": 5}
      }
    },
    "components": {
      "minecraft:type_family": {"family": ["monster", "undead"]},
      "minecraft:physics": {},
      "minecraft:pushable": {"is_pushable": true, "is_pushable_by_piston": true},
      "minecraft:navigation.walk": {"can_path_over_water": false},
      "minecraft:movement.basic": {},
      "minecraft:jump.static": {},
      "minecraft:scale": {"value": 1.2}
    }
  }
}
```

## 步骤 4：创建掉落物配置

创建 `loot_tables/entities/frost_ghost.json`：

```json
{
  "pools": [
    {
      "rolls": 1,
      "entries": [
        {
          "type": "item",
          "name": "custom:frost_essence",
          "weight": 1,
          "functions": [
            {
              "function": "set_count",
              "count": {"min": 1, "max": 3}
            }
          ]
        }
      ]
    }
  ]
}
```

## 步骤 5：添加生成规则

在游戏中添加实体生成规则：

```python
# 在 frost_ghost.py 中添加

def _setup_spawning(self):
    """设置实体生成规则"""
    spawn_rule = {
        "population_control": "monster",
        "conditions": [
            {
                "type": "spawns_on_surface",
                "biomes": ["snowy_tundra", "ice_spikes", "frozen_river"],
                "weight": 10,
                "min_brightness": 0,
                "max_brightness": 7
            }
        ]
    }
    self.comp_factory.RegisterSpawnRule(FROST_GHOST_ID, spawn_rule)
```

## 步骤 6：检查代码

```bash
# 检查最佳实践
mc-agent check -f frost_ghost.py

# 生成重构建议
mc-agent refactor -f frost_ghost.py -a suggest
```

## 步骤 7：测试实体

```bash
# 启动游戏测试
mc-agent launch --addon ./frost-ghost-mod

# 召唤实体（游戏内执行）
mc-agent exec --command "summon custom:frost_ghost ~ ~ ~"
```

## 完整项目结构

```
frost-ghost-mod/
├── mod.json
├── frost_ghost.py
├── entities/
│   └── frost_ghost.json
├── models/
│   └── entity/
│       └── frost_ghost.json
├── textures/
│   └── entity/
│       └── frost_ghost.png
└── loot_tables/
    └── entities/
        └── frost_ghost.json
```

## 扩展功能

### 添加特殊攻击

```python
def _frost_attack(self, target_id):
    """冰霜攻击"""
    # 发射冰霜投射物
    projectile_id = self.comp_factory.CreateEntity(
        "custom:frost_projectile",
        self.comp_factory.GetPosition(self.entity_id)
    )
    self.comp_factory.ShootProjectile(projectile_id, target_id)
```

### 添加 AI 行为

```python
"minecraft:behavior.nearest_attackable_target": {
    "priority": 2,
    "within_radius": 20.0,
    "reselect_targets": true,
    "entity_types": [
        {"filters": {"test": "is_family", "subject": "other", "value": "player"}}
    ]
}
```

## 下一步

- 学习 [自定义物品教程](custom-item.md)
- 学习 [自定义 UI 教程](custom-ui.md)
- 查看 [实体 API 参考](api-entity.md)

---

*最后更新：2026-03-22*