"""
游戏启动器诊断模块

诊断游戏启动配置问题，帮助排查内存分配错误等问题。
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DiagnosticSeverity(Enum):
    """诊断问题严重程度"""
    ERROR = "error"          # 必须修复
    WARNING = "warning"      # 建议修复
    INFO = "info"            # 信息提示


class DiagnosticCategory(Enum):
    """诊断问题类别"""
    PATH = "path"            # 路径问题
    CONFIG = "config"        # 配置问题
    VERSION = "version"      # 版本问题
    PERMISSION = "permission"  # 权限问题
    RESOURCE = "resource"    # 资源问题
    ADDON = "addon"          # Addon 问题
    SYSTEM = "system"        # 系统问题


@dataclass
class DiagnosticIssue:
    """诊断问题"""
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    code: str
    message: str
    details: str = ""
    suggestion: str = ""
    location: str = ""  # 文件路径或配置项


@dataclass
class DiagnosticReport:
    """诊断报告"""
    success: bool
    issues: list[DiagnosticIssue] = field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warning: int = 0
    game_path: str = ""
    game_version: str = ""
    addon_path: str = ""
    config_path: str = ""
    system_info: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == DiagnosticSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == DiagnosticSeverity.WARNING for i in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks_warning": self.checks_warning,
            "game_path": self.game_path,
            "game_version": self.game_version,
            "addon_path": self.addon_path,
            "config_path": self.config_path,
            "system_info": self.system_info,
            "issues": [
                {
                    "category": i.category.value,
                    "severity": i.severity.value,
                    "code": i.code,
                    "message": i.message,
                    "details": i.details,
                    "suggestion": i.suggestion,
                    "location": i.location,
                }
                for i in self.issues
            ],
        }


class LauncherDiagnoser:
    """
    游戏启动器诊断器

    检查游戏启动配置是否正确，识别常见问题。
    """

    # 常见游戏路径
    DEFAULT_GAME_PATHS = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "x64_mc", "Minecraft.Windows.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "Minecraft.Windows.exe"),
        "C:\\Program Files\\Netease\\MCStudio\\x64_mc\\Minecraft.Windows.exe",
        "C:\\Program Files (x86)\\Netease\\MCStudio\\x64_mc\\Minecraft.Windows.exe",
    ]

    # 常见 MC Studio 配置目录
    MC_STUDIO_PATHS = {
        "config": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "config"),
        "log": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "log"),
        "addons": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Netease", "MCStudio", "addons"),
    }

    def __init__(self, game_path: str | None = None):
        """
        初始化诊断器。

        Args:
            game_path: 游戏可执行文件路径（可选）
        """
        self.game_path = game_path
        self._detected_game_path: str | None = None

    def diagnose(
        self,
        addon_path: str | None = None,
        config_path: str | None = None,
        game_path: str | None = None,
    ) -> DiagnosticReport:
        """
        执行全面诊断。

        Args:
            addon_path: Addon 目录路径
            config_path: 配置文件路径
            game_path: 游戏可执行文件路径

        Returns:
            DiagnosticReport 诊断报告
        """
        report = DiagnosticReport(success=True)
        report.addon_path = addon_path or ""
        report.config_path = config_path or ""
        report.game_path = game_path or self.game_path or ""

        # 收集系统信息
        report.system_info = self._collect_system_info()

        # 1. 检查游戏路径
        self._check_game_path(report, game_path)

        # 2. 检查游戏版本
        self._check_game_version(report)

        # 3. 检查 Addon 目录
        if addon_path:
            self._check_addon(report, addon_path)

        # 4. 检查配置文件
        if config_path:
            self._check_config(report, config_path)

        # 5. 检查系统环境
        self._check_system_environment(report)

        # 6. 检查常见内存问题
        self._check_memory_issues(report)

        # 更新报告状态
        report.success = not report.has_errors

        return report

    def _collect_system_info(self) -> dict[str, Any]:
        """收集系统信息"""
        import platform

        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
        }

        # 获取内存信息（Windows）
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", c_ulonglong),
                    ("ullAvailPhys", c_ulonglong),
                    ("ullTotalPageFile", c_ulonglong),
                    ("ullAvailPageFile", c_ulonglong),
                    ("ullTotalVirtual", c_ulonglong),
                    ("ullAvailVirtual", c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

            info["memory_total_gb"] = round(stat.ullTotalPhys / (1024 ** 3), 2)
            info["memory_available_gb"] = round(stat.ullAvailPhys / (1024 ** 3), 2)
            info["memory_load_percent"] = stat.dwMemoryLoad
        except Exception:
            pass

        return info

    def _check_game_path(self, report: DiagnosticReport, game_path: str | None) -> None:
        """检查游戏路径"""
        path = game_path or self.game_path

        if not path:
            # 尝试自动检测
            path = self._detect_game_path()
            if path:
                self._detected_game_path = path
                report.game_path = path
            else:
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.PATH,
                    severity=DiagnosticSeverity.ERROR,
                    code="GAME_PATH_NOT_FOUND",
                    message="未找到游戏可执行文件",
                    details="无法自动检测 Minecraft.Windows.exe 的位置",
                    suggestion="请手动指定游戏路径: --game-path <path>",
                ))
                report.checks_failed += 1
                return

        if not os.path.exists(path):
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.PATH,
                severity=DiagnosticSeverity.ERROR,
                code="GAME_PATH_INVALID",
                message="游戏路径不存在",
                details=f"路径: {path}",
                suggestion="请检查游戏是否正确安装，或提供正确的游戏路径",
                location=path,
            ))
            report.checks_failed += 1
            return

        if not path.endswith("Minecraft.Windows.exe"):
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.PATH,
                severity=DiagnosticSeverity.WARNING,
                code="GAME_PATH_SUSPICIOUS",
                message="游戏路径可能不正确",
                details=f"路径不以 Minecraft.Windows.exe 结尾: {path}",
                suggestion="请确认这是正确的游戏可执行文件",
                location=path,
            ))
            report.checks_warning += 1
        else:
            report.checks_passed += 1

        report.game_path = path

    def _detect_game_path(self) -> str | None:
        """自动检测游戏路径"""
        for path in self.DEFAULT_GAME_PATHS:
            if os.path.exists(path):
                return path
        return None

    def _check_game_version(self, report: DiagnosticReport) -> None:
        """检查游戏版本"""
        # 尝试从配置目录读取版本信息
        version_file = os.path.join(
            self.MC_STUDIO_PATHS["config"],
            "version.json"
        )

        if os.path.exists(version_file):
            try:
                with open(version_file, encoding="utf-8") as f:
                    data = json.load(f)
                    report.game_version = data.get("version", "unknown")
                    report.checks_passed += 1
            except Exception:
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.VERSION,
                    severity=DiagnosticSeverity.INFO,
                    code="VERSION_FILE_READ_ERROR",
                    message="无法读取版本文件",
                    details=f"文件: {version_file}",
                ))
        else:
            # 尝试从游戏可执行文件获取版本
            game_path = report.game_path
            if game_path and os.path.exists(game_path):
                try:
                    import ctypes
                    size = ctypes.windll.version.GetFileVersionInfoSizeW(game_path, None)
                    if size:
                        report.checks_passed += 1
                        # 版本信息可用，但不解析详细版本号
                    else:
                        report.issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.VERSION,
                            severity=DiagnosticSeverity.INFO,
                            code="VERSION_NOT_DETECTED",
                            message="无法检测游戏版本",
                            suggestion="游戏可能正常运行，但建议检查版本兼容性",
                        ))
                except Exception:
                    pass

    def _check_addon(self, report: DiagnosticReport, addon_path: str) -> None:
        """检查 Addon 目录"""
        if not os.path.exists(addon_path):
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.ADDON,
                severity=DiagnosticSeverity.ERROR,
                code="ADDON_PATH_NOT_FOUND",
                message="Addon 目录不存在",
                details=f"路径: {addon_path}",
                suggestion="请确认 Addon 目录路径正确",
                location=addon_path,
            ))
            report.checks_failed += 1
            return

        # 检查目录结构
        expected_dirs = ["behavior_pack", "resource_pack"]
        found_dirs = []

        for d in expected_dirs:
            full_path = os.path.join(addon_path, d)
            if os.path.exists(full_path):
                found_dirs.append(d)

        if not found_dirs:
            # 尝试直接查找 manifest.json
            has_bp = False
            has_rp = False
            for root, dirs, files in os.walk(addon_path):
                if "manifest.json" in files:
                    manifest_path = os.path.join(root, "manifest.json")
                    try:
                        with open(manifest_path, encoding="utf-8") as f:
                            data = json.load(f)
                            modules = data.get("modules", [])
                            for m in modules:
                                if m.get("type") == "data":
                                    has_bp = True
                                elif m.get("type") == "resources":
                                    has_rp = True
                    except Exception:
                        pass

            if not has_bp and not has_rp:
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.ADDON,
                    severity=DiagnosticSeverity.WARNING,
                    code="ADDON_STRUCTURE_UNKNOWN",
                    message="Addon 目录结构不标准",
                    details="未找到 behavior_pack 或 resource_pack 目录",
                    suggestion="标准结构应包含 behavior_pack/ 和 resource_pack/ 目录",
                    location=addon_path,
                ))
                report.checks_warning += 1
            else:
                report.checks_passed += 1
        else:
            # 检查 manifest.json
            for d in found_dirs:
                manifest_path = os.path.join(addon_path, d, "manifest.json")
                if os.path.exists(manifest_path):
                    self._validate_manifest(report, manifest_path)
                else:
                    report.issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.ADDON,
                        severity=DiagnosticSeverity.ERROR,
                        code="MANIFEST_MISSING",
                        message=f"{d} 缺少 manifest.json",
                        details=f"预期路径: {manifest_path}",
                        suggestion="请确保每个 Pack 都有 manifest.json 文件",
                        location=manifest_path,
                    ))
                    report.checks_failed += 1

    def _validate_manifest(self, report: DiagnosticReport, manifest_path: str) -> None:
        """验证 manifest.json 文件"""
        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)

            # 检查必要字段
            required_fields = ["format_version", "header"]
            for field in required_fields:
                if field not in data:
                    report.issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.ADDON,
                        severity=DiagnosticSeverity.ERROR,
                        code="MANIFEST_FIELD_MISSING",
                        message=f"manifest.json 缺少必要字段: {field}",
                        location=manifest_path,
                    ))
                    report.checks_failed += 1
                    return

            header = data.get("header", {})
            header_required = ["name", "description", "uuid", "version"]
            for field in header_required:
                if field not in header:
                    report.issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.ADDON,
                        severity=DiagnosticSeverity.WARNING,
                        code="MANIFEST_HEADER_INCOMPLETE",
                        message=f"manifest.json header 缺少字段: {field}",
                        location=manifest_path,
                    ))
                    report.checks_warning += 1

            report.checks_passed += 1

        except json.JSONDecodeError as e:
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.ADDON,
                severity=DiagnosticSeverity.ERROR,
                code="MANIFEST_JSON_ERROR",
                message="manifest.json 格式错误",
                details=f"JSON 解析错误: {e}",
                location=manifest_path,
                suggestion="请检查 JSON 语法，确保格式正确",
            ))
            report.checks_failed += 1

    def _check_config(self, report: DiagnosticReport, config_path: str) -> None:
        """检查配置文件"""
        if not os.path.exists(config_path):
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CONFIG,
                severity=DiagnosticSeverity.ERROR,
                code="CONFIG_NOT_FOUND",
                message="配置文件不存在",
                details=f"路径: {config_path}",
                suggestion="请确保配置文件存在",
                location=config_path,
            ))
            report.checks_failed += 1
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CONFIG,
                severity=DiagnosticSeverity.ERROR,
                code="CONFIG_JSON_ERROR",
                message="配置文件 JSON 格式错误",
                details=f"JSON 解析错误: {e}",
                location=config_path,
            ))
            report.checks_failed += 1
            return

        # 检查必要字段
        required_fields = ["version", "MainComponentId", "world_info"]
        for field in required_fields:
            if field not in data:
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.CONFIG,
                    severity=DiagnosticSeverity.ERROR,
                    code="CONFIG_FIELD_MISSING",
                    message=f"配置文件缺少必要字段: {field}",
                    location=config_path,
                ))
                report.checks_failed += 1

        # 检查路径配置
        local_paths = data.get("LocalComponentPathsDict", {})
        main_id = data.get("MainComponentId", "")

        if main_id and main_id in local_paths:
            path_info = local_paths[main_id]
            cfg_path = path_info.get("cfg_path", "")
            if cfg_path and not os.path.exists(cfg_path):
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.PATH,
                    severity=DiagnosticSeverity.ERROR,
                    code="CONFIG_ADDON_PATH_INVALID",
                    message="配置文件中的 Addon 路径无效",
                    details=f"路径: {cfg_path}",
                    location=config_path,
                    suggestion="请更新配置文件中的 Addon 路径",
                ))
                report.checks_failed += 1
            else:
                report.checks_passed += 1

        # 检查 Pack 配置
        world_info = data.get("world_info", {})
        resource_packs = world_info.get("resource_packs", [])
        behavior_packs = world_info.get("behavior_packs", [])

        if not resource_packs and not behavior_packs:
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CONFIG,
                severity=DiagnosticSeverity.WARNING,
                code="CONFIG_NO_PACKS",
                message="配置文件未指定任何 Pack",
                location=config_path,
                suggestion="请确保至少配置一个 behavior_pack 或 resource_pack",
            ))
            report.checks_warning += 1
        else:
            report.checks_passed += 1

    def _check_system_environment(self, report: DiagnosticReport) -> None:
        """检查系统环境"""
        # 检查 MC Studio 目录
        mc_studio_path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Netese",
            "MCStudio"
        )

        if not os.path.exists(mc_studio_path):
            # 尝试另一种拼写
            mc_studio_path = os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Netease",
                "MCStudio"
            )

        if os.path.exists(mc_studio_path):
            report.checks_passed += 1
        else:
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.SYSTEM,
                severity=DiagnosticSeverity.WARNING,
                code="MC_STUDIO_NOT_FOUND",
                message="未找到 MC Studio 安装目录",
                details="这可能影响游戏启动和日志捕获",
                suggestion="请确认 MC Studio 已正确安装",
            ))
            report.checks_warning += 1

        # 检查日志目录
        log_path = self.MC_STUDIO_PATHS.get("log", "")
        if log_path and os.path.exists(log_path):
            report.checks_passed += 1
        else:
            report.issues.append(DiagnosticIssue(
                category=DiagnosticCategory.SYSTEM,
                severity=DiagnosticSeverity.INFO,
                code="LOG_DIR_NOT_FOUND",
                message="未找到日志目录",
                details=f"路径: {log_path}",
            ))

    def _check_memory_issues(self, report: DiagnosticReport) -> None:
        """检查常见内存问题"""
        # 检查可用内存
        if "memory_available_gb" in report.system_info:
            available = report.system_info["memory_available_gb"]
            if available < 2:
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SYSTEM,
                    severity=DiagnosticSeverity.ERROR,
                    code="MEMORY_LOW",
                    message="系统可用内存不足",
                    details=f"可用内存: {available} GB (建议 > 4 GB)",
                    suggestion="请关闭其他应用程序释放内存，或增加系统内存",
                ))
                report.checks_failed += 1
            elif available < 4:
                report.issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SYSTEM,
                    severity=DiagnosticSeverity.WARNING,
                    code="MEMORY_WARNING",
                    message="系统可用内存较低",
                    details=f"可用内存: {available} GB (建议 > 4 GB)",
                    suggestion="建议关闭不必要的应用程序以获得更好的游戏体验",
                ))
                report.checks_warning += 1
            else:
                report.checks_passed += 1

        # 添加已知内存问题的说明
        report.issues.append(DiagnosticIssue(
            category=DiagnosticCategory.SYSTEM,
            severity=DiagnosticSeverity.INFO,
            code="MEMORY_ALLOCATION_NOTE",
            message="关于内存分配错误的说明",
            details=(
                "游戏启动时出现 'Assertion failed: We failed to allocate XXX bytes' 错误，"
                "通常与以下因素有关：\n"
                "1. 游戏配置文件格式不正确\n"
                "2. Addon 资源文件过大或损坏\n"
                "3. 游戏版本与 Addon 不兼容\n"
                "4. 系统内存不足\n"
                "5. 显卡驱动问题"
            ),
            suggestion=(
                "建议尝试：\n"
                "1. 使用 MC Studio 直接启动游戏，验证游戏本身是否正常\n"
                "2. 对比 MC Studio 生成的配置文件\n"
                "3. 检查 Addon 是否有语法错误\n"
                "4. 更新显卡驱动"
            ),
        ))

    def quick_check(self, addon_path: str) -> DiagnosticReport:
        """
        快速检查 Addon 是否可以启动。

        Args:
            addon_path: Addon 目录路径

        Returns:
            DiagnosticReport 诊断报告
        """
        return self.diagnose(addon_path=addon_path)

    def compare_with_mc_studio_config(
        self,
        config_path: str,
        mc_studio_config_path: str | None = None
    ) -> dict[str, Any]:
        """
        与 MC Studio 生成的配置文件进行对比。

        Args:
            config_path: 当前配置文件路径
            mc_studio_config_path: MC Studio 配置文件路径（可选）

        Returns:
            对比结果
        """
        result: dict[str, Any] = {
            "differences": [],
            "warnings": [],
            "suggestions": [],
            "missing_fields": [],
            "extra_fields": [],
            "type_mismatches": [],
        }

        # 读取当前配置
        try:
            with open(config_path, encoding="utf-8") as f:
                current_config = json.load(f)
        except Exception as e:
            result["warnings"].append(f"无法读取当前配置文件: {e}")
            return result

        # 尝试找到 MC Studio 配置
        if not mc_studio_config_path:
            mc_studio_config_path = self._find_mc_studio_config()

        if not mc_studio_config_path:
            result["warnings"].append("未找到 MC Studio 配置文件进行对比")
            return result

        try:
            with open(mc_studio_config_path, encoding="utf-8") as f:
                mc_config = json.load(f)
        except Exception as e:
            result["warnings"].append(f"无法读取 MC Studio 配置文件: {e}")
            return result

        # 深度比较配置
        self._deep_compare(
            current_config, mc_config,
            "", result
        )

        # 检查关键字段
        key_fields = [
            "version",
            "MainComponentId",
            "LocalComponentPathsDict",
            "world_info",
            "player_info",
            "room_info",
        ]

        for field in key_fields:
            if field not in current_config and field in mc_config:
                result["missing_fields"].append(field)
            elif field in current_config and field not in mc_config:
                result["extra_fields"].append(field)

        # 检查 LocalComponentPathsDict 结构
        current_paths = current_config.get("LocalComponentPathsDict", {})
        mc_paths = mc_config.get("LocalComponentPathsDict", {})

        if current_paths.keys() != mc_paths.keys():
            result["differences"].append({
                "field": "LocalComponentPathsDict keys",
                "current": list(current_paths.keys()),
                "mc_studio": list(mc_paths.keys()),
            })

        # 检查路径配置结构
        for key, path_info in current_paths.items():
            if isinstance(path_info, dict):
                required_path_fields = ["cfg_path", "work_path"]
                for pf in required_path_fields:
                    if pf not in path_info:
                        result["warnings"].append(
                            f"LocalComponentPathsDict[{key}] 缺少字段: {pf}"
                        )

        # 检查 world_info 结构
        current_world = current_config.get("world_info", {})
        mc_world = mc_config.get("world_info", {})

        world_fields = ["game_type", "difficulty", "permission_level", "cheat", "cheat_info"]
        for field in world_fields:
            if field in mc_world and field not in current_world:
                result["missing_fields"].append(f"world_info.{field}")
            elif field in current_world and field in mc_world:
                if current_world.get(field) != mc_world.get(field):
                    result["differences"].append({
                        "field": f"world_info.{field}",
                        "current": current_world.get(field),
                        "mc_studio": mc_world.get(field),
                    })

        # 检查 room_info 结构
        current_room = current_config.get("room_info", {})
        mc_room = mc_config.get("room_info", {})

        room_fields = ["token", "room_id", "host_id", "max_player"]
        for field in room_fields:
            if field in mc_room and field in current_room:
                if current_room.get(field) != mc_room.get(field):
                    result["differences"].append({
                        "field": f"room_info.{field}",
                        "current": current_room.get(field),
                        "mc_studio": mc_room.get(field),
                    })

        # 生成建议
        if result["differences"]:
            result["suggestions"].append(
                "建议参考 MC Studio 生成的配置文件格式，调整当前配置"
            )

        if result["missing_fields"]:
            result["suggestions"].append(
                f"配置文件缺少字段: {', '.join(result['missing_fields'])}"
            )

        if result["type_mismatches"]:
            result["suggestions"].append(
                "检查数据类型是否正确，部分字段可能需要类型转换"
            )

        return result

    def _deep_compare(
        self,
        current: Any,
        reference: Any,
        path: str,
        result: dict[str, Any]
    ) -> None:
        """
        深度比较两个配置对象。

        Args:
            current: 当前配置
            reference: 参考配置
            path: 当前路径
            result: 结果字典
        """
        if type(current) != type(reference):
            result["type_mismatches"].append({
                "path": path,
                "current_type": type(current).__name__,
                "reference_type": type(reference).__name__,
            })
            return

        if isinstance(current, dict):
            # 检查字典键
            current_keys = set(current.keys())
            reference_keys = set(reference.keys())

            # 缺少的键
            missing = reference_keys - current_keys
            for key in missing:
                result["missing_fields"].append(f"{path}.{key}" if path else key)

            # 多余的键
            extra = current_keys - reference_keys
            for key in extra:
                result["extra_fields"].append(f"{path}.{key}" if path else key)

            # 递归比较共同键
            for key in current_keys & reference_keys:
                new_path = f"{path}.{key}" if path else key
                self._deep_compare(current[key], reference[key], new_path, result)

        elif isinstance(current, list):
            # 列表长度不同
            if len(current) != len(reference):
                result["differences"].append({
                    "field": f"{path} (length)",
                    "current": len(current),
                    "mc_studio": len(reference),
                })
            else:
                # 逐项比较
                for i, (c, r) in enumerate(zip(current, reference)):
                    self._deep_compare(c, r, f"{path}[{i}]", result)

        else:
            # 基本类型值比较
            if current != reference:
                result["differences"].append({
                    "field": path,
                    "current": current,
                    "mc_studio": reference,
                })

    def _find_mc_studio_config(self) -> str | None:
        """查找 MC Studio 配置文件"""
        config_dir = self.MC_STUDIO_PATHS.get("config", "")
        if config_dir and os.path.exists(config_dir):
            for f in os.listdir(config_dir):
                if f.endswith(".cppconfig"):
                    return os.path.join(config_dir, f)
        return None


@dataclass
class ConfigFix:
    """配置修复项"""
    field: str
    current_value: Any
    suggested_value: Any
    description: str
    auto_fixable: bool = True


@dataclass
class ConfigFixReport:
    """配置修复报告"""
    fixes: list[ConfigFix] = field(default_factory=list)
    fixed: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixes": [
                {
                    "field": f.field,
                    "current_value": f.current_value,
                    "suggested_value": f.suggested_value,
                    "description": f.description,
                    "auto_fixable": f.auto_fixable,
                }
                for f in self.fixes
            ],
            "fixed": self.fixed,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ConfigAutoFixer:
    """
    配置文件自动修复器

    分析配置文件问题并提供自动修复功能。
    """

    # 必要字段及其默认值
    REQUIRED_FIELDS = {
        "version": "1.0.0",
        "client_type": 0,
        "MainComponentId": "",
        "LocalComponentPathsDict": {},
        "world_info": {
            "level_id": "",
            "game_type": 1,
            "difficulty": 2,
            "permission_level": 1,
            "cheat": True,
            "cheat_info": {},
            "resource_packs": [],
            "behavior_packs": [],
            "name": "",
            "world_type": 2,
        },
        "room_info": {
            "ip": "",
            "port": 0,
            "muiltClient": False,
            "room_name": "",
            "token": "",
            "room_id": 0,
            "host_id": 0,
            "allow_pe": True,
            "max_player": 0,
            "visibility_mode": 0,
            "is_pe": True,
        },
        "player_info": {
            "user_id": 0,
            "user_name": "",
            "urs": "",
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
            "is_store_enabled": 1,
        },
    }

    # CheatInfo 默认值
    CHEAT_INFO_DEFAULTS = {
        "pvp": True,
        "show_coordinates": False,
        "always_day": False,
        "daylight_cycle": True,
        "fire_spreads": True,
        "tnt_explodes": True,
        "keep_inventory": True,
        "mob_spawn": True,
        "natural_regeneration": True,
        "mob_loot": True,
        "mob_griefing": True,
        "tile_drops": True,
        "entities_drop_loot": True,
        "weather_cycle": True,
        "command_blocks_enabled": True,
        "random_tick_speed": 1,
        "experimental_holiday": False,
        "experimental_biomes": False,
        "fancy_bubbles": False,
    }

    def analyze(self, config: dict[str, Any]) -> ConfigFixReport:
        """
        分析配置文件问题。

        Args:
            config: 配置字典

        Returns:
            ConfigFixReport 修复报告
        """
        report = ConfigFixReport()

        # 检查必要字段
        self._check_required_fields(config, report)

        # 检查 world_info 结构
        world_info = config.get("world_info", {})
        self._check_world_info(world_info, report)

        # 检查 room_info 结构
        room_info = config.get("room_info", {})
        self._check_room_info(room_info, report)

        # 检查 player_info 结构
        player_info = config.get("player_info", {})
        self._check_player_info(player_info, report)

        # 检查 LocalComponentPathsDict
        paths = config.get("LocalComponentPathsDict", {})
        self._check_paths(paths, report)

        return report

    def _check_required_fields(
        self,
        config: dict[str, Any],
        report: ConfigFixReport
    ) -> None:
        """检查必要字段"""
        for field, default_value in self.REQUIRED_FIELDS.items():
            if field not in config:
                report.fixes.append(ConfigFix(
                    field=field,
                    current_value=None,
                    suggested_value=default_value,
                    description=f"缺少必要字段: {field}",
                    auto_fixable=True,
                ))

    def _check_world_info(
        self,
        world_info: dict[str, Any],
        report: ConfigFixReport
    ) -> None:
        """检查 world_info 结构"""
        required = ["level_id", "game_type", "difficulty", "cheat", "resource_packs", "behavior_packs"]

        for field in required:
            if field not in world_info:
                report.fixes.append(ConfigFix(
                    field=f"world_info.{field}",
                    current_value=None,
                    suggested_value="" if field in ["level_id", "name"] else ([] if field.endswith("packs") else 0),
                    description=f"world_info 缺少字段: {field}",
                    auto_fixable=True,
                ))

        # 检查 cheat_info
        cheat_info = world_info.get("cheat_info", {})
        for field, default in self.CHEAT_INFO_DEFAULTS.items():
            if field not in cheat_info:
                report.fixes.append(ConfigFix(
                    field=f"world_info.cheat_info.{field}",
                    current_value=None,
                    suggested_value=default,
                    description=f"cheat_info 缺少字段: {field}",
                    auto_fixable=True,
                ))

    def _check_room_info(
        self,
        room_info: dict[str, Any],
        report: ConfigFixReport
    ) -> None:
        """检查 room_info 结构"""
        required = ["token", "room_id", "host_id", "max_player", "allow_pe"]

        for field in required:
            if field not in room_info:
                default = "" if field == "token" else 0
                if field == "allow_pe":
                    default = True

                report.fixes.append(ConfigFix(
                    field=f"room_info.{field}",
                    current_value=None,
                    suggested_value=default,
                    description=f"room_info 缺少字段: {field}",
                    auto_fixable=True,
                ))

    def _check_player_info(
        self,
        player_info: dict[str, Any],
        report: ConfigFixReport
    ) -> None:
        """检查 player_info 结构"""
        required = ["user_id", "user_name", "urs"]

        for field in required:
            if field not in player_info:
                report.fixes.append(ConfigFix(
                    field=f"player_info.{field}",
                    current_value=None,
                    suggested_value="" if field != "user_id" else 0,
                    description=f"player_info 缺少字段: {field}",
                    auto_fixable=True,
                ))

    def _check_paths(
        self,
        paths: dict[str, Any],
        report: ConfigFixReport
    ) -> None:
        """检查 LocalComponentPathsDict 结构"""
        for component_id, path_info in paths.items():
            if not isinstance(path_info, dict):
                report.errors.append(
                    f"LocalComponentPathsDict[{component_id}] 应该是字典类型"
                )
                continue

            for field in ["cfg_path", "work_path"]:
                if field not in path_info:
                    report.fixes.append(ConfigFix(
                        field=f"LocalComponentPathsDict[{component_id}].{field}",
                        current_value=None,
                        suggested_value="",
                        description=f"路径配置缺少字段: {field}",
                        auto_fixable=True,
                    ))

    def fix(
        self,
        config: dict[str, Any],
        report: ConfigFixReport | None = None
    ) -> tuple[dict[str, Any], ConfigFixReport]:
        """
        自动修复配置文件。

        Args:
            config: 原始配置
            report: 预先分析的修复报告（可选）

        Returns:
            (修复后的配置, 修复报告)
        """
        if report is None:
            report = self.analyze(config)

        fixed_config = dict(config)

        # 应用所有可自动修复的修复项
        for fix in report.fixes:
            if not fix.auto_fixable:
                continue

            self._apply_fix(fixed_config, fix.field, fix.suggested_value)

        report.fixed = True
        return fixed_config, report

    def _apply_fix(
        self,
        config: dict[str, Any],
        field: str,
        value: Any
    ) -> None:
        """
        应用单个修复项。

        Args:
            config: 配置字典
            field: 字段路径（如 "world_info.game_type"）
            value: 要设置的值
        """
        parts = field.split(".")
        current = config

        for i, part in enumerate(parts[:-1]):
            # 处理数组索引
            if "[" in part and part.endswith("]"):
                key = part.split("[")[0]
                index = int(part.split("[")[1].rstrip("]"))
                if key not in current:
                    current[key] = []
                while len(current[key]) <= index:
                    current[key].append({})
                current = current[key][index]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # 设置最终值
        final_key = parts[-1]
        if "[" in final_key and final_key.endswith("]"):
            key = final_key.split("[")[0]
            index = int(final_key.split("[")[1].rstrip("]"))
            if key not in current:
                current[key] = []
            while len(current[key]) <= index:
                current[key].append(None)
            current[key][index] = value
        else:
            current[final_key] = value

    def fix_from_file(
        self,
        config_path: str,
        output_path: str | None = None
    ) -> ConfigFixReport:
        """
        从文件读取配置并修复。

        Args:
            config_path: 配置文件路径
            output_path: 输出路径（默认覆盖原文件）

        Returns:
            ConfigFixReport 修复报告
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            report = ConfigFixReport()
            report.errors.append(f"无法读取配置文件: {e}")
            return report

        fixed_config, report = self.fix(config)

        if report.fixed:
            output = output_path or config_path
            try:
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(fixed_config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                report.errors.append(f"无法保存配置文件: {e}")

        return report


def diagnose_launcher(
    addon_path: str | None = None,
    config_path: str | None = None,
    game_path: str | None = None,
) -> DiagnosticReport:
    """
    便捷函数：诊断游戏启动器配置。

    Args:
        addon_path: Addon 目录路径
        config_path: 配置文件路径
        game_path: 游戏可执行文件路径

    Returns:
        DiagnosticReport 诊断报告
    """
    diagnoser = LauncherDiagnoser(game_path)
    return diagnoser.diagnose(addon_path, config_path, game_path)


def fix_config(
    config_path: str,
    output_path: str | None = None
) -> ConfigFixReport:
    """
    便捷函数：修复配置文件。

    Args:
        config_path: 配置文件路径
        output_path: 输出路径（默认覆盖原文件）

    Returns:
        ConfigFixReport 修复报告
    """
    fixer = ConfigAutoFixer()
    return fixer.fix_from_file(config_path, output_path)


# ============================================================
# Iteration #31: Memory Issue Diagnosis
# ============================================================

@dataclass
class MemoryDiagnosticReport:
    """内存问题诊断报告"""
    addon_path: str
    config_path: str
    has_memory_issues: bool
    issues: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "addon_path": self.addon_path,
            "config_path": self.config_path,
            "has_memory_issues": self.has_memory_issues,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class AddonResourceAnalyzer:
    """
    Addon 资源分析器

    分析 Addon 中的资源文件，识别可能导致内存问题的资源。
    """

    # 纹理文件大小阈值（字节）
    TEXTURE_SIZE_WARNING = 2 * 1024 * 1024  # 2MB
    TEXTURE_SIZE_ERROR = 5 * 1024 * 1024  # 5MB

    # 模型文件大小阈值
    MODEL_SIZE_WARNING = 500 * 1024  # 500KB

    def analyze_texture_sizes(self, textures_dir: str) -> dict[str, Any]:
        """
        分析纹理文件大小。

        Args:
            textures_dir: 纹理目录路径

        Returns:
            分析结果字典
        """
        result: dict[str, Any] = {
            "total_files": 0,
            "total_size_bytes": 0,
            "large_files": [],
            "warnings": [],
        }

        if not os.path.exists(textures_dir):
            return result

        for root, _, files in os.walk(textures_dir):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)

                    result["total_files"] += 1
                    result["total_size_bytes"] += size

                    if size >= self.TEXTURE_SIZE_ERROR:
                        result["large_files"].append({
                            "path": file_path,
                            "size_bytes": size,
                            "severity": "error",
                        })
                    elif size >= self.TEXTURE_SIZE_WARNING:
                        result["large_files"].append({
                            "path": file_path,
                            "size_bytes": size,
                            "severity": "warning",
                        })

        return result

    def analyze_model_files(self, models_dir: str) -> dict[str, Any]:
        """
        分析模型文件。

        Args:
            models_dir: 模型目录路径

        Returns:
            分析结果字典
        """
        result: dict[str, Any] = {
            "total_models": 0,
            "total_size_bytes": 0,
            "complex_models": [],
        }

        if not os.path.exists(models_dir):
            return result

        for root, _, files in os.walk(models_dir):
            for file in files:
                if file.endswith(".geo.json"):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)

                    result["total_models"] += 1
                    result["total_size_bytes"] += size

                    if size >= self.MODEL_SIZE_WARNING:
                        result["complex_models"].append({
                            "path": file_path,
                            "size_bytes": size,
                        })

        return result

    def analyze_scripts(self, scripts_dir: str) -> dict[str, Any]:
        """
        分析脚本文件。

        Args:
            scripts_dir: 脚本目录路径

        Returns:
            分析结果字典
        """
        result = {
            "total_scripts": 0,
            "total_lines": 0,
            "large_scripts": [],
        }

        if not os.path.exists(scripts_dir):
            return result

        for root, _, files in os.walk(scripts_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, encoding="utf-8") as f:
                            lines = f.readlines()

                        result["total_scripts"] += 1
                        result["total_lines"] += len(lines)

                        if len(lines) > 500:
                            result["large_scripts"].append({
                                "path": file_path,
                                "lines": len(lines),
                            })
                    except Exception:
                        continue

        return result


class GameVersionChecker:
    """
    游戏版本检查器

    检查游戏版本兼容性和特性支持。
    """

    # 版本特性映射
    VERSION_FEATURES = {
        "1.21.0": ["新实体 API", "改进的渲染系统"],
        "1.20.50": ["UI 增强", "网络 API 改进"],
        "1.20.0": ["基础 Addon 支持"],
        "1.19.0": ["早期 Addon 支持"],
        "1.18.0": ["实验性 Addon"],
        "1.17.0": ["实验性 Addon"],
        "1.16.0": ["初始 Addon 支持"],
    }

    def parse_version(self, version_str: str) -> dict[str, int] | None:
        """
        解析版本字符串。

        Args:
            version_str: 版本字符串，如 "1.21.0"

        Returns:
            版本字典 {"major": 1, "minor": 21, "patch": 0}
        """
        try:
            parts = version_str.split(".")
            return {
                "major": int(parts[0]) if len(parts) > 0 else 0,
                "minor": int(parts[1]) if len(parts) > 1 else 0,
                "patch": int(parts[2]) if len(parts) > 2 else 0,
            }
        except (ValueError, IndexError):
            return None

    def check_compatibility(
        self,
        addon_version: str,
        game_version: str,
    ) -> dict[str, Any]:
        """
        检查版本兼容性。

        Args:
            addon_version: Addon 目标版本
            game_version: 游戏版本

        Returns:
            兼容性结果 {"compatible": bool, "message": str}
        """
        addon_parsed = self.parse_version(addon_version)
        game_parsed = self.parse_version(game_version)

        if not addon_parsed or not game_parsed:
            return {
                "compatible": False,
                "message": "无法解析版本号",
            }

        # 游戏版本 >= Addon 版本则兼容
        if game_parsed["major"] > addon_parsed["major"]:
            return {"compatible": True, "message": "兼容"}
        elif game_parsed["major"] < addon_parsed["major"]:
            return {
                "compatible": False,
                "message": "游戏版本过低",
            }

        # 主版本相同，比较次版本
        if game_parsed["minor"] >= addon_parsed["minor"]:
            return {"compatible": True, "message": "兼容"}
        else:
            return {
                "compatible": False,
                "message": "游戏版本过低",
            }

    def get_version_features(self, version: str) -> list[str]:
        """
        获取指定版本支持的特性。

        Args:
            version: 版本号

        Returns:
            特性列表
        """
        # 查找最接近的版本
        parsed = self.parse_version(version)
        if not parsed:
            return []

        # 按版本降序查找
        for v in sorted(self.VERSION_FEATURES.keys(), reverse=True):
            v_parsed = self.parse_version(v)
            if v_parsed and parsed["major"] >= v_parsed["major"] and parsed["minor"] >= v_parsed["minor"]:
                return self.VERSION_FEATURES.get(v, [])

        return []
