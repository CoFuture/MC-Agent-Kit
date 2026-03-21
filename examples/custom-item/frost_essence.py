# 冰霜精华物品模组
# 演示自定义物品的创建和使用

import mod.server.extraServerApi as serverApi

# 物品 ID
FROST_ESSENCE_ID = "custom:frost_essence"

# 获取组件工厂
comp_factory = serverApi.GetEngineCompFactory()

# 冷却追踪
_player_cooldowns = {}


class FrostEssenceMod:
    """冰霜精华模组"""
    
    def __init__(self):
        self.cooldown_duration = 30  # 冷却时间（秒）
    
    def on_load(self):
        """模组加载"""
        self._register_events()
        print("[FrostEssence] 冰霜精华模组已加载")
    
    def _register_events(self):
        """注册事件监听器"""
        comp_factory.RegisterOnServerItemUse(self._on_item_use)
    
    def _on_item_use(self, args):
        """物品使用回调"""
        player_id = args.get('playerId')
        item_id = args.get('itemId')
        
        # 检查是否是冰霜精华
        if item_id == FROST_ESSENCE_ID:
            # 检查冷却
            if self._is_on_cooldown(player_id):
                comp_factory.NotifyToClient(
                    player_id,
                    "§c冰霜精华正在冷却中..."
                )
                return False
            
            # 使用物品
            self._use_frost_essence(player_id)
            return True  # 消耗物品
        
        return False
    
    def _use_frost_essence(self, player_id):
        """使用冰霜精华"""
        import time
        
        # 给予效果
        comp_factory.AddEffectToEntity(
            player_id,
            "slowness",
            10,  # 持续时间（秒）
            2    # 效果等级
        )
        
        comp_factory.AddEffectToEntity(
            player_id,
            "speed",
            10,
            1
        )
        
        # 发送消息
        comp_factory.NotifyToClient(
            player_id,
            "§b你使用了冰霜精华！"
        )
        
        # 设置冷却
        _player_cooldowns[player_id] = time.time()
        
        print("[FrostEssence] Player {} used frost essence".format(player_id))
    
    def _is_on_cooldown(self, player_id):
        """检查是否在冷却中"""
        import time
        
        if player_id not in _player_cooldowns:
            return False
        
        last_use = _player_cooldowns[player_id]
        elapsed = time.time() - last_use
        
        return elapsed < self.cooldown_duration


# 模组入口
mod = FrostEssenceMod()
mod.on_load()