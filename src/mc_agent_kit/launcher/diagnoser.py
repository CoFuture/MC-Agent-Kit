"""
游戏启动器诊断模块

诊断游戏启动配置问题，帮助排查内存分配错误等问题。
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
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
                    details=f"未找到 behavior_pack 或 resource_pack 目录",
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
        result = {
            "differences": [],
            "warnings": [],
            "suggestions": [],
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

        # 比较关键字段
        key_fields = [
            "version",
            "MainComponentId",
            "world_info",
            "player_info",
            "room_info",
        ]

        for field in key_fields:
            current_val = current_config.get(field)
            mc_val = mc_config.get(field)

            if current_val != mc_val:
                result["differences"].append({
                    "field": field,
                    "current": current_val,
                    "mc_studio": mc_val,
                })

        # 检查 LocalComponentPathsDict
        current_paths = current_config.get("LocalComponentPathsDict", {})
        mc_paths = mc_config.get("LocalComponentPathsDict", {})

        if current_paths.keys() != mc_paths.keys():
            result["differences"].append({
                "field": "LocalComponentPathsDict keys",
                "current": list(current_paths.keys()),
                "mc_studio": list(mc_paths.keys()),
            })

        # 生成建议
        if result["differences"]:
            result["suggestions"].append(
                "建议参考 MC Studio 生成的配置文件格式，调整当前配置"
            )

        return result

    def _find_mc_studio_config(self) -> str | None:
        """查找 MC Studio 配置文件"""
        config_dir = self.MC_STUDIO_PATHS.get("config", "")
        if config_dir and os.path.exists(config_dir):
            for f in os.listdir(config_dir):
                if f.endswith(".cppconfig"):
                    return os.path.join(config_dir, f)
        return None


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