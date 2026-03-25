# 插件钩子 API

> 版本：v1.0.0
> 最后更新：2026-03-25

---

## 概述

钩子系统允许插件在特定事件发生时执行自定义逻辑。

---

## 核心类

### HookRegistry

钩子注册表，管理所有注册的钩子。

```python
from mc_agent_kit.contrib.plugin.hooks import HookRegistry

registry = HookRegistry()
```

#### 方法

##### register()

注册钩子回调。

```python
def register(
    hook_type: str | HookType,
    callback: Callable[..., Any],
    priority: HookPriority = HookPriority.NORMAL,
    plugin_name: str | None = None,
    description: str = "",
) -> str:
    """注册钩子回调。
    
    Args:
        hook_type: 钩子类型（HookType 枚举或字符串）
        callback: 回调函数
        priority: 优先级（高优先级先执行）
        plugin_name: 插件名称
        description: 描述
    
    Returns:
        钩子名称
    """
```

**示例**:
```python
registry.register(
    HookType.ON_STARTUP,
    my_callback,
    HookPriority.HIGH,
    plugin_name="my_plugin",
    description="启动时执行",
)
```

##### unregister()

注销钩子回调。

```python
def unregister(
    hook_type: str | HookType,
    callback: Callable[..., Any],
) -> bool:
    """注销钩子回调。
    
    Args:
        hook_type: 钩子类型
        callback: 要移除的回调函数
    
    Returns:
        True 如果成功移除
    """
```

##### trigger()

触发所有指定类型的钩子。

```python
def trigger(
    hook_type: str | HookType,
    *args: Any,
    **kwargs: Any,
) -> list[HookResult]:
    """触发所有钩子。
    
    Args:
        hook_type: 钩子类型
        *args: 位置参数
        **kwargs: 关键字参数
    
    Returns:
        钩子结果列表
    """
```

**示例**:
```python
results = registry.trigger(
    HookType.ON_CODE_GENERATE,
    code="print('hello')",
)

for result in results:
    if result.success:
        print(f"Hook succeeded: {result.result}")
    else:
        print(f"Hook failed: {result.error}")
```

##### trigger_until()

触发钩子直到满足条件。

```python
def trigger_until(
    hook_type: str | HookType,
    *args: Any,
    stop_on: Callable[[Any], bool] = lambda r: r is not None,
    **kwargs: Any,
) -> Any:
    """触发钩子直到满足条件。
    
    Args:
        hook_type: 钩子类型
        *args: 位置参数
        stop_on: 停止条件函数
        **kwargs: 关键字参数
    
    Returns:
        第一个满足条件的结果
    """
```

**示例**:
```python
# 找到第一个返回非 None 结果的钩子
result = registry.trigger_until(
    HookType.ON_SEARCH,
    query="test",
    stop_on=lambda r: r is not None,
)
```

##### get_hooks()

获取指定类型的所有钩子信息。

```python
def get_hooks(hook_type: str | HookType) -> list[HookInfo]:
    """获取钩子列表。
    
    Args:
        hook_type: 钩子类型
    
    Returns:
        钩子信息列表
    """
```

##### list_all()

列出所有注册的钩子。

```python
def list_all() -> dict[str, list[HookInfo]]:
    """列出所有钩子。
    
    Returns:
        字典：钩子类型 -> 钩子信息列表
    """
```

---

### HookType

预定义钩子类型枚举。

```python
from mc_agent_kit.contrib.plugin.hooks import HookType

# 生命周期
HookType.ON_STARTUP      # 系统启动
HookType.ON_SHUTDOWN     # 系统关闭

# 知识库
HookType.ON_INDEX_BUILD      # 构建索引
HookType.ON_INDEX_UPDATE     # 更新索引
HookType.ON_SEARCH           # 搜索前
HookType.ON_SEARCH_RESULT    # 搜索后

# 代码生成
HookType.ON_CODE_GENERATE    # 生成代码前
HookType.ON_CODE_GENERATED   # 生成代码后
HookType.ON_CODE_REVIEW      # 代码审查

# 项目
HookType.ON_PROJECT_CREATE   # 创建项目
HookType.ON_PROJECT_LOAD     # 加载项目
HookType.ON_PROJECT_SAVE     # 保存项目

# 文件
HookType.ON_FILE_READ        # 读取文件
HookType.ON_FILE_WRITE       # 写入文件
HookType.ON_FILE_CHANGE      # 文件变化

# 执行
HookType.ON_EXECUTION_START  # 执行开始
HookType.ON_EXECUTION_END    # 执行结束
HookType.ON_EXECUTION_ERROR  # 执行错误

# 调试
HookType.ON_ERROR            # 发生错误
HookType.ON_LOG              # 日志记录
HookType.ON_DIAGNOSE         # 诊断
```

---

### HookPriority

钩子优先级枚举。

```python
from mc_agent_kit.contrib.plugin.hooks import HookPriority

HookPriority.LOWEST    # 0 - 最低优先级
HookPriority.LOW       # 25 - 低优先级
HookPriority.NORMAL    # 50 - 正常优先级（默认）
HookPriority.HIGH      # 75 - 高优先级
HookPriority.HIGHEST   # 100 - 最高优先级
HookPriority.MONITOR   # 200 - 监控（最后执行）
```

---

### HookInfo

钩子信息数据结构。

```python
from dataclasses import dataclass

@dataclass
class HookInfo:
    name: str                      # 钩子名称
    callback: Callable[..., Any]   # 回调函数
    priority: HookPriority         # 优先级
    plugin_name: str | None        # 插件名称
    description: str               # 描述
```

---

### HookResult

钩子执行结果。

```python
from dataclasses import dataclass

@dataclass
class HookResult:
    success: bool                  # 是否成功
    result: Any                    # 返回结果
    error: str | None              # 错误信息
    hook_name: str                 # 钩子名称
    plugin_name: str | None        # 插件名称
```

---

## 便捷函数

### get_hook_registry()

获取全局钩子注册表单例。

```python
from mc_agent_kit.contrib.plugin.hooks import get_hook_registry

registry = get_hook_registry()
```

### register_hook()

便捷注册函数。

```python
from mc_agent_kit.contrib.plugin.hooks import register_hook

register_hook(
    HookType.ON_STARTUP,
    my_callback,
    HookPriority.NORMAL,
    plugin_name="my_plugin",
)
```

### trigger_hooks()

便捷触发函数。

```python
from mc_agent_kit.contrib.plugin.hooks import trigger_hooks

results = trigger_hooks(HookType.ON_CODE_GENERATE, code="...")
```

### hook_decorator()

装饰器方式注册钩子。

```python
from mc_agent_kit.contrib.plugin.hooks import hook_decorator, HookType

@hook_decorator(HookType.ON_CODE_GENERATE)
def process_code(code: str) -> str:
    return code.upper()
```

---

## 使用示例

### 示例 1：启动时初始化

```python
from mc_agent_kit.contrib.plugin.hooks import (
    HookRegistry,
    HookType,
    HookPriority,
)

registry = HookRegistry()

def on_startup():
    print("System starting up...")
    # 初始化资源
    return True

registry.register(
    HookType.ON_STARTUP,
    on_startup,
    HookPriority.HIGH,
    description="系统启动初始化",
)
```

### 示例 2：代码生成前处理

```python
def before_code_generate(code: str) -> str:
    # 添加代码头
    header = "# Auto-generated code\n"
    return header + code

registry.register(
    HookType.ON_CODE_GENERATE,
    before_code_generate,
    HookPriority.NORMAL,
)
```

### 示例 3：错误通知

```python
def on_error(error: Exception):
    # 发送错误通知
    send_notification(f"Error occurred: {error}")
    return True

registry.register(
    HookType.ON_ERROR,
    on_error,
    HookPriority.HIGHEST,
    description="错误通知",
)
```

### 示例 4：文件变化监控

```python
def on_file_change(file_path: str, event_type: str):
    print(f"File {event_type}: {file_path}")
    # 触发热重载
    hot_reload(file_path)
    return True

registry.register(
    HookType.ON_FILE_CHANGE,
    on_file_change,
    HookPriority.LOW,
)
```

---

## 最佳实践

### 1. 保持钩子函数简洁

```python
# ✅ 好的做法
def on_startup():
    initialize_cache()
    return True

# ❌ 不好的做法
def on_startup():
    # 执行大量耗时操作
    load_all_data()
    process_everything()
    return True
```

### 2. 错误处理

```python
def safe_hook():
    try:
        return do_something()
    except Exception as e:
        logger.error(f"Hook failed: {e}")
        return None  # 钩子失败不影响其他钩子
```

### 3. 使用合适的优先级

```python
# 关键操作使用高优先级
registry.register(HookType.ON_ERROR, critical_handler, HookPriority.HIGHEST)

# 监控操作使用 MONITOR 优先级
registry.register(HookType.ON_LOG, monitor_handler, HookPriority.MONITOR)
```

### 4. 避免循环依赖

```python
# ❌ 避免在钩子中触发同一钩子
def on_search(query: str):
    # 不要这样做！
    registry.trigger(HookType.ON_SEARCH, query)
```

---

## 性能考虑

### 钩子执行顺序

钩子按优先级降序执行（高优先级先执行）：

```
HIGHEST (100) → HIGH (75) → NORMAL (50) → LOW (25) → LOWEST (0) → MONITOR (200)
```

### 性能基准

- 注册 100 个钩子：< 10ms
- 触发 100 个钩子：< 500ms
- 单个钩子执行：取决于回调函数

### 优化建议

1. 避免在钩子中执行耗时操作
2. 使用异步钩子处理 I/O 操作
3. 对钩子结果进行缓存
4. 限制钩子数量

---

## 故障排查

### 钩子未执行

检查：
1. 钩子是否正确注册
2. 钩子类型是否匹配
3. 优先级是否合适

### 钩子执行顺序错误

检查：
1. 优先级设置是否正确
2. 是否有多个插件注册了同一钩子

### 钩子抛出异常

钩子异常会被捕获，不影响其他钩子执行。查看日志获取详细信息。

---

## 参考

- [插件开发指南](../user-guide/plugin-development.md)
- [配置管理 API](./config.md)
- [内置插件文档](./builtin.md)

---

*最后更新：2026-03-25*
