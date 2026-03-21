# ModSDK 自动修复 Skill

## 概述

自动诊断和修复 ModSDK 代码中的常见错误，支持修复预览和批量处理。

## 使用场景

- 错误自动诊断
- 代码自动修复
- 修复预览对比
- 批量问题处理

## 工具说明

### mc_diagnose

诊断代码错误。

**参数**:
- `code` (str): 代码内容
- `error_log` (str): 错误日志

**返回**:
- `errors`: 错误列表
- `suggestions`: 修复建议

### mc_autofix

自动修复代码错误。

**参数**:
- `code` (str): 原始代码
- `error_log` (str): 错误日志
- `auto_apply` (bool, optional): 是否自动应用，默认 False

**返回**:
- `fixed_code`: 修复后的代码
- `replacements`: 替换列表
- `status`: 修复状态

### mc_preview_fix

预览修复效果。

**参数**:
- `code` (str): 原始代码
- `error_log` (str): 错误日志

**返回**:
- `diff`: 差异对比（unified diff 格式）

### mc_list_fixes

列出支持的自动修复。

**返回**:
- `fixes`: 支持的修复类型列表

## 使用示例

### 示例 1: 诊断并修复 KeyError

```
code = '''
data = {"name": "test"}
value = data["missing_key"]
'''

error_log = "KeyError: 'missing_key'"

# 诊断
result = mc_diagnose(code, error_log)
print(result['suggestions'])

# 预览修复
diff = mc_preview_fix(code, error_log)
print(diff)

# 应用修复
fix_result = mc_autofix(code, error_log, auto_apply=True)
print(fix_result['fixed_code'])
```

输出:

```python
data = {"name": "test"}
value = data.get("missing_key")  # 自动添加默认值
```

### 示例 2: 修复 AttributeError

```
code = '''
obj = SomeClass()
obj.non_existent_method()
'''

result = mc_autofix(code, "AttributeError: 'SomeClass' has no attribute 'non_existent_method'")
```

输出:

```python
obj = SomeClass()
getattr(obj, 'non_existent_method', None)()  # 安全调用
```

### 示例 3: 修复 IndexError

```
code = '''
items = [1, 2, 3]
value = items[5]
'''

result = mc_autofix(code, "IndexError: list index out of range")
```

输出:

```python
items = [1, 2, 3]
value = items[5] if len(items) > 5 else None  # 边界检查
```

### 示例 4: 批量修复

```
code = '''
# 多个错误的代码
data = {}
value = data["key"]  # KeyError
items = [1]
item = items[5]  # IndexError
result = 10 / 0  # ZeroDivisionError
'''

# 获取所有修复建议
result = mc_diagnose(code, "...")
for error in result['errors']:
    print(f"- {error['type']}: {error['message']}")
    for suggestion in error['suggestions']:
        print(f"  → {suggestion}")
```

## 支持的自动修复

### KeyError 修复

**问题**: 访问不存在的字典键

**修复策略**: 使用 `.get()` 方法

```python
# 修复前
value = data["key"]

# 修复后
value = data.get("key")
# 或
value = data.get("key", default_value)
```

### AttributeError 修复

**问题**: 访问不存在的属性或方法

**修复策略**: 使用 `getattr()` 或 `hasattr()`

```python
# 修复前
obj.method()

# 修复后
getattr(obj, 'method', lambda: None)()
# 或
if hasattr(obj, 'method'):
    obj.method()
```

### IndexError 修复

**问题**: 列表索引越界

**修复策略**: 添加边界检查

```python
# 修复前
value = items[index]

# 修复后
value = items[index] if index < len(items) else None
```

### ZeroDivisionError 修复

**问题**: 除零错误

**修复策略**: 添加除零检查

```python
# 修复前
result = a / b

# 修复后
result = a / b if b != 0 else 0
```

### NameError 修复

**问题**: 变量未定义

**修复策略**: 提示定义变量或检查拼写

```python
# 修复前
print(unknown_var)

# 建议
# 1. 检查变量名拼写
# 2. 确认变量是否已定义
# 3. 检查作用域
```

## 修复信心等级

| 等级 | 说明 | 建议 |
|------|------|------|
| high | 高信心，修复安全 | 可直接应用 |
| medium | 中等信心，建议检查 | 预览后应用 |
| low | 低信心，需要人工判断 | 仅提供建议 |

## 修复状态

| 状态 | 说明 |
|------|------|
| success | 修复成功 |
| partial | 部分修复 |
| failed | 修复失败 |
| manual_required | 需要人工处理 |

## 最佳实践

1. 先预览再应用修复
2. 一次修复一个错误类型
3. 修复后运行测试验证
4. 复杂问题考虑手动修复

## 注意事项

- 自动修复可能改变代码行为
- 修复后务必测试验证
- 不支持所有错误类型
- 复杂逻辑需要人工判断

---

*Skill 版本: 1.0.0*
*最后更新: 2026-03-22*