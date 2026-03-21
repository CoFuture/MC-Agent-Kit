# 自定义实体示例模组

演示如何创建自定义实体（怪物/动物）。

## 功能

- 注册自定义实体 "冰霜幽灵"
- 设置实体属性（生命值、移动速度、攻击力）
- 定义实体行为和事件响应
- 配置生成规则和掉落物

## 文件结构

```
custom-entity/
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

## 使用方法

1. 准备模型文件和材质文件
2. 将此目录复制到 ModSDK 开发目录
3. 重启游戏服务器
4. 使用命令召唤实体: `/summon custom:frost_ghost ~ ~ ~`

## 测试

```bash
# 检查代码
mc-agent check -f frost_ghost.py

# 搜索实体相关 API
mc-agent api -q "CreateEntity"

# 搜索实体事件
mc-agent event -q "entity" -m "entity"
```