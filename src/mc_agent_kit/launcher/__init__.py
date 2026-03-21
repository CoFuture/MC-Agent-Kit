"""
游戏启动器模块

负责扫描 Addon、生成配置、启动游戏进程。
"""

from .addon_scanner import AddonInfo, list_addons, scan_addon
from .config_generator import GameConfig, generate_config
from .game_launcher import GameProcess, launch_game

__all__ = [
    "AddonInfo",
    "scan_addon",
    "list_addons",
    "GameConfig",
    "generate_config",
    "launch_game",
    "GameProcess",
]
