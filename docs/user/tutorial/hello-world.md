# Hello World 教程

本教程将带你创建第一个 ModSDK Hello World 模组。

## 目标

创建一个简单的模组，当玩家进入服务器时显示欢迎消息。

## 准备工作

确保你已经：

1. 安装了 MC-Agent-Kit
2. 安装了网易 Minecraft 开发环境
3. 了解了基本的 ModSDK 概念

## 步骤 1：创建项目目录

```bash
mkdir hello-world-mod
cd hello-world-mod
```

## 步骤 2：搜索相关事件

首先，我们需要找到玩家进入服务器的事件：

```bash
# 搜索 "OnJoin" 相关事件
mc-agent event -q "OnJoin"
```

输出示例：

```
事件: OnJoinServer
模块: player
描述: 玩家加入服务器时触发
参数:
  - playerId: 玩家 ID
  - playerName: 玩家名称
```

## 步骤 3：生成事件监听器代码

使用 MC-Agent-Kit 生成代码：

```bash
mc-agent gen -t event_listener -p '{
  "event_name": "OnJoinServer",
  "callback": "on_player_join",
  "module": "player"
}'
```

生成的代码：

```python
# OnJoinServer 事件监听器
# 触发时机：玩家加入服务器时

import mod.server.extraServerApi as serverApi

def on_player_join(args):
    """
    玩家加入服务器回调
    
    Args:
        args: 事件参数
            - playerId: 玩家 ID
            - playerName: 玩家名称
    """
    player_id = args.get('playerId')
    player_name = args.get('playerName', 'Player')
    
    # 在这里添加你的逻辑
    print(f"Player {player_name} joined the server")


# 注册事件监听器
serverApi.GetEngineCompFactory().RegisterOnJoinServer(on_player_join)
```

## 步骤 4：搜索显示消息 API

搜索如何在游戏中显示消息：

```bash
mc-agent api -q "NotifyToClient"
```

输出示例：

```
API: NotifyToClient
模块: game
描述: 向客户端发送通知消息
参数:
  - msg: 消息内容
返回值: 无
```

## 步骤 5：完善代码

将生成的代码与 API 结合：

```python
# hello_world.py
# ModSDK Hello World 示例

import mod.server.extraServerApi as serverApi

# 获取游戏组件工厂
comp_factory = serverApi.GetEngineCompFactory()

def on_player_join(args):
    """
    玩家加入服务器回调
    
    Args:
        args: 事件参数
            - playerId: 玩家 ID
            - playerName: 玩家名称
    """
    player_id = args.get('playerId')
    player_name = args.get('playerName', 'Player')
    
    # 向玩家发送欢迎消息
    comp_factory.NotifyToClient(player_id, f"欢迎 {player_name} 来到服务器！")
    
    # 在控制台打印日志
    print(f"[HelloWorld] Player {player_name} (ID: {player_id}) joined")


# 注册事件监听器
comp_factory.RegisterOnJoinServer(on_player_join)


# 服务器启动时的初始化
def on_server_start(args):
    """服务器启动回调"""
    print("[HelloWorld] Hello World Mod 已加载！")


comp_factory.RegisterOnServerStart(on_server_start)
```

## 步骤 6：创建配置文件

创建 `mod.json` 配置文件：

```json
{
  "mod_id": "hello_world",
  "name": "Hello World Mod",
  "version": "1.0.0",
  "description": "一个简单的欢迎消息模组",
  "author": "Your Name",
  "entry": "hello_world.py",
  "type": "behavior"
}
```

## 步骤 7：检查代码质量

使用 MC-Agent-Kit 检查代码：

```bash
# 检查最佳实践
mc-agent check -f hello_world.py

# 检测代码异味
mc-agent refactor -f hello_world.py -a detect
```

## 步骤 8：测试模组

1. 将模组放入开发目录
2. 使用 MC-Agent-Kit 启动游戏：

```bash
mc-agent launch --addon ./hello-world-mod
```

3. 观察日志输出：

```bash
mc-agent logs --follow
```

## 步骤 9：调试问题

如果遇到问题，使用调试命令：

```bash
# 诊断错误日志
mc-agent debug -f error.log

# 自动修复代码问题
mc-agent autofix -f hello_world.py -e error.log -a fix
```

## 完整项目结构

```
hello-world-mod/
├── mod.json           # 模组配置
├── hello_world.py     # 主代码
└── README.md          # 说明文档
```

## 下一步

- 学习 [自定义实体教程](custom-entity.md)
- 学习 [自定义物品教程](custom-item.md)
- 查看 [API 参考](api-reference.md)

## 常见问题

### Q: 事件没有触发？

确保事件名称正确，区分大小写。使用 `mc-agent event -q "事件名"` 搜索正确的事件名称。

### Q: NotifyToClient 没有效果？

确保 `playerId` 参数正确。使用 `GetPlayerId()` API 获取玩家 ID。

### Q: 如何调试代码？

1. 使用 `print()` 输出日志
2. 使用 `mc-agent logs --follow` 查看实时日志
3. 使用 `mc-agent debug` 分析错误

---

*最后更新：2026-03-22*