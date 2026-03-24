# 第一个项目

本指南将带你创建一个完整的 ModSDK Addon 项目，实现一个简单的功能：玩家聊天时自动回复。

## 项目规划

### 功能需求
1. 监听玩家聊天事件
2. 识别特定命令
3. 执行相应操作并回复

### 技术选型
- 运行环境：服务端
- 主要 API：OnServerChat 事件
- 项目结构：标准 Addon 结构

## 创建项目

### 第一步：初始化项目

```bash
# 创建项目目录
mc-create project chat-bot

# 进入项目
cd chat-bot
```

### 第二步：查看项目结构

```
chat-bot/
├── behavior_pack/
│   ├── manifest.json       # 行为包清单
│   ├── entities/           # 实体定义（可选）
│   └── scripts/
│       └── main.py         # 主脚本
└── resource_pack/
    ├── manifest.json       # 资源包清单
    └── textures/           # 纹理资源（可选）
```

### 第三步：编写代码

打开 `behavior_pack/scripts/main.py`，编写以下代码：

```python
# -*- coding: utf-8 -*-
"""
ChatBot - 一个简单的聊天机器人示例
功能：监听玩家聊天，响应特定命令
"""

from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi

# 获取服务端系统类
ServerSystem = serverApi.GetServerSystemCls()

# 定义命名空间
NAMESPACE = "chatbot"
SYSTEM_NAME = "ChatBotSystem"


class ChatBotSystem(ServerSystem):
    """聊天机器人系统"""
    
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 注册事件监听
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            "OnServerChat",
            self, self.OnChat
        )
        
        # 命令处理器映射
        self.commands = {
            "!hello": self.cmd_hello,
            "!time": self.cmd_time,
            "!help": self.cmd_help,
        }
        
        print("[ChatBot] System initialized")
    
    def OnDestroy(self):
        """系统销毁时调用"""
        print("[ChatBot] System destroyed")
    
    def OnChat(self, args):
        """处理聊天事件"""
        player_id = args.get("playerId")
        player_name = args.get("name", "Unknown")
        message = args.get("message", "").strip()
        
        # 检查是否是命令
        if message.startswith("!"):
            self.ProcessCommand(player_id, player_name, message)
    
    def ProcessCommand(self, player_id, player_name, command):
        """处理命令"""
        # 查找命令处理器
        handler = self.commands.get(command.lower())
        
        if handler:
            handler(player_id, player_name)
        else:
            self.SendMessage(player_id, f"未知命令: {command}，输入 !help 查看帮助")
    
    def cmd_hello(self, player_id, player_name):
        """!hello 命令 - 打招呼"""
        self.SendMessage(player_id, f"你好，{player_name}！我是 ChatBot！")
    
    def cmd_time(self, player_id, player_name):
        """!time 命令 - 显示时间"""
        # 获取游戏时间
        time_data = self.GetGameTime()
        self.SendMessage(player_id, f"当前游戏时间: {time_data}")
    
    def cmd_help(self, player_id, player_name):
        """!help 命令 - 显示帮助"""
        help_text = """可用命令:
!hello - 打招呼
!time - 显示游戏时间
!help - 显示此帮助"""
        self.SendMessage(player_id, help_text)
    
    def SendMessage(self, player_id, message):
        """发送消息给玩家"""
        self.NotifyToClient(player_id, "OnChatBotMessage", {
            "message": message
        })


# 系统工厂函数
def create_system(namespace, systemName):
    return ChatBotSystem(namespace, systemName)
```

### 第四步：更新清单文件

打开 `behavior_pack/manifest.json`，确保内容正确：

```json
{
    "format_version": 1,
    "header": {
        "name": "ChatBot",
        "description": "A simple chat bot addon",
        "uuid": "generated-uuid-here",
        "version": [1, 0, 0]
    },
    "modules": [
        {
            "type": "python",
            "uuid": "generated-uuid-here",
            "version": [1, 0, 0],
            "entry": "scripts/main.py"
        }
    ]
}
```

## 测试项目

### 方法一：使用 mc-run

```bash
# 运行 Addon
mc-run ./chat-bot --timeout 120

# 查看日志
mc-logs --tail
```

### 方法二：手动测试

1. 将项目复制到游戏 Addons 目录
2. 启动 Minecraft 网易版
3. 创建新世界或打开存档
4. 添加 ChatBot Addon
5. 进入游戏测试命令

### 测试命令

在游戏中输入以下命令测试：

```
!hello    # 应该回复打招呼消息
!time     # 显示游戏时间
!help     # 显示帮助信息
!unknown  # 应该提示未知命令
```

## 使用 AI 辅助开发

### 生成代码

```bash
# 使用 AI 生成新命令
mc-llm gen "添加一个 !pos 命令，显示玩家当前位置"

# 输出会包含新命令的代码
```

### 审查代码

```bash
# 审查你的代码
mc-llm review behavior_pack/scripts/main.py

# 输出会包含改进建议
```

### 诊断错误

如果遇到错误：

```bash
# 诊断错误
mc-llm diagnose "KeyError: 'playerId'" --code behavior_pack/scripts/main.py

# 输出会包含原因分析和修复建议
```

## 扩展功能

### 添加新命令

在 `__init__` 方法中添加命令映射：

```python
self.commands = {
    "!hello": self.cmd_hello,
    "!time": self.cmd_time,
    "!help": self.cmd_help,
    "!pos": self.cmd_pos,  # 新增命令
}
```

实现新命令：

```python
def cmd_pos(self, player_id, player_name):
    """!pos 命令 - 显示位置"""
    pos = self.GetPos(player_id)
    if pos:
        self.SendMessage(player_id, f"你的位置: X={pos[0]:.1f}, Y={pos[1]:.1f}, Z={pos[2]:.1f}")
    else:
        self.SendMessage(player_id, "无法获取位置")
```

### 添加权限控制

```python
# 管理员列表
self.admins = {"AdminName1", "AdminName2"}

def ProcessCommand(self, player_id, player_name, command):
    # 检查管理员权限
    if command in ["!kick", "!ban"]:
        if player_name not in self.admins:
            self.SendMessage(player_id, "你没有权限执行此命令")
            return
    
    # 继续处理...
```

## 下一步

- 📖 [代码生成](./code-generation.md) - 深入了解 AI 代码生成
- 🔧 [配置文件详解](./configuration.md) - 高级配置
- 💡 [最佳实践](../best-practices.md) - 开发技巧
- 📚 [示例项目](../../examples/) - 更多示例

---

*最后更新: 2026-03-25*