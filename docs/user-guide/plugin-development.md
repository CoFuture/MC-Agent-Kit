# 插件开发指南

> 版本：v1.0.0
> 最后更新：2026-03-25

---

## 快速入门

### 5 分钟创建第一个插件

```python
from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginState,
)

class MyPlugin(PluginBase):
    """我的第一个插件"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="我的第一个 MC-Agent-Kit 插件",
            author="Your Name",
        )
        super().__init__(metadata)
    
    def initialize(self) -> bool:
        """初始化插件"""
        self._state = PluginState.LOADED
        print("Plugin initialized!")
        return True
    
    def shutdown(self) -> None:
        """关闭插件"""
        self._state = PluginState.UNLOADED
        print("Plugin shutdown!")
    
    def execute(self, **kwargs) -> PluginResult:
        """执行插件功能"""
        # 实现你的功能
        return PluginResult(
            success=True,
            data={"message": "Hello from plugin!"},
        )

# 使用插件
plugin = MyPlugin()
plugin.initialize()
result = plugin.execute()
print(result.data)  # {'message': 'Hello from plugin!'}
plugin.shutdown()
```

---

## 插件元数据

### PluginMetadata 字段

```python
from mc_agent_kit.contrib.plugin.base import PluginMetadata, PluginPriority

metadata = PluginMetadata(
    name="my_plugin",              # 必需：插件名称
    version="1.0.0",               # 必需：版本号
    description="插件描述",         # 可选：描述
    author="Your Name",            # 可选：作者
    dependencies=["other_plugin"], # 可选：依赖列表
    capabilities=["git", "sync"],  # 可选：能力标签
    priority=PluginPriority.NORMAL,# 可选：优先级
    min_version="1.50.0",          # 可选：最低兼容版本
    max_version="2.0.0",           # 可选：最高兼容版本
)
```

### 优先级说明

| 优先级 | 说明 |
|--------|------|
| `LOW` | 低优先级，最后执行 |
| `NORMAL` | 正常优先级（默认） |
| `HIGH` | 高优先级，优先执行 |
| `CRITICAL` | 关键优先级，最先执行 |

---

## 钩子系统

### 注册钩子

```python
from mc_agent_kit.contrib.plugin.hooks import (
    HookRegistry,
    HookType,
    HookPriority,
)

registry = HookRegistry()

# 方法 1：直接注册
def my_handler():
    print("Hook triggered!")
    return True

registry.register(
    HookType.ON_STARTUP,
    my_handler,
    HookPriority.HIGH,
    plugin_name="my_plugin",
    description="我的钩子处理器",
)

# 方法 2：使用装饰器
from mc_agent_kit.contrib.plugin.hooks import hook_decorator

@hook_decorator(HookType.ON_CODE_GENERATE, HookPriority.NORMAL)
def on_code_generate(code: str) -> str:
    # 在代码生成前处理
    return code.upper()
```

### 预定义钩子类型

#### 生命周期钩子
- `ON_STARTUP` - 系统启动时
- `ON_SHUTDOWN` - 系统关闭时

#### 知识库钩子
- `ON_INDEX_BUILD` - 构建索引时
- `ON_INDEX_UPDATE` - 更新索引时
- `ON_SEARCH` - 搜索前
- `ON_SEARCH_RESULT` - 搜索后

#### 代码生成钩子
- `ON_CODE_GENERATE` - 生成代码前
- `ON_CODE_GENERATED` - 生成代码后
- `ON_CODE_REVIEW` - 代码审查时

#### 项目钩子
- `ON_PROJECT_CREATE` - 创建项目时
- `ON_PROJECT_LOAD` - 加载项目时
- `ON_PROJECT_SAVE` - 保存项目时

#### 文件钩子
- `ON_FILE_READ` - 读取文件时
- `ON_FILE_WRITE` - 写入文件时
- `ON_FILE_CHANGE` - 文件变化时

#### 执行钩子
- `ON_EXECUTION_START` - 执行开始
- `ON_EXECUTION_END` - 执行结束
- `ON_EXECUTION_ERROR` - 执行错误时

#### 调试钩子
- `ON_ERROR` - 发生错误时
- `ON_LOG` - 日志记录时
- `ON_DIAGNOSE` - 诊断时

### 触发钩子

```python
# 触发所有钩子
results = registry.trigger(HookType.ON_STARTUP)

# 触发直到满足条件
result = registry.trigger_until(
    HookType.ON_SEARCH,
    query="test",
    stop_on=lambda r: r is not None,
)

# 获取所有钩子信息
hooks = registry.get_hooks(HookType.ON_STARTUP)
```

---

## 配置管理

### 注册配置模式

```python
from mc_agent_kit.contrib.plugin.config import (
    PluginConfigManager,
    PluginConfigSchema,
    PluginConfig,
)

manager = PluginConfigManager()

# 注册配置模式
schemas = [
    PluginConfigSchema(
        key="enabled",
        type="bool",
        default=True,
        description="是否启用插件",
        required=True,
    ),
    PluginConfigSchema(
        key="timeout",
        type="int",
        default=30,
        min_value=0,
        max_value=300,
        description="超时时间（秒）",
    ),
    PluginConfigSchema(
        key="log_level",
        type="string",
        default="info",
        choices=["debug", "info", "warning", "error"],
        description="日志级别",
    ),
]

manager.register_schema("my_plugin", schemas)
```

### 访问配置

```python
# 获取配置
config = manager.get_config("my_plugin")
enabled = config.enabled
timeout = config.get("timeout", 30)

# 更新配置
config.set("timeout", 60)
manager.set_config("my_plugin", config)

# 更新单个设置
manager.update_setting("my_plugin", "enabled", False)
```

### 配置持久化

配置自动保存到 `~/.mc-agent-kit/plugins/<plugin_name>.json`

```json
{
  "enabled": true,
  "settings": {
    "timeout": 60,
    "log_level": "info"
  }
}
```

---

## 内置插件示例

### Git 操作插件

```python
from mc_agent_kit.contrib.plugin.builtin.git_plugin import GitPlugin

git = GitPlugin()
git.initialize()

# 查看状态
result = git.execute(operation="status", path="/path/to/repo")

# 提交
result = git.execute(
    operation="commit",
    path="/path/to/repo",
    message="Initial commit",
)

# 推送
result = git.execute(
    operation="push",
    path="/path/to/repo",
    branch="main",
)
```

### 通知插件

```python
from mc_agent_kit.contrib.plugin.builtin.notification_plugin import (
    NotificationPlugin,
    NotificationLevel,
)

notifier = NotificationPlugin()
notifier.initialize()

# 发送通知
notifier.send(
    message="Build completed!",
    level=NotificationLevel.INFO,
    channel="console",  # console, file, email, webhook, feishu, dingtalk
)

# 配置通知渠道
notifier.configure_channel(
    channel="email",
    smtp_server="smtp.example.com",
    from_addr="bot@example.com",
    to_addrs=["user@example.com"],
)
```

### 文件监控插件

```python
from mc_agent_kit.contrib.plugin.builtin.file_monitor_plugin import (
    FileMonitorPlugin,
)

monitor = FileMonitorPlugin()
monitor.initialize()

# 开始监控
monitor.start_monitoring(
    path="/path/to/watch",
    pattern="*.py",
    recursive=True,
    callback=lambda event: print(f"File {event.type}: {event.path}"),
)

# 停止监控
monitor.stop_monitoring()
```

### 代码格式化插件

```python
from mc_agent_kit.contrib.plugin.builtin.code_format_plugin import (
    CodeFormatPlugin,
    FormatterType,
)

formatter = CodeFormatPlugin()
formatter.initialize()

# 格式化代码
result = formatter.format_code(
    code="x=1+2",
    formatter=FormatterType.AUTO,  # AUTO, BLACK, RUFF, YAPF, etc.
)

print(result.formatted)  # "x = 1 + 2"

# 格式化文件
result = formatter.format_file("/path/to/file.py")
```

---

## 插件打包

### 插件结构

```
my_plugin/
├── plugin.json           # 插件清单
├── __init__.py          # 插件入口
├── main.py              # 主逻辑
└── README.md            # 使用说明
```

### plugin.json

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "我的插件",
  "author": "Your Name",
  "main": "main.py",
  "dependencies": [],
  "capabilities": ["git", "sync"],
  "license": "MIT"
}
```

### 发布到插件市场

1. 打包插件为 ZIP 文件
2. 提交到插件市场仓库
3. 等待审核通过

---

## 最佳实践

### 1. 错误处理

```python
def execute(self, **kwargs) -> PluginResult:
    try:
        # 实现功能
        result = self.do_something()
        return PluginResult(success=True, data=result)
    except Exception as e:
        return PluginResult(
            success=False,
            error=str(e),
            message="操作失败",
        )
```

### 2. 日志记录

```python
import logging

logger = logging.getLogger("my_plugin")

def execute(self, **kwargs) -> PluginResult:
    logger.info("Starting execution")
    try:
        # ...
        logger.debug("Debug info")
        return PluginResult(success=True)
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return PluginResult(success=False, error=str(e))
```

### 3. 性能优化

```python
# 使用缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(key: str):
    # ...
    return result

# 异步执行
import asyncio

async def execute_async(self, **kwargs) -> PluginResult:
    result = await self.async_operation()
    return PluginResult(success=True, data=result)
```

### 4. 配置验证

```python
def validate_config(self, config: PluginConfig) -> bool:
    if config.get("timeout", 0) < 0:
        return False
    if config.get("max_size", 0) > 1000:
        return False
    return True
```

---

## 常见问题

### Q: 插件如何与其他插件通信？

A: 使用钩子系统。插件可以注册钩子来响应其他插件触发的事件。

### Q: 如何调试插件？

A: 启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q: 插件可以访问文件系统吗？

A: 可以，但建议限制在用户授权的目录内。

### Q: 如何测试插件？

A: 编写单元测试：
```python
def test_my_plugin():
    plugin = MyPlugin()
    assert plugin.initialize() is True
    result = plugin.execute()
    assert result.success is True
```

---

## 参考文档

- [API 文档](./api/plugins/README.md)
- [钩子类型参考](./api/plugins/hooks.md)
- [配置管理参考](./api/plugins/config.md)
- [内置插件文档](./api/plugins/builtin.md)

---

*最后更新：2026-03-25*
