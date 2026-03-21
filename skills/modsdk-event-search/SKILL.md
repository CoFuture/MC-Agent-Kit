# ModSDK 事件文档检索

## 描述

搜索网易 Minecraft ModSDK 事件文档，支持关键词搜索、模块过滤、作用域过滤。

## 使用场景

- 查询 ModSDK 事件用法
- 查找特定事件
- 了解事件参数
- 获取事件监听示例

## 调用方式

```python
from mc_agent_kit.skills import ModSDKEventSearchSkill

skill = ModSDKEventSearchSkill()
skill.initialize()

# 搜索事件
result = skill.execute(query="hurt", scope="server")

# 获取指定事件
result = skill.execute(name="AddEntityClientEvent")

# 按模块搜索
result = skill.execute(module="实体")
```

## 参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| query | str | 搜索关键词 | 否 |
| name | str | 事件名称（精确匹配） | 否 |
| module | str | 模块过滤 | 否 |
| scope | str | 作用域过滤：client/server/both | 否 |
| param_name | str | 按参数名搜索 | 否 |
| fuzzy | bool | 是否模糊搜索 | 否 |
| limit | int | 返回结果数量限制 | 否 |

## 返回格式

```json
{
  "success": true,
  "data": [
    {
      "name": "AddEntityClientEvent",
      "module": "实体",
      "description": "实体被添加到客户端时触发",
      "scope": "client",
      "parameters": [
        {
          "name": "id",
          "type": "str",
          "description": "实体 ID"
        }
      ],
      "examples": [],
      "remarks": []
    }
  ],
  "message": "找到 1 个匹配的事件"
}
```

## 示例

### 搜索伤害相关事件

```
用户: 有哪些与伤害相关的事件？
助手: 我来搜索伤害相关的事件...
```

```python
skill.execute(query="hurt")
```

### 获取指定事件详情

```
用户: AddEntityClientEvent 事件什么时候触发？
助手: 我来查询 AddEntityClientEvent 的详细信息...
```

```python
skill.execute(name="AddEntityClientEvent")
```

### 按模块和作用域搜索

```
用户: 服务端有哪些玩家相关事件？
助手: 我来搜索服务端玩家相关事件...
```

```python
skill.execute(query="player", scope="server")
```

## 注意事项

- 需要先加载知识库才能使用
- 支持中英文关键词
- 作用域支持中文：客户端/服务端/双端

---

*版本: 1.0.0*
*作者: MC-Agent-Kit*