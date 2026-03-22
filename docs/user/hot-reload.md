# 热重载功能使用教程

本教程介绍如何使用 MC-Agent-Kit 的插件热重载功能，实现插件代码修改后自动重载，无需重启应用。

## 目录

1. [功能概述](#功能概述)
2. [快速开始](#快速开始)
3. [配置选项](#配置选项)
4. [文件监控](#文件监控)
5. [回调通知](#回调通知)
6. [高级用法](#高级用法)
7. [最佳实践](#最佳实践)

---

## 功能概述

热重载功能允许你在不重启应用的情况下更新插件代码：

- **自动检测**: 监控插件文件变化
- **防抖处理**: 避免频繁重载
- **回调通知**: 重载完成后通知
- **状态管理**: 追踪重载历史

### 适用场景

- 开发阶段快速迭代
- 调试插件代码
- 生产环境热更新
- 自动化测试

---

## 快速开始

### 基本用法

```python
from pathlib import Path
from mc_agent_kit.plugin import PluginManager, PluginHotReloader

# 创建插件管理器
manager = PluginManager()

# 创建热重载器
reloader = PluginHotReloader(manager)

# 监控插件
reloader.watch_plugin("my_plugin", Path("/plugins/my_plugin"))

# 启动监控
reloader.start()

# 应用会持续运行，插件修改后自动重载
try:
    while True:
        pass
finally:
    reloader.stop()
```

### 使用便捷函数

```python
from mc_agent_kit.plugin import create_hot_reloader

# 一行创建热重载器
reloader = create_hot_reloader(
    manager,
    watch_dirs=["/plugins"],
    auto_start=True
)
```

---

## 配置选项

### HotReloadConfig

```python
from mc_agent_kit.plugin import HotReloadConfig

config = HotReloadConfig(
    watch_interval_ms=500,      # 检查间隔（毫秒）
    debounce_ms=300,            # 防抖时间（毫秒）
    auto_enable=True,           # 重载后自动启用
    exclude_patterns=[          # 排除文件模式
        "__pycache__",
        "*.pyc",
        ".git",
        "test_*"
    ],
    notify_callback=None        # 通知回调
)

reloader = PluginHotReloader(manager, config)
```

### 配置说明

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `watch_interval_ms` | int | 500 | 文件检查间隔 |
| `debounce_ms` | int | 300 | 防抖等待时间 |
| `auto_enable` | bool | True | 重载后自动启用插件 |
| `exclude_patterns` | list | [...] | 要排除的文件模式 |
| `notify_callback` | Callable | None | 重载通知回调 |

---

## 文件监控

### 监控单个插件

```python
# 监控指定插件目录
reloader.watch_plugin("my_plugin", Path("/plugins/my_plugin"))
```

### 监控目录

```python
# 扫描目录下的所有插件
reloader.watch_directory(Path("/plugins"))

# 只监控包含 plugin.json 的子目录
```

### 排除文件

默认排除以下文件：

- `__pycache__/` - Python 缓存目录
- `*.pyc` - 编译的 Python 文件
- `.git/` - Git 目录
- `test_*` - 测试文件

自定义排除模式：

```python
config = HotReloadConfig(
    exclude_patterns=[
        "__pycache__",
        "*.pyc",
        ".git",
        "*.tmp",
        "*.bak",
        "test_*",
        "docs/*"
    ]
)
```

### 检查排除规则

```python
# 检查文件是否被排除
from pathlib import PurePath

is_excluded = reloader._should_exclude(PurePath("__pycache__/module.pyc"))
print(is_excluded)  # True
```

---

## 回调通知

### 添加重载回调

```python
from mc_agent_kit.plugin import ReloadEvent

def on_reload(event: ReloadEvent) -> None:
    """重载完成回调"""
    if event.success:
        print(f"插件 {event.plugin_name} 重载成功")
    else:
        print(f"插件 {event.plugin_name} 重载失败: {event.error}")

reloader.add_reload_callback(on_reload)
```

### 使用配置回调

```python
def notify(name: str, success: bool, message: str) -> None:
    """简化的通知回调"""
    status = "成功" if success else "失败"
    print(f"[{name}] 重载{status}: {message}")

config = HotReloadConfig(notify_callback=notify)
reloader = PluginHotReloader(manager, config)
```

### 移除回调

```python
reloader.remove_reload_callback(on_reload)
```

---

## 高级用法

### 手动重载

```python
# 手动触发重载
event = reloader.reload_plugin("my_plugin")
print(f"重载结果: {event.success}")
```

### 批量重载

```python
from mc_agent_kit.plugin import reload_all_plugins

# 重载所有监控的插件
results = reload_all_plugins(reloader)
for name, event in results.items():
    print(f"{name}: {'成功' if event.success else '失败'}")
```

### 获取状态

```python
status = reloader.get_status()
print(f"运行中: {status['running']}")
print(f"监控插件数: {status['watched_count']}")
print(f"监控插件: {status['watched_plugins']}")
```

### 获取重载历史

```python
# 获取最近的重载事件
events = reloader.get_events(limit=20)
for event in events:
    print(f"[{event.timestamp}] {event.plugin_name}: {event.success}")
```

### ReloadEvent 属性

| 属性 | 类型 | 说明 |
|-----|------|------|
| `plugin_name` | str | 插件名称 |
| `file_path` | str | 文件路径 |
| `success` | bool | 是否成功 |
| `error` | str \| None | 错误信息 |
| `timestamp` | datetime | 事件时间 |
| `reload_time_ms` | float | 重载耗时（毫秒）|

---

## 最佳实践

### 1. 开发环境配置

```python
# 开发环境：高频检查，快速反馈
dev_config = HotReloadConfig(
    watch_interval_ms=200,  # 更频繁检查
    debounce_ms=100,        # 更短防抖
    auto_enable=True
)
```

### 2. 生产环境配置

```python
# 生产环境：低频检查，稳定优先
prod_config = HotReloadConfig(
    watch_interval_ms=2000,  # 降低检查频率
    debounce_ms=1000,        # 更长防抖
    auto_enable=False        # 手动启用
)
```

### 3. 错误处理

```python
def safe_reload_handler(event: ReloadEvent) -> None:
    if not event.success:
        # 记录错误
        logger.error(f"重载失败: {event.plugin_name} - {event.error}")
        
        # 发送告警
        send_alert(f"插件 {event.plugin_name} 重载失败")
        
        # 尝试回滚
        try:
            manager.rollback(event.plugin_name)
        except Exception as e:
            logger.error(f"回滚失败: {e}")

reloader.add_reload_callback(safe_reload_handler)
```

### 4. 优雅关闭

```python
import signal
import sys

def signal_handler(sig, frame):
    print("正在关闭...")
    reloader.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### 5. 配合日志

```python
import logging

# 启用热重载模块日志
logging.getLogger("mc_agent_kit.plugin.hot_reload").setLevel(logging.DEBUG)
```

---

## 注意事项

### 文件系统兼容性

- Windows 和 Linux 的文件事件可能有差异
- 网络文件系统（NFS、SMB）可能无法正确触发事件
- 建议使用本地文件系统

### 防抖机制

- 防抖是为了避免频繁重载
- 连续修改会在最后一次修改后等待防抖时间再重载
- 根据实际需求调整防抖时间

### 线程安全

- 热重载器使用独立线程监控文件
- 回调函数需要注意线程安全
- 避免在回调中执行耗时操作

---

## 相关文档

- [插件开发指南](plugin-development.md)
- [插件调试指南](plugin-debugging.md)
- [插件最佳实践](plugin-best-practices.md)

---

## API 参考

### 类

#### `PluginHotReloader`

插件热重载管理器。

**方法**:

- `watch_plugin(name, path)` - 监控插件
- `unwatch_plugin(name)` - 取消监控
- `watch_directory(directory)` - 监控目录
- `start()` - 启动监控
- `stop()` - 停止监控
- `reload_plugin(name)` - 手动重载
- `get_status()` - 获取状态
- `get_events(limit)` - 获取事件历史
- `add_reload_callback(callback)` - 添加回调
- `remove_reload_callback(callback)` - 移除回调

#### `HotReloadConfig`

热重载配置。

**属性**:

- `watch_interval_ms: int` - 检查间隔
- `debounce_ms: int` - 防抖时间
- `auto_enable: bool` - 自动启用
- `exclude_patterns: list[str]` - 排除模式
- `notify_callback: Callable | None` - 通知回调

#### `ReloadEvent`

重载事件记录。

**属性**:

- `plugin_name: str` - 插件名称
- `file_path: str` - 文件路径
- `success: bool` - 是否成功
- `error: str | None` - 错误信息
- `timestamp: datetime` - 事件时间
- `reload_time_ms: float` - 重载耗时

### 函数

#### `create_hot_reloader(manager, watch_dirs, config)`

便捷创建热重载器。

#### `reload_all_plugins(reloader)`

批量重载所有监控的插件。

---

*文档版本: v1.0.0*
*最后更新: 2026-03-22*