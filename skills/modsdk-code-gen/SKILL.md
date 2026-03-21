# ModSDK 代码生成 Skill

## 概述

基于 Jinja2 模板引擎生成 ModSDK 代码，支持事件监听器、API 调用、实体创建、物品注册、UI 屏幕等模板。

## 使用场景

- 生成事件监听器代码
- 生成 API 调用代码
- 生成实体创建代码
- 生成物品注册代码
- 生成 UI 屏幕代码
- 自定义模板渲染

## 工具说明

### mc_code_gen

生成 ModSDK 代码。

**参数**:
- `template` (str): 模板名称
- `params` (dict): 模板参数
- `action` (str): 操作类型 (generate/list/info/search)
- `keyword` (str): 搜索关键词 (用于搜索模板)
- `custom_template` (str): 自定义 Jinja2 模板

**返回**:
- `code`: 生成的代码
- `template_name`: 模板名称
- `template_type`: 模板类型
- `language`: 代码语言

## 内置模板

### 1. event_listener
生成事件监听器代码。

**参数**:
- `event_name` (str, 必需): 事件名称
- `scope` (str): 作用域 (客户端/服务端)，默认服务端
- `event_params` (list): 事件参数列表
- `description` (str): 事件描述
- `event_namespace` (str): 事件命名空间，默认 Minecraft

**示例**:
```
mc_code_gen(
    template="event_listener",
    params={
        "event_name": "OnServerChat",
        "scope": "服务端",
        "event_params": [
            {"name": "message", "type": "str", "desc": "聊天消息"}
        ]
    }
)
```

### 2. api_call
生成 API 调用代码。

**参数**:
- `api_name` (str, 必需): API 名称
- `scope` (str): 作用域
- `component_factory` (str): 组件工厂方法名
- `api_params` (list): API 参数列表
- `return_type` (str): 返回类型

**示例**:
```
mc_code_gen(
    template="api_call",
    params={
        "api_name": "GetEngineType",
        "scope": "服务端"
    }
)
```

### 3. entity_create
生成创建实体代码。

**参数**:
- `entity_type` (str): 实体类型标识符
- `scope` (str): 作用域，默认服务端

### 4. item_register
生成注册自定义物品代码。

**参数**:
- `item_name` (str, 必需): 物品名称
- `item_identifier` (str, 必需): 物品标识符
- `item_category` (str): 物品分类
- `max_stack` (int): 最大堆叠数量

### 5. ui_screen
生成 UI 屏幕代码。

**参数**:
- `ui_name` (str, 必需): UI 名称
- `description` (str): UI 描述
- `buttons` (list): 按钮名称列表

## 操作类型

### list
列出可用模板。

```
mc_code_gen(action="list")
```

### info
获取模板详细信息。

```
mc_code_gen(action="info", template="event_listener")
```

### search
搜索模板。

```
mc_code_gen(action="search", keyword="event")
```

### generate
生成代码。

```
mc_code_gen(template="event_listener", params={...})
```

## 自定义模板

支持使用 Jinja2 语法编写自定义模板：

```
mc_code_gen(
    custom_template="Hello, {{ name }}!",
    params={"name": "World"}
)
```

## 注意事项

- 生成的代码需要根据实际需求调整
- 注意 Python 2.7 兼容性（ModSDK 运行环境）
- 建议结合 API 文档使用

---

*Skill 版本: 1.0.0*
*最后更新: 2026-03-22*