# 自定义物品示例模组

演示如何创建自定义物品。

## 功能

- 注册自定义物品 "冰霜精华"
- 物品使用功能（给予玩家效果）
- 可堆叠、可合成

## 文件结构

```
custom-item/
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

## 使用方法

1. 准备物品图标（16x16 或 32x32 PNG）
2. 将此目录复制到 ModSDK 开发目录
3. 重启游戏服务器
4. 使用命令获取物品: `/give @p custom:frost_essence`

## 测试

```bash
# 检查代码
mc-agent check -f frost_essence.py

# 搜索物品相关 API
mc-agent api -q "RegisterItem"

# 搜索物品事件
mc-agent event -q "ItemUse"
```