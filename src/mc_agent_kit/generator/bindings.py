"""
API 绑定生成器

生成 ModSDK API 的类型存根文件 (.pyi) 和文档索引。
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..knowledge_base.models import APIEntry, EventEntry, KnowledgeBase, Scope

logger = logging.getLogger(__name__)


@dataclass
class StubClass:
    """存根类定义"""

    name: str
    methods: list["StubMethod"] = field(default_factory=list)
    description: str = ""


@dataclass
class StubMethod:
    """存根方法定义"""

    name: str
    parameters: list["StubParameter"] = field(default_factory=list)
    return_type: str = "None"
    description: str = ""
    scope: Scope = Scope.UNKNOWN


@dataclass
class StubParameter:
    """存根参数定义"""

    name: str
    type_annotation: str
    default: str | None = None
    description: str = ""


class APIBindingGenerator:
    """API 绑定生成器

    从知识库生成类型存根文件和文档索引。

    使用示例:
        generator = APIBindingGenerator(knowledge_base)
        
        # 生成类型存根
        stub_content = generator.generate_stubs()
        
        # 生成文档索引
        doc_index = generator.generate_doc_index()
    """

    def __init__(self, knowledge_base: KnowledgeBase | None = None):
        """初始化生成器

        Args:
            knowledge_base: 可选的知识库对象
        """
        self._kb = knowledge_base
        self._classes: dict[str, StubClass] = {}

    def set_knowledge_base(self, kb: KnowledgeBase) -> None:
        """设置知识库"""
        self._kb = kb

    def generate_stubs(
        self,
        module_name: str = "modsdk",
        include_docstrings: bool = True,
    ) -> str:
        """生成类型存根文件 (.pyi)

        Args:
            module_name: 模块名称
            include_docstrings: 是否包含文档字符串

        Returns:
            存根文件内容
        """
        if not self._kb:
            raise ValueError("知识库未设置")

        lines: list[str] = []

        # 文件头部
        lines.append('"""')
        lines.append(f"ModSDK 类型存根文件")
        lines.append(f"自动生成，请勿手动修改")
        lines.append(f"API 数量: {len(self._kb.apis)}")
        lines.append(f"事件数量: {len(self._kb.events)}")
        lines.append('"""')
        lines.append("")
        lines.append("from typing import Any, Callable, Dict, List, Optional, Tuple, Union")
        lines.append("")

        # 按模块分组
        modules = self._group_apis_by_module()

        # 生成每个模块的类
        for module_name_key, apis in modules.items():
            class_name = self._module_to_class_name(module_name_key)
            lines.append(f"# {'=' * 60}")
            lines.append(f"# 模块: {module_name_key}")
            lines.append(f"# {'=' * 60}")
            lines.append("")

            # 生成类
            lines.append(f"class {class_name}:")
            if include_docstrings:
                lines.append(f'    """{module_name_key} 模块 API"""')
                lines.append("")

            for api in apis:
                self._generate_api_method(lines, api, include_docstrings)

            lines.append("")

        # 生成事件类型
        lines.append("# " + "=" * 60)
        lines.append("# 事件类型")
        lines.append("# " + "=" * 60)
        lines.append("")

        for event in self._kb.events.values():
            self._generate_event_type(lines, event, include_docstrings)

        return "\n".join(lines)

    def _generate_api_method(
        self,
        lines: list[str],
        api: APIEntry,
        include_docstrings: bool,
    ) -> None:
        """生成 API 方法存根"""
        # 构建参数列表
        params = ["self"]
        for param in api.parameters:
            type_str = self._map_type_to_stub(param.data_type)
            if param.optional:
                params.append(f"{param.name}: {type_str} = ...")
            else:
                params.append(f"{param.name}: {type_str}")

        # 返回类型
        return_type = self._map_type_to_stub(api.return_type or "None")

        # 方法签名
        method_sig = f"    def {api.name}({', '.join(params)}) -> {return_type}:"
        lines.append(method_sig)

        # 文档字符串
        if include_docstrings and api.description:
            lines.append(f'        """{api.description}"""')
        else:
            lines.append("        ...")

        lines.append("")

    def _generate_event_type(
        self,
        lines: list[str],
        event: EventEntry,
        include_docstrings: bool,
    ) -> None:
        """生成事件类型定义"""
        lines.append(f"# {event.name}")
        if include_docstrings and event.description:
            lines.append(f"# {event.description}")
        lines.append(f"{event.name.upper()}: str = \"{event.name}\"")
        lines.append("")

    def generate_doc_index(self, format: str = "markdown") -> str:
        """生成 API 文档索引

        Args:
            format: 输出格式 (markdown/json)

        Returns:
            文档索引内容
        """
        if not self._kb:
            raise ValueError("知识库未设置")

        if format == "json":
            return self._generate_json_index()
        return self._generate_markdown_index()

    def _generate_markdown_index(self) -> str:
        """生成 Markdown 格式的文档索引"""
        lines: list[str] = []

        lines.append("# ModSDK API 文档索引")
        lines.append("")
        lines.append(f"- API 总数: {len(self._kb.apis)}")
        lines.append(f"- 事件总数: {len(self._kb.events)}")
        lines.append(f"- 枚举总数: {len(self._kb.enums)}")
        lines.append("")

        # 按模块分组 API
        lines.append("## API 索引")
        lines.append("")

        modules = self._group_apis_by_module()
        for module_name, apis in sorted(modules.items()):
            lines.append(f"### {module_name}")
            lines.append("")
            lines.append("| API 名称 | 描述 | 作用域 |")
            lines.append("|----------|------|--------|")

            for api in sorted(apis, key=lambda x: x.name):
                scope_str = self._scope_to_string(api.scope)
                lines.append(f"| {api.name} | {api.description[:50]}... | {scope_str} |")

            lines.append("")

        # 事件索引
        lines.append("## 事件索引")
        lines.append("")

        event_modules = self._group_events_by_module()
        for module_name, events in sorted(event_modules.items()):
            lines.append(f"### {module_name}")
            lines.append("")
            lines.append("| 事件名称 | 描述 | 作用域 |")
            lines.append("|----------|------|--------|")

            for event in sorted(events, key=lambda x: x.name):
                scope_str = self._scope_to_string(event.scope)
                lines.append(f"| {event.name} | {event.description[:50]}... | {scope_str} |")

            lines.append("")

        return "\n".join(lines)

    def _generate_json_index(self) -> str:
        """生成 JSON 格式的文档索引"""
        import json

        index = {
            "stats": self._kb.stats(),
            "apis": {},
            "events": {},
        }

        for name, api in self._kb.apis.items():
            index["apis"][name] = {
                "name": api.name,
                "module": api.module,
                "description": api.description,
                "scope": api.scope.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.data_type,
                        "description": p.description,
                        "optional": p.optional,
                    }
                    for p in api.parameters
                ],
                "return_type": api.return_type,
            }

        for name, event in self._kb.events.items():
            index["events"][name] = {
                "name": event.name,
                "module": event.module,
                "description": event.description,
                "scope": event.scope.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.data_type,
                        "description": p.description,
                    }
                    for p in event.parameters
                ],
            }

        return json.dumps(index, ensure_ascii=False, indent=2)

    def generate_completion_suggestions(self, prefix: str = "") -> list[dict[str, Any]]:
        """生成自动补全建议

        Args:
            prefix: 前缀过滤

        Returns:
            补全建议列表
        """
        if not self._kb:
            raise ValueError("知识库未设置")

        suggestions = []
        prefix_lower = prefix.lower()

        # API 建议
        for api in self._kb.apis.values():
            if prefix_lower and prefix_lower not in api.name.lower():
                continue

            suggestions.append(
                {
                    "type": "api",
                    "name": api.name,
                    "module": api.module,
                    "description": api.description[:100],
                    "scope": api.scope.value,
                    "parameters": [
                        {"name": p.name, "type": p.data_type, "optional": p.optional}
                        for p in api.parameters
                    ],
                    "return_type": api.return_type,
                }
            )

        # 事件建议
        for event in self._kb.events.values():
            if prefix_lower and prefix_lower not in event.name.lower():
                continue

            suggestions.append(
                {
                    "type": "event",
                    "name": event.name,
                    "module": event.module,
                    "description": event.description[:100],
                    "scope": event.scope.value,
                    "parameters": [
                        {"name": p.name, "type": p.data_type}
                        for p in event.parameters
                    ],
                }
            )

        return suggestions

    def save_stubs(self, output_path: str | Path) -> None:
        """保存类型存根到文件

        Args:
            output_path: 输出文件路径
        """
        content = self.generate_stubs()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        logger.info(f"类型存根已保存到: {output_path}")

    def save_doc_index(self, output_path: str | Path, format: str = "markdown") -> None:
        """保存文档索引到文件

        Args:
            output_path: 输出文件路径
            format: 输出格式
        """
        content = self.generate_doc_index(format)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        logger.info(f"文档索引已保存到: {output_path}")

    def _group_apis_by_module(self) -> dict[str, list[APIEntry]]:
        """按模块分组 API"""
        modules: dict[str, list[APIEntry]] = {}
        for api in self._kb.apis.values():
            if api.module not in modules:
                modules[api.module] = []
            modules[api.module].append(api)
        return modules

    def _group_events_by_module(self) -> dict[str, list[EventEntry]]:
        """按模块分组事件"""
        modules: dict[str, list[EventEntry]] = {}
        for event in self._kb.events.values():
            if event.module not in modules:
                modules[event.module] = []
            modules[event.module].append(event)
        return modules

    def _module_to_class_name(self, module_name: str) -> str:
        """将模块名转换为类名"""
        # 移除特殊字符
        clean_name = module_name.replace("/", "_").replace("-", "_").replace(" ", "_")
        # PascalCase
        parts = clean_name.split("_")
        return "".join(part.capitalize() for part in parts if part)

    def _map_type_to_stub(self, type_str: str) -> str:
        """将 ModSDK 类型映射到 Python 类型注解"""
        type_lower = type_str.lower().strip()

        # 基本类型映射
        type_map = {
            "int": "int",
            "integer": "int",
            "float": "float",
            "bool": "bool",
            "boolean": "bool",
            "str": "str",
            "string": "str",
            "none": "None",
            "dict": "Dict[str, Any]",
            "dict[str, any]": "Dict[str, Any]",
            "list": "List[Any]",
            "list[any]": "List[Any]",
            "tuple": "Tuple[Any, ...]",
            "any": "Any",
            "callable": "Callable",
            "function": "Callable",
        }

        if type_lower in type_map:
            return type_map[type_lower]

        # 处理 None 可选类型
        if "none" in type_lower or "可选" in type_str:
            return f"Optional[{type_map.get(type_lower.replace('none', '').replace('|', '').strip(), 'Any')}]"

        return type_str

    def _scope_to_string(self, scope: Scope) -> str:
        """将作用域转换为字符串"""
        scope_map = {
            Scope.CLIENT: "客户端",
            Scope.SERVER: "服务端",
            Scope.BOTH: "双端",
            Scope.UNKNOWN: "未知",
        }
        return scope_map.get(scope, "未知")