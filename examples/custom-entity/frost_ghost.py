# 冰霜幽灵实体模组
# 演示自定义实体的创建和配置

import mod.server.extraServerApi as serverApi

# 实体 ID
FROST_GHOST_ID = "custom:frost_ghost"

# 获取组件工厂
comp_factory = serverApi.GetEngineCompFactory()


class FrostGhostMod:
    """冰霜幽灵模组"""
    
    def __init__(self):
        self.entity_events = {}
    
    def on_load(self):
        """模组加载"""
        self._register_events()
        print("[FrostGhost] 冰霜幽灵模组已加载")
    
    def _register_events(self):
        """注册事件监听器"""
        # 实体创建事件
        comp_factory.RegisterOnEntityCreated(self._on_entity_created)
        
        # 实体受伤事件
        comp_factory.RegisterOnEntityHurt(self._on_entity_hurt)
        
        # 实体死亡事件
        comp_factory.RegisterOnEntityDie(self._on_entity_die)
    
    def _on_entity_created(self, args):
        """实体创建回调"""
        entity_id = args.get('entityId')
        entity_type = args.get('entityType')
        
        if entity_type == FROST_GHOST_ID:
            print("[FrostGhost] 冰霜幽灵已创建: {}".format(entity_id))
            self.entity_events[entity_id] = True
    
    def _on_entity_hurt(self, args):
        """实体受伤回调"""
        entity_id = args.get('entityId')
        damage = args.get('damage', 0)
        
        if entity_id in self.entity_events:
            print("[FrostGhost] 冰霜幽灵受到 {} 点伤害".format(damage))
            
            # 获取攻击者
            attacker_id = args.get('srcId')
            if attacker_id:
                self._apply_frost_effect(attacker_id)
    
    def _on_entity_die(self, args):
        """实体死亡回调"""
        entity_id = args.get('entityId')
        
        if entity_id in self.entity_events:
            print("[FrostGhost] 冰霜幽灵被击败！")
            del self.entity_events[entity_id]
    
    def _apply_frost_effect(self, target_id):
        """对目标施加冰霜效果"""
        # 减速效果
        comp_factory.AddEffectToEntity(
            target_id,
            "slowness",
            3,  # 持续时间（秒）
            1   # 效果等级
        )


# 模组入口
mod = FrostGhostMod()
mod.on_load()