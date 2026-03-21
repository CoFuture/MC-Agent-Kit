# Hello World Mod
# 玩家加入/离开服务器欢迎消息示例

import mod.server.extraServerApi as serverApi

# 获取组件工厂
comp_factory = serverApi.GetEngineCompFactory()


def on_player_join(args):
    """玩家加入服务器回调
    
    Args:
        args: 事件参数
            - playerId: 玩家 ID
            - playerName: 玩家名称
    """
    player_id = args.get('playerId')
    player_name = args.get('playerName', 'Player')
    
    # 发送欢迎消息
    comp_factory.NotifyToClient(
        player_id, 
        "§a欢迎 {} 来到服务器！".format(player_name)
    )
    
    # 控制台日志
    print("[HelloWorld] {} joined the server".format(player_name))


def on_player_leave(args):
    """玩家离开服务器回调
    
    Args:
        args: 事件参数
            - playerId: 玩家 ID
            - playerName: 玩家名称
    """
    player_name = args.get('playerName', 'Player')
    print("[HelloWorld] {} left the server".format(player_name))


def on_server_start(args):
    """服务器启动回调"""
    print("[HelloWorld] Hello World Mod 已加载！")


# 注册事件监听器
comp_factory.RegisterOnJoinServer(on_player_join)
comp_factory.RegisterOnLeaveServer(on_player_leave)
comp_factory.RegisterOnServerStart(on_server_start)