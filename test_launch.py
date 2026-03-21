"""
测试启动游戏脚本
"""
import subprocess
import sys
import os
import time
import socket
import json
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mc_agent_kit.launcher.addon_scanner import scan_addon, list_addons, AddonInfo
from mc_agent_kit.launcher.game_launcher import launch_game, find_free_port, generate_error_log_path

# 配置
MC_STUDIO_ROOT = "D:\\MCStudioDownload"
ACCOUNT = "ningboo666@163.com"
GAME_VERSION = "3.7.0.222545"
GAME_EXE = os.path.join(MC_STUDIO_ROOT, "game", "MinecraftPE_Netease", GAME_VERSION, "Minecraft.Windows.exe")
ADDON_DIR = os.path.join(MC_STUDIO_ROOT, "work", ACCOUNT, "Cpp", "AddOn")
GEN_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "generated")

def generate_config(addon: AddonInfo, launcher_port: int, logging_port: int):
    """生成配置文件"""
    import base64
    token = base64.b64encode(os.urandom(16)).decode()
    
    resource_pack_dirs = [rp.dir_name for rp in addon.resource_packs]
    behavior_pack_dirs = [bp.dir_name for bp in addon.behavior_packs]
    
    os.makedirs(GEN_CONFIG_DIR, exist_ok=True)
    config_path = os.path.join(GEN_CONFIG_DIR, f"{addon.id}.cppconfig")
    
    config = {
        "version": GAME_VERSION,
        "client_type": 0,
        "MainComponentId": addon.id,
        "LocalComponentPathsDict": {
            addon.id: {
                "cfg_path": addon.path,
                "work_path": addon.path,
            }
        },
        "LocalComponentPaths": None,
        "world_info": {
            "level_id": addon.id,
            "game_type": 1,  # 创造模式
            "difficulty": 2,
            "permission_level": 1,
            "cheat": True,
            "cheat_info": {
                "pvp": True, "show_coordinates": False, "always_day": False,
                "daylight_cycle": True, "fire_spreads": True, "tnt_explodes": True,
                "keep_inventory": True, "mob_spawn": True, "natural_regeneration": True,
                "mob_loot": True, "mob_griefing": True, "tile_drops": True,
                "entities_drop_loot": True, "weather_cycle": True,
                "command_blocks_enabled": True, "random_tick_speed": 1,
            },
            "resource_packs": resource_pack_dirs,
            "behavior_packs": behavior_pack_dirs,
            "name": addon.name,
            "world_type": 2,
            "start_with_map": False,
            "bonus_items": False,
            "seed": "",
        },
        "room_info": {
            "ip": "", "port": 0, "muiltClient": False, "room_name": "",
            "token": token, "room_id": 0, "host_id": 0, "allow_pe": True,
            "max_player": 0, "visibility_mode": 0, "is_pe": True,
            "tag_ids": None, "item_ids": [],
        },
        "player_info": {
            "user_id": 2147672241,
            "user_name": "开发者DQcZc",
            "urs": ACCOUNT,
        },
        "skin_info": {
            "skin": os.path.join(MC_STUDIO_ROOT, "componentcache", "support", "steve", "steve.png"),
        },
        "anti_addiction_info": {
            "enable": False, "left_time": 0, "exp_multiplier": 1.0,
            "block_multplier": 1.0, "first_message": "",
        },
        "misc": {
            "multiplayer_game_type": 0, "game_id": None,
            "auth_server_url": "https://g79authexpr1.nie.netease.com",
            "launcher_port": launcher_port,
            "sensitive_word_file": "", "is_store_enabled": 1,
        },
        "path": config_path,
        "web_server_url": "https://x19mclexpr.nie.netease.com",
        "core_server_url": "https://x19exprcore.nie.netease.com:8443",
        "last_play_time": int(time.time()),
        "vip_using_mod": [bp.uuid for bp in addon.behavior_packs] + [rp.uuid for rp in addon.resource_packs],
        "isCloud": False,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_path

def main():
    print("=" * 50)
    print("  MC-Agent-Kit 游戏启动测试")
    print("=" * 50)
    
    # 检查游戏
    if not os.path.exists(GAME_EXE):
        print(f"错误: 找不到游戏 {GAME_EXE}")
        return
    
    print(f"游戏路径: {GAME_EXE}")
    
    # 扫描 Addon
    addons = list_addons(ADDON_DIR)
    if not addons:
        print(f"错误: 没有找到 Addon")
        return
    
    # 选择第一个有 behavior pack 的 addon
    selected = None
    for addon in addons:
        if addon.behavior_packs:
            selected = addon
            break
    
    if not selected:
        selected = addons[0]
    
    print(f"\n选择的 Addon: {selected.name}")
    print(f"  ID: {selected.id}")
    print(f"  Behavior Packs: {len(selected.behavior_packs)}")
    print(f"  Resource Packs: {len(selected.resource_packs)}")
    
    # 生成配置
    launcher_port = find_free_port()
    logging_port = find_free_port()
    config_path = generate_config(selected, launcher_port, logging_port)
    error_log_path = generate_error_log_path()
    
    print(f"\n配置已生成: {config_path}")
    print(f"  launcher_port = {launcher_port}")
    print(f"  logging_port = {logging_port}")
    print(f"  error_log = {error_log_path}")
    
    # 启动游戏
    print("\n启动游戏...")
    game_process = launch_game(
        game_exe_path=GAME_EXE,
        config_path=config_path,
        logging_port=logging_port,
        logging_ip="127.0.0.1",
        error_log_path=error_log_path,
    )
    
    print(f"游戏进程已启动, PID: {game_process.pid}")
    print("\n等待 5 秒后检查进程状态...")
    time.sleep(5)
    
    if game_process.is_running():
        print("游戏正在运行!")
        print(f"  请手动截图游戏窗口")
        print(f"  进程 PID: {game_process.pid}")
    else:
        print(f"游戏已退出, 返回码: {game_process.process.returncode}")
    
    return game_process

if __name__ == "__main__":
    proc = main()