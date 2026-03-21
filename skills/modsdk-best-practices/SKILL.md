# ModSDK 最佳实践 Skill

提供 ModSDK 开发最佳实践检查和建议。

## 工具说明

### mc_check_best_practices

检查代码是否遵循 ModSDK 最佳实践。

**参数**:
- `code` (string): 源代码

**返回**: 检查结果列表，包含：
- `practice_id`: 实践 ID
- `practice_name`: 实践名称
- `category`: 类别
- `message`: 检查消息
- `line`: 行号
- `passed`: 是否通过
- `suggestion`: 修复建议

**示例**:
```
用户: 检查这段代码是否符合最佳实践
代码:
def on_tick(args):
    for player in GetPlayerList():
        heavy_operation(player)

助手: 检测到以下问题：

1. [PERF001] 避免在 Tick 事件中进行昂贵操作
   第 2 行：Tick 事件处理函数中包含循环，可能影响性能
   建议：考虑将操作分摊到多个 Tick 中执行
```

### mc_list_practices

列出 ModSDK 最佳实践。

**参数**:
- `category` (string, 可选): 按类别过滤
  - performance: 性能优化
  - security: 安全性
  - maintainability: 可维护性
  - modsdk: ModSDK 特定
  - coding_style: 编码风格
  - error_handling: 错误处理

**返回**: 最佳实践列表

**示例**:
```
用户: 列出性能相关的最佳实践
助手: 性能优化最佳实践：

1. PERF001: 避免在 Tick 事件中进行昂贵操作
   Tick 事件每帧触发，应避免在其中执行耗时操作

2. PERF002: 使用缓存避免重复计算
   对于频繁访问但不常变化的数据，应使用缓存

3. PERF003: 批量操作代替循环调用
   优先使用批量 API 而不是循环调用单个 API
```

### mc_get_practice

获取特定最佳实践的详细信息。

**参数**:
- `practice_id` (string): 实践 ID（如 PERF001）

**返回**: 最佳实践详情，包含：
- `name`: 名称
- `description`: 描述
- `rationale`: 原因说明
- `examples_good`: 好的示例
- `examples_bad`: 坏的示例
- `severity`: 严重程度

**示例**:
```
用户: 详细说明 MSDK001 最佳实践
助手: MSDK001: 使用正确的事件监听注册

描述：使用 ListenForEvent 或 RegisterXxxEventListener 注册事件

原因：正确的事件注册确保事件能够被正确触发

好的示例：
ListenForEvent('OnScriptTickServerEvent', self, self.on_tick)
RegisterEntityEventListener(entity_id, 'EntityHurtEvent', self, self.on_hurt)

坏的示例：
def OnScriptTickServerEvent(args):
    pass  # 定义但未注册
```

## 最佳实践类别

### 性能优化 (PERF)
- PERF001: 避免在 Tick 事件中进行昂贵操作
- PERF002: 使用缓存避免重复计算
- PERF003: 批量操作代替循环调用

### 安全性 (SEC)
- SEC001: 验证外部输入
- SEC002: 限制敏感操作权限

### 可维护性 (MAIN)
- MAIN001: 使用有意义的变量名
- MAIN002: 避免魔法数字
- MAIN003: 函数职责单一

### ModSDK 特定 (MSDK)
- MSDK001: 使用正确的事件监听注册
- MSDK002: 服务端/客户端代码分离
- MSDK003: 使用 NotifyToClient/NotifyToServer 进行通信
- MSDK004: 正确处理实体 ID

### 错误处理 (ERR)
- ERR001: 使用 try-except 处理可能失败的 API 调用
- ERR002: 提供有意义的错误信息

### 编码风格 (STYLE)
- STYLE001: 遵循 PEP 8 编码规范
- STYLE002: 使用文档字符串

## 使用场景

- 代码审查
- 新手学习 ModSDK 开发
- 代码质量改进
- 团队规范执行