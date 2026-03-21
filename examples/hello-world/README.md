# Hello World 示例模组

一个简单的 ModSDK 模组示例，演示基本的事件监听和消息显示功能。

## 功能

- 玩家加入服务器时显示欢迎消息
- 玩家离开服务器时显示离开消息
- 服务器启动时输出日志

## 文件结构

```
hello-world/
├── mod.json           # 模组配置
├── hello_world.py     # 主代码
└── README.md          # 说明文档
```

## 使用方法

1. 将此目录复制到 ModSDK 开发目录
2. 重启游戏服务器
3. 观察控制台日志

## 代码说明

### hello_world.py

```python
# 导入 ModSDK API
import mod.server.extraServerApi as serverApi

# 获取组件工厂
comp_factory = serverApi.GetEngineCompFactory()

def on_player_join(args):
    """玩家加入服务器回调"""
    player_id = args.get('playerId')
    player_name = args.get('playerName', 'Player')
    
    # 发送欢迎消息
    comp_factory.NotifyToClient(
        player_id, 
        f"§a欢迎 {player_name} 来到服务器！"
    )
    
    # 控制台日志
    print(f"[HelloWorld] {player_name} joined the server")

def on_player_leave(args):
    """玩家离开服务器回调"""
    player_name = args.get('playerName', 'Player')
    print(f"[HelloWorld] {player_name} left the server")

def on_server_start(args):
    """服务器启动回调"""
    print("[HelloWorld] Hello World Mod 已加载！")

# 注册事件监听器
comp_factory.RegisterOnJoinServer(on_player_join)
comp_factory.RegisterOnLeaveServer(on_player_leave)
comp_factory.RegisterOnServerStart(on_server_start)
```

## 测试

使用 MC-Agent-Kit CLI 测试：

```bash
# 检查代码
mc-agent check -f hello_world.py

# 搜索相关 API
mc-agent api -q "NotifyToClient"

# 搜索相关事件
mc-agent event -q "OnJoin"
```