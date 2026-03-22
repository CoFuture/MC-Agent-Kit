"""
插件依赖自动安装

自动检测和安装插件所需的依赖。
"""

import logging
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """依赖类型"""

    PYTHON = "python"  # Python 包
    SYSTEM = "system"  # 系统依赖
    PLUGIN = "plugin"  # 其他插件


class InstallStatus(Enum):
    """安装状态"""

    PENDING = "pending"  # 待安装
    INSTALLING = "installing"  # 安装中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过


@dataclass
class DependencyInfo:
    """依赖信息"""

    name: str
    version: str | None = None
    version_spec: str | None = None  # 如 ">=1.0.0,<2.0.0"
    dep_type: DependencyType = DependencyType.PYTHON
    optional: bool = False
    description: str | None = None
    homepage: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "version_spec": self.version_spec,
            "dep_type": self.dep_type.value,
            "optional": self.optional,
            "description": self.description,
            "homepage": self.homepage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DependencyInfo":
        return cls(
            name=data["name"],
            version=data.get("version"),
            version_spec=data.get("version_spec"),
            dep_type=DependencyType(data.get("dep_type", "python")),
            optional=data.get("optional", False),
            description=data.get("description"),
            homepage=data.get("homepage"),
        )


@dataclass
class InstallResult:
    """安装结果"""

    dependency: DependencyInfo
    status: InstallStatus
    message: str = ""
    output: str | None = None
    duration: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dependency": self.dependency.to_dict(),
            "status": self.status.value,
            "message": self.message,
            "output": self.output,
            "duration": self.duration,
        }


@dataclass
class InstallReport:
    """安装报告"""

    dependencies: list[DependencyInfo] = field(default_factory=list)
    results: list[InstallResult] = field(default_factory=list)
    total_time: float = 0.0

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.status == InstallStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == InstallStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.status == InstallStatus.SKIPPED)

    @property
    def all_success(self) -> bool:
        return all(
            r.status in (InstallStatus.SUCCESS, InstallStatus.SKIPPED)
            for r in self.results
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dependencies": [d.to_dict() for d in self.dependencies],
            "results": [r.to_dict() for r in self.results],
            "total_time": self.total_time,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "all_success": self.all_success,
        }


@dataclass
class DependencyInstallerConfig:
    """依赖安装器配置"""

    auto_install: bool = False  # 是否自动安装
    use_uv: bool = True  # 使用 uv 而非 pip
    upgrade: bool = False  # 是否升级已安装的包
    timeout: int = 300  # 超时时间 (秒)
    index_url: str | None = None  # 自定义 PyPI 索引 URL
    extra_index_url: str | None = None  # 额外的索引 URL
    trusted_host: str | None = None  # 信任的主机


class DependencyInstaller:
    """依赖安装器

    自动检测和安装插件所需的依赖。

    使用示例:
        installer = DependencyInstaller()
        deps = [DependencyInfo(name="requests", version_spec=">=2.0.0")]
        report = installer.install_all(deps)
    """

    def __init__(self, config: DependencyInstallerConfig | None = None):
        """初始化依赖安装器

        Args:
            config: 安装器配置
        """
        self.config = config or DependencyInstallerConfig()
        self._installed_cache: dict[str, str] | None = None

    def check_installed(self, dep: DependencyInfo) -> tuple[bool, str | None]:
        """检查依赖是否已安装

        Args:
            dep: 依赖信息

        Returns:
            (是否已安装, 已安装版本)
        """
        if dep.dep_type != DependencyType.PYTHON:
            return False, None

        try:
            import importlib.metadata as metadata

            installed_version = metadata.version(dep.name)
            return True, installed_version
        except Exception:
            return False, None

    def get_installed_packages(self) -> dict[str, str]:
        """获取已安装的包列表"""
        if self._installed_cache is not None:
            return self._installed_cache

        try:
            import importlib.metadata as metadata

            self._installed_cache = {
                dist.metadata["name"]: dist.version
                for dist in metadata.distributions()
            }
            return self._installed_cache
        except Exception:
            return {}

    def check_version_compatibility(
        self, dep: DependencyInfo, installed_version: str
    ) -> bool:
        """检查版本兼容性

        Args:
            dep: 依赖信息
            installed_version: 已安装版本

        Returns:
            是否兼容
        """
        if not dep.version_spec:
            return True

        try:
            from packaging.specifiers import SpecifierSet
            from packaging.version import Version

            spec = SpecifierSet(dep.version_spec)
            return Version(installed_version) in spec
        except ImportError:
            # 如果没有 packaging 包，简单比较
            return True

    def install(self, dep: DependencyInfo) -> InstallResult:
        """安装单个依赖

        Args:
            dep: 依赖信息

        Returns:
            安装结果
        """
        import time

        start_time = time.time()

        # 检查是否已安装
        installed, installed_version = self.check_installed(dep)

        if installed and installed_version:
            if self.check_version_compatibility(dep, installed_version):
                return InstallResult(
                    dependency=dep,
                    status=InstallStatus.SKIPPED,
                    message=f"已安装 {dep.name}=={installed_version}",
                    duration=time.time() - start_time,
                )
            elif not self.config.upgrade:
                return InstallResult(
                    dependency=dep,
                    status=InstallStatus.SKIPPED,
                    message=f"已安装 {dep.name}=={installed_version}，版本不匹配但未启用升级",
                    duration=time.time() - start_time,
                )

        # 非自动安装模式
        if not self.config.auto_install:
            return InstallResult(
                dependency=dep,
                status=InstallStatus.PENDING,
                message="需要安装，但未启用自动安装",
                duration=time.time() - start_time,
            )

        # 执行安装
        return self._do_install(dep, start_time)

    def _do_install(self, dep: DependencyInfo, start_time: float) -> InstallResult:
        """执行安装"""
        if dep.dep_type != DependencyType.PYTHON:
            return InstallResult(
                dependency=dep,
                status=InstallStatus.SKIPPED,
                message="只支持 Python 包自动安装",
                duration=0.0,
            )

        # 构建安装命令
        package_spec = dep.name
        if dep.version_spec:
            package_spec = f"{dep.name}{dep.version_spec}"
        elif dep.version:
            package_spec = f"{dep.name}=={dep.version}"

        cmd = []
        if self.config.use_uv:
            cmd = [sys.executable, "-m", "uv", "pip", "install", package_spec]
        else:
            cmd = [sys.executable, "-m", "pip", "install", package_spec]

        if self.config.upgrade:
            cmd.append("--upgrade")

        if self.config.index_url:
            cmd.extend(["--index-url", self.config.index_url])

        if self.config.extra_index_url:
            cmd.extend(["--extra-index-url", self.config.extra_index_url])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                # 清除缓存
                self._installed_cache = None
                return InstallResult(
                    dependency=dep,
                    status=InstallStatus.SUCCESS,
                    message=f"成功安装 {package_spec}",
                    output=result.stdout,
                    duration=duration,
                )
            else:
                return InstallResult(
                    dependency=dep,
                    status=InstallStatus.FAILED,
                    message=f"安装失败: {result.stderr}",
                    output=result.stderr,
                    duration=duration,
                )

        except subprocess.TimeoutExpired:
            return InstallResult(
                dependency=dep,
                status=InstallStatus.FAILED,
                message=f"安装超时 ({self.config.timeout}s)",
                duration=self.config.timeout,
            )
        except Exception as e:
            return InstallResult(
                dependency=dep,
                status=InstallStatus.FAILED,
                message=f"安装出错: {e}",
                duration=time.time() - start_time,
            )

    def install_all(self, dependencies: list[DependencyInfo]) -> InstallReport:
        """安装所有依赖

        Args:
            dependencies: 依赖列表

        Returns:
            安装报告
        """
        import time

        start_time = time.time()
        report = InstallReport(dependencies=dependencies)

        # 分离必需和可选依赖
        required = [d for d in dependencies if not d.optional]
        optional = [d for d in dependencies if d.optional]

        # 先安装必需依赖
        for dep in required:
            result = self.install(dep)
            report.results.append(result)

            if result.status == InstallStatus.FAILED:
                logger.error(f"必需依赖安装失败: {dep.name}")
                # 继续安装其他依赖

        # 再安装可选依赖
        for dep in optional:
            result = self.install(dep)
            report.results.append(result)

            if result.status == InstallStatus.FAILED:
                logger.warning(f"可选依赖安装失败: {dep.name}")

        report.total_time = time.time() - start_time
        return report

    def get_install_commands(self, dependencies: list[DependencyInfo]) -> list[str]:
        """获取安装命令 (不执行)

        Args:
            dependencies: 依赖列表

        Returns:
            安装命令列表
        """
        commands = []

        for dep in dependencies:
            if dep.dep_type != DependencyType.PYTHON:
                continue

            package_spec = dep.name
            if dep.version_spec:
                package_spec = f"{dep.name}{dep.version_spec}"
            elif dep.version:
                package_spec = f"{dep.name}=={dep.version}"

            if self.config.use_uv:
                cmd = f"uv pip install {package_spec}"
            else:
                cmd = f"pip install {package_spec}"

            commands.append(cmd)

        return commands


def create_dependency_installer(config: DependencyInstallerConfig | None = None) -> DependencyInstaller:
    """创建依赖安装器的便捷函数"""
    return DependencyInstaller(config)