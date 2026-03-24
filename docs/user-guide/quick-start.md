# 5 分钟上手

本指南将帮助你在 5 分钟内体验 MC-Agent-Kit 的核心功能。

## 前置条件

确保已完成 [安装指南](./installation.md) 中的安装步骤。

## 第一步：初始化配置

```bash
# 创建默认配置
mc-llm providers

# 输出示例：
# Available providers:
# - mock (default)
# - openai
# - anthropic
# - gemini
# - ollama
```

## 第二步：搜索 ModSDK API

```bash
# 语义搜索 API
mc-kb search "如何创建自定义实体"

# 输出示例：
# Found 5 results:
# 
# 1. CreateEngineEntity (API)
#    Module: 实体
#    Description: 创建引擎实体
#    
# 2. SetEntityAttr (API)
#    Module: 实体
#    Description: 设置实体属性
```

## 第三步：创建项目

```bash
# 创建新项目
mc-create project my-addon

# 输出：
# Creating project: my-addon
# ✓ Created behavior_pack/
# ✓ Created resource_pack/
# ✓ Created manifest.json
# ✓ Created main.py
# 
# Project created successfully!
```

## 第四步：使用 AI 助手

### 代码生成

```bash
# 生成事件监听代码
mc-llm gen "创建一个监听玩家聊天事件的监听器"

# 输出：
# ✅ Code Generated Successfully
# 
# Code:
# ```python
# from mod.common import minecraftEnum
# import mod.server.extraServerApi as serverApi
# 
# ServerSystem = serverApi.GetServerSystemCls()
# 
# class MySystem(ServerSystem):
#     def __init__(self, namespace, systemName):
#         ServerSystem.__init__(self, namespace, systemName)
#         self.ListenForEvent(
#             serverApi.GetEngineNamespace(),
#             serverApi.GetEngineSystemName(),
#             'OnServerChat',
#             self, self.OnChat
#         )
#     
#     def OnChat(self, args):
#         player_name = args.get('name', 'Unknown')
#         message = args.get('message', '')
#         print(f"[Chat] {player_name}: {message}")
# ```
```

### 代码审查

```bash
# 审查代码文件
mc-llm review main.py

# 输出：
# ✅ Code Review Passed (Score: 85, Grade: B)
# 
# Issues (2):
#   ⚠️ [style] Line 15: Consider adding docstring
#   💡 [hint] Line 20: Could use get() for safer dict access
# 
# Summary: Good code structure with minor improvements possible.
```

### 交互式聊天

```bash
# 启动交互模式
mc-llm chat

# 欢迎信息
# MC-Agent-Kit AI Assistant
# Type /help for commands, /exit to quit.
# 
# mc-llm> 如何获取玩家位置？
# 
# 可以使用 GetPos API 获取玩家位置：
# 
# pos = self.GetPos(player_id)
# # pos = (x, y, z)
# 
# 相关 API：
# - GetPos: 获取位置
# - SetPos: 设置位置
# - GetRotation: 获取旋转角度
# 
# mc-llm> /exit
# Goodbye!
```

## 第五步：运行测试

```bash
# 启动游戏测试 Addon
mc-run ./my-addon --timeout 60

# 输出：
# Starting Minecraft...
# Loading addon: my-addon
# ✓ Addon loaded successfully
# Running for 60 seconds...
# 
# Logs captured: ./logs/session-20260325.log
# Errors: 0
# Warnings: 2
```

## 常用命令速查

| 命令 | 功能 |
|------|------|
| `mc-kb search <query>` | 搜索 ModSDK 文档 |
| `mc-kb api <name>` | 查看特定 API |
| `mc-create project <name>` | 创建项目 |
| `mc-create entity <name>` | 创建实体 |
| `mc-run <path>` | 运行 Addon |
| `mc-llm chat` | AI 聊天模式 |
| `mc-llm gen <prompt>` | 生成代码 |
| `mc-llm review <file>` | 审查代码 |
| `mc-llm diagnose <error>` | 诊断错误 |

## 下一步

- 🎯 [第一个项目](./first-project.md) - 创建完整的 ModSDK 项目
- 🔧 [配置文件详解](./configuration.md) - 深入了解配置
- 💡 [最佳实践](../best-practices.md) - 学习开发技巧

---

*最后更新: 2026-03-25*