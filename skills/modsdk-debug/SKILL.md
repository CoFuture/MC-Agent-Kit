# ModSDK 调试辅助 Skill

## 概述

分析 ModSDK 错误日志，提供错误诊断和解决方案建议。

## 使用场景

- 错误日志分析
- 错误类型识别
- 解决方案建议
- 常见问题诊断

## 工具说明

### mc_debug

分析 ModSDK 错误日志。

**参数**:
- `log_content` (str): 日志内容
- `action` (str): 操作类型 (diagnose/analyze/list_errors)

**返回**:
- `errors`: 诊断结果列表
- `statistics`: 错误统计信息

## 操作类型

### diagnose
诊断错误日志，返回识别到的错误和解决建议。

```
mc_debug(
    action="diagnose",
    log_content="SyntaxError: invalid syntax on line 10"
)
```

**返回**:
```json
{
  "errors": [
    {
      "error_type": "SyntaxError",
      "message": "SyntaxError: invalid syntax on line 10",
      "category": "syntax",
      "severity": "error",
      "line_number": 10,
      "suggestions": [
        "检查代码语法是否正确",
        "检查括号、引号是否匹配",
        "检查缩进是否正确"
      ]
    }
  ]
}
```

### analyze
深度分析日志内容，提供错误统计和优先处理建议。

```
mc_debug(
    action="analyze",
    log_content="..."
)
```

**返回**:
```json
{
  "errors": [...],
  "statistics": {
    "total_errors": 5,
    "by_type": {"SyntaxError": 2, "NameError": 3},
    "by_severity": {"error": 5, "warning": 0},
    "by_category": {"syntax": 2, "runtime": 3}
  },
  "total_lines": 100
}
```

### list_errors
列出支持的错误模式。

```
mc_debug(action="list_errors")
```

## 支持的错误类型

### 语法错误
- `SyntaxError` - Python 语法错误
- `IndentationError` - 缩进错误

### 运行时错误
- `NameError` - 变量未定义
- `TypeError` - 类型错误
- `AttributeError` - 属性不存在
- `KeyError` - 字典键不存在
- `IndexError` - 索引越界

### API 错误
- `ComponentNotFound` - 组件未找到
- `APINotFound` - API 未找到
- `InvalidParameter` - 参数无效

### 事件错误
- `EventNotRegistered` - 事件未注册
- `EventListenFailed` - 事件监听失败

### 配置错误
- `ConfigNotFound` - 配置文件未找到
- `InvalidConfig` - 配置无效
- `AddonNotFound` - Addon 未找到

### ModSDK 特定错误
- `ModNotLoaded` - Mod 未加载

## 错误严重程度

| 级别 | 说明 |
|------|------|
| error | 错误，需要立即处理 |
| warning | 警告，建议处理 |
| info | 信息，可忽略 |

## 使用示例

### 示例 1: 诊断语法错误

```
mc_debug(
    action="diagnose",
    log_content="File \"main.py\", line 10\nSyntaxError: invalid syntax"
)
```

### 示例 2: 分析完整日志

```
mc_debug(
    action="analyze",
    log_content="完整的日志内容..."
)
```

### 示例 3: 处理 NameError

```
mc_debug(
    action="diagnose",
    log_content="NameError: name 'player_id' is not defined"
)
```

## 最佳实践

1. 提供完整的错误日志，包括文件名和行号
2. 从错误类型最多的问题开始修复
3. 修复后重新运行测试验证
4. 结合 API 文档确认正确用法

## 注意事项

- 仅识别已定义的错误模式
- 复杂问题可能需要人工分析
- 建议配合代码生成 Skill 使用

---

*Skill 版本: 1.0.0*
*最后更新: 2026-03-22*