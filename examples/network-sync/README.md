# 网络同步示例

本示例演示如何在客户端和服务端之间同步数据。

## 功能

- 服务端保存玩家金币数据
- 客户端请求并显示金币数量
- 服务端金币变化时自动通知客户端

## 结构

```
network-sync/
├── behavior_pack/
│   ├── manifest.json
│   └── scripts/
│       └── main.py        # 服务端代码
└── resource_pack/
    ├── manifest.json
    └── scripts/
        └── main.py        # 客户端代码
```

## 运行方式

1. 复制到游戏 Addons 目录
2. 创建新世界并启用 Addon
3. 使用命令测试：
   - `!coins` - 查看金币
   - `!earn` - 获得金币
   - `!spend` - 消耗金币

## 代码说明

### 服务端

```python
# behavior_pack/scripts/main.py
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

class CoinSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # 玩家金币数据
        self.player_coins = {}
        
        # 监听事件
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.on_chat
        )
        
        # 监听客户端请求
        self.ListenForEvent(
            namespace,
            systemName,
            'RequestCoins',
            self, self.on_request_coins
        )
    
    def on_chat(self, args):
        message = args.get('message', '')
        player_id = args.get('playerId')
        
        if message == '!coins':
            coins = self.player_coins.get(player_id, 0)
            self.NotifyToClient(player_id, 'UpdateCoins', {'coins': coins})
        
        elif message == '!earn':
            self.player_coins[player_id] = self.player_coins.get(player_id, 0) + 10
            self.NotifyToClient(player_id, 'UpdateCoins', {
                'coins': self.player_coins[player_id]
            })
        
        elif message == '!spend':
            if self.player_coins.get(player_id, 0) >= 5:
                self.player_coins[player_id] -= 5
                self.NotifyToClient(player_id, 'UpdateCoins', {
                    'coins': self.player_coins[player_id]
                })
    
    def on_request_coins(self, args):
        player_id = args.get('playerId')
        coins = self.player_coins.get(player_id, 0)
        self.NotifyToClient(player_id, 'UpdateCoins', {'coins': coins})

def create_system(namespace, systemName):
    return CoinSystem(namespace, systemName)
```

### 客户端

```python
# resource_pack/scripts/main.py
import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()

class CoinClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        
        self.coins = 0
        
        # 监听服务端消息
        self.ListenForEvent(
            namespace,
            systemName,
            'UpdateCoins',
            self, self.on_update_coins
        )
    
    def on_update_coins(self, args):
        self.coins = args.get('coins', 0)
        print("Coins: {}".format(self.coins))

def create_system(namespace, systemName):
    return CoinClientSystem(namespace, systemName)
```

---

*MC-Agent-Kit 示例*