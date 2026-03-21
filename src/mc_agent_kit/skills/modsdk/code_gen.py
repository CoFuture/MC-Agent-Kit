"""
ModSDK 代码生成 Skill

提供 ModSDK 代码生成功能，支持事件监听器、API 调用等模板。
"""

import logging
from dataclasses import dataclass

from ...generator import CodeGenerator
from ...generator.templates import TemplateType
from ..base import BaseSkill, SkillCategory, SkillMetadata, SkillPriority, SkillResult

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCode:
    """生成的代码结果"""

    code: str
    template_name: str
    template_type: str
    language: str = "python"
    description: str = ""


class ModSDKCodeGenSkill(BaseSkill):
    """ModSDK 代码生成 Skill

    基于 Jinja2 模板生成 ModSDK 代码，支持：
    - 事件监听器生成
    - API 调用代码生成
    - 实体创建代码生成
    - 物品注册代码生成
    - UI 屏幕代码生成
    - 自定义模板渲染

    使用示例:
        skill = ModSDKCodeGenSkill()
        
        # 生成事件监听器
        result = skill.execute(
            template="event_listener",
            params={"event_name": "OnServerChat"}
        )
        
        # 列出可用模板
        result = skill.execute(action="list")
        
        # 获取模板信息
        result = skill.execute(action="info", template="event_listener")
    """

    def __init__(self):
        """初始化 Skill"""
        super().__init__(
            metadata=SkillMetadata(
                name="modsdk-code-gen",
                description="生成 ModSDK 代码，支持事件监听器、API 调用等模板",
                version="1.0.0",
                author="MC-Agent-Kit",
                category=SkillCategory.CODE_GEN,
                priority=SkillPriority.HIGH,
                tags=["modsdk", "code", "generation", "template"],
                examples=[
                    "生成事件监听器: execute(template='event_listener', params={'event_name': 'OnServerChat'})",
                    "列出模板: execute(action='list')",
                    "搜索模板: execute(action='search', keyword='event')",
                ],
            )
        )
        self._generator: CodeGenerator | None = None

    def initialize(self) -> bool:
        """初始化代码生成器

        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True

        try:
            self._generator = CodeGenerator()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"初始化代码生成器失败: {e}")
            return False

    def execute(
        self,
        template: str | None = None,
        params: dict | None = None,
        action: str = "generate",
        template_type: str | None = None,
        keyword: str | None = None,
        custom_template: str | None = None,
        **kwargs,
    ) -> SkillResult:
        """执行代码生成

        Args:
            template: 模板名称
            params: 模板参数
            action: 操作类型 (generate/list/info/search)
            template_type: 模板类型过滤 (event_listener/api_call/entity/item/ui)
            keyword: 搜索关键词
            custom_template: 自定义模板内容

        Returns:
            SkillResult: 生成结果
        """
        if not self._initialized:
            self.initialize()

        if not self._generator:
            return SkillResult(
                success=False,
                error="代码生成器未初始化",
            )

        try:
            if action == "list":
                return self._list_templates(template_type)
            elif action == "info":
                if not template:
                    return SkillResult(
                        success=False,
                        error="请提供 template 参数",
                    )
                return self._get_template_info(template)
            elif action == "search":
                if not keyword:
                    return SkillResult(
                        success=False,
                        error="请提供 keyword 参数",
                    )
                return self._search_templates(keyword)
            elif action == "generate":
                return self._generate_code(template, params, custom_template)
            else:
                return SkillResult(
                    success=False,
                    error=f"未知操作: {action}",
                    suggestions=["generate", "list", "info", "search"],
                )

        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                message="代码生成失败",
            )

    def _generate_code(
        self,
        template_name: str | None,
        params: dict | None,
        custom_template: str | None,
    ) -> SkillResult:
        """生成代码"""
        params = params or {}

        try:
            if custom_template:
                # 使用自定义模板
                code = self._generator.generate_with_template(custom_template, params)
                return SkillResult(
                    success=True,
                    data={
                        "code": code,
                        "template_name": "custom",
                        "template_type": "custom",
                        "language": "python",
                    },
                    message="使用自定义模板生成代码成功",
                )

            if not template_name:
                return SkillResult(
                    success=False,
                    error="请提供 template 参数或 custom_template 参数",
                    suggestions=[
                        "使用 template 参数选择预定义模板",
                        "使用 custom_template 参数提供自定义 Jinja2 模板",
                        "使用 action='list' 查看可用模板",
                    ],
                )

            # 使用预定义模板
            code = self._generator.generate(template_name, params)
            template_info = self._generator.get_template_info(template_name)

            return SkillResult(
                success=True,
                data={
                    "code": code,
                    "template_name": template_name,
                    "template_type": template_info.get("type", "unknown") if template_info else "unknown",
                    "language": "python",
                },
                message=f"使用模板 '{template_name}' 生成代码成功",
                metadata={"template": template_info},
            )

        except ValueError as e:
            return SkillResult(
                success=False,
                error=str(e),
                message="代码生成失败",
            )

    def _list_templates(self, template_type: str | None = None) -> SkillResult:
        """列出模板"""
        type_enum = None
        if template_type:
            type_map = {
                "event_listener": TemplateType.EVENT_LISTENER,
                "api_call": TemplateType.API_CALL,
                "entity": TemplateType.ENTITY,
                "item": TemplateType.ITEM,
                "ui": TemplateType.UI,
            }
            type_enum = type_map.get(template_type)

        templates = self._generator.list_templates(type_enum)

        return SkillResult(
            success=True,
            data=[
                {
                    "name": t.name,
                    "type": t.template_type.value,
                    "description": t.description,
                    "tags": t.tags,
                    "scope": t.scope,
                }
                for t in templates
            ],
            message=f"共 {len(templates)} 个模板",
        )

    def _get_template_info(self, template_name: str) -> SkillResult:
        """获取模板信息"""
        info = self._generator.get_template_info(template_name)

        if not info:
            return SkillResult(
                success=False,
                error=f"模板不存在: {template_name}",
                suggestions=[t.name for t in self._generator.list_templates()],
            )

        return SkillResult(
            success=True,
            data=info,
            message=f"模板 '{template_name}' 信息",
        )

    def _search_templates(self, keyword: str) -> SkillResult:
        """搜索模板"""
        templates = self._generator.search_templates(keyword)

        return SkillResult(
            success=True,
            data=[
                {
                    "name": t.name,
                    "type": t.template_type.value,
                    "description": t.description,
                    "tags": t.tags,
                }
                for t in templates
            ],
            message=f"找到 {len(templates)} 个匹配的模板",
        )

    def generate_event_listener(
        self,
        event_name: str,
        scope: str = "服务端",
        event_params: list[dict] | None = None,
    ) -> SkillResult:
        """生成事件监听器的便捷方法

        Args:
            event_name: 事件名称
            scope: 作用域
            event_params: 事件参数列表

        Returns:
            SkillResult: 生成结果
        """
        return self.execute(
            template="event_listener",
            params={
                "event_name": event_name,
                "scope": scope,
                "event_params": event_params or [],
            },
        )

    def generate_api_call(
        self,
        api_name: str,
        scope: str = "服务端",
        api_params: list[dict] | None = None,
    ) -> SkillResult:
        """生成 API 调用代码的便捷方法

        Args:
            api_name: API 名称
            scope: 作用域
            api_params: API 参数列表

        Returns:
            SkillResult: 生成结果
        """
        return self.execute(
            template="api_call",
            params={
                "api_name": api_name,
                "scope": scope,
                "api_params": api_params or [],
            },
        )
