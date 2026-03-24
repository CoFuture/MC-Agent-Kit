# 聊天模式

MC-Agent-Kit 的聊天模式让你可以与 AI 助手交互，获取 ModSDK 开发帮助。

## 启动聊天

```bash
# 启动交互式聊天
mc-llm chat

# 指定欢迎消息
mc-llm chat --welcome "欢迎使用 MC-Agent-Kit!"

# 指定提示符
mc-llm chat --prompt "mc> "
```

## 聊天界面

```
MC-Agent-Kit AI Assistant
Type /help for commands, /exit to quit.

mc-llm> 你好！

你好！我是 MC-Agent-Kit 的 AI 助手，专门帮助开发者进行 Minecraft 网易版 ModSDK 开发。

我可以帮助你：
1. 查询 ModSDK API 和事件
2. 生成 ModSDK 代码
3. 分析和修复代码错误
4. 提供开发建议和最佳实践

有什么我可以帮助你的吗？

mc-llm> _
```

## 聊天命令

### 内置命令

| 命令 | 说明 |
|------|------|
| `/help`, `/h`, `?` | 显示帮助信息 |
| `/exit`, `/quit`, `/q` | 退出聊天 |
| `/clear`, `/c` | 清除对话历史 |

### 使用命令

```
mc-llm> /help

Commands:
  /exit, /quit, /q  - Exit chat
  /clear, /c        - Clear history
  /help, /h, ?      - Show this help

mc-llm> /clear
History cleared.

mc-llm> /exit
Goodbye!
```

## 交互示例

### 查询 API

```
mc-llm> 如何获取玩家位置？

可以使用 GetPos API 获取玩家位置：

```python
# 服务端
pos = self.GetPos(player_id)
# pos = (x, y, z)

# 客户端
pos = clientApi.GetPos(player_id)
```

相关 API：
- GetPos: 获取实体位置
- SetPos: 设置实体位置
- GetRotation: 获取旋转角度
- SetRotation: 设置旋转角度

mc-llm> _
```

### 生成代码

```
mc-llm> 请帮我写一个监听玩家加入事件的代码

```python
from mod.server.extraServerApi import serverApi

ServerSystem = serverApi.GetServerSystemCls()

class MySystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 监听玩家加入事件
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnAddServerPlayer',
            self, self.OnPlayerJoin
        )
    
    def OnPlayerJoin(self, args):
        player_id = args.get('id')
        player_name = args.get('name', 'Unknown')
        
        print(f"Player joined: {player_name}")
        
        # 发送欢迎消息
        self.NotifyToClient(player_id, 'OnWelcomeMessage', {
            'message': f'欢迎 {player_name} 加入服务器！'
        })
```

注意事项：
- OnAddServerPlayer 是服务端事件
- 需要在系统初始化时注册监听
- 记得在 OnDestroy 中取消监听（如果需要）

mc-llm> _
```

### 调试问题

```
mc-llm> 我遇到了一个错误：KeyError: 'playerId'

这个错误表示在访问字典时，键 'playerId' 不存在。

可能的原因：
1. 事件参数中没有 playerId 字段
2. 使用了错误的事件参数名
3. 事件参数结构发生变化

解决方案：

```python
# 方案 1：使用 get() 安全访问
player_id = args.get('playerId')
if player_id is None:
    print("Warning: playerId not found")
    return

# 方案 2：检查事件参数结构
print("Event args:", args)  # 调试输出

# 方案 3：使用正确的字段名
# 不同事件可能使用不同的字段名
# 例如：OnServerChat 使用 'playerId'
#      OnAddServerPlayer 使用 'id'
```

建议检查事件文档确认正确的参数名。

mc-llm> _
```

## 流式输出

启用流式输出可以实时看到 AI 的回复：

```bash
# 默认启用流式输出
mc-llm chat

# 禁用流式输出
mc-llm chat --no-stream
```

流式输出效果：

```
mc-llm> 介绍一下 ModSDK

ModSDK 是 Minecraft 网易版提供的开发工具包...
（逐字显示，实时更新）
```

## 历史记录

### 自动保存

聊天历史会自动保存到配置文件指定的位置：

```yaml
# ~/.mc-agent-kit/config.yaml
history_file: ~/.mc-agent-kit/chat_history.json
max_history_entries: 100
```

### 清除历史

```
mc-llm> /clear
History cleared.
```

## 高级用法

### 指定上下文

在聊天中提供更多上下文：

```
mc-llm> 我正在开发一个 RPG 服务器，需要实现玩家属性系统

明白了！RPG 玩家属性系统通常包括：

1. 基础属性：力量、敏捷、智力等
2. 派生属性：攻击力、防御力、暴击率等
3. 等级系统：经验值和升级

你想要实现哪些功能？我可以帮你设计...

mc-llm> _
```

### 请求代码解释

```
mc-llm> 请解释这段代码的作用：
```python
self.ListenForEvent(
    serverApi.GetEngineNamespace(),
    serverApi.GetEngineSystemName(),
    'OnServerChat',
    self, self.OnChat
)
```

这段代码的作用是注册事件监听器：

1. serverApi.GetEngineNamespace() - 获取引擎命名空间
2. serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName() - 
   指定事件来源（引擎系统）
3. 'OnServerChat' - 要监听的事件名称（服务器聊天事件）
4. self - 事件处理器所属对象
5. self.OnChat - 回调函数，当事件触发时调用

简单说：当玩家发送聊天消息时，会自动调用 self.OnChat 方法。

mc-llm> _
```

### 多轮对话

```
mc-llm> 如何创建自定义实体？

可以使用 CreateEngineEntity API...

mc-llm> 那如何给实体添加 AI 行为？

可以结合定时器和位置计算实现 AI 行为...

mc-llm> 有没有更简单的方法？

可以使用行为树或者状态机模式...

mc-llm> _
```

## 配置选项

### 系统提示

自定义 AI 助手的行为：

```yaml
# ~/.mc-agent-kit/config.yaml
providers:
  openai:
    system_prompt: |
      你是一个 ModSDK 专家。
      回答要简洁、准确。
      代码要完整、可运行。
```

### 温度参数

调整回复的创造性：

```yaml
providers:
  openai:
    temperature: 0.7  # 0.0 严谨，1.0 创造性
```

## 快捷键

| 快捷键 | 说明 |
|--------|------|
| `Ctrl+C` | 中断当前操作 |
| `Ctrl+D` | 退出聊天（EOF） |
| `上箭头` | 历史命令 |
| `下箭头` | 历史命令 |

## 下一步

- 🔧 [自定义提示词](./custom-prompts.md) - 优化聊天效果
- 🔧 [多提供商配置](./multi-provider.md) - 使用不同的 LLM
- 💡 [最佳实践](../best-practices.md) - 开发技巧

---

*最后更新: 2026-03-25*