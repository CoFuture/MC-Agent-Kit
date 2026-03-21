# 自定义物品教程

本教程将带你创建一个自定义物品。

## 目标

创建一个自定义物品 "冰霜精华"，具有以下特性：

- 独特的图标和名称
- 右键使用功能（给予玩家冰霜效果）
- 可堆叠

## 准备工作

- 完成 [Hello World 教程](hello-world.md)
- 准备物品图标文件（.png，推荐 16x16 或 32x32）

## 步骤 1：搜索物品相关 API

```bash
# 搜索物品注册 API
mc-agent api -q "item" -l 5

# 搜索物品使用事件
mc-agent event -q "UseItem" -l 5
```

## 步骤 2：生成物品注册代码

```bash
mc-agent gen -t item_register -p '{
  "item_id": "frost_essence",
  "item_name": "冰霜精华",
  "namespace": "custom",
  "icon_path": "textures/items/frost_essence.png",
  "max_stack": 64
}'
```

生成的代码：

```python
# frost_essence.py
# 冰霜精华物品定义

import mod.server.extraServerApi as serverApi

# 物品 ID
FROST_ESSENCE_ID = "custom:frost_essence"

class FrostEssenceMod:
    """冰霜精华模组"""
    
    def __init__(self):
        self.comp_factory = serverApi.GetEngineCompFactory()
    
    def on_load(self):
        """模组加载时调用"""
        self._register_item()
        self._register_events()
        print("[FrostEssence] 冰霜精华模组已加载")
    
    def _register_item(self):
        """注册自定义物品"""
        item_def = {
            "identifier": FROST_ESSENCE_ID,
            "components": {
                "minecraft:icon": "frost_essence",
                "minecraft:max_stack_size": 64,
                "minecraft:hand_equipped": False,
                "minecraft:foil": True  # 附魔光效
            }
        }
        
        # 注册物品
        self.comp_factory.RegisterItem(item_def)
    
    def _register_events(self):
        """注册事件监听器"""
        # 物品使用事件
        self.comp_factory.RegisterOnServerItemUse(self._on_item_use)
    
    def _on_item_use(self, args):
        """物品使用回调"""
        player_id = args.get('playerId')
        item_id = args.get('itemId')
        
        # 检查是否是冰霜精华
        if item_id == FROST_ESSENCE_ID:
            self._use_frost_essence(player_id)
            return True  # 消耗物品
        return False
    
    def _use_frost_essence(self, player_id):
        """使用冰霜精华"""
        # 给予玩家冰霜效果
        self.comp_factory.AddEffectToEntity(
            player_id,
            "slowness",
            10,  # 持续时间（秒）
            2    # 效果等级
        )
        
        # 给予速度效果（对自身）
        self.comp_factory.AddEffectToEntity(
            player_id,
            "speed",
            10,
            1
        )
        
        # 发送消息
        self.comp_factory.NotifyToClient(
            player_id,
            "§b你使用了冰霜精华！"
        )
        
        print(f"[FrostEssence] Player {player_id} used frost essence")


# 模组入口
mod = FrostEssenceMod()
mod.on_load()
```

## 步骤 3：创建物品配置文件

创建 `items/frost_essence.json`：

```json
{
  "format_version": "1.10.0",
  "minecraft:item": {
    "description": {
      "identifier": "custom:frost_essence",
      "category": "Items"
    },
    "components": {
      "minecraft:icon": {
        "texture": "frost_essence"
      },
      "minecraft:max_stack_size": 64,
      "minecraft:hand_equipped": false,
      "minecraft:foil": true,
      "minecraft:creative_category": {
        "parent": "itemGroup.name.items"
      }
    }
    "events": {
      "minecraft:entity_use": {
        "sequence": [
          {
            "run_command": {
              "command": "effect @p slowness 10 2"
            }
          },
          {
            "run_command": {
              "command": "effect @p speed 10 1"
            }
          }
        ]
      }
    }
  }
}
```

## 步骤 4：创建语言文件

创建 `texts/zh_CN.lang`：

```
item.custom:frost_essence=冰霜精华
item.custom:frost_essence.description=蕴含冰霜之力的神秘精华
```

创建 `texts/en_US.lang`：

```
item.custom:frost_essence=Frost Essence
item.custom:frost_essence.description=A mysterious essence containing frost power
```

## 步骤 5：添加合成配方

创建 `recipes/frost_essence.json`：

```json
{
  "format_version": "1.12.0",
  "minecraft:recipe_shaped": {
    "description": {
      "identifier": "custom:frost_essence_recipe"
    },
    "tags": ["crafting_table"],
    "pattern": [
      " I ",
      "ISI",
      " I "
    ],
    "key": {
      "I": {
        "item": "minecraft:ice"
      },
      "S": {
        "item": "minecraft:snowball"
      }
    },
    "result": {
      "item": "custom:frost_essence",
      "count": 1
    }
  }
}
```

## 步骤 6：检查代码

```bash
# 检查最佳实践
mc-agent check -f frost_essence.py

# 生成重构建议
mc-agent refactor -f frost_essence.py -a suggest
```

## 步骤 7：测试物品

```bash
# 启动游戏测试
mc-agent launch --addon ./frost-essence-mod

# 给予物品（游戏内执行）
mc-agent exec --command "give @p custom:frost_essence 10"
```

## 完整项目结构

```
frost-essence-mod/
├── mod.json
├── frost_essence.py
├── items/
│   └── frost_essence.json
├── textures/
│   └── items/
│       └── frost_essence.png
├── texts/
│   ├── zh_CN.lang
│   └── en_US.lang
└── recipes/
    └── frost_essence.json
```

## 扩展功能

### 添加冷却时间

```python
# 使用字典存储冷却时间
_cooldowns = {}

def _on_item_use(self, args):
    player_id = args.get('playerId')
    item_id = args.get('itemId')
    
    if item_id == FROST_ESSENCE_ID:
        # 检查冷却
        if self._is_on_cooldown(player_id):
            self.comp_factory.NotifyToClient(
                player_id,
                "§c冰霜精华正在冷却中..."
            )
            return False
        
        self._use_frost_essence(player_id)
        self._set_cooldown(player_id, 30)  # 30秒冷却
        return True
    return False
```

### 添加耐久度

```python
"minecraft:durability": {
    "max_durability": 50,
    "damage_chance": {
        "min": 1,
        "max": 1
    }
}
```

## 常见问题

### Q: 物品图标不显示？

1. 确保图标文件路径正确
2. 检查 `textures/item_texture.json` 配置
3. 确保 PNG 文件格式正确

### Q: 物品名称显示为 key？

检查语言文件是否正确放置在 `texts/` 目录下。

### Q: 物品使用没有反应？

确保事件回调返回 `True` 来消耗物品，并检查事件是否正确注册。

## 下一步

- 学习 [自定义 UI 教程](custom-ui.md)
- 查看 [物品 API 参考](api-item.md)

---

*最后更新：2026-03-22*