# ModSDK API 文档检索

## 描述

搜索网易 Minecraft ModSDK API 文档，支持关键词搜索、模块过滤、作用域过滤。

## 使用场景

- 查询 ModSDK API 接口用法
- 查找特定功能的 API
- 了解 API 参数和返回值
- 获取 API 代码示例

## 调用方式

```python
from mc_agent_kit.skills import ModSDKAPISearchSkill

skill = ModSDKAPISearchSkill()
skill.initialize()

# 搜索 API
result = skill.execute(query="entity", scope="server", limit=5)

# 获取指定 API
result = skill.execute(name="GetEngineType")

# 按模块搜索
result = skill.execute(query="create", module="物品")
```

## 参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| query | str | 搜索关键词 | 否 |
| name | str | API 名称（精确匹配） | 否 |
| module | str | 模块过滤 | 否 |
| scope | str | 作用域过滤：client/server/both | 否 |
| return_type | str | 按返回类型搜索 | 否 |
| param_name | str | 按参数名搜索 | 否 |
| fuzzy | bool | 是否模糊搜索 | 否 |
| limit | int | 返回结果数量限制 | 否 |

## 返回格式

```json
{
  "success": true,
  "data": [
    {
      "name": "GetEngineType",
      "module": "游戏通用",
      "description": "获取引擎类型",
      "scope": "both",
      "parameters": [],
      "return_type": "str",
      "examples": [],
      "remarks": []
    }
  ],
  "message": "找到 1 个匹配的 API"
}
```

## 示例

### 搜索实体相关 API

```
用户: 查找实体相关的服务端 API
助手: 我来搜索实体相关的服务端 API...
```

```python
skill.execute(query="entity", scope="server")
```

### 获取指定 API 详情

```
用户: GetEngineType 这个 API 怎么用？
助手: 我来查询 GetEngineType 的详细信息...
```

```python
skill.execute(name="GetEngineType")
```

### 按模块搜索

```
用户: 物品模块有哪些创建类 API？
助手: 我来搜索物品模块的创建类 API...
```

```python
skill.execute(query="create", module="物品")
```

## 注意事项

- 需要先加载知识库才能使用
- 支持中英文关键词
- 作用域支持中文：客户端/服务端/双端

---

*版本: 1.0.0*
*作者: MC-Agent-Kit*