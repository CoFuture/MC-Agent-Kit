"""
代码生成器

使用 Jinja2 模板引擎生成 ModSDK 代码。
"""

import logging
import re
from typing import Any

from jinja2 import BaseLoader, Environment, TemplateSyntaxError

from .templates import CodeTemplate, TemplateManager, TemplateType

logger = logging.getLogger(__name__)


class CodeGenerator:
    """代码生成器

    使用模板生成 ModSDK 代码。

    使用示例:
        generator = CodeGenerator()
        
        # 生成事件监听器代码
        code = generator.generate(
            template_name="event_listener",
            params={
                "event_name": "OnServerChat",
                "scope": "服务端",
                "event_params": [
                    {"name": "message", "type": "str", "desc": "聊天消息"}
                ]
            }
        )
        
        # 列出可用模板
        templates = generator.list_templates()
    """

    def __init__(self, template_manager: TemplateManager | None = None):
        """初始化代码生成器

        Args:
            template_manager: 可选的模板管理器，默认创建新的
        """
        self._manager = template_manager or TemplateManager()
        self._jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 注册自定义过滤器
        self._register_filters()

    def _register_filters(self) -> None:
        """注册 Jinja2 自定义过滤器"""

        def snake_case(value: str) -> str:
            """转换为 snake_case"""
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

        def camel_case(value: str) -> str:
            """转换为 camelCase"""
            words = value.replace("-", "_").split("_")
            return words[0].lower() + "".join(w.title() for w in words[1:])

        def pascal_case(value: str) -> str:
            """转换为 PascalCase"""
            words = value.replace("-", "_").split("_")
            return "".join(w.title() for w in words)

        def quote(value: str) -> str:
            """添加引号"""
            return f'"{value}"'

        def comment(value: str) -> str:
            """添加注释前缀"""
            lines = value.split("\n")
            return "\n".join(f"# {line}" for line in lines)

        self._jinja_env.filters["snake_case"] = snake_case
        self._jinja_env.filters["camel_case"] = camel_case
        self._jinja_env.filters["pascal_case"] = pascal_case
        self._jinja_env.filters["quote"] = quote
        self._jinja_env.filters["comment"] = comment

    def generate(
        self,
        template_name: str,
        params: dict[str, Any],
        validate: bool = True,
    ) -> str:
        """生成代码

        Args:
            template_name: 模板名称
            params: 模板参数
            validate: 是否验证参数

        Returns:
            生成的代码

        Raises:
            ValueError: 模板不存在或参数无效
        """
        # 获取模板
        template = self._manager.get(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")

        # 验证参数
        if validate:
            valid, errors = template.validate_params(params)
            if not valid:
                raise ValueError(f"参数验证失败: {'; '.join(errors)}")

        # 合并默认值
        final_params = self._merge_defaults(template, params)

        # 渲染模板
        try:
            jinja_template = self._jinja_env.from_string(template.template)
            code = jinja_template.render(**final_params)
        except TemplateSyntaxError as e:
            raise ValueError(f"模板语法错误: {e}") from e

        return code

    def generate_with_template(
        self,
        template_content: str,
        params: dict[str, Any],
    ) -> str:
        """使用自定义模板生成代码

        Args:
            template_content: Jinja2 模板内容
            params: 模板参数

        Returns:
            生成的代码
        """
        try:
            template = self._jinja_env.from_string(template_content)
            return template.render(**params)
        except TemplateSyntaxError as e:
            raise ValueError(f"模板语法错误: {e}") from e

    def _merge_defaults(
        self,
        template: CodeTemplate,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """合并默认值

        Args:
            template: 模板对象
            params: 用户提供的参数

        Returns:
            合并后的参数
        """
        result = {}

        # 先设置默认值
        for param in template.parameters:
            if param.default is not None:
                result[param.name] = param.default

        # 覆盖用户参数
        result.update(params)

        return result

    def get_template(self, name: str) -> CodeTemplate | None:
        """获取模板"""
        return self._manager.get(name)

    def list_templates(
        self,
        template_type: TemplateType | None = None,
    ) -> list[CodeTemplate]:
        """列出模板

        Args:
            template_type: 可选的模板类型过滤

        Returns:
            模板列表
        """
        if template_type:
            return self._manager.list_by_type(template_type)
        return self._manager.list_all()

    def search_templates(self, keyword: str) -> list[CodeTemplate]:
        """搜索模板

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的模板列表
        """
        return self._manager.search(keyword)

    def register_template(self, template: CodeTemplate) -> None:
        """注册自定义模板

        Args:
            template: 要注册的模板
        """
        self._manager.register(template)

    def get_template_info(self, name: str) -> dict[str, Any] | None:
        """获取模板信息

        Args:
            name: 模板名称

        Returns:
            模板信息字典
        """
        template = self._manager.get(name)
        if not template:
            return None

        return {
            "name": template.name,
            "type": template.template_type.value,
            "description": template.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type,
                    "required": p.required,
                    "default": p.default,
                    "description": p.description,
                    "choices": p.choices,
                }
                for p in template.parameters
            ],
            "tags": template.tags,
            "examples": template.examples,
            "scope": template.scope,
        }


def generate_event_listener(
    event_name: str,
    scope: str = "服务端",
    event_params: list[dict] | None = None,
    description: str | None = None,
) -> str:
    """生成事件监听器代码的便捷函数

    Args:
        event_name: 事件名称
        scope: 作用域
        event_params: 事件参数列表
        description: 事件描述

    Returns:
        生成的代码
    """
    generator = CodeGenerator()
    return generator.generate(
        "event_listener",
        {
            "event_name": event_name,
            "scope": scope,
            "event_params": event_params or [],
            "description": description,
        },
    )


def generate_api_call(
    api_name: str,
    scope: str = "服务端",
    component_factory: str | None = None,
    api_params: list[dict] | None = None,
) -> str:
    """生成 API 调用代码的便捷函数

    Args:
        api_name: API 名称
        scope: 作用域
        component_factory: 组件工厂方法名
        api_params: API 参数列表

    Returns:
        生成的代码
    """
    generator = CodeGenerator()
    return generator.generate(
        "api_call",
        {
            "api_name": api_name,
            "scope": scope,
            "component_factory": component_factory,
            "api_params": api_params or [],
        },
    )
