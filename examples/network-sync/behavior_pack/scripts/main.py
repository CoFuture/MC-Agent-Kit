# -*- coding: utf-8 -*-
"""
网络同步示例 - 服务端代码
演示如何在客户端和服务端之间同步数据
"""

import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

# 定义命名空间
NAMESPACE = "network_sync"
SYSTEM_NAME = "NetworkSyncSystem"


class NetworkSyncSystem(ServerSystem):
    """网络同步系统 - 服务端"""
    
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 玩家数据存储
        self.player_data = {}
        
        # 注册事件监听
        self._register_events()
        
        print("[NetworkSync] Server system initialized")
    
    def _register_events(self):
        """注册事件监听"""
        # 监听玩家聊天
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.on_chat
        )
        
        # 监听玩家加入
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnAddServerPlayer',
            self, self.on_player_join
        )
        
        # 监听玩家离开
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnDelServerPlayer',
            self, self.on_player_leave
        )
        
        # 监听客户端请求
        self.ListenForEvent(
            NAMESPACE,
            SYSTEM_NAME,
            'RequestData',
            self, self.on_request_data
        )
    
    def on_player_join(self, args):
        """玩家加入"""
        player_id = args.get('id')
        player_name = args.get('name', 'Unknown')
        
        # 初始化玩家数据
        self.player_data[player_id] = {
            'name': player_name,
            'coins': 100,  # 初始金币
            'level': 1,
            'exp': 0
        }
        
        # 同步数据给客户端
        self.sync_player_data(player_id)
        
        print("[NetworkSync] Player joined: {}".format(player_name))
    
    def on_player_leave(self, args):
        """玩家离开"""
        player_id = args.get('id')
        
        # 清理数据
        if player_id in self.player_data:
            del self.player_data[player_id]
        
        print("[NetworkSync] Player left")
    
    def on_chat(self, args):
        """处理聊天命令"""
        player_id = args.get('playerId')
        message = args.get('message', '').strip()
        
        # 命令处理
        if message == '!coins':
            self.cmd_show_coins(player_id)
        elif message == '!earn':
            self.cmd_earn_coins(player_id)
        elif message == '!spend':
            self.cmd_spend_coins(player_id)
        elif message == '!level':
            self.cmd_show_level(player_id)
        elif message == '!exp':
            self.cmd_add_exp(player_id)
    
    def cmd_show_coins(self, player_id):
        """显示金币"""
        data = self.player_data.get(player_id, {})
        coins = data.get('coins', 0)
        self.notify_client(player_id, 'ShowMessage', {
            'message': 'Your coins: {}'.format(coins)
        })
    
    def cmd_earn_coins(self, player_id):
        """获得金币"""
        if player_id not in self.player_data:
            return
        
        # 增加金币
        self.player_data[player_id]['coins'] += 10
        
        # 同步给客户端
        self.sync_player_data(player_id)
        
        self.notify_client(player_id, 'ShowMessage', {
            'message': 'Earned 10 coins! Total: {}'.format(
                self.player_data[player_id]['coins']
            )
        })
    
    def cmd_spend_coins(self, player_id):
        """消费金币"""
        if player_id not in self.player_data:
            return
        
        data = self.player_data[player_id]
        
        if data['coins'] >= 5:
            data['coins'] -= 5
            self.sync_player_data(player_id)
            self.notify_client(player_id, 'ShowMessage', {
                'message': 'Spent 5 coins! Remaining: {}'.format(data['coins'])
            })
        else:
            self.notify_client(player_id, 'ShowMessage', {
                'message': 'Not enough coins!'
            })
    
    def cmd_show_level(self, player_id):
        """显示等级"""
        data = self.player_data.get(player_id, {})
        level = data.get('level', 1)
        exp = data.get('exp', 0)
        self.notify_client(player_id, 'ShowMessage', {
            'message': 'Level: {}, EXP: {}'.format(level, exp)
        })
    
    def cmd_add_exp(self, player_id):
        """增加经验"""
        if player_id not in self.player_data:
            return
        
        data = self.player_data[player_id]
        data['exp'] += 10
        
        # 升级检查 (每 100 经验升一级)
        if data['exp'] >= 100:
            data['level'] += 1
            data['exp'] -= 100
            self.notify_client(player_id, 'ShowMessage', {
                'message': 'Level UP! Now level {}'.format(data['level'])
            })
        
        self.sync_player_data(player_id)
    
    def on_request_data(self, args):
        """处理客户端数据请求"""
        player_id = args.get('playerId')
        self.sync_player_data(player_id)
    
    def sync_player_data(self, player_id):
        """同步玩家数据给客户端"""
        data = self.player_data.get(player_id)
        if data:
            self.notify_client(player_id, 'SyncData', {
                'coins': data['coins'],
                'level': data['level'],
                'exp': data['exp']
            })
    
    def notify_client(self, player_id, event, data):
        """通知客户端"""
        self.NotifyToClient(player_id, event, data)
    
    def OnDestroy(self):
        """系统销毁"""
        self.player_data.clear()
        print("[NetworkSync] Server system destroyed")


# 系统工厂函数
def create_system(namespace, systemName):
    return NetworkSyncSystem(namespace, systemName)