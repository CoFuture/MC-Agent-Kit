"""
事件处理生成器

生成事件监听器代码和事件文档索引。
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..knowledge_base.models import EventEntry, EventParameter, KnowledgeBase, Scope
from .code_gen import CodeGenerator
from .templates import CodeTemplate, TemplateParameter, TemplateType

logger = logging.getLogger(__name__)


@dataclass
class EventListenerConfig:
    """事件监听器配置"""

    event_name: str
    scope: Scope = Scope.SERVER
    callback_name: str | None = None
    description: str | None = None
    include_validation: bool = True
    include_logging: bool = True
    custom_code: str | None = None


class EventGenerator:
    """事件处理生成器

    从知识库生成事件监听器代码和文档索引。

    使用示例:
        generator = EventGenerator(knowledge_base)
        
        # 生成事件监听器
        code = generator.generate_listener("OnServerChat")
        
        # 生成批量事件索引
        index = generator.generate_event_index()
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        code_generator: CodeGenerator | None = None,
    ):
        """初始化事件生成器

        Args:
            knowledge_base: 可选的知识库对象
            code_generator: 可选的代码生成器
        """
        self._kb = knowledge_base
        self._generator = code_generator or CodeGenerator()
        self._register_event_templates()

    def _register_event_templates(self) -> None:
        """注册事件相关模板"""
        # 注册事件监听器模板（增强版）
        self._generator.register_template(
            CodeTemplate(
                name="event_listener_advanced",
                template_type=TemplateType.EVENT_LISTENER,
                description="高级事件监听器模板，包含参数验证和日志",
                template="""# {{ event_name }} 事件监听器
# {{ description | default('事件监听器') }}
# 作用域: {{ scope_text }}
# 来源模块: {{ module | default('通用') }}

import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi

# 获取引擎类型
EngineType = clientApi.GetEngineVersion()[0]

{% if scope == 'client' %}
SystemName = clientApi.GetSystemName()
{% else %}
SystemName = serverApi.GetSystemName()
{% endif %}

{% if include_validation %}
# 事件参数验证器
def validate_{{ event_name | snake_case }}_params(args):
    \"\"\"
    验证 {{ event_name }} 事件参数
    
    预期参数:
    {% for param in event_params %}
    - {{ param.name }} ({{ param.type }}): {{ param.desc }}
    {% endfor %}
    \"\"\"
    errors = []
    {% for param in event_params %}
    if '{{ param.name }}' not in args:
        errors.append("缺少参数: {{ param.name }}")
    {% endfor %}
    
    if errors:
        print("[ValidationError] {{ event_name }}:", errors)
        return False
    return True
{% endif %}

def {{ callback_name }}(args):
    \"\"\"
    {{ event_name }} 事件回调
    
    参数:
    {% for param in event_params %}
    - {{ param.name }} ({{ param.type }}): {{ param.desc }}
    {% endfor %}
    
    返回值控制:
    - return True: 继续传播事件
    - return False: 取消事件传播
    \"\"\"
    {% if include_validation %}
    # 参数验证
    if not validate_{{ event_name | snake_case }}_params(args):
        return True  # 验证失败，但不影响事件传播
    {% endif %}
    
    {% if include_logging %}
    # 日志记录
    print("[{{ event_name }}] 事件触发")
    {% for param in event_params[:3] %}
    print("  {{ param.name }}:", args.get('{{ param.name }}'))
    {% endfor %}
    {% endif %}
    
    {% if custom_code %}
    # 自定义代码
    {{ custom_code | indent(4) }}
    {% else %}
    # TODO: 实现事件处理逻辑
    pass
    {% endif %}
    
    return True  # 继续传播

# 注册事件监听
def register_{{ event_name | snake_case }}_listener():
    \"\"\"注册 {{ event_name }} 事件监听器\"\"\"
    {% if scope == 'client' %}
    clientApi.ListenForEvent(
        '{{ namespace | default('Minecraft') }}',
        '{{ event_name }}',
        {{ callback_name }}
    )
    {% else %}
    serverApi.ListenForEvent(
        '{{ namespace | default('Minecraft') }}',
        '{{ event_name }}',
        {{ callback_name }}
    )
    {% endif %}
    print("[Event] 已注册 {{ event_name }} 监听器")

# 注销事件监听
def unregister_{{ event_name | snake_case }}_listener():
    \"\"\"注销 {{ event_name }} 事件监听器\"\"\"
    {% if scope == 'client' %}
    clientApi.UnListenForEvent(
        '{{ namespace | default('Minecraft') }}',
        '{{ event_name }}',
        {{ callback_name }}
    )
    {% else %}
    serverApi.UnListenForEvent(
        '{{ namespace | default('Minecraft') }}',
        '{{ event_name }}',
        {{ callback_name }}
    )
    {% endif %}
    print("[Event] 已注销 {{ event_name }} 监听器")

# 初始化时注册
# register_{{ event_name | snake_case }}_listener()
""",
                parameters=[
                    TemplateParameter(
                        name="event_name",
                        description="事件名称",
                        param_type="str",
                        required=True,
                    ),
                    TemplateParameter(
                        name="scope",
                        description="作用域 (client/server)",
                        param_type="str",
                        required=False,
                        default="server",
                        choices=["client", "server"],
                    ),
                    TemplateParameter(
                        name="scope_text",
                        description="作用域文本",
                        param_type="str",
                        required=False,
                        default="服务端",
                    ),
                    TemplateParameter(
                        name="callback_name",
                        description="回调函数名",
                        param_type="str",
                        required=False,
                    ),
                    TemplateParameter(
                        name="description",
                        description="事件描述",
                        param_type="str",
                        required=False,
                    ),
                    TemplateParameter(
                        name="module",
                        description="来源模块",
                        param_type="str",
                        required=False,
                    ),
                    TemplateParameter(
                        name="namespace",
                        description="事件命名空间",
                        param_type="str",
                        required=False,
                        default="Minecraft",
                    ),
                    TemplateParameter(
                        name="event_params",
                        description="事件参数列表",
                        param_type="list",
                        required=False,
                        default=[],
                    ),
                    TemplateParameter(
                        name="include_validation",
                        description="是否包含参数验证",
                        param_type="bool",
                        required=False,
                        default=True,
                    ),
                    TemplateParameter(
                        name="include_logging",
                        description="是否包含日志记录",
                        param_type="bool",
                        required=False,
                        default=True,
                    ),
                    TemplateParameter(
                        name="custom_code",
                        description="自定义处理代码",
                        param_type="str",
                        required=False,
                    ),
                ],
                tags=["event", "listener", "advanced"],
                examples=[
                    "event_listener_advanced(event_name='OnServerChat', include_validation=True)",
                    "event_listener_advanced(event_name='OnPlayerDeath', scope='server', custom_code='print(\"Player died\")')",
                ],
                scope="both",
            )
        )

    def set_knowledge_base(self, kb: KnowledgeBase) -> None:
        """设置知识库"""
        self._kb = kb

    def generate_listener(
        self,
        event_name: str,
        config: EventListenerConfig | None = None,
        **kwargs: Any,
    ) -> str:
        """生成事件监听器代码

        Args:
            event_name: 事件名称
            config: 监听器配置
            **kwargs: 额外参数

        Returns:
            生成的代码
        """
        # 合并配置
        if config is None:
            config = EventListenerConfig(event_name=event_name)

        # 从知识库获取事件信息
        event_info = None
        if self._kb:
            event_info = self._kb.get_event(event_name)

        # 构建参数
        params = {
            "event_name": event_name,
            "callback_name": config.callback_name or f"On{event_name}",
            "description": config.description,
            "include_validation": config.include_validation,
            "include_logging": config.include_logging,
            "custom_code": config.custom_code,
        }

        # 设置作用域
        if config.scope != Scope.UNKNOWN:
            params["scope"] = "client" if config.scope == Scope.CLIENT else "server"
            params["scope_text"] = "客户端" if config.scope == Scope.CLIENT else "服务端"
        elif event_info:
            if event_info.scope == Scope.CLIENT:
                params["scope"] = "client"
                params["scope_text"] = "客户端"
            else:
                params["scope"] = "server"
                params["scope_text"] = "服务端"
        else:
            params["scope"] = "server"
            params["scope_text"] = "服务端"

        # 添加事件参数
        if event_info:
            params["module"] = event_info.module
            params["description"] = config.description or event_info.description
            params["event_params"] = [
                {"name": p.name, "type": p.data_type, "desc": p.description}
                for p in event_info.parameters
            ]
        else:
            params["event_params"] = kwargs.get("event_params", [])

        # 更新额外参数
        params.update(kwargs)

        # 生成代码
        return self._generator.generate("event_listener_advanced", params)

    def generate_validation_code(
        self,
        event_name: str,
        parameters: list[EventParameter] | None = None,
    ) -> str:
        """生成参数验证代码

        Args:
            event_name: 事件名称
            parameters: 参数列表

        Returns:
            验证代码
        """
        # 从知识库获取参数
        if parameters is None and self._kb:
            event = self._kb.get_event(event_name)
            if event:
                parameters = event.parameters

        if not parameters:
            return "# 无需验证的参数"

        import re

        def snake_case(value: str) -> str:
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

        lines = [
            f"def validate_{snake_case(event_name)}_params(args):",
            '    """验证事件参数"""',
            "    errors = []",
            "",
        ]

        for param in parameters:
            lines.append(f"    # 验证 {param.name}")
            lines.append(f"    if '{param.name}' not in args:")
            lines.append(f"        errors.append('缺少参数: {param.name}')")
            # 类型检查
            lines.append(f"    elif not isinstance(args.get('{param.name}'), {param.data_type}):")
            lines.append(
                f"        errors.append('参数类型错误: {param.name} 期望 {param.data_type}')"
            )
            lines.append("")

        lines.extend([
            "    if errors:",
            '        print("[ValidationError]", errors)',
            "        return False",
            "    return True",
        ])

        return "\n".join(lines)

    def generate_event_index(
        self,
        format: str = "markdown",
        scope_filter: Scope | None = None,
    ) -> str:
        """生成事件文档索引

        Args:
            format: 输出格式 (markdown/json)
            scope_filter: 作用域过滤

        Returns:
            文档索引内容
        """
        if not self._kb:
            raise ValueError("知识库未设置")

        events = list(self._kb.events.values())

        # 过滤作用域
        if scope_filter and scope_filter != Scope.UNKNOWN:
            events = [e for e in events if e.scope == scope_filter]

        if format == "json":
            return self._generate_json_event_index(events)
        return self._generate_markdown_event_index(events)

    def _generate_markdown_event_index(self, events: list[EventEntry]) -> str:
        """生成 Markdown 格式的事件索引"""
        lines = [
            "# ModSDK 事件索引",
            "",
            f"事件总数: {len(events)}",
            "",
        ]

        # 按模块分组
        modules: dict[str, list[EventEntry]] = {}
        for event in events:
            if event.module not in modules:
                modules[event.module] = []
            modules[event.module].append(event)

        for module_name in sorted(modules.keys()):
            module_events = modules[module_name]
            lines.append(f"## {module_name}")
            lines.append("")
            lines.append("| 事件名称 | 描述 | 作用域 | 参数数量 |")
            lines.append("|----------|------|--------|----------|")

            for event in sorted(module_events, key=lambda x: x.name):
                scope_str = "客户端" if event.scope == Scope.CLIENT else "服务端"
                lines.append(
                    f"| {event.name} | {event.description[:40]}... | {scope_str} | {len(event.parameters)} |"
                )

            lines.append("")

        return "\n".join(lines)

    def _generate_json_event_index(self, events: list[EventEntry]) -> str:
        """生成 JSON 格式的事件索引"""
        import json

        index = {
            "total": len(events),
            "events": [
                {
                    "name": e.name,
                    "module": e.module,
                    "description": e.description,
                    "scope": e.scope.value,
                    "parameters": [
                        {"name": p.name, "type": p.data_type, "description": p.description}
                        for p in e.parameters
                    ],
                }
                for e in events
            ],
        }

        return json.dumps(index, ensure_ascii=False, indent=2)

    def list_events(
        self,
        keyword: str | None = None,
        scope: Scope | None = None,
        module: str | None = None,
    ) -> list[EventEntry]:
        """列出事件

        Args:
            keyword: 关键词过滤
            scope: 作用域过滤
            module: 模块过滤

        Returns:
            事件列表
        """
        if not self._kb:
            return []

        events = list(self._kb.events.values())

        # 关键词过滤
        if keyword:
            keyword_lower = keyword.lower()
            events = [
                e
                for e in events
                if keyword_lower in e.name.lower()
                or keyword_lower in e.description.lower()
            ]

        # 作用域过滤
        if scope and scope != Scope.UNKNOWN:
            events = [e for e in events if e.scope == scope]

        # 模块过滤
        if module:
            events = [e for e in events if e.module == module]

        return events

    def save_event_index(
        self,
        output_path: str | Path,
        format: str = "markdown",
    ) -> None:
        """保存事件索引到文件

        Args:
            output_path: 输出文件路径
            format: 输出格式
        """
        content = self.generate_event_index(format)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        logger.info(f"事件索引已保存到: {output_path}")