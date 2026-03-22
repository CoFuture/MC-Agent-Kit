"""
测试游戏启动器 - 启动游戏并捕获日志
"""
import base64
import json
import os
import subprocess
import socket
import threading
import time
from datetime import datetime

# 配置
MC_STUDIO_ROOT = "D:\\MCStudioDownload"
ACCOUNT = "ningboo666@163.com"
GAME_VERSION = "3.7.0.222545"
GAME_EXE = os.path.join(MC_STUDIO_ROOT, "game", "MinecraftPE_Netease", GAME_VERSION, "Minecraft.Windows.exe")
ADDON_DIR = os.path.join(MC_STUDIO_ROOT, "work", ACCOUNT, "Cpp", "AddOn")

# 选择的 addon
ADDON_ID = "3c5afc820e514210ba430db5d46ac2b1"
ADDON_NAME = "自定义中国版粒子特效材质"

# 用户配置
PLAYER_USER_ID = 2147672241
PLAYER_USER_NAME = "开发者DQcZc"
SKIN_PATH = ""  # 不设置皮肤，避免路径问题
AUTH_SERVER_URL = "https://g79authexpr1.nie.netease.com"
WEB_SERVER_URL = "https://x19mclexpr.nie.netease.com"
CORE_SERVER_URL = "https://x19exprcore.nie.netease.com:8443"
DC_WEB = "https://x19apigatewayexpr.nie.netease.com"
DC_UID = "188593"

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class TCPServer:
    """TCP 日志服务器"""
    
    def __init__(self, name, host, port, log_file):
        self.name = name
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        self._thread = None
        self._lock = threading.Lock()
        self.log_file_path = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self._log_file = open(log_file, "a", encoding="utf-8")
        self.logs = []  # 存储所有日志
    
    def _log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] [{self.name}] {msg}"
        print(line)
        self.logs.append(line)
        with self._lock:
            self._log_file.write(line + "\n")
            self._log_file.flush()
    
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        self.running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        self._log(f"TCP 服务器已启动, 监听 {self.host}:{self.port}")
    
    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                self._log(f"新连接: {addr}")
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
                self._log(f"[{addr}] ({len(data)} bytes): {text}")
        except (ConnectionResetError, OSError):
            pass
        finally:
            self._log(f"连接断开: {addr}")
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
        self._log("服务器已关闭")
        self._log_file.close()
    
    def get_logs(self):
        return "\n".join(self.logs)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def generate_error_log_path():
    base_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "log", "x64_mc", "errorlogs")
    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return os.path.join(base_dir, f"{timestamp}.log")


def scan_addon(addon_path):
    """扫描 addon 信息"""
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
        with open(mcscfg, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        info["name"] = cfg.get("Name", addon_id)
    
    for entry in os.listdir(addon_path):
        entry_path = os.path.join(addon_path, entry)
        if not os.path.isdir(entry_path):
            continue
        
        # 尝试两种 manifest 文件名
        manifest_path = os.path.join(entry_path, "pack_manifest.json")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(entry_path, "manifest.json")
        if not os.path.exists(manifest_path):
            continue
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        header = manifest.get("header", {})
        pack_uuid = header.get("uuid", "")
        pack_version = header.get("version", [0, 0, 1])
        
        if entry.startswith("behavior_pack") or "BehaviorPack" in entry:
            info["behavior_packs"].append({
                "dir_name": entry, "uuid": pack_uuid, "version": pack_version,
            })
        elif entry.startswith("resource_pack") or "ResourcePack" in entry:
            info["resource_packs"].append({
                "dir_name": entry, "uuid": pack_uuid, "version": pack_version,
            })
    
    return info


def generate_config(addon, launcher_port, logging_port):
    """生成游戏配置"""
    token = base64.b64encode(os.urandom(16)).decode()
    
    resource_pack_dirs = [rp["dir_name"] for rp in addon["resource_packs"]]
    behavior_pack_dirs = [bp["dir_name"] for bp in addon["behavior_packs"]]
    all_pack_uuids = [bp["uuid"] for bp in addon["behavior_packs"]] + \
                     [rp["uuid"] for rp in addon["resource_packs"]]
    
    config_path = os.path.join(OUTPUT_DIR, f"{addon['id']}.cppconfig")
    
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
                "experimental_holiday": False, "experimental_biomes": False,
                "fancy_bubbles": False,
            },
            "resource_packs": resource_pack_dirs,
            "behavior_packs": behavior_pack_dirs,
            "name": addon["name"],
            "world_type": 2,  # 平坦
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
            "user_id": PLAYER_USER_ID,
            "user_name": PLAYER_USER_NAME,
            "urs": ACCOUNT,
        },
        "anti_addiction_info": {
            "enable": False, "left_time": 0, "exp_multiplier": 1.0,
            "block_multplier": 1.0, "first_message": "",
        },
        "misc": {
            "multiplayer_game_type": 0, "game_id": None,
            "auth_server_url": AUTH_SERVER_URL,
            "launcher_port": launcher_port,
            "sensitive_word_file": "", "is_store_enabled": 1,
        },
        "path": config_path,
        "web_server_url": WEB_SERVER_URL,
        "core_server_url": CORE_SERVER_URL,
        "last_play_time": int(time.time()),
        "vip_using_mod": all_pack_uuids,
        "isCloud": False,
    }
    
    return config, config_path


def main():
    print("=" * 60)
    print("  MC-Agent-Kit 游戏启动器测试")
    print("=" * 60)
    print()
    
    # 检查游戏 exe
    if not os.path.exists(GAME_EXE):
        print(f"错误: 找不到游戏文件 {GAME_EXE}")
        return None, None
    
    print(f"游戏路径: {GAME_EXE}")
    
    # 扫描 addon
    addon_path = os.path.join(ADDON_DIR, ADDON_ID)
    addon = scan_addon(addon_path)
    print(f"Addon: {addon['name']}")
    print(f"  Behavior Packs: {len(addon['behavior_packs'])}")
    print(f"  Resource Packs: {len(addon['resource_packs'])}")
    print()
    
    # 分配端口
    launcher_port = find_free_port()
    logging_port = find_free_port()
    print(f"端口分配:")
    print(f"  launcher_port = {launcher_port}")
    print(f"  logging_port  = {logging_port}")
    
    # 生成配置
    config_data, config_path = generate_config(addon, launcher_port, logging_port)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    print(f"配置文件: {config_path}")
    
    # 错误日志路径
    error_log_path = generate_error_log_path()
    print(f"错误日志: {error_log_path}")
    
    # 日志文件
    log_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    launcher_log = os.path.join(OUTPUT_DIR, f"launcher_{log_timestamp}.log")
    gamelog_log = os.path.join(OUTPUT_DIR, f"gamelog_{log_timestamp}.log")
    
    # 启动 TCP 服务器
    print("\n启动日志服务器...")
    launcher_server = TCPServer("Launcher", "127.0.0.1", launcher_port, launcher_log)
    launcher_server.start()
    
    logging_server = TCPServer("Logging", "127.0.0.1", logging_port, gamelog_log)
    logging_server.start()
    
    # 启动游戏
    cmd = [
        GAME_EXE,
        f"config={config_path}",
        f"errorlog={error_log_path}",
        "dc_tag1=studio_no_launcher",
        f"dc_web={DC_WEB}",
        f"dc_uid={DC_UID}",
        "loggingIP=127.0.0.1",
        f"loggingPort={logging_port}",
    ]
    
    print(f"\n启动游戏...")
    print(f"  命令: {GAME_EXE}")
    for arg in cmd[1:]:
        print(f"    {arg}")
    
    process = subprocess.Popen(cmd, cwd=os.path.dirname(GAME_EXE))
    print(f"\n游戏进程已启动, PID: {process.pid}")
    print("\n等待游戏启动 (30秒)...")
    
    # 等待 30 秒让游戏完全启动
    time.sleep(30)
    
    print("\n游戏已运行 30 秒，检查进程状态...")
    if process.poll() is None:
        print("游戏进程运行正常!")
        game_running = True
    else:
        print(f"游戏进程已退出, 返回码: {process.returncode}")
        game_running = False
    
    # 收集日志
    print("\n收集日志...")
    launcher_logs = launcher_server.get_logs()
    game_logs = logging_server.get_logs()
    
    # 停止服务器
    launcher_server.stop()
    logging_server.stop()
    
    print(f"\n日志文件:")
    print(f"  Launcher: {launcher_log}")
    print(f"  GameLog:  {gamelog_log}")
    
    # 保存日志到输出文件
    output_log = os.path.join(OUTPUT_DIR, f"test_result_{log_timestamp}.json")
    result = {
        "success": game_running,
        "addon_name": addon["name"],
        "addon_id": addon["id"],
        "game_pid": process.pid,
        "config_path": config_path,
        "launcher_log": launcher_log,
        "game_log": gamelog_log,
        "error_log": error_log_path,
    }
    with open(output_log, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  结果: {output_log}")
    
    return process, gamelog_log


if __name__ == "__main__":
    main()