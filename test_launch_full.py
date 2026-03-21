"""
测试启动游戏脚本 - 完整版
包含 TCP 服务器来接收游戏连接
"""
import subprocess
import sys
import os
import time
import socket
import json
import threading
import base64
from datetime import datetime

# 配置
MC_STUDIO_ROOT = "D:\\MCStudioDownload"
ACCOUNT = "ningboo666@163.com"
GAME_VERSION = "3.7.0.222545"
GAME_EXE = os.path.join(MC_STUDIO_ROOT, "game", "MinecraftPE_Netease", GAME_VERSION, "Minecraft.Windows.exe")
ADDON_DIR = os.path.join(MC_STUDIO_ROOT, "work", ACCOUNT, "Cpp", "AddOn")
GEN_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "generated")


class TCPServer:
    """TCP 服务器接收游戏连接"""
    
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        self._thread = None
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        self.running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        print(f"[{self.name}] TCP 服务器已启动 {self.host}:{self.port}")
        
    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                print(f"[{self.name}] 新连接: {addr}")
                self.clients.append(client)
                t = threading.Thread(target=self._handle_client, args=(client, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break
                
    def _handle_client(self, client, addr):
        try:
            while self.running:
                data = client.recv(4096)
                if not data:
                    break
                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = data.hex()
                print(f"[{self.name}] [{addr}] ({len(data)} bytes): {text[:200]}...")
        except (ConnectionResetError, OSError):
            pass
        finally:
            print(f"[{self.name}] 连接断开: {addr}")
            client.close()
            
    def stop(self):
        self.running = False
        for c in self.clients:
            try:
                c.close()
            except OSError:
                pass
        if self.server_socket:
            self.server_socket.close()
        if self._thread:
            self._thread.join(timeout=3)
        print(f"[{self.name}] 服务器已关闭")


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def scan_addon(addon_path):
    """扫描 Addon 目录"""
    addon_id = os.path.basename(addon_path)
    info = {
        "id": addon_id,
        "name": addon_id,
        "path": addon_path,
        "behavior_packs": [],
        "resource_packs": [],
    }
    
    mcscfg = os.path.join(addon_path, "work.mcscfg")
    if os.path.exists(mcscfg):
        try:
            with open(mcscfg, encoding="utf-8") as f:
                cfg = json.load(f)
            info["name"] = cfg.get("Name", addon_id)
        except Exception:
            pass
    
    for entry in os.listdir(addon_path):
        entry_path = os.path.join(addon_path, entry)
        if not os.path.isdir(entry_path):
            continue
        
        manifest_path = os.path.join(entry_path, "pack_manifest.json")
        if not os.path.exists(manifest_path):
            continue
        
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            header = manifest.get("header", {})
            pack_uuid = header.get("uuid", "")
            pack_version = header.get("version", [0, 0, 1])
            
            pack_info = {"dir_name": entry, "uuid": pack_uuid, "version": pack_version}
            
            if entry.startswith("behavior_pack"):
                info["behavior_packs"].append(pack_info)
            elif entry.startswith("resource_pack"):
                info["resource_packs"].append(pack_info)
        except Exception:
            continue
    
    return info


def list_addons(addon_dir):
    """列出所有 Addon"""
    addons = []
    if not os.path.exists(addon_dir):
        return addons
    for d in os.listdir(addon_dir):
        addon_path = os.path.join(addon_dir, d)
        if os.path.isdir(addon_path):
            addons.append(scan_addon(addon_path))
    return addons


def generate_config(addon, launcher_port, logging_port):
    """生成配置文件"""
    token = base64.b64encode(os.urandom(16)).decode()
    
    resource_pack_dirs = [rp["dir_name"] for rp in addon["resource_packs"]]
    behavior_pack_dirs = [bp["dir_name"] for bp in addon["behavior_packs"]]
    
    os.makedirs(GEN_CONFIG_DIR, exist_ok=True)
    config_path = os.path.join(GEN_CONFIG_DIR, f"{addon['id']}.cppconfig")
    
    config = {
        "version": GAME_VERSION,
        "client_type": 0,
        "MainComponentId": addon["id"],
        "LocalComponentPathsDict": {
            addon["id"]: {
                "cfg_path": addon["path"],
                "work_path": addon["path"],
            }
        },
        "LocalComponentPaths": None,
        "world_info": {
            "level_id": addon["id"],
            "game_type": 1,
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
            "name": addon["name"],
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
        "vip_using_mod": [bp["uuid"] for bp in addon["behavior_packs"]] + [rp["uuid"] for rp in addon["resource_packs"]],
        "isCloud": False,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_path


def generate_error_log_path():
    base_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "log", "x64_mc", "errorlogs")
    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return os.path.join(base_dir, f"{timestamp}.log")


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
        if addon["behavior_packs"]:
            selected = addon
            break
    
    if not selected:
        selected = addons[0]
    
    print(f"\n选择的 Addon: {selected['name']}")
    print(f"  ID: {selected['id']}")
    print(f"  Behavior Packs: {len(selected['behavior_packs'])}")
    print(f"  Resource Packs: {len(selected['resource_packs'])}")
    
    # 分配端口
    launcher_port = find_free_port()
    logging_port = find_free_port()
    
    # 生成配置
    config_path = generate_config(selected, launcher_port, logging_port)
    error_log_path = generate_error_log_path()
    
    print(f"\n配置已生成: {config_path}")
    print(f"  launcher_port = {launcher_port}")
    print(f"  logging_port = {logging_port}")
    print(f"  error_log = {error_log_path}")
    
    # 启动 TCP 服务器
    launcher_server = TCPServer("Launcher", "127.0.0.1", launcher_port)
    launcher_server.start()
    
    logging_server = TCPServer("Logging", "127.0.0.1", logging_port)
    logging_server.start()
    
    # 启动游戏
    print("\n启动游戏...")
    
    cmd = [
        GAME_EXE,
        f"config={config_path}",
        f"errorlog={error_log_path}",
        "dc_tag1=studio_no_launcher",
        f"loggingIP=127.0.0.1",
        f"loggingPort={logging_port}",
    ]
    
    process = subprocess.Popen(cmd, cwd=os.path.dirname(GAME_EXE))
    print(f"游戏进程已启动, PID: {process.pid}")
    print("\n游戏正在运行... 等待 30 秒后截图")
    
    # 等待游戏启动
    time.sleep(30)
    
    print("\n游戏启动成功!")
    print(f"  进程 PID: {process.pid}")
    print(f"  是否运行: {process.poll() is None}")
    
    # 保持运行
    try:
        while True:
            ret = process.poll()
            if ret is not None:
                print(f"\n游戏已退出, 返回码: {ret}")
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n终止游戏...")
        process.terminate()
        process.wait()
    finally:
        launcher_server.stop()
        logging_server.stop()


if __name__ == "__main__":
    main()