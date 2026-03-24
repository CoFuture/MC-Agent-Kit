# MC-Agent-Kit 最佳实践

本指南总结了 ModSDK 开发的最佳实践和使用 MC-Agent-Kit 的建议。

## 代码规范

### Python 2.7 兼容性

ModSDK 使用 Python 2.7，请注意以下限制：

```python
# ❌ 不兼容 Python 2.7
def func(a: int, b: str) -> None:  # 类型注解不支持
    pass

# ✅ 兼容 Python 2.7
def func(a, b):
    # type: (int, str) -> None  # 使用注释形式
    pass
```

```python
# ❌ f-string 不支持
message = f"Hello {name}"

# ✅ 使用 format
message = "Hello {}".format(name)
# 或
message = "Hello %s" % name
```

```python
# ❌ super() 简写不支持
class MyClass(Base):
    def __init__(self):
        super().__init__()  # Python 3 语法

# ✅ 使用完整形式
class MyClass(Base):
    def __init__(self):
        super(MyClass, self).__init__()
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `MySystem`, `ChatBot` |
| 函数名 | snake_case | `on_player_join`, `get_position` |
| 变量名 | snake_case | `player_id`, `entity_data` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PLAYERS`, `DEFAULT_SPEED` |
| 私有属性 | _leading_underscore | `_internal_data` |

### 注释规范

```python
def on_player_join(self, args):
    """处理玩家加入事件
    
    Args:
        args: 事件参数字典，包含 'id' 和 'name' 字段
        
    Returns:
        None
        
    Raises:
        ValueError: 如果 player_id 为空
    """
    player_id = args.get('id')
    if not player_id:
        raise ValueError("player_id is required")
    
    player_name = args.get('name', 'Unknown')
    # 发送欢迎消息
    self.send_welcome(player_id, player_name)
```

## ModSDK 特定规范

### 服务端 vs 客户端

明确区分服务端和客户端代码：

```python
# ✅ 服务端代码
# mod/server/extraServerApi.py
ServerSystem = serverApi.GetServerSystemCls()

class MyServerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
    def on_player_join(self, args):
        # 服务端逻辑
        pass
```

```python
# ✅ 客户端代码
# mod/client/extraClientApi.py
ClientSystem = clientApi.GetClientSystemCls()

class MyClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        
    def on_key_press(self, args):
        # 客户端逻辑
        pass
```

### 事件监听管理

正确管理事件监听的生命周期：

```python
class MySystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 注册事件
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.on_chat
        )
    
    def OnDestroy(self):
        """清理资源"""
        # 取消事件监听（如果需要）
        self.UnListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.on_chat
        )
```

## 性能优化

### 缓存数据

避免重复查询：

```python
class OptimizedSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 缓存玩家数据
        self.player_cache = {}
        
    def on_player_join(self, args):
        player_id = args['id']
        # 缓存玩家名称，避免重复查询
        self.player_cache[player_id] = {
            'name': args.get('name', 'Unknown'),
            'join_time': time.time()
        }
    
    def get_player_name(self, player_id):
        # 从缓存获取，避免每次都调用 API
        if player_id in self.player_cache:
            return self.player_cache[player_id]['name']
        return 'Unknown'
```

### 批量处理

批量处理减少开销：

```python
class BatchSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 待处理队列
        self.pending_updates = []
        
        # 定时批量处理
        self.CreateRepeatedTimer(1.0, self.process_batch)
    
    def add_update(self, update):
        """添加到队列"""
        self.pending_updates.append(update)
    
    def process_batch(self):
        """批量处理"""
        if not self.pending_updates:
            return
            
        # 批量处理
        for update in self.pending_updates:
            self._process_single(update)
        
        # 清空队列
        self.pending_updates = []
```

### 避免频繁操作

```python
# ❌ 频繁操作
def on_tick(self):
    for player_id in self.get_all_players():
        pos = self.GetPos(player_id)  # 每帧都查询

# ✅ 优化：减少查询频率
def __init__(self):
    self.update_interval = 20  # 1秒（假设20fps）
    self.tick_count = 0

def on_tick(self):
    self.tick_count += 1
    if self.tick_count % self.update_interval != 0:
        return
    
    # 只在需要时查询
    for player_id in self.get_all_players():
        pos = self.GetPos(player_id)
```

## 内存管理

### 清理数据

及时清理不再需要的数据：

```python
class MemoryAwareSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        self.entity_data = {}
        
        # 监听实体销毁
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnEntityDestruct',
            self, self.on_entity_destruct
        )
    
    def on_entity_destruct(self, args):
        entity_id = args.get('entityId')
        # 清理实体数据
        if entity_id in self.entity_data:
            del self.entity_data[entity_id]
    
    def OnDestroy(self):
        # 系统销毁时清理所有数据
        self.entity_data.clear()
```

### 限制数据大小

```python
class BoundedSystem(ServerSystem):
    MAX_HISTORY = 1000
    
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.history = []
    
    def add_to_history(self, item):
        self.history.append(item)
        
        # 限制大小
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY:]
```

## 错误处理

### 安全的字典访问

```python
# ❌ 可能抛出 KeyError
value = data['key']

# ✅ 安全访问
value = data.get('key', default_value)

# ✅ 带验证的访问
if 'key' in data:
    value = data['key']
else:
    # 处理缺失情况
    value = default_value
```

### 异常处理

```python
def safe_operation(self, player_id):
    """安全执行操作"""
    try:
        pos = self.GetPos(player_id)
        if pos is None:
            print("Warning: Could not get position for player {}".format(player_id))
            return None
            
        return self.do_something(pos)
        
    except Exception as e:
        print("Error in safe_operation: {}".format(str(e)))
        return None
```

### 参数验证

```python
def process_event(self, args):
    """处理事件，带参数验证"""
    # 验证必需参数
    player_id = args.get('playerId')
    if not player_id:
        print("Error: Missing playerId in event args")
        return
    
    # 验证参数类型
    message = args.get('message')
    if message is not None and not isinstance(message, str):
        print("Warning: message is not a string, converting")
        message = str(message)
    
    # 处理...
```

## LLM 使用最佳实践

### 提示词优化

```bash
# ❌ 模糊请求
mc-llm gen "写代码"

# ✅ 明确请求
mc-llm gen "创建一个监听 OnServerChat 事件的监听器，
当玩家输入 !hello 时回复 'Hello, {player_name}!'"
```

### 迭代开发

```bash
# 1. 生成基础代码
mc-llm gen "创建宠物实体基础框架" > pet_base.py

# 2. 审查代码
mc-llm review pet_base.py

# 3. 添加功能
mc-llm gen "为宠物添加跟随主人的行为" >> pet_base.py

# 4. 再次审查
mc-llm review pet_base.py

# 5. 修复问题
mc-llm fix "发现的问题" --code pet_base.py
```

### 代码验证

```bash
# 生成后审查
mc-llm gen "功能需求" --output code.py
mc-llm review code.py

# 诊断潜在问题
mc-llm diagnose --code code.py
```

## 项目组织

### 目录结构

```
my-addon/
├── behavior_pack/
│   ├── manifest.json
│   ├── entities/          # 实体定义
│   │   └── my_entity.json
│   ├── items/             # 物品定义
│   │   └── my_item.json
│   └── scripts/
│       ├── main.py        # 主入口
│       ├── events.py      # 事件处理
│       ├── entities.py    # 实体逻辑
│       └── utils.py       # 工具函数
└── resource_pack/
    ├── manifest.json
    ├── textures/          # 纹理
    │   └── entity/
    └── models/            # 模型
        └── entity/
```

### 模块划分

```python
# main.py - 主入口
from events import EventSystem

NAMESPACE = "myaddon"

def create_system(namespace, systemName):
    return EventSystem(namespace, systemName)
```

```python
# events.py - 事件处理
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

class EventSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self._register_events()
    
    def _register_events(self):
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.on_chat
        )
```

## 测试建议

### 单元测试

```python
# test_my_system.py
import unittest

class TestMySystem(unittest.TestCase):
    def test_process_command(self):
        system = MySystem("test", "TestSystem")
        result = system.process_command({"message": "!hello"})
        self.assertEqual(result, "Hello!")
    
    def test_invalid_command(self):
        system = MySystem("test", "TestSystem")
        result = system.process_command({"message": "!invalid"})
        self.assertIn("Unknown command", result)
```

### 集成测试

```bash
# 运行 Addon 并捕获日志
mc-run ./my-addon --timeout 120 --log-file test.log

# 分析日志
mc-logs --analyze test.log
```

---

*最后更新: 2026-03-25*
*版本: v1.54.0*