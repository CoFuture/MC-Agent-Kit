"""
配置生成模块

生成游戏启动所需的 cppconfig 配置文件。
"""

from __future__ import annotations
import base64
import json
import os
import time
from dataclasses import dataclass, field


@dataclass
class CheatInfo:
    """作弊选项配置"""
    pvp: bool = True
    show_coordinates: bool = False
    always_day: bool = False
    daylight_cycle: bool = True
    fire_spreads: bool = True
    tnt_explodes: bool = True
    keep_inventory: bool = True
    mob_spawn: bool = True
    natural_regeneration: bool = True
    mob_loot: bool = True
    mob_griefing: bool = True
    tile_drops: bool = True
    entities_drop_loot: bool = True
    weather_cycle: bool = True
    command_blocks_enabled: bool = True
    random_tick_speed: int = 1
    experimental_holiday: bool = False
    experimental_biomes: bool = False
    fancy_bubbles: bool = False


@dataclass
class WorldInfo:
    """世界配置"""
    game_type: int = 1  # 0=生存, 1=创造, 2=冒险
    difficulty: int = 2  # 0=和平, 1=简单, 2=普通, 3=困难
    world_type: int = 2  # 0=旧世界, 1=无限, 2=平坦
    permission_level: int = 1
    cheat: bool = True
    cheat_info: CheatInfo = field(default_factory=CheatInfo)
    seed: str = ""
    start_with_map: bool = False
    bonus_items: bool = False
    resource_packs: list[str] = field(default_factory=list)
    behavior_packs: list[str] = field(default_factory=list)
    name: str = ""


@dataclass
class PlayerInfo:
    """玩家配置"""
    user_id: int = 0
    user_name: str = ""
    account: str = ""
    skin_path: str = ""


@dataclass
class ServerInfo:
    """服务器配置"""
    auth_server_url: str = ""
    web_server_url: str = ""
    core_server_url: str = ""
    dc_web: str = ""
    dc_uid: str = ""


@dataclass
class GameConfig:
    """游戏启动配置"""
    addon_id: str
    addon_name: str
    addon_path: str
    game_version: str
    game_exe_path: str
    world_info: WorldInfo
    player_info: PlayerInfo
    server_info: ServerInfo
    launcher_port: int = 0
    logging_port: int = 0
    logging_ip: str = "127.0.0.1"
    error_log_path: str = ""


def generate_config(
    addon_info,
    game_config: GameConfig,
    output_dir: str,
) -> tuple[dict, str]:
    """
    生成 cppconfig 配置文件。

    Args:
        addon_info: AddonInfo 对象
        game_config: GameConfig 配置对象
        output_dir: 配置输出目录

    Returns:
        (配置字典, 配置文件路径)
    """
    token = base64.b64encode(os.urandom(16)).decode()

    resource_pack_dirs = [rp.dir_name for rp in addon_info.resource_packs]
    behavior_pack_dirs = [bp.dir_name for bp in addon_info.behavior_packs]
    all_pack_uuids = [bp.uuid for bp in addon_info.behavior_packs] + \
                     [rp.uuid for rp in addon_info.resource_packs]

    os.makedirs(output_dir, exist_ok=True)
    config_path = os.path.join(output_dir, f"{addon_info.id}.cppconfig")

    world = game_config.world_info
    player = game_config.player_info
    server = game_config.server_info

    config = {
        "version": game_config.game_version,
        "client_type": 0,
        "MainComponentId": addon_info.id,
        "LocalComponentPathsDict": {
            addon_info.id: {
                "cfg_path": addon_info.path,
                "work_path": addon_info.path,
            }
        },
        "LocalComponentPaths": None,
        "world_info": {
            "level_id": addon_info.id,
            "game_type": world.game_type,
            "difficulty": world.difficulty,
            "permission_level": world.permission_level,
            "cheat": world.cheat,
            "cheat_info": {
                "pvp": world.cheat_info.pvp,
                "show_coordinates": world.cheat_info.show_coordinates,
                "always_day": world.cheat_info.always_day,
                "daylight_cycle": world.cheat_info.daylight_cycle,
                "fire_spreads": world.cheat_info.fire_spreads,
                "tnt_explodes": world.cheat_info.tnt_explodes,
                "keep_inventory": world.cheat_info.keep_inventory,
                "mob_spawn": world.cheat_info.mob_spawn,
                "natural_regeneration": world.cheat_info.natural_regeneration,
                "mob_loot": world.cheat_info.mob_loot,
                "mob_griefing": world.cheat_info.mob_griefing,
                "tile_drops": world.cheat_info.tile_drops,
                "entities_drop_loot": world.cheat_info.entities_drop_loot,
                "weather_cycle": world.cheat_info.weather_cycle,
                "command_blocks_enabled": world.cheat_info.command_blocks_enabled,
                "random_tick_speed": world.cheat_info.random_tick_speed,
                "experimental_holiday": world.cheat_info.experimental_holiday,
                "experimental_biomes": world.cheat_info.experimental_biomes,
                "fancy_bubbles": world.cheat_info.fancy_bubbles,
            },
            "resource_packs": resource_pack_dirs,
            "behavior_packs": behavior_pack_dirs,
            "name": addon_info.name,
            "world_type": world.world_type,
            "start_with_map": world.start_with_map,
            "bonus_items": world.bonus_items,
            "seed": world.seed,
        },
        "room_info": {
            "ip": "",
            "port": 0,
            "muiltClient": False,
            "room_name": "",
            "token": token,
            "room_id": 0,
            "host_id": 0,
            "allow_pe": True,
            "max_player": 0,
            "visibility_mode": 0,
            "is_pe": True,
            "tag_ids": None,
            "item_ids": [],
        },
        "player_info": {
            "user_id": player.user_id,
            "user_name": player.user_name,
            "urs": player.account,
        },
        "skin_info": {
            "skin": player.skin_path,
        },
        "anti_addiction_info": {
            "enable": False,
            "left_time": 0,
            "exp_multiplier": 1.0,
            "block_multplier": 1.0,
            "first_message": "",
        },
        "misc": {
            "multiplayer_game_type": 0,
            "game_id": None,
            "auth_server_url": server.auth_server_url,
            "launcher_port": game_config.launcher_port,
            "sensitive_word_file": "",
            "is_store_enabled": 1,
        },
        "path": config_path,
        "web_server_url": server.web_server_url,
        "core_server_url": server.core_server_url,
        "last_play_time": int(time.time()),
        "vip_using_mod": all_pack_uuids,
        "isCloud": False,
    }

    return config, config_path


def save_config(config: dict, config_path: str) -> None:
    """
    保存配置到文件。

    Args:
        config: 配置字典
        config_path: 配置文件路径
    """
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
