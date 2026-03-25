"""
API 文档生成模块

提供自动 API 文档生成、多格式输出和示例代码生成。
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class DocFormat(Enum):
    """文档格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"
    JSON = "json"
    OPENAPI = "openapi"


class ParameterType(Enum):
    """参数类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"
    CALLABLE = "callable"
    OPTIONAL = "optional"


@dataclass
class ParameterDoc:
    """参数文档"""
    name: str
    type: ParameterType = ParameterType.ANY
    description: str = ""
    default: Any = None
    required: bool = True
    example: Any = None
    constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "default": str(self.default) if self.default is not None else None,
            "required": self.required,
            "example": self.example,
            "constraints": self.constraints,
        }


@dataclass
class ReturnDoc:
    """返回值文档"""
    type: ParameterType = ParameterType.ANY
    description: str = ""
    example: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "description": self.description,
            "example": self.example,
        }


@dataclass
class ExceptionDoc:
    """异常文档"""
    type: str
    description: str = ""
    condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "condition": self.condition,
        }


@dataclass
class ExampleCode:
    """示例代码"""
    title: str
    code: str
    language: str = "python"
    description: str = ""
    output: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "code": self.code,
            "language": self.language,
            "description": self.description,
            "output": self.output,
            "tags": self.tags,
        }


@dataclass
class FunctionDoc:
    """函数文档"""
    name: str
    description: str = ""
    parameters: list[ParameterDoc] = field(default_factory=list)
    returns: ReturnDoc | None = None
    exceptions: list[ExceptionDoc] = field(default_factory=list)
    examples: list[ExampleCode] = field(default_factory=list)
    deprecated: bool = False
    deprecation_message: str = ""
    since_version: str = ""
    tags: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "returns": self.returns.to_dict() if self.returns else None,
            "exceptions": [e.to_dict() for e in self.exceptions],
            "examples": [e.to_dict() for e in self.examples],
            "deprecated": self.deprecated,
            "deprecation_message": self.deprecation_message,
            "since_version": self.since_version,
            "tags": self.tags,
            "see_also": self.see_also,
            "notes": self.notes,
        }


@dataclass
class ClassDoc:
    """类文档"""
    name: str
    description: str = ""
    parameters: list[ParameterDoc] = field(default_factory=list)
    attributes: list[ParameterDoc] = field(default_factory=list)
    methods: list[FunctionDoc] = field(default_factory=list)
    examples: list[ExampleCode] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)
    deprecated: bool = False
    since_version: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "attributes": [a.to_dict() for a in self.attributes],
            "methods": [m.to_dict() for m in self.methods],
            "examples": [e.to_dict() for e in self.examples],
            "base_classes": self.base_classes,
            "deprecated": self.deprecated,
            "since_version": self.since_version,
            "tags": self.tags,
        }


@dataclass
class ModuleDoc:
    """模块文档"""
    name: str
    description: str = ""
    functions: list[FunctionDoc] = field(default_factory=list)
    classes: list[ClassDoc] = field(default_factory=list)
    constants: list[ParameterDoc] = field(default_factory=list)
    examples: list[ExampleCode] = field(default_factory=list)
    version: str = ""
    author: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "functions": [f.to_dict() for f in self.functions],
            "classes": [c.to_dict() for c in self.classes],
            "constants": [c.to_dict() for c in self.constants],
            "examples": [e.to_dict() for e in self.examples],
            "version": self.version,
            "author": self.author,
        }


@dataclass
class ApiDocResult:
    """API 文档生成结果"""
    module: ModuleDoc | None = None
    format: DocFormat = DocFormat.MARKDOWN
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module.to_dict() if self.module else None,
            "format": self.format.value,
            "content": self.content,
            "metadata": self.metadata,
        }


class DocstringParser:
    """
    Docstring 解析器

    解析 Python docstring 提取文档信息。
    """

    # 常见 docstring 风格
    STYLES = ["google", "numpy", "sphinx", "rest"]

    def parse(self, docstring: str | None) -> dict[str, Any]:
        """
        解析 docstring

        Args:
            docstring: 原始 docstring

        Returns:
            dict: 解析后的文档信息
        """
        if not docstring:
            return {}

        result: dict[str, Any] = {
            "description": "",
            "parameters": [],
            "returns": None,
            "exceptions": [],
            "examples": [],
        }

        lines = docstring.strip().split("\n")

        # 解析描述
        description_lines = []
        in_section = False

        for line in lines:
            stripped = line.strip()

            # 检查是否进入特定部分
            if stripped.lower().startswith(("args:", "arguments:", "参数:", "参数：")):
                in_section = True
                break
            if stripped.lower().startswith(("returns:", "return:", "返回:", "返回：")):
                in_section = True
                break
            if stripped.lower().startswith(("raises:", "raise:", "异常:", "异常：")):
                in_section = True
                break
            if stripped.lower().startswith(("example:", "examples:", "示例:", "示例：")):
                in_section = True
                break

            if not in_section and stripped:
                description_lines.append(stripped)

        result["description"] = "\n".join(description_lines)

        # 解析参数部分
        result["parameters"] = self._parse_parameters(docstring)

        # 解析返回值
        result["returns"] = self._parse_returns(docstring)

        # 解析异常
        result["exceptions"] = self._parse_exceptions(docstring)

        # 解析示例
        result["examples"] = self._parse_examples(docstring)

        return result

    def _parse_parameters(self, docstring: str) -> list[dict[str, Any]]:
        """解析参数部分"""
        parameters = []
        lines = docstring.split("\n")

        in_args = False
        current_param: dict[str, Any] | None = None

        for line in lines:
            stripped = line.strip()

            # 检测参数部分开始
            if stripped.lower().startswith(("args:", "arguments:", "参数:", "参数：")):
                in_args = True
                continue

            # 检测其他部分开始（参数部分结束）
            if in_args and stripped.lower().startswith(("returns:", "raises:", "example:", "返回:", "异常:", "示例:")):
                if current_param:
                    parameters.append(current_param)
                in_args = False
                break

            if in_args:
                # 解析参数行
                # 格式: name (type): description 或 name: description
                if ":" in stripped:
                    if current_param:
                        parameters.append(current_param)

                    # 解析参数定义
                    parts = stripped.split(":", 1)
                    name_part = parts[0].strip()
                    desc_part = parts[1].strip() if len(parts) > 1 else ""

                    param_name = name_part
                    param_type = ParameterType.ANY.value

                    # 提取类型
                    if "(" in name_part and ")" in name_part:
                        type_start = name_part.index("(")
                        type_end = name_part.index(")")
                        param_type = name_part[type_start + 1:type_end].strip()
                        param_name = name_part[:type_start].strip()

                    current_param = {
                        "name": param_name,
                        "type": param_type,
                        "description": desc_part,
                    }
                elif current_param and stripped:
                    # 续行描述
                    current_param["description"] += " " + stripped

        if current_param:
            parameters.append(current_param)

        return parameters

    def _parse_returns(self, docstring: str) -> dict[str, Any] | None:
        """解析返回值部分"""
        lines = docstring.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.lower().startswith(("returns:", "return:", "返回:", "返回：")):
                # 提取返回值描述
                desc_part = stripped.split(":", 1)[-1].strip() if ":" in stripped else ""

                # 收集后续行
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line and not next_line.lower().startswith(("raises:", "example:", "异常:", "示例:")):
                        desc_part += " " + next_line
                    elif next_line:
                        break

                return {
                    "type": ParameterType.ANY.value,
                    "description": desc_part.strip(),
                }

        return None

    def _parse_exceptions(self, docstring: str) -> list[dict[str, Any]]:
        """解析异常部分"""
        exceptions = []
        lines = docstring.split("\n")

        in_raises = False
        current_exc: dict[str, Any] | None = None

        for line in lines:
            stripped = line.strip()

            if stripped.lower().startswith(("raises:", "raise:", "异常:", "异常：")):
                in_raises = True
                continue

            if in_raises and stripped.lower().startswith(("example:", "示例:", "note:", "注意:")):
                if current_exc:
                    exceptions.append(current_exc)
                break

            if in_raises:
                if ":" in stripped:
                    if current_exc:
                        exceptions.append(current_exc)

                    parts = stripped.split(":", 1)
                    exc_type = parts[0].strip()
                    exc_desc = parts[1].strip() if len(parts) > 1 else ""

                    current_exc = {
                        "type": exc_type,
                        "description": exc_desc,
                    }
                elif current_exc and stripped:
                    current_exc["description"] += " " + stripped

        if current_exc:
            exceptions.append(current_exc)

        return exceptions

    def _parse_examples(self, docstring: str) -> list[dict[str, Any]]:
        """解析示例部分"""
        examples = []
        lines = docstring.split("\n")

        in_example = False
        code_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            if stripped.lower().startswith(("example:", "examples:", "示例:", "示例：")):
                in_example = True
                continue

            if in_example:
                if stripped.startswith(">>>") or stripped.startswith("..."):
                    code_lines.append(stripped[4:] if stripped.startswith(">>> ") else stripped[4:])
                elif stripped and code_lines:
                    # 示例结束
                    examples.append({
                        "title": "示例",
                        "code": "\n".join(code_lines),
                        "language": "python",
                    })
                    code_lines = []

        if code_lines:
            examples.append({
                "title": "示例",
                "code": "\n".join(code_lines),
                "language": "python",
            })

        return examples


class TypeInferer:
    """
    类型推断器

    从代码中推断参数和返回值类型。
    """

    TYPE_MAPPING = {
        str: ParameterType.STRING,
        int: ParameterType.INTEGER,
        float: ParameterType.FLOAT,
        bool: ParameterType.BOOLEAN,
        list: ParameterType.LIST,
        dict: ParameterType.DICT,
        callable: ParameterType.CALLABLE,
    }

    def infer_parameter_type(self, param: inspect.Parameter) -> ParameterType:
        """推断参数类型"""
        if param.annotation != inspect.Parameter.empty:
            return self._type_to_enum(param.annotation)

        if param.default is not None:
            return self._type_to_enum(type(param.default))

        return ParameterType.ANY

    def infer_return_type(self, func: Callable) -> ParameterType:
        """推断返回值类型"""
        sig = inspect.signature(func)

        if sig.return_annotation != inspect.Signature.empty:
            return self._type_to_enum(sig.return_annotation)

        return ParameterType.ANY

    def _type_to_enum(self, type_hint: Any) -> ParameterType:
        """将类型转换为枚举"""
        if type_hint in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[type_hint]

        # 处理 Optional
        if hasattr(type_hint, "__origin__"):
            if type_hint.__origin__ is type(None) | type:
                return ParameterType.OPTIONAL

        return ParameterType.ANY


class ExampleGenerator:
    """
    示例代码生成器

    自动生成 API 使用示例。
    """

    def generate_function_example(
        self,
        func_doc: FunctionDoc,
        module_name: str = "",
    ) -> ExampleCode:
        """生成函数示例代码"""
        # 构建函数调用
        args = []
        for param in func_doc.parameters:
            if param.required:
                args.append(self._generate_example_value(param))

        call_args = ", ".join(args)
        func_name = func_doc.name

        if module_name:
            code = f"from {module_name} import {func_name}\n\n"
        else:
            code = ""

        code += f"# {func_doc.description[:50] if func_doc.description else '调用示例'}\n"
        code += f"result = {func_name}({call_args})\n"

        if func_doc.returns:
            code += f"print(result)  # {func_doc.returns.description[:50] if func_doc.returns.description else ''}\n"

        return ExampleCode(
            title=f"{func_name} 使用示例",
            code=code,
            language="python",
            description=func_doc.description,
        )

    def generate_class_example(
        self,
        class_doc: ClassDoc,
        module_name: str = "",
    ) -> ExampleCode:
        """生成类示例代码"""
        class_name = class_doc.name

        # 构建构造函数调用
        init_args = []
        for param in class_doc.parameters:
            if param.required:
                init_args.append(self._generate_example_value(param))

        call_args = ", ".join(init_args)

        if module_name:
            code = f"from {module_name} import {class_name}\n\n"
        else:
            code = ""

        code += f"# {class_doc.description[:50] if class_doc.description else '创建实例'}\n"
        code += f"instance = {class_name}({call_args})\n"

        # 添加方法调用示例
        if class_doc.methods:
            first_method = class_doc.methods[0]
            method_args = ", ".join(
                self._generate_example_value(p)
                for p in first_method.parameters[:2]
                if p.required
            )
            code += f"\n# 调用方法\n"
            code += f"instance.{first_method.name}({method_args})\n"

        return ExampleCode(
            title=f"{class_name} 使用示例",
            code=code,
            language="python",
            description=class_doc.description,
        )

    def _generate_example_value(self, param: ParameterDoc) -> str:
        """生成参数示例值"""
        if param.example is not None:
            return repr(param.example)

        type_examples = {
            ParameterType.STRING: f'"example_{param.name}"',
            ParameterType.INTEGER: "42",
            ParameterType.FLOAT: "3.14",
            ParameterType.BOOLEAN: "True",
            ParameterType.LIST: "[]",
            ParameterType.DICT: "{}",
            ParameterType.CALLABLE: "lambda x: x",
            ParameterType.ANY: "None",
            ParameterType.OPTIONAL: "None",
        }

        return type_examples.get(param.type, "None")


class DocFormatter:
    """
    文档格式化器

    将文档转换为不同格式输出。
    """

    def format(self, doc: ModuleDoc | FunctionDoc | ClassDoc, format_type: DocFormat) -> str:
        """格式化文档"""
        formatters = {
            DocFormat.MARKDOWN: self._format_markdown,
            DocFormat.HTML: self._format_html,
            DocFormat.RST: self._format_rst,
            DocFormat.JSON: self._format_json,
        }

        formatter = formatters.get(format_type, self._format_markdown)
        return formatter(doc)

    def _format_markdown(self, doc: ModuleDoc | FunctionDoc | ClassDoc) -> str:
        """Markdown 格式化"""
        if isinstance(doc, ModuleDoc):
            return self._format_module_markdown(doc)
        elif isinstance(doc, ClassDoc):
            return self._format_class_markdown(doc)
        else:
            return self._format_function_markdown(doc)

    def _format_module_markdown(self, doc: ModuleDoc) -> str:
        """模块 Markdown 格式化"""
        lines = [
            f"# {doc.name}",
            "",
            doc.description,
            "",
        ]

        if doc.functions:
            lines.append("## 函数")
            lines.append("")
            for func in doc.functions:
                lines.append(f"### `{func.name}`")
                lines.append("")
                lines.append(func.description)
                lines.append("")

        if doc.classes:
            lines.append("## 类")
            lines.append("")
            for cls in doc.classes:
                lines.append(f"### `{cls.name}`")
                lines.append("")
                lines.append(cls.description)
                lines.append("")

        return "\n".join(lines)

    def _format_class_markdown(self, doc: ClassDoc) -> str:
        """类 Markdown 格式化"""
        lines = [
            f"# class {doc.name}",
            "",
            doc.description,
            "",
        ]

        if doc.base_classes:
            lines.append(f"**继承自:** {', '.join(doc.base_classes)}")
            lines.append("")

        if doc.parameters:
            lines.append("## 参数")
            lines.append("")
            lines.append("| 名称 | 类型 | 描述 | 必需 |")
            lines.append("|------|------|------|------|")
            for param in doc.parameters:
                lines.append(f"| {param.name} | {param.type.value} | {param.description} | {'是' if param.required else '否'} |")
            lines.append("")

        if doc.methods:
            lines.append("## 方法")
            lines.append("")
            for method in doc.methods:
                lines.append(f"### `{method.name}`")
                lines.append("")
                lines.append(method.description)
                lines.append("")

        if doc.examples:
            lines.append("## 示例")
            lines.append("")
            for example in doc.examples:
                lines.append(f"### {example.title}")
                lines.append("")
                if example.description:
                    lines.append(example.description)
                    lines.append("")
                lines.append(f"```{example.language}")
                lines.append(example.code)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def _format_function_markdown(self, doc: FunctionDoc) -> str:
        """函数 Markdown 格式化"""
        lines = [
            f"# {doc.name}",
            "",
            doc.description,
            "",
        ]

        if doc.deprecated:
            lines.append(f"> ⚠️ **已弃用**: {doc.deprecation_message}")
            lines.append("")

        if doc.parameters:
            lines.append("## 参数")
            lines.append("")
            lines.append("| 名称 | 类型 | 描述 | 必需 | 默认值 |")
            lines.append("|------|------|------|------|--------|")
            for param in doc.parameters:
                default = str(param.default) if param.default is not None else "-"
                lines.append(f"| {param.name} | {param.type.value} | {param.description[:50]} | {'是' if param.required else '否'} | {default} |")
            lines.append("")

        if doc.returns:
            lines.append("## 返回值")
            lines.append("")
            lines.append(f"| 类型 | 描述 |")
            lines.append(f"|------|------|")
            lines.append(f"| {doc.returns.type.value} | {doc.returns.description} |")
            lines.append("")

        if doc.exceptions:
            lines.append("## 异常")
            lines.append("")
            for exc in doc.exceptions:
                lines.append(f"- `{exc.type}`: {exc.description}")
            lines.append("")

        if doc.examples:
            lines.append("## 示例")
            lines.append("")
            for example in doc.examples:
                lines.append(f"### {example.title}")
                lines.append("")
                lines.append(f"```{example.language}")
                lines.append(example.code)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def _format_html(self, doc: ModuleDoc | FunctionDoc | ClassDoc) -> str:
        """HTML 格式化"""
        # 简化的 HTML 输出
        html = f"<article>\n"
        html += f"<h1>{doc.name}</h1>\n"
        html += f"<p>{doc.description}</p>\n"
        html += "</article>\n"
        return html

    def _format_rst(self, doc: ModuleDoc | FunctionDoc | ClassDoc) -> str:
        """reStructuredText 格式化"""
        lines = [
            doc.name,
            "=" * len(doc.name),
            "",
            doc.description,
            "",
        ]
        return "\n".join(lines)

    def _format_json(self, doc: ModuleDoc | FunctionDoc | ClassDoc) -> str:
        """JSON 格式化"""
        return json.dumps(doc.to_dict(), ensure_ascii=False, indent=2)


class ApiDocGenerator:
    """
    API 文档生成器

    从代码自动生成 API 文档。
    """

    def __init__(self) -> None:
        self.docstring_parser = DocstringParser()
        self.type_inferer = TypeInferer()
        self.example_generator = ExampleGenerator()
        self.formatter = DocFormatter()

    def generate_from_function(
        self,
        func: Callable,
        module_name: str = "",
        generate_example: bool = True,
    ) -> FunctionDoc:
        """
        从函数生成文档

        Args:
            func: 函数对象
            module_name: 模块名称
            generate_example: 是否生成示例代码

        Returns:
            FunctionDoc: 函数文档
        """
        # 获取基本信息
        name = func.__name__
        docstring = func.__doc__
        parsed = self.docstring_parser.parse(docstring)

        # 获取签名
        sig = inspect.signature(func)

        # 解析参数
        parameters = []
        for param_name, param in sig.parameters.items():
            # 跳过 self 参数
            if param_name == "self":
                continue

            # 查找 docstring 中的参数描述
            param_desc = next(
                (p for p in parsed.get("parameters", []) if p["name"] == param_name),
                {}
            )

            param_doc = ParameterDoc(
                name=param_name,
                type=self.type_inferer.infer_parameter_type(param),
                description=param_desc.get("description", ""),
                default=param.default if param.default != inspect.Parameter.empty else None,
                required=param.default == inspect.Parameter.empty,
            )
            parameters.append(param_doc)

        # 解析返回值
        returns = None
        if parsed.get("returns"):
            returns = ReturnDoc(
                type=ParameterType(parsed.get("returns", {}).get("type", "any")),
                description=parsed.get("returns", {}).get("description", ""),
            )
        elif sig.return_annotation != inspect.Signature.empty:
            returns = ReturnDoc(
                type=self.type_inferer._type_to_enum(sig.return_annotation),
                description="",
            )

        # 解析异常
        exceptions = []
        for exc_data in parsed.get("exceptions", []):
            exceptions.append(ExceptionDoc(
                type=exc_data.get("type", "Exception"),
                description=exc_data.get("description", ""),
            ))

        # 创建函数文档
        func_doc = FunctionDoc(
            name=name,
            description=parsed.get("description", ""),
            parameters=parameters,
            returns=returns,
            exceptions=exceptions,
        )

        # 生成示例
        if generate_example:
            example = self.example_generator.generate_function_example(func_doc, module_name)
            func_doc.examples.append(example)

        return func_doc

    def generate_from_class(
        self,
        cls: type,
        module_name: str = "",
        generate_example: bool = True,
        include_private: bool = False,
    ) -> ClassDoc:
        """
        从类生成文档

        Args:
            cls: 类对象
            module_name: 模块名称
            generate_example: 是否生成示例代码
            include_private: 是否包含私有方法

        Returns:
            ClassDoc: 类文档
        """
        name = cls.__name__
        docstring = cls.__doc__
        parsed = self.docstring_parser.parse(docstring)

        # 获取基类
        base_classes = [base.__name__ for base in cls.__bases__ if base.__name__ != "object"]

        # 解析 __init__ 参数
        parameters = []
        if hasattr(cls, "__init__"):
            init_sig = inspect.signature(cls.__init__)
            for param_name, param in init_sig.parameters.items():
                if param_name in ("self", "args", "kwargs"):
                    continue

                param_doc = ParameterDoc(
                    name=param_name,
                    type=self.type_inferer.infer_parameter_type(param),
                    default=param.default if param.default != inspect.Parameter.empty else None,
                    required=param.default == inspect.Parameter.empty,
                )
                parameters.append(param_doc)

        # 解析属性
        attributes = []
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            attr = getattr(cls, attr_name)
            if not callable(attr):
                attributes.append(ParameterDoc(
                    name=attr_name,
                    type=self.type_inferer._type_to_enum(type(attr)),
                    description="",
                ))

        # 解析方法
        methods = []
        for method_name in dir(cls):
            if method_name.startswith("_") and not include_private:
                continue

            method = getattr(cls, method_name)
            if callable(method) and not isinstance(method, type):
                try:
                    method_doc = self.generate_from_function(
                        method,
                        module_name=f"{module_name}.{name}" if module_name else name,
                        generate_example=False,
                    )
                    methods.append(method_doc)
                except (ValueError, TypeError):
                    pass

        # 创建类文档
        class_doc = ClassDoc(
            name=name,
            description=parsed.get("description", ""),
            parameters=parameters,
            attributes=attributes,
            methods=methods,
            base_classes=base_classes,
        )

        # 生成示例
        if generate_example:
            example = self.example_generator.generate_class_example(class_doc, module_name)
            class_doc.examples.append(example)

        return class_doc

    def generate_from_module(
        self,
        module: Any,
        include_private: bool = False,
        generate_examples: bool = True,
    ) -> ModuleDoc:
        """
        从模块生成文档

        Args:
            module: 模块对象
            include_private: 是否包含私有成员
            generate_examples: 是否生成示例代码

        Returns:
            ModuleDoc: 模块文档
        """
        name = module.__name__
        docstring = module.__doc__ or ""
        parsed = self.docstring_parser.parse(docstring)

        functions = []
        classes = []
        constants = []

        # 遍历模块成员
        for member_name in dir(module):
            if member_name.startswith("_") and not include_private:
                continue

            member = getattr(module, member_name)

            if inspect.isfunction(member):
                func_doc = self.generate_from_function(
                    member,
                    module_name=name,
                    generate_example=generate_examples,
                )
                functions.append(func_doc)

            elif inspect.isclass(member):
                class_doc = self.generate_from_class(
                    member,
                    module_name=name,
                    generate_example=generate_examples,
                    include_private=include_private,
                )
                classes.append(class_doc)

            elif not callable(member) and not member_name.isupper():
                # 常量
                constants.append(ParameterDoc(
                    name=member_name,
                    type=self.type_inferer._type_to_enum(type(member)),
                ))

        return ModuleDoc(
            name=name,
            description=parsed.get("description", docstring),
            functions=functions,
            classes=classes,
            constants=constants,
        )

    def generate_and_format(
        self,
        obj: Any,
        format_type: DocFormat = DocFormat.MARKDOWN,
        **kwargs: Any,
    ) -> ApiDocResult:
        """
        生成并格式化文档

        Args:
            obj: 要生成文档的对象（函数、类或模块）
            format_type: 输出格式
            **kwargs: 其他参数

        Returns:
            ApiDocResult: 文档生成结果
        """
        doc: ModuleDoc | FunctionDoc | ClassDoc | None = None

        if inspect.isfunction(obj):
            doc = self.generate_from_function(obj, **kwargs)
        elif inspect.isclass(obj):
            doc = self.generate_from_class(obj, **kwargs)
        elif inspect.ismodule(obj):
            doc = self.generate_from_module(obj, **kwargs)

        if doc is None:
            return ApiDocResult(
                format=format_type,
                content="无法生成文档",
            )

        content = self.formatter.format(doc, format_type)

        return ApiDocResult(
            module=doc if isinstance(doc, ModuleDoc) else None,
            format=format_type,
            content=content,
            metadata={
                "name": doc.name,
                "type": type(doc).__name__,
            },
        )


# 便捷函数
_doc_generator: ApiDocGenerator | None = None


def get_doc_generator() -> ApiDocGenerator:
    """获取文档生成器单例"""
    global _doc_generator
    if _doc_generator is None:
        _doc_generator = ApiDocGenerator()
    return _doc_generator


def generate_api_doc(
    obj: Any,
    format_type: DocFormat = DocFormat.MARKDOWN,
    **kwargs: Any,
) -> ApiDocResult:
    """
    生成 API 文档

    Args:
        obj: 要生成文档的对象
        format_type: 输出格式
        **kwargs: 其他参数

    Returns:
        ApiDocResult: 文档生成结果
    """
    return get_doc_generator().generate_and_format(obj, format_type, **kwargs)