"""Documentation generator for MC-Agent-Kit.

This module generates documentation from code and templates:
- API documentation
- Example code
- Version management
- Multi-language support
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import ast
import inspect
import re


class DocLanguage(Enum):
    """Supported documentation languages."""
    EN = "en"
    ZH_CN = "zh_CN"


@dataclass
class ApiDocField:
    """A field in API documentation."""
    name: str
    type: str = ""
    description: str = ""
    default: str | None = None
    required: bool = True


@dataclass
class ApiDoc:
    """API documentation entry."""
    name: str
    module: str = ""
    description: str = ""
    parameters: list[ApiDocField] = field(default_factory=list)
    returns: ApiDocField | None = None
    raises: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    deprecated: bool = False
    deprecation_message: str = ""
    version_added: str = ""
    version_changed: dict[str, str] = field(default_factory=dict)


@dataclass
class ExampleDoc:
    """Example documentation."""
    title: str
    description: str = ""
    code: str = ""
    language: str = "python"
    output: str = ""
    tags: list[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    time_estimate: str = ""


@dataclass
class DocVersion:
    """Documentation version info."""
    version: str
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    changes: list[str] = field(default_factory=list)
    author: str = ""


@dataclass
class GeneratorConfig:
    """Configuration for documentation generator."""
    output_dir: str = "docs/api"
    language: DocLanguage = DocLanguage.EN
    version: str = "1.0"
    include_private: bool = False
    include_deprecated: bool = True
    generate_examples: bool = True
    generate_toc: bool = True
    template_dir: str | None = None


class DocGenerator:
    """Documentation generator.

    Features:
    - Generate API docs from code
    - Generate examples from templates
    - Version management
    - Multi-language support
    """

    def __init__(self, config: GeneratorConfig | None = None):
        """Initialize generator.

        Args:
            config: Generator configuration
        """
        self.config = config or GeneratorConfig()
        self._api_docs: dict[str, ApiDoc] = {}
        self._examples: list[ExampleDoc] = []
        self._version = DocVersion(version=self.config.version)

    def register_api(self, doc: ApiDoc) -> None:
        """Register API documentation.

        Args:
            doc: API documentation
        """
        self._api_docs[doc.name] = doc

    def register_example(self, example: ExampleDoc) -> None:
        """Register example documentation.

        Args:
            example: Example documentation
        """
        self._examples.append(example)

    def from_function(
        self,
        func: Callable,
        module: str = "",
    ) -> ApiDoc | None:
        """Generate API doc from function.

        Args:
            func: Function to document
            module: Module name

        Returns:
            Generated ApiDoc
        """
        try:
            # Get docstring
            docstring = inspect.getdoc(func) or ""

            # Parse docstring
            description, params, returns, raises = self._parse_docstring(docstring)

            # Get signature
            sig = inspect.signature(func)

            # Build parameters
            parameters = []
            for name, param in sig.parameters.items():
                if name == "self":
                    continue

                param_doc = ApiDocField(name=name)

                # Type annotation
                if param.annotation != inspect.Parameter.empty:
                    param_doc.type = self._format_type(param.annotation)

                # Default value
                if param.default != inspect.Parameter.empty:
                    param_doc.default = repr(param.default)
                    param_doc.required = False

                # Description from docstring
                if name in params:
                    param_doc.description = params[name]

                parameters.append(param_doc)

            # Return type
            returns_doc = None
            if sig.return_annotation != inspect.Signature.empty:
                returns_doc = ApiDocField(
                    name="returns",
                    type=self._format_type(sig.return_annotation),
                    description=returns,
                )

            return ApiDoc(
                name=func.__name__,
                module=module,
                description=description,
                parameters=parameters,
                returns=returns_doc,
                raises=list(raises),
            )
        except Exception:
            return None

    def from_class(
        self,
        cls: type,
        module: str = "",
    ) -> list[ApiDoc]:
        """Generate API docs from class.

        Args:
            cls: Class to document
            module: Module name

        Returns:
            List of generated ApiDocs (class + methods)
        """
        docs = []

        # Class doc
        class_doc = ApiDoc(
            name=cls.__name__,
            module=module,
            description=inspect.getdoc(cls) or "",
        )

        # Get methods
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("_") and not self.config.include_private:
                continue

            method_doc = self.from_function(method, f"{module}.{cls.__name__}")
            if method_doc:
                docs.append(method_doc)

        docs.insert(0, class_doc)
        return docs

    def _parse_docstring(
        self,
        docstring: str,
    ) -> tuple[str, dict[str, str], str, list[str]]:
        """Parse docstring for components.

        Args:
            docstring: Docstring to parse

        Returns:
            Tuple of (description, params, returns, raises)
        """
        description = ""
        params: dict[str, str] = {}
        returns = ""
        raises: list[str] = []

        if not docstring:
            return description, params, returns, raises

        lines = docstring.split("\n")
        current_section = "description"
        current_param = ""

        for line in lines:
            stripped = line.strip()

            # Section headers
            if stripped.lower().startswith(("args:", "arguments:", "parameters:")):
                current_section = "params"
                continue
            elif stripped.lower().startswith(("returns:", "return:")):
                current_section = "returns"
                continue
            elif stripped.lower().startswith(("raises:", "raise:")):
                current_section = "raises"
                continue
            elif stripped.lower().startswith(("example:", "examples:")):
                current_section = "examples"
                continue

            # Parse sections
            if current_section == "description":
                if description:
                    description += " "
                description += stripped
            elif current_section == "params":
                # Parse "param_name (type): description"
                match = re.match(r"(\w+)\s*(?:\([^)]*\))?\s*:\s*(.+)", stripped)
                if match:
                    current_param = match.group(1)
                    params[current_param] = match.group(2)
                elif current_param and stripped:
                    params[current_param] += " " + stripped
            elif current_section == "returns":
                if returns:
                    returns += " "
                returns += stripped
            elif current_section == "raises":
                # Parse "ExceptionType: description"
                match = re.match(r"(\w+):\s*(.+)", stripped)
                if match:
                    raises.append(f"{match.group(1)}: {match.group(2)}")

        return description, params, returns, raises

    def _format_type(self, type_hint: Any) -> str:
        """Format type hint to string.

        Args:
            type_hint: Type annotation

        Returns:
            Formatted type string
        """
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__

        # Handle generic types
        origin = getattr(type_hint, "__origin__", None)
        if origin:
            args = getattr(type_hint, "__args__", ())
            if args:
                args_str = ", ".join(self._format_type(a) for a in args)
                origin_name = getattr(origin, "__name__", str(origin))
                return f"{origin_name}[{args_str}]"

        return str(type_hint)

    def generate_markdown(
        self,
        output_path: str | None = None,
    ) -> str:
        """Generate markdown documentation.

        Args:
            output_path: Optional path to write output

        Returns:
            Generated markdown
        """
        lines = [
            f"# API Documentation",
            "",
            f"Version: {self._version.version}",
            "",
            "---",
            "",
        ]

        # Table of contents
        if self.config.generate_toc:
            lines.append("## Table of Contents")
            lines.append("")
            for name in sorted(self._api_docs.keys()):
                anchor = name.lower().replace(".", "-")
                lines.append(f"- [{name}](#{anchor})")
            lines.append("")
            lines.append("---")
            lines.append("")

        # API documentation
        for name in sorted(self._api_docs.keys()):
            doc = self._api_docs[name]
            lines.extend(self._api_to_markdown(doc))

        # Examples
        if self._examples:
            lines.append("## Examples")
            lines.append("")
            for example in self._examples:
                lines.extend(self._example_to_markdown(example))

        result = "\n".join(lines)

        # Write to file
        if output_path:
            Path(output_path).write_text(result, encoding="utf-8")

        return result

    def _api_to_markdown(self, doc: ApiDoc) -> list[str]:
        """Convert API doc to markdown lines."""
        lines = [f"### {doc.name}", ""]

        if doc.deprecated:
            lines.append("> **Deprecated**: " + doc.deprecation_message)
            lines.append("")

        if doc.module:
            lines.append(f"**Module**: `{doc.module}`")
            lines.append("")

        lines.append(doc.description)
        lines.append("")

        if doc.parameters:
            lines.append("**Parameters:**")
            lines.append("")
            lines.append("| Name | Type | Required | Default | Description |")
            lines.append("|------|------|----------|---------|-------------|")
            for p in doc.parameters:
                default = p.default or "-"
                required = "Yes" if p.required else "No"
                lines.append(
                    f"| `{p.name}` | `{p.type}` | {required} | {default} | {p.description} |"
                )
            lines.append("")

        if doc.returns:
            lines.append("**Returns:**")
            lines.append("")
            lines.append(f"- `{doc.returns.type}`: {doc.returns.description}")
            lines.append("")

        if doc.raises:
            lines.append("**Raises:**")
            lines.append("")
            for r in doc.raises:
                lines.append(f"- {r}")
            lines.append("")

        if doc.examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in doc.examples:
                lines.append("```python")
                lines.append(example)
                lines.append("```")
                lines.append("")

        return lines

    def _example_to_markdown(self, example: ExampleDoc) -> list[str]:
        """Convert example to markdown lines."""
        lines = [f"### {example.title}", ""]

        if example.description:
            lines.append(example.description)
            lines.append("")

        if example.code:
            lines.append(f"```{example.language}")
            lines.append(example.code)
            lines.append("```")
            lines.append("")

        if example.output:
            lines.append("**Output:**")
            lines.append("```")
            lines.append(example.output)
            lines.append("```")
            lines.append("")

        return lines

    def generate_json(self) -> str:
        """Generate JSON documentation.

        Returns:
            JSON string
        """
        import json

        data = {
            "version": self._version.version,
            "generated": self._version.date,
            "apis": {
                name: {
                    "name": doc.name,
                    "module": doc.module,
                    "description": doc.description,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "description": p.description,
                            "default": p.default,
                            "required": p.required,
                        }
                        for p in doc.parameters
                    ],
                    "returns": {
                        "type": doc.returns.type,
                        "description": doc.returns.description,
                    } if doc.returns else None,
                    "raises": doc.raises,
                    "examples": doc.examples,
                    "deprecated": doc.deprecated,
                }
                for name, doc in self._api_docs.items()
            },
            "examples": [
                {
                    "title": e.title,
                    "description": e.description,
                    "code": e.code,
                    "language": e.language,
                    "output": e.output,
                    "tags": e.tags,
                    "difficulty": e.difficulty,
                }
                for e in self._examples
            ],
        }

        return json.dumps(data, indent=2)


def create_doc_generator(config: GeneratorConfig | None = None) -> DocGenerator:
    """Create a documentation generator.

    Args:
        config: Generator configuration

    Returns:
        DocGenerator instance
    """
    return DocGenerator(config)