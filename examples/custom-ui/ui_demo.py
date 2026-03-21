# UI 示例模组
# 演示自定义 UI 的创建和交互

import mod.server.extraServerApi as serverApi

# UI 名称
DEMO_UI_NAME = "demo_screen"

# 获取组件工厂
comp_factory = serverApi.GetEngineCompFactory()


class UIDemoMod:
    """UI 示例模组"""
    
    def __init__(self):
        self.active_uis = {}  # player_id -> ui_data
    
    def on_load(self):
        """模组加载"""
        self._register_events()
        self._register_commands()
        print("[UIDemo] UI 示例模组已加载")
    
    def _register_events(self):
        """注册事件监听器"""
        # UI 按钮点击事件
        comp_factory.RegisterOnUIButtonClick(self._on_ui_button_click)
        
        # 玩家离开事件（清理 UI）
        comp_factory.RegisterOnLeaveServer(self._on_player_leave)
    
    def _register_commands(self):
        """注册自定义命令"""
        # 注册 /open_demo_ui 命令
        comp_factory.RegisterCommand(
            "open_demo_ui",
            self._cmd_open_ui,
            "打开演示 UI"
        )
    
    def _cmd_open_ui(self, player_id, args):
        """打开 UI 命令处理"""
        self._open_demo_ui(player_id)
        return True
    
    def _open_demo_ui(self, player_id):
        """打开演示 UI"""
        # 创建 UI 数据
        ui_data = {
            "title": "演示界面",
            "content": "欢迎使用 MC-Agent-Kit UI 示例！",
            "buttons": [
                {"id": "btn_ok", "text": "确定"},
                {"id": "btn_info", "text": "信息"},
                {"id": "btn_close", "text": "关闭"}
            ]
        }
        
        # 显示 UI
        comp_factory.NotifyToClient(
            player_id,
            "demo_screen",
            ui_data
        )
        
        # 记录活跃 UI
        self.active_uis[player_id] = ui_data
        
        print("[UIDemo] Opened demo UI for player {}".format(player_id))
    
    def _on_ui_button_click(self, args):
        """UI 按钮点击回调"""
        player_id = args.get('playerId')
        button_id = args.get('buttonId')
        ui_name = args.get('uiName')
        
        if ui_name != DEMO_UI_NAME:
            return
        
        print("[UIDemo] Player {} clicked button {}".format(player_id, button_id))
        
        # 处理不同按钮
        if button_id == "btn_ok":
            comp_factory.NotifyToClient(
                player_id,
                "§a你点击了确定按钮！"
            )
        
        elif button_id == "btn_info":
            # 显示信息
            info_text = "§eMC-Agent-Kit UI 示例\n§f版本: 1.0.0\n作者: MC-Agent-Kit"
            comp_factory.NotifyToClient(player_id, info_text)
        
        elif button_id == "btn_close":
            # 关闭 UI
            self._close_ui(player_id)
    
    def _close_ui(self, player_id):
        """关闭 UI"""
        comp_factory.NotifyToClient(
            player_id,
            "close_ui",
            {"ui_name": DEMO_UI_NAME}
        )
        
        if player_id in self.active_uis:
            del self.active_uis[player_id]
        
        print("[UIDemo] Closed demo UI for player {}".format(player_id))
    
    def _on_player_leave(self, args):
        """玩家离开回调"""
        player_id = args.get('playerId')
        
        if player_id in self.active_uis:
            del self.active_uis[player_id]


# 模组入口
mod = UIDemoMod()
mod.on_load()