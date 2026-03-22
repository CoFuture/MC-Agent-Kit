"""
内存问题自动修复模块

提供内存问题的自动修复建议和工具集成。
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FixType(Enum):
    """修复类型"""
    TEXTURE_COMPRESS = "texture_compress"
    MODEL_SIMPLIFY = "model_simplify"
    SCRIPT_OPTIMIZE = "script_optimize"
    CONFIG_FIX = "config_fix"
    MEMORY_SETTING = "memory_setting"


class FixSeverity(Enum):
    """修复严重程度"""
    CRITICAL = "critical"  # 必须修复
    HIGH = "high"          # 强烈建议修复
    MEDIUM = "medium"      # 建议修复
    LOW = "low"            # 可选修复


@dataclass
class FixSuggestion:
    """修复建议"""
    fix_type: FixType
    severity: FixSeverity
    title: str
    description: str
    location: str
    current_value: Any = None
    suggested_value: Any = None
    auto_fixable: bool = False
    fix_command: str | None = None
    estimated_savings: str | None = None  # 预计节省的资源

    def to_dict(self) -> dict[str, Any]:
        return {
            "fix_type": self.fix_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "auto_fixable": self.auto_fixable,
            "fix_command": self.fix_command,
            "estimated_savings": self.estimated_savings,
        }


@dataclass
class MemoryFixReport:
    """内存修复报告"""
    addon_path: str
    total_issues: int = 0
    critical_issues: int = 0
    auto_fixable_issues: int = 0
    suggestions: list[FixSuggestion] = field(default_factory=list)
    applied_fixes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_critical_issues(self) -> bool:
        return self.critical_issues > 0

    @property
    def has_auto_fixable(self) -> bool:
        return self.auto_fixable_issues > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "addon_path": self.addon_path,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "auto_fixable_issues": self.auto_fixable_issues,
            "has_critical_issues": self.has_critical_issues,
            "has_auto_fixable": self.has_auto_fixable,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "applied_fixes": self.applied_fixes,
            "errors": self.errors,
        }


class TextureAnalyzer:
    """纹理分析器"""

    # 推荐的纹理尺寸
    RECOMMENDED_SIZES = [16, 32, 64, 128, 256, 512]

    # 大纹理阈值（像素）
    LARGE_TEXTURE_THRESHOLD = 1024

    def analyze(self, textures_dir: str) -> list[FixSuggestion]:
        """
        分析纹理目录，生成修复建议。

        Args:
            textures_dir: 纹理目录路径

        Returns:
            修复建议列表
        """
        suggestions = []

        if not os.path.exists(textures_dir):
            return suggestions

        for root, _, files in os.walk(textures_dir):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg", ".tga")):
                    file_path = os.path.join(root, file)
                    suggestion = self._analyze_texture(file_path)
                    if suggestion:
                        suggestions.append(suggestion)

        return suggestions

    def _analyze_texture(self, file_path: str) -> FixSuggestion | None:
        """分析单个纹理文件"""
        # 获取文件大小
        file_size = os.path.getsize(file_path)

        # 尝试获取图像尺寸
        try:
            # 使用 PIL 获取尺寸（如果可用）
            from PIL import Image

            with Image.open(file_path) as img:
                width, height = img.size

            # 检查尺寸
            if width > self.LARGE_TEXTURE_THRESHOLD or height > self.LARGE_TEXTURE_THRESHOLD:
                # 计算推荐的缩小尺寸
                recommended_size = self._get_recommended_size(max(width, height))

                return FixSuggestion(
                    fix_type=FixType.TEXTURE_COMPRESS,
                    severity=FixSeverity.HIGH,
                    title=f"大纹理文件: {os.path.basename(file_path)}",
                    description=f"纹理尺寸 {width}x{height} 过大，可能导致内存问题",
                    location=file_path,
                    current_value=f"{width}x{height}",
                    suggested_value=f"{recommended_size}x{recommended_size}",
                    auto_fixable=False,  # 需要图像处理工具
                    fix_command=f"# 使用图像编辑软件缩小到 {recommended_size}x{recommended_size}",
                    estimated_savings=f"约 {(width * height - recommended_size * recommended_size) * 4 / 1024 / 1024:.1f} MB",
                )

            # 检查是否为非 2 的幂次尺寸
            if width not in self.RECOMMENDED_SIZES or height not in self.RECOMMENDED_SIZES:
                nearest_width = self._get_nearest_power_of_2(width)
                nearest_height = self._get_nearest_power_of_2(height)

                return FixSuggestion(
                    fix_type=FixType.TEXTURE_COMPRESS,
                    severity=FixSeverity.LOW,
                    title=f"非标准纹理尺寸: {os.path.basename(file_path)}",
                    description=f"纹理尺寸 {width}x{height} 不是 2 的幂次，可能影响性能",
                    location=file_path,
                    current_value=f"{width}x{height}",
                    suggested_value=f"{nearest_width}x{nearest_height}",
                    auto_fixable=False,
                )

        except ImportError:
            # PIL 不可用，仅检查文件大小
            if file_size > 2 * 1024 * 1024:  # 2MB
                return FixSuggestion(
                    fix_type=FixType.TEXTURE_COMPRESS,
                    severity=FixSeverity.MEDIUM,
                    title=f"大纹理文件: {os.path.basename(file_path)}",
                    description=f"纹理文件大小 {file_size / 1024 / 1024:.1f} MB 超过建议值",
                    location=file_path,
                    current_value=f"{file_size / 1024 / 1024:.1f} MB",
                    suggested_value="< 2 MB",
                    auto_fixable=False,
                )

        except Exception:
            pass

        return None

    def _get_recommended_size(self, current_size: int) -> int:
        """获取推荐的纹理尺寸"""
        for size in self.RECOMMENDED_SIZES:
            if size >= current_size:
                return size
        return 512

    def _get_nearest_power_of_2(self, size: int) -> int:
        """获取最近的 2 的幂次尺寸"""
        power = 1
        while power < size:
            power *= 2
        return power


class ModelAnalyzer:
    """模型分析器"""

    # 模型复杂度阈值
    VERTEX_WARNING_THRESHOLD = 1000
    VERTEX_ERROR_THRESHOLD = 5000

    def analyze(self, models_dir: str) -> list[FixSuggestion]:
        """
        分析模型目录，生成修复建议。

        Args:
            models_dir: 模型目录路径

        Returns:
            修复建议列表
        """
        suggestions = []

        if not os.path.exists(models_dir):
            return suggestions

        for root, _, files in os.walk(models_dir):
            for file in files:
                if file.endswith(".geo.json"):
                    file_path = os.path.join(root, file)
                    suggestion = self._analyze_model(file_path)
                    if suggestion:
                        suggestions.append(suggestion)

        return suggestions

    def _analyze_model(self, file_path: str) -> FixSuggestion | None:
        """分析单个模型文件"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # 计算顶点数和面数
            total_vertices = 0
            total_bones = 0

            # 分析 geometry
            if "minecraft:geometry" in data:
                geometries = data["minecraft:geometry"]
                if isinstance(geometries, list):
                    for geo in geometries:
                        bones = geo.get("bones", [])
                        total_bones += len(bones)
                        for bone in bones:
                            cubes = bone.get("cubes", [])
                            for cube in cubes:
                                # 每个立方体约 24 个顶点
                                total_vertices += 24
                elif isinstance(geometries, dict):
                    bones = geometries.get("bones", [])
                    total_bones = len(bones)
                    for bone in bones:
                        cubes = bone.get("cubes", [])
                        total_vertices += len(cubes) * 24

            # 检查复杂度
            if total_vertices > self.VERTEX_ERROR_THRESHOLD:
                return FixSuggestion(
                    fix_type=FixType.MODEL_SIMPLIFY,
                    severity=FixSeverity.HIGH,
                    title=f"复杂模型: {os.path.basename(file_path)}",
                    description=f"模型包含约 {total_vertices} 个顶点和 {total_bones} 个骨骼，过于复杂",
                    location=file_path,
                    current_value=f"{total_vertices} 顶点",
                    suggested_value=f"< {self.VERTEX_WARNING_THRESHOLD} 顶点",
                    auto_fixable=False,
                    fix_command="# 使用 Blockbench 或其他工具简化模型",
                    estimated_savings=f"可减少约 {(total_vertices - self.VERTEX_WARNING_THRESHOLD) * 32 / 1024:.1f} KB 内存",
                )

            elif total_vertices > self.VERTEX_WARNING_THRESHOLD:
                return FixSuggestion(
                    fix_type=FixType.MODEL_SIMPLIFY,
                    severity=FixSeverity.MEDIUM,
                    title=f"较复杂模型: {os.path.basename(file_path)}",
                    description=f"模型包含约 {total_vertices} 个顶点，建议简化",
                    location=file_path,
                    current_value=f"{total_vertices} 顶点",
                    suggested_value=f"< {self.VERTEX_WARNING_THRESHOLD} 顶点",
                    auto_fixable=False,
                )

        except json.JSONDecodeError:
            return FixSuggestion(
                fix_type=FixType.MODEL_SIMPLIFY,
                severity=FixSeverity.LOW,
                title=f"模型文件格式错误: {os.path.basename(file_path)}",
                description="无法解析模型 JSON 文件",
                location=file_path,
                auto_fixable=False,
            )

        except Exception:
            pass

        return None


class ScriptAnalyzer:
    """脚本分析器"""

    # 脚本行数阈值
    LINES_WARNING_THRESHOLD = 500
    LINES_ERROR_THRESHOLD = 2000

    # 复杂度阈值
    FUNCTION_LENGTH_WARNING = 50

    def analyze(self, scripts_dir: str) -> list[FixSuggestion]:
        """
        分析脚本目录，生成修复建议。

        Args:
            scripts_dir: 脚本目录路径

        Returns:
            修复建议列表
        """
        suggestions = []

        if not os.path.exists(scripts_dir):
            return suggestions

        for root, _, files in os.walk(scripts_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    file_suggestions = self._analyze_script(file_path)
                    suggestions.extend(file_suggestions)

        return suggestions

    def _analyze_script(self, file_path: str) -> list[FixSuggestion]:
        """分析单个脚本文件"""
        suggestions = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # 检查文件大小
            if len(lines) > self.LINES_ERROR_THRESHOLD:
                suggestions.append(FixSuggestion(
                    fix_type=FixType.SCRIPT_OPTIMIZE,
                    severity=FixSeverity.HIGH,
                    title=f"过大脚本文件: {os.path.basename(file_path)}",
                    description=f"脚本文件包含 {len(lines)} 行，建议拆分",
                    location=file_path,
                    current_value=f"{len(lines)} 行",
                    suggested_value=f"< {self.LINES_WARNING_THRESHOLD} 行",
                    auto_fixable=False,
                    fix_command="# 将相关功能拆分到独立模块中",
                ))

            elif len(lines) > self.LINES_WARNING_THRESHOLD:
                suggestions.append(FixSuggestion(
                    fix_type=FixType.SCRIPT_OPTIMIZE,
                    severity=FixSeverity.MEDIUM,
                    title=f"较大脚本文件: {os.path.basename(file_path)}",
                    description=f"脚本文件包含 {len(lines)} 行，建议拆分",
                    location=file_path,
                    current_value=f"{len(lines)} 行",
                    suggested_value=f"< {self.LINES_WARNING_THRESHOLD} 行",
                    auto_fixable=False,
                ))

            # 检查潜在的性能问题
            performance_issues = self._check_performance_issues(file_path, content)
            suggestions.extend(performance_issues)

        except Exception:
            pass

        return suggestions

    def _check_performance_issues(self, file_path: str, content: str) -> list[FixSuggestion]:
        """检查脚本中的性能问题"""
        suggestions = []

        # 检查全局变量滥用
        global_count = content.count("global ")
        if global_count > 10:
            suggestions.append(FixSuggestion(
                fix_type=FixType.SCRIPT_OPTIMIZE,
                severity=FixSeverity.LOW,
                title=f"全局变量过多: {os.path.basename(file_path)}",
                description=f"发现 {global_count} 个全局变量声明，建议使用类或模块封装",
                location=file_path,
                current_value=f"{global_count} 个全局变量",
                suggested_value="使用类或模块封装",
                auto_fixable=False,
            ))

        # 检查 print 调试语句
        print_count = content.count("print(")
        if print_count > 5:
            suggestions.append(FixSuggestion(
                fix_type=FixType.SCRIPT_OPTIMIZE,
                severity=FixSeverity.LOW,
                title=f"调试语句残留: {os.path.basename(file_path)}",
                description=f"发现 {print_count} 个 print 语句，建议移除或使用日志",
                location=file_path,
                current_value=f"{print_count} 个 print",
                suggested_value="使用 logging 模块",
                auto_fixable=False,
            ))

        return suggestions


class MemoryAutoFixer:
    """
    内存问题自动修复器

    分析 Addon 资源并提供自动修复建议。
    """

    def __init__(self, addon_path: str):
        """
        初始化修复器。

        Args:
            addon_path: Addon 目录路径
        """
        self.addon_path = addon_path
        self._texture_analyzer = TextureAnalyzer()
        self._model_analyzer = ModelAnalyzer()
        self._script_analyzer = ScriptAnalyzer()

    def analyze(self) -> MemoryFixReport:
        """
        分析 Addon 并生成修复报告。

        Returns:
            MemoryFixReport 修复报告
        """
        report = MemoryFixReport(addon_path=self.addon_path)

        if not os.path.exists(self.addon_path):
            report.errors.append(f"Addon 目录不存在: {self.addon_path}")
            return report

        # 分析纹理
        textures_dir = self._find_textures_dir()
        if textures_dir:
            texture_suggestions = self._texture_analyzer.analyze(textures_dir)
            report.suggestions.extend(texture_suggestions)

        # 分析模型
        models_dir = self._find_models_dir()
        if models_dir:
            model_suggestions = self._model_analyzer.analyze(models_dir)
            report.suggestions.extend(model_suggestions)

        # 分析脚本
        scripts_dir = self._find_scripts_dir()
        if scripts_dir:
            script_suggestions = self._script_analyzer.analyze(scripts_dir)
            report.suggestions.extend(script_suggestions)

        # 统计
        report.total_issues = len(report.suggestions)
        report.critical_issues = sum(
            1 for s in report.suggestions
            if s.severity in (FixSeverity.CRITICAL, FixSeverity.HIGH)
        )
        report.auto_fixable_issues = sum(
            1 for s in report.suggestions
            if s.auto_fixable
        )

        return report

    def apply_fixes(
        self,
        report: MemoryFixReport,
        dry_run: bool = True,
    ) -> MemoryFixReport:
        """
        应用自动修复。

        Args:
            report: 修复报告
            dry_run: 是否仅模拟运行

        Returns:
            更新后的修复报告
        """
        for suggestion in report.suggestions:
            if not suggestion.auto_fixable:
                continue

            if dry_run:
                report.applied_fixes.append(f"[DRY RUN] {suggestion.title}")
                continue

            try:
                self._apply_fix(suggestion)
                report.applied_fixes.append(suggestion.title)
            except Exception as e:
                report.errors.append(f"修复失败 {suggestion.title}: {e}")

        return report

    def _apply_fix(self, suggestion: FixSuggestion) -> None:
        """应用单个修复"""
        if suggestion.fix_type == FixType.CONFIG_FIX:
            # 配置文件修复
            if suggestion.location.endswith(".json"):
                with open(suggestion.location, encoding="utf-8") as f:
                    data = json.load(f)

                # 应用修复
                # ...（根据具体修复类型处理）

                with open(suggestion.location, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    def _find_textures_dir(self) -> str | None:
        """查找纹理目录"""
        possible_paths = [
            os.path.join(self.addon_path, "resource_pack", "textures"),
            os.path.join(self.addon_path, "textures"),
            os.path.join(self.addon_path, "resource_pack"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _find_models_dir(self) -> str | None:
        """查找模型目录"""
        possible_paths = [
            os.path.join(self.addon_path, "resource_pack", "models"),
            os.path.join(self.addon_path, "models"),
            os.path.join(self.addon_path, "resource_pack", "entity"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _find_scripts_dir(self) -> str | None:
        """查找脚本目录"""
        possible_paths = [
            os.path.join(self.addon_path, "behavior_pack", "scripts"),
            os.path.join(self.addon_path, "scripts"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None


def analyze_addon_memory(addon_path: str) -> MemoryFixReport:
    """
    便捷函数：分析 Addon 内存问题。

    Args:
        addon_path: Addon 目录路径

    Returns:
        MemoryFixReport 修复报告
    """
    fixer = MemoryAutoFixer(addon_path)
    return fixer.analyze()


def get_memory_optimization_tips() -> list[dict[str, str]]:
    """
    获取内存优化技巧列表。

    Returns:
        优化技巧列表
    """
    return [
        {
            "category": "纹理",
            "tip": "使用 2 的幂次尺寸（16, 32, 64, 128, 256, 512）",
            "reason": "GPU 可以更高效地处理标准尺寸纹理",
        },
        {
            "category": "纹理",
            "tip": "避免使用大于 1024x1024 的纹理",
            "reason": "大纹理会占用大量显存和内存",
        },
        {
            "category": "纹理",
            "tip": "使用纹理图集（Texture Atlas）合并小纹理",
            "reason": "减少纹理切换开销，提升渲染性能",
        },
        {
            "category": "模型",
            "tip": "限制每个模型的顶点数在 1000 以内",
            "reason": "复杂模型会显著增加内存和渲染开销",
        },
        {
            "category": "模型",
            "tip": "使用 LOD（Level of Detail）技术",
            "reason": "远距离使用简化模型，降低内存占用",
        },
        {
            "category": "脚本",
            "tip": "拆分大脚本文件（>500 行）到多个模块",
            "reason": "便于维护和减少内存占用",
        },
        {
            "category": "脚本",
            "tip": "避免全局变量滥用，使用类或模块封装",
            "reason": "全局变量可能导致内存泄漏",
        },
        {
            "category": "脚本",
            "tip": "使用对象池复用频繁创建的对象",
            "reason": "减少内存分配和垃圾回收开销",
        },
        {
            "category": "配置",
            "tip": "确保 manifest.json 格式正确",
            "reason": "格式错误可能导致游戏解析失败",
        },
        {
            "category": "配置",
            "tip": "使用正确的 UUID 避免冲突",
            "reason": "UUID 冲突可能导致 Addon 加载失败",
        },
    ]
