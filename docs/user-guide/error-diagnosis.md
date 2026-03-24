# 错误诊断

MC-Agent-Kit 的错误诊断功能帮助你快速定位和修复代码问题。

## 基本用法

### 诊断错误消息

```bash
# 诊断错误消息
mc-llm diagnose "KeyError: 'speed' not found"

# 带代码上下文
mc-llm diagnose "KeyError: 'speed'" --code main.py

# 带堆栈跟踪
mc-llm diagnose "KeyError: 'speed'" --trace stack_trace.txt
```

### 自动修复

```bash
# 获取修复建议
mc-llm fix "KeyError: 'speed'" --code main.py

# 自动应用修复
mc-llm fix "KeyError: 'speed'" --code main.py --apply
```

## 诊断结果

### 结果格式

```
🔍 Error Diagnosis

Error Type: KeyError
Error Message: 'speed' not found

Location:
  File: main.py
  Line: 42
  Code: speed = config['speed']

Possible Causes:
  1. 变量 speed 未定义
  2. 字典 config 中缺少 speed 键
  3. 拼写错误

Fix Suggestions:

  💡 Confidence: High
  Description: 使用 get() 方法安全访问字典
  Code:
    speed = config.get('speed', 1.0)  # 默认值 1.0

  💡 Confidence: Medium
  Description: 检查键是否存在
  Code:
    if 'speed' in config:
        speed = config['speed']
    else:
        speed = 1.0  # 默认值

Related Documentation:
  - Python Dict get() 方法
  - KeyError 异常处理
```

## 常见错误类型

### KeyError

字典键不存在：

```python
# ❌ 问题代码
value = config['key']

# ✅ 修复方案 1：使用 get()
value = config.get('key', default_value)

# ✅ 修复方案 2：检查键存在
if 'key' in config:
    value = config['key']
```

### AttributeError

对象没有该属性：

```python
# ❌ 问题代码
result = obj.nonexistent_method()

# ✅ 修复方案
if hasattr(obj, 'nonexistent_method'):
    result = obj.nonexistent_method()
else:
    # 处理不存在的情况
    pass
```

### TypeError

类型错误：

```python
# ❌ 问题代码
result = 'string' + 123  # 字符串和数字相加

# ✅ 修复方案
result = 'string' + str(123)  # 转换类型
```

### IndentationError

缩进错误：

```python
# ❌ 问题代码
def func():
print('hello')  # 缩进不正确

# ✅ 修复方案
def func():
    print('hello')  # 正确缩进
```

### NameError

变量未定义：

```python
# ❌ 问题代码
result = undefined_variable

# ✅ 修复方案
defined_variable = some_value
result = defined_variable
```

## ModSDK 特定错误

### API 调用错误

```python
# ❌ 问题：服务端调用客户端 API
# 在 ServerSystem 中
self.CreateUIScreen(...)

# ✅ 修复：使用正确的 API
# 服务端使用 ServerSystem 方法
# 客户端使用 ClientSystem 方法
```

### 事件监听错误

```python
# ❌ 问题：事件名拼写错误
self.ListenForEvent(..., 'OnServerChatWrong', ...)

# ✅ 修复：使用正确的事件名
self.ListenForEvent(..., 'OnServerChat', ...)
```

### 实体操作错误

```python
# ❌ 问题：实体 ID 无效
self.DestroyEntity(invalid_entity_id)

# ✅ 修复：验证实体存在
if self.EntityExists(entity_id):
    self.DestroyEntity(entity_id)
```

## 诊断配置

### 置信度阈值

```bash
# 只显示高置信度的建议
mc-llm diagnose "error" --min-confidence 0.8
```

### 最大建议数

```bash
# 限制建议数量
mc-llm diagnose "error" --max-suggestions 3
```

## 自动修复

### 安全修复

自动修复会先备份原文件：

```bash
# 自动修复会创建备份
mc-llm fix "error" --code main.py --apply

# 备份文件位置
# main.py.backup
```

### 审查修复

```bash
# 先预览修复
mc-llm fix "error" --code main.py --preview

# 确认后再应用
mc-llm fix "error" --code main.py --apply
```

## 调试工作流

### 完整调试流程

```bash
# 1. 运行项目捕获错误
mc-run ./my-addon --timeout 60

# 2. 查看日志
mc-logs --analyze

# 3. 诊断错误
mc-llm diagnose "$(cat error.log)"

# 4. 应用修复
mc-llm fix "error" --code main.py --apply

# 5. 验证修复
mc-run ./my-addon --timeout 60
```

### 交互式调试

```bash
# 启动聊天模式
mc-llm chat

# 描述问题
mc-llm> 我遇到了一个 KeyError: 'playerId' 的错误
mc-llm> 代码是：pos = self.GetPos(args['playerId'])

# AI 会分析问题并给出建议
```

## 常见问题

### Q: 诊断结果不准确？

A: 提供更多上下文：

```bash
# 提供完整代码
mc-llm diagnose "error" --code full_code.py --trace full_trace.txt
```

### Q: 修复后仍有问题？

A: 检查是否有多个问题：

```bash
# 审查修复后的代码
mc-llm review main.py

# 再次诊断
mc-llm diagnose "new error"
```

### Q: 自动修复不安全？

A: 始终预览修复：

```bash
# 先预览
mc-llm fix "error" --preview

# 确认安全后再应用
mc-llm fix "error" --apply
```

## 下一步

- 💬 [聊天模式](./chat-mode.md) - 交互式调试
- 🔧 [自定义提示词](./custom-prompts.md) - 优化诊断效果
- 💡 [最佳实践](../best-practices.md) - 避免常见错误

---

*最后更新: 2026-03-25*