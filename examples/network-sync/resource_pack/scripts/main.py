# -*- coding: utf-8 -*-
"""
网络同步示例 - 客户端代码
演示如何接收服务端同步的数据
"""

import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()

# 定义命名空间
NAMESPACE = "network_sync"
SYSTEM_NAME = "NetworkSyncSystem"


class NetworkSyncClientSystem(ClientSystem):
    """网络同步系统 - 客户端"""
    
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        
        # 本地数据缓存
        self.local_data = {
            'coins': 0,
            'level': 1,
            'exp': 0
        }
        
        # 注册事件监听
        self._register_events()
        
        print("[NetworkSyncClient] Client system initialized")
    
    def _register_events(self):
        """注册事件监听"""
        # 监听服务端同步数据
        self.ListenForEvent(
            NAMESPACE,
            SYSTEM_NAME,
            'SyncData',
            self, self.on_sync_data
        )
        
        # 监听服务端消息
        self.ListenForEvent(
            NAMESPACE,
            SYSTEM_NAME,
            'ShowMessage',
            self, self.on_show_message
        )
        
        # 监听按键事件
        self.ListenForEvent(
            clientApi.GetEngineNamespace(),
            clientApi.GetEngineSystemName(),
            'OnKeyPress',
            self, self.on_key_press
        )
    
    def on_sync_data(self, args):
        """处理服务端同步的数据"""
        self.local_data['coins'] = args.get('coins', 0)
        self.local_data['level'] = args.get('level', 1)
        self.local_data['exp'] = args.get('exp', 0)
        
        print("[NetworkSyncClient] Data synced: coins={}, level={}, exp={}".format(
            self.local_data['coins'],
            self.local_data['level'],
            self.local_data['exp']
        ))
    
    def on_show_message(self, args):
        """显示服务端消息"""
        message = args.get('message', '')
        print("[NetworkSyncClient] Message: {}".format(message))
    
    def on_key_press(self, args):
        """处理按键"""
        key = args.get('key')
        
        # P 键请求同步数据
        if key == 'P':
            self.request_sync()
    
    def request_sync(self):
        """请求服务端同步数据"""
        self.NotifyToServer('RequestData', {})
    
    def get_coins(self):
        """获取金币数"""
        return self.local_data['coins']
    
    def get_level(self):
        """获取等级"""
        return self.local_data['level']
    
    def OnDestroy(self):
        """系统销毁"""
        print("[NetworkSyncClient] Client system destroyed")


# 系统工厂函数
def create_system(namespace, systemName):
    return NetworkSyncClientSystem(namespace, systemName)