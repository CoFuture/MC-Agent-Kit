"""
模板加载器

支持从文件系统加载自定义模板，支持模板热重载。
"""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .templates import CodeTemplate, TemplateManager, TemplateParameter, TemplateType

logger = logging.getLogger(__name__)


@dataclass
class TemplateFile:
    """模板文件信息"""

    path: Path
    name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    loaded_at: float = 0.0


class TemplateLoader:
    """模板加载器

    从文件系统加载自定义模板，支持热重载。

    模板文件格式 (YAML frontmatter + Jinja2):
    ```yaml
    ---
    name: my_template
    type: custom
    description: My custom template
    parameters:
      - name: param1
        description: First parameter
        type: str
        required: true
    tags:
      - custom
      - example
    ---
    # Template content here
    {{ param1 }}
    ```

    使用示例:
        loader = TemplateLoader()
        loader.load_directory("templates/custom")
        templates = loader.get_templates()
    """

    TEMPLATE_EXTENSIONS = {".j2", ".jinja2", ".tmpl", ".template"}

    def __init__(self, template_manager: TemplateManager | None = None):
        """初始化模板加载器

        Args:
            template_manager: 可选的模板管理器，默认创建新的
        """
        self._manager = template_manager or TemplateManager()
        self._loaded_files: dict[str, TemplateFile] = {}  # path -> TemplateFile
        self._template_dirs: list[Path] = []

    def load_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        register: bool = True,
    ) -> int:
        """从目录加载模板

        Args:
            directory: 模板目录路径
            recursive: 是否递归加载子目录
            register: 是否注册到模板管理器

        Returns:
            加载的模板数量
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"模板目录不存在: {directory}")
            return 0

        if dir_path not in self._template_dirs:
            self._template_dirs.append(dir_path)

        count = 0
        pattern = "**/*" if recursive else "*"

        for ext in self.TEMPLATE_EXTENSIONS:
            for file_path in dir_path.glob(f"{pattern}{ext}"):
                if self._load_file(file_path, register):
                    count += 1

        # 也支持 .md 文件中的 YAML frontmatter
        for file_path in dir_path.glob(f"{pattern}.md"):
            if self._load_file(file_path, register):
                count += 1

        logger.info(f"从 {directory} 加载了 {count} 个模板")
        return count

    def _load_file(self, file_path: Path, register: bool = True) -> bool:
        """加载单个模板文件

        Args:
            file_path: 模板文件路径
            register: 是否注册到模板管理器

        Returns:
            是否成功加载
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            checksum = hashlib.md5(content.encode()).hexdigest()

            # 检查是否已加载且未更改
            file_key = str(file_path)
            if file_key in self._loaded_files:
                existing = self._loaded_files[file_key]
                if existing.checksum == checksum:
                    return False  # 未更改

            # 解析模板
            template = self._parse_template(file_path, content)
            if not template:
                return False

            # 记录文件信息
            import time

            self._loaded_files[file_key] = TemplateFile(
                path=file_path,
                name=template.name,
                content=content,
                metadata={
                    "type": template.template_type.value,
                    "description": template.description,
                    "tags": template.tags,
                    "scope": template.scope,
                },
                checksum=checksum,
                loaded_at=time.time(),
            )

            # 注册到管理器
            if register:
                self._manager.register(template)

            return True

        except Exception as e:
            logger.error(f"加载模板文件失败 {file_path}: {e}")
            return False

    def _parse_template(self, file_path: Path, content: str) -> CodeTemplate | None:
        """解析模板文件内容

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            解析的模板对象，失败返回 None
        """
        # 解析 YAML frontmatter
        metadata, template_content = self._parse_frontmatter(content)

        # 从文件名获取默认名称
        default_name = file_path.stem
        if file_path.suffix in self.TEMPLATE_EXTENSIONS:
            default_name = file_path.stem

        # 构建模板
        name = metadata.get("name", default_name)
        template_type_str = metadata.get("type", "custom")
        description = metadata.get("description", f"Template from {file_path.name}")
        tags = metadata.get("tags", [])
        scope = metadata.get("scope", "both")
        parameters_data = metadata.get("parameters", [])
        examples = metadata.get("examples", [])

        # 解析模板类型
        try:
            template_type = TemplateType(template_type_str)
        except ValueError:
            template_type = TemplateType.CUSTOM

        # 解析参数
        parameters = []
        for param_data in parameters_data:
            param = TemplateParameter(
                name=param_data.get("name", ""),
                description=param_data.get("description", ""),
                param_type=param_data.get("type", "str"),
                required=param_data.get("required", True),
                default=param_data.get("default"),
                choices=param_data.get("choices"),
            )
            parameters.append(param)

        return CodeTemplate(
            name=name,
            template_type=template_type,
            description=description,
            template=template_content.strip(),
            parameters=parameters,
            tags=tags,
            examples=examples,
            scope=scope,
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """解析 YAML frontmatter

        Args:
            content: 文件内容

        Returns:
            (元数据字典, 模板内容)
        """
        if not content.startswith("---"):
            return {}, content

        # 查找结束标记
        end_idx = content.find("\n---", 4)
        if end_idx == -1:
            return {}, content

        frontmatter = content[4:end_idx].strip()
        template_content = content[end_idx + 4 :].strip()

        # 解析 YAML
        try:
            import yaml

            metadata = yaml.safe_load(frontmatter)
            if not isinstance(metadata, dict):
                metadata = {}
        except ImportError:
            # 如果没有 PyYAML，使用简单的行解析
            metadata = self._parse_simple_frontmatter(frontmatter)
        except Exception as e:
            logger.warning(f"解析 frontmatter 失败: {e}")
            metadata = {}

        return metadata, template_content

    def _parse_simple_frontmatter(self, frontmatter: str) -> dict[str, Any]:
        """简单解析 frontmatter（不需要 YAML 库）

        Args:
            frontmatter: frontmatter 内容

        Returns:
            解析的元数据
        """
        metadata: dict[str, Any] = {}
        current_key = None
        current_list: list[Any] | None = None
        lines = frontmatter.split("\n")

        for i, line in enumerate(lines):
            line = line.rstrip()
            if not line:
                continue

            # 列表项 (以 "  - " 开头)
            if line.startswith("  - "):
                if current_key and current_list is not None:
                    current_list.append(line[4:])
                continue

            # 键值对 (可能没有值)
            if ": " in line:
                key, value = line.split(": ", 1)
                key = key.strip()
                value = value.strip()

                # 移除引号
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                current_key = key

                # 检查下一行是否是列表
                if i + 1 < len(lines) and lines[i + 1].startswith("  - "):
                    current_list = []
                    metadata[key] = current_list
                elif value == "" or value == "[]":
                    current_list = []
                    metadata[key] = current_list
                else:
                    metadata[key] = value
                    current_list = None
            elif line.endswith(":"):
                # 没有 value 的键 (如 "tags:")
                key = line[:-1].strip()
                current_key = key
                # 检查下一行是否是列表
                if i + 1 < len(lines) and lines[i + 1].startswith("  - "):
                    current_list = []
                    metadata[key] = current_list
                else:
                    metadata[key] = None
                    current_list = None

        return metadata

    def reload(self) -> int:
        """热重载所有已加载的模板

        Returns:
            重新加载的模板数量
        """
        count = 0

        # 重新加载所有目录
        for dir_path in self._template_dirs:
            count += self.load_directory(dir_path, recursive=True, register=True)

        # 检查已加载文件的变更
        for file_key in list(self._loaded_files.keys()):
            file_path = Path(file_key)
            if self._load_file(file_path, register=True):
                count += 1

        logger.info(f"热重载完成，更新了 {count} 个模板")
        return count

    def reload_file(self, file_path: str | Path) -> bool:
        """热重载指定文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功重载
        """
        return self._load_file(Path(file_path), register=True)

    def get_loaded_files(self) -> list[TemplateFile]:
        """获取所有已加载的文件信息"""
        return list(self._loaded_files.values())

    def get_manager(self) -> TemplateManager:
        """获取模板管理器"""
        return self._manager


def load_templates_from_directory(
    directory: str | Path,
    template_manager: TemplateManager | None = None,
) -> tuple[TemplateManager, int]:
    """从目录加载模板的便捷函数

    Args:
        directory: 模板目录路径
        template_manager: 可选的模板管理器

    Returns:
        (模板管理器, 加载的模板数量)
    """
    loader = TemplateLoader(template_manager)
    count = loader.load_directory(directory)
    return loader.get_manager(), count
