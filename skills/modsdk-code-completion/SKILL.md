# ModSDK 代码补全 Skill

提供 ModSDK 智能代码补全功能，支持 API、事件、参数提示等。

## 工具说明

### mc_code_complete

智能代码补全，根据上下文提供补全建议。

**参数**:
- `code` (string): 当前代码
- `cursor_line` (integer): 光标所在行（0-based）
- `cursor_column` (integer): 光标所在列（0-based）

**返回**: 补全建议列表，包含：
- `label`: 显示文本
- `kind`: 补全类型（api/event/parameter/snippet）
- `detail`: 详细信息
- `insert_text`: 插入文本

**示例**:
```
用户: 帮我补全 GetEngine
助手: 我来提供代码补全建议...

补全建议：
1. GetEngine - 获取引擎对象
2. GetEngineType - 获取引擎类型
```

### mc_complete_api

API 名称自动补全。

**参数**:
- `prefix` (string): API 名称前缀
- `limit` (integer, 可选): 返回数量，默认 20

**返回**: 匹配的 API 名称列表

**示例**:
```
用户: 列出以 Get 开头的 API
助手: 找到以下 API：
- GetConfig
- GetEngine
- GetGameType
- GetEngineType
...
```

### mc_complete_event

事件名称自动补全。

**参数**:
- `prefix` (string): 事件名称前缀
- `limit` (integer, 可选): 返回数量，默认 20

**返回**: 匹配的事件名称列表

**示例**:
```
用户: 列出 Entity 相关的事件
助手: 找到以下事件：
- EntityHurtEvent
- EntityDieEvent
- EntityStepOnBlockEvent
...
```

## 使用场景

- 编写 ModSDK 代码时需要 API 提示
- 需要查找特定事件名称
- 函数参数补全
- 代码片段插入

## 注意事项

- 补全基于内置 API 和事件列表
- 可与知识库集成提供更多补全
- 支持成员补全（如 `GetConfig.` 后的成员）