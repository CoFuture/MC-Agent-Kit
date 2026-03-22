"""Code generation plugin for MC-Agent-Kit.

This plugin demonstrates how to create a plugin that generates
code snippets and templates for various purposes.

Features:
- Generate boilerplate code
- Create code from templates
- Support multiple output styles
- Configurable code style options
"""

import logging
from datetime import datetime
from typing import Any

from mc_agent_kit.plugin import PluginBase, PluginResult

logger = logging.getLogger(__name__)


class CodegenPlugin(PluginBase):
    """Code generation plugin.

    Provides code generation capabilities through templates and snippets.

    Example:
        >>> plugin = CodegenPlugin()
        >>> result = plugin.execute("generate", template="class", name="MyClass")
        >>> print(result.data["code"])
    """

    def __init__(self) -> None:
        """Initialize codegen plugin."""
        self._default_style = "pep8"
        self._add_docstrings = True
        self._add_type_hints = True

    def set_config(self, config: dict[str, Any]) -> None:
        """Set plugin configuration.

        Args:
            config: Configuration dictionary
        """
        self._default_style = config.get("default_style", self._default_style)
        self._add_docstrings = config.get("add_docstrings", self._add_docstrings)
        self._add_type_hints = config.get("add_type_hints", self._add_type_hints)

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info("Codegen plugin loaded")

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        logger.info("Codegen plugin enabled")

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        logger.info("Codegen plugin disabled")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info("Codegen plugin unloaded")

    def execute(self, action: str = "generate", **kwargs: Any) -> PluginResult:
        """Execute plugin action.

        Args:
            action: Action to perform:
                - "generate": Generate code from template
                - "list": List available templates
                - "snippet": Generate a code snippet
                - "help": Get help information
            **kwargs: Action-specific arguments

        Returns:
            PluginResult with generated code
        """
        try:
            if action == "generate":
                return self._generate(kwargs)
            elif action == "list":
                return self._list_templates()
            elif action == "snippet":
                return self._generate_snippet(kwargs)
            elif action == "help":
                return self._get_help()
            else:
                return PluginResult(
                    success=False,
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            logger.error("Error executing codegen action: %s", e)
            return PluginResult(success=False, error=str(e))

    def _generate(self, kwargs: dict[str, Any]) -> PluginResult:
        """Generate code from template.

        Args:
            kwargs: Template parameters

        Returns:
            PluginResult with generated code
        """
        template = kwargs.get("template")
        if not template:
            return PluginResult(
                success=False,
                error="Template name is required",
            )

        generators = {
            "class": self._generate_class,
            "function": self._generate_function,
            "dataclass": self._generate_dataclass,
            "enum": self._generate_enum,
            "unittest": self._generate_unittest,
        }

        generator = generators.get(template)
        if not generator:
            return PluginResult(
                success=False,
                error=f"Unknown template: {template}. Available: {list(generators.keys())}",
            )

        code = generator(kwargs)
        return PluginResult(
            success=True,
            data={
                "code": code,
                "template": template,
                "generated_at": datetime.now().isoformat(),
            },
        )

    def _generate_class(self, kwargs: dict[str, Any]) -> str:
        """Generate class template.

        Args:
            kwargs: Class parameters

        Returns:
            Generated class code
        """
        name = kwargs.get("name", "MyClass")
        base = kwargs.get("base", "")
        methods = kwargs.get("methods", [])
        attributes = kwargs.get("attributes", [])

        lines = []

        # Class docstring
        if self._add_docstrings:
            lines.append(f'"""{name} class."""')
            lines.append("")

        # Class definition
        if base:
            lines.append(f"class {name}({base}):")
        else:
            lines.append(f"class {name}:")

        # Class docstring
        if self._add_docstrings:
            lines.append(f'    """{name} class."""')
            lines.append("")

        # __init__ method
        init_params = []
        init_body = []
        for attr in attributes:
            attr_name = attr.get("name", "attr")
            attr_type = attr.get("type", "Any")
            attr_default = attr.get("default")

            if self._add_type_hints:
                if attr_default is not None:
                    init_params.append(f"{attr_name}: {attr_type} = {attr_default}")
                else:
                    init_params.append(f"{attr_name}: {attr_type}")
            else:
                if attr_default is not None:
                    init_params.append(f"{attr_name}={attr_default}")
                else:
                    init_params.append(attr_name)

            init_body.append(f"        self.{attr_name} = {attr_name}")

        if init_params:
            lines.append(f"    def __init__(self, {', '.join(init_params)}):")
            if self._add_docstrings:
                lines.append('        """Initialize instance."""')
            lines.append("        pass")
            for line in init_body:
                lines.append(line)
        else:
            lines.append("    def __init__(self):")
            if self._add_docstrings:
                lines.append('        """Initialize instance."""')
            lines.append("        pass")

        # Additional methods
        for method in methods:
            method_name = method.get("name", "method")
            method_params = method.get("params", [])
            method_return = method.get("return", "None")

            lines.append("")
            if self._add_type_hints:
                params_str = ", ".join(["self"] + method_params)
                lines.append(f"    def {method_name}({params_str}) -> {method_return}:")
            else:
                params_str = ", ".join(["self"] + [p.split(":")[0] for p in method_params])
                lines.append(f"    def {method_name}({params_str}):")

            if self._add_docstrings:
                lines.append(f'        """{method_name} method."""')
            lines.append("        pass")

        if not methods and not attributes:
            lines.append("    pass")

        return "\n".join(lines)

    def _generate_function(self, kwargs: dict[str, Any]) -> str:
        """Generate function template.

        Args:
            kwargs: Function parameters

        Returns:
            Generated function code
        """
        name = kwargs.get("name", "my_function")
        params = kwargs.get("params", [])
        return_type = kwargs.get("return", "None")
        body = kwargs.get("body", "pass")

        lines = []

        if self._add_docstrings:
            lines.append(f'"""{name} function."""')
            lines.append("")

        if self._add_type_hints:
            params_str = ", ".join(params) if params else ""
            lines.append(f"def {name}({params_str}) -> {return_type}:")
        else:
            param_names = [p.split(":")[0] for p in params] if params else []
            lines.append(f"def {name}({', '.join(param_names)}):")

        if self._add_docstrings:
            lines.append(f'    """{name} function."""')

        lines.append(f"    {body}")

        return "\n".join(lines)

    def _generate_dataclass(self, kwargs: dict[str, Any]) -> str:
        """Generate dataclass template.

        Args:
            kwargs: Dataclass parameters

        Returns:
            Generated dataclass code
        """
        name = kwargs.get("name", "MyData")
        fields = kwargs.get("fields", [])
        frozen = kwargs.get("frozen", False)

        lines = []
        lines.append("from dataclasses import dataclass")
        lines.append("")

        if self._add_docstrings:
            lines.append(f'"""{name} dataclass."""')
            lines.append("")

        # Decorator
        if frozen:
            lines.append("@dataclass(frozen=True)")
        else:
            lines.append("@dataclass")

        lines.append(f"class {name}:")

        if self._add_docstrings:
            lines.append(f'    """{name} dataclass."""')
            lines.append("")

        if not fields:
            lines.append("    pass")
        else:
            for field in fields:
                field_name = field.get("name", "field")
                field_type = field.get("type", "Any")
                field_default = field.get("default")

                if self._add_type_hints:
                    if field_default is not None:
                        lines.append(f"    {field_name}: {field_type} = {field_default}")
                    else:
                        lines.append(f"    {field_name}: {field_type}")
                else:
                    lines.append(f"    {field_name} = {field_default or 'None'}")

        return "\n".join(lines)

    def _generate_enum(self, kwargs: dict[str, Any]) -> str:
        """Generate enum template.

        Args:
            kwargs: Enum parameters

        Returns:
            Generated enum code
        """
        name = kwargs.get("name", "MyEnum")
        values = kwargs.get("values", ["VALUE1", "VALUE2"])

        lines = []
        lines.append("from enum import Enum, auto")
        lines.append("")

        if self._add_docstrings:
            lines.append(f'"""{name} enum."""')
            lines.append("")

        lines.append(f"class {name}(Enum):")

        if self._add_docstrings:
            lines.append(f'    """{name} enumeration."""')
            lines.append("")

        for value in values:
            if isinstance(value, dict):
                key = value.get("name", "VALUE")
                val = value.get("value", "auto()")
                lines.append(f"    {key} = {val}")
            else:
                lines.append(f"    {value} = auto()")

        return "\n".join(lines)

    def _generate_unittest(self, kwargs: dict[str, Any]) -> str:
        """Generate unittest template.

        Args:
            kwargs: Test parameters

        Returns:
            Generated unittest code
        """
        test_class = kwargs.get("test_class", "MyClass")
        test_methods = kwargs.get("methods", ["test_method"])

        lines = []
        lines.append("import unittest")
        lines.append("")

        if self._add_docstrings:
            lines.append(f'"""Tests for {test_class}."""')
            lines.append("")

        lines.append(f"class Test{test_class}(unittest.TestCase):")

        if self._add_docstrings:
            lines.append(f'    """Test cases for {test_class}."""')
            lines.append("")

        for method in test_methods:
            if isinstance(method, dict):
                method_name = method.get("name", "test_method")
            else:
                method_name = method if method.startswith("test_") else f"test_{method}"

            lines.append(f"    def {method_name}(self):")
            if self._add_docstrings:
                lines.append(f'        """Test {method_name}."""')
            lines.append("        # TODO: Implement test")
            lines.append("        pass")
            lines.append("")

        lines.append("")
        lines.append('if __name__ == "__main__":')
        lines.append("    unittest.main()")

        return "\n".join(lines)

    def _list_templates(self) -> PluginResult:
        """List available templates.

        Returns:
            PluginResult with template list
        """
        templates = [
            {
                "name": "class",
                "description": "Generate a Python class",
                "params": {
                    "name": "Class name (required)",
                    "base": "Base class (optional)",
                    "methods": "List of methods (optional)",
                    "attributes": "List of attributes (optional)",
                },
            },
            {
                "name": "function",
                "description": "Generate a Python function",
                "params": {
                    "name": "Function name (required)",
                    "params": "Parameter list (optional)",
                    "return": "Return type (optional)",
                    "body": "Function body (optional)",
                },
            },
            {
                "name": "dataclass",
                "description": "Generate a Python dataclass",
                "params": {
                    "name": "Dataclass name (required)",
                    "fields": "List of fields (optional)",
                    "frozen": "Make frozen dataclass (optional)",
                },
            },
            {
                "name": "enum",
                "description": "Generate a Python enum",
                "params": {
                    "name": "Enum name (required)",
                    "values": "List of values (optional)",
                },
            },
            {
                "name": "unittest",
                "description": "Generate a unittest test class",
                "params": {
                    "test_class": "Class to test (required)",
                    "methods": "List of test methods (optional)",
                },
            },
        ]

        return PluginResult(
            success=True,
            data={"templates": templates},
        )

    def _generate_snippet(self, kwargs: dict[str, Any]) -> PluginResult:
        """Generate a code snippet.

        Args:
            kwargs: Snippet parameters

        Returns:
            PluginResult with snippet code
        """
        snippet_type = kwargs.get("type", "print")
        name = kwargs.get("name", "value")

        snippets = {
            "print": f'print(f"{{{name}}} = {{{name}}}")',
            "log_debug": f'logger.debug("{name} = %s", {name})',
            "log_info": f'logger.info("{name} = %s", {name})',
            "try_except": f'''try:
    # TODO: Add code
    pass
except Exception as e:
    logger.error("Error: %s", e)''',
            "if_name_main": '''if __name__ == "__main__":
    # TODO: Add main code
    pass''',
        }

        code = snippets.get(snippet_type)
        if not code:
            return PluginResult(
                success=False,
                error=f"Unknown snippet type: {snippet_type}. Available: {list(snippets.keys())}",
            )

        return PluginResult(
            success=True,
            data={
                "code": code,
                "type": snippet_type,
            },
        )

    def _get_help(self) -> PluginResult:
        """Get help information.

        Returns:
            PluginResult with help text
        """
        return PluginResult(
            success=True,
            data={
                "description": "Code generation plugin for MC-Agent-Kit",
                "actions": [
                    {
                        "name": "generate",
                        "description": "Generate code from template",
                        "params": {
                            "template": "Template name (required)",
                        },
                    },
                    {
                        "name": "list",
                        "description": "List available templates",
                        "params": {},
                    },
                    {
                        "name": "snippet",
                        "description": "Generate a code snippet",
                        "params": {
                            "type": "Snippet type (required)",
                        },
                    },
                    {
                        "name": "help",
                        "description": "Show this help",
                        "params": {},
                    },
                ],
                "config": {
                    "default_style": "Code style (default: pep8)",
                    "add_docstrings": "Add docstrings (default: true)",
                    "add_type_hints": "Add type hints (default: true)",
                },
            },
        )


# Plugin entry point
def create_plugin() -> CodegenPlugin:
    """Create plugin instance.

    Returns:
        CodegenPlugin instance
    """
    return CodegenPlugin()