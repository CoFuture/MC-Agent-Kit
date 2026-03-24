"""
模板管理器

管理项目模板和代码模板。
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Template:
    """模板信息"""
    name: str
    description: str
    path: Path | None = None
    content: str | None = None
    variables: dict[str, Any] | None = None


class TemplateManager:
    """
    模板管理器

    用于管理和渲染项目模板。
    """

    def __init__(self, template_dir: Path | None = None):
        """
        初始化模板管理器

        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = template_dir
        self._templates: dict[str, Template] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """加载内置模板"""
        self._templates = {
            "empty": Template(
                name="empty",
                description="空项目，只有基础结构",
            ),
            "entity": Template(
                name="entity",
                description="包含实体开发模板",
            ),
            "item": Template(
                name="item",
                description="包含物品开发模板",
            ),
            "block": Template(
                name="block",
                description="包含方块开发模板",
            ),
        }

    def get_template(self, name: str) -> Template | None:
        """
        获取模板

        Args:
            name: 模板名称

        Returns:
            模板对象，不存在则返回 None
        """
        return self._templates.get(name)

    def list_templates(self) -> list[Template]:
        """
        列出所有模板

        Returns:
            模板列表
        """
        return list(self._templates.values())

    def render(self, template: Template, params: dict[str, Any]) -> str:
        """
        渲染模板

        Args:
            template: 模板对象
            params: 模板参数

        Returns:
            渲染后的内容
        """
        # TODO: 实现 Jinja2 模板渲染
        if template.content:
            return template.content
        return ""
