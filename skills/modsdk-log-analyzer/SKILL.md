# ModSDK 日志分析器 Skill

## 概述

实时分析和处理 Minecraft 游戏日志，支持错误检测、告警和统计。

## 使用场景

- 实时日志监控
- 错误模式检测
- 日志聚合统计
- 告警通知

## 工具说明

### mc_log_stream

启动日志流处理。

**参数**:
- `port` (int): 日志服务器端口
- `buffer_size` (int, optional): 缓冲区大小，默认 1000

**返回**:
- `stream_id` (str): 日志流 ID

### mc_log_analyze

分析日志内容。

**参数**:
- `log_content` (str): 日志内容
- `patterns` (list, optional): 自定义匹配模式

**返回**:
- `errors`: 错误列表
- `warnings`: 警告列表
- `statistics`: 统计信息

### mc_log_search

搜索日志内容。

**参数**:
- `query` (str): 搜索关键词或正则
- `time_range` (tuple, optional): 时间范围 (start, end)
- `level` (str, optional): 日志级别过滤

**返回**:
- `matches`: 匹配结果列表

### mc_log_alert

配置日志告警。

**参数**:
- `pattern` (str): 告警模式
- `severity` (str): 严重程度 (info/warning/error/critical)
- `callback` (str): 告警回调函数

**返回**:
- `alert_id` (str): 告警 ID

## 使用示例

### 示例 1: 实时监控日志

```
# 启动日志流
stream_id = mc_log_stream(port=9000)

# 分析日志
result = mc_log_analyze(log_content="...")
print(f"Found {len(result['errors'])} errors")
```

### 示例 2: 搜索特定错误

```
# 搜索 NameError
matches = mc_log_search(
    query="NameError",
    level="error"
)

for match in matches:
    print(f"Line {match['line']}: {match['content']}")
```

### 示例 3: 配置告警

```
# 配置错误告警
mc_log_alert(
    pattern="SyntaxError|NameError|TypeError",
    severity="error",
    callback="handle_error_alert"
)
```

### 示例 4: 获取统计信息

```
result = mc_log_analyze(log_content="...")
stats = result['statistics']

print(f"Total lines: {stats['total_lines']}")
print(f"Error count: {stats['error_count']}")
print(f"Warning count: {stats['warning_count']}")

# 按类型统计
for error_type, count in stats['by_type'].items():
    print(f"  {error_type}: {count}")
```

## 内置错误模式

### Python 错误

| 模式 | 正则 | 说明 |
|------|------|------|
| SyntaxError | `SyntaxError:.*` | 语法错误 |
| NameError | `NameError:.*` | 变量未定义 |
| TypeError | `TypeError:.*` | 类型错误 |
| KeyError | `KeyError:.*` | 键不存在 |
| IndexError | `IndexError:.*` | 索引越界 |
| AttributeError | `AttributeError:.*` | 属性不存在 |

### ModSDK 错误

| 模式 | 正则 | 说明 |
|------|------|------|
| ComponentNotFound | `Component .* not found` | 组件未找到 |
| EventError | `Event .* error` | 事件错误 |
| ConfigError | `Config .* invalid` | 配置错误 |

## 日志级别

| 级别 | 说明 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 普通信息 |
| WARNING | 警告 |
| ERROR | 错误 |
| CRITICAL | 严重错误 |

## 统计信息

`mc_log_analyze` 返回的统计信息包括：

```json
{
  "total_lines": 1000,
  "error_count": 5,
  "warning_count": 10,
  "info_count": 985,
  "by_type": {
    "SyntaxError": 2,
    "NameError": 3
  },
  "by_level": {
    "error": 5,
    "warning": 10,
    "info": 985
  },
  "time_range": {
    "start": "2026-03-22T10:00:00",
    "end": "2026-03-22T10:30:00"
  }
}
```

## 告警回调

配置告警时，需要定义回调函数：

```python
def handle_error_alert(alert):
    print(f"Alert: {alert['message']}")
    print(f"Severity: {alert['severity']}")
    print(f"Time: {alert['timestamp']}")
```

## 最佳实践

1. 使用 buffer_size 控制内存使用
2. 合理设置告警严重程度
3. 定期清理旧日志
4. 结合调试 Skill 分析错误

## 注意事项

- 大量日志可能影响性能
- 正则模式需要正确转义
- 告警回调不应阻塞主线程

---

*Skill 版本: 1.0.0*
*最后更新: 2026-03-22*