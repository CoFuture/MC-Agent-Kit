"""Configuration template generator for MC-Agent-Kit.

This module provides configuration templates with:
- Template generation
- Field definitions
- Multiple output formats
- Interactive prompts
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TemplateType(Enum):
    """Template type."""
    PROJECT = "project"
    ADDON = "addon"
    LAUNCHER = "launcher"
    KNOWLEDGE = "knowledge"
    CLI = "cli"
    FULL = "full"


@dataclass
class TemplateField:
    """A field in the configuration template."""
    name: str
    label: str = ""
    description: str = ""
    type: type = str
    default: Any = None
    required: bool = True
    choices: list[Any] | None = None
    validation: str | None = None  # regex pattern
    placeholder: str = ""
    group: str = "general"

    def get_label(self) -> str:
        """Get display label."""
        return self.label or self.name.replace("_", " ").title()

    def get_default_display(self) -> str:
        """Get default value display string."""
        if self.default is None:
            return ""
        if isinstance(self.default, bool):
            return "true" if self.default else "false"
        return str(self.default)


@dataclass
class ConfigTemplate:
    """A configuration template."""
    name: str
    type: TemplateType
    description: str = ""
    fields: list[TemplateField] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    version: str = "1.0"

    def get_fields_by_group(self, group: str) -> list[TemplateField]:
        """Get fields in a group.

        Args:
            group: Group name

        Returns:
            List of fields
        """
        return [f for f in self.fields if f.group == group]

    def to_dict(self) -> dict[str, Any]:
        """Convert template to dictionary format.

        Returns:
            Template as dictionary
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "version": self.version,
            "fields": [
                {
                    "name": f.name,
                    "label": f.get_label(),
                    "description": f.description,
                    "type": f.type.__name__,
                    "default": f.default,
                    "required": f.required,
                    "choices": f.choices,
                    "group": f.group,
                }
                for f in self.fields
            ],
            "groups": self.groups,
        }


class TemplateGenerator:
    """Configuration template generator.

    Features:
    - Generate configuration files
    - Multiple output formats
    - Interactive prompts
    - Validation
    """

    def __init__(self) -> None:
        """Initialize template generator."""
        self._templates: dict[str, ConfigTemplate] = {}

        # Register default templates
        for template in get_default_templates():
            self._templates[template.name] = template

    def register_template(self, template: ConfigTemplate) -> None:
        """Register a template.

        Args:
            template: Template to register
        """
        self._templates[template.name] = template

    def get_template(self, name: str) -> ConfigTemplate | None:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            Template or None
        """
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        """List available templates.

        Returns:
            List of template names
        """
        return list(self._templates.keys())

    def generate(
        self,
        template_name: str,
        values: dict[str, Any] | None = None,
        use_defaults: bool = True,
    ) -> dict[str, Any]:
        """Generate configuration from template.

        Args:
            template_name: Template name
            values: Custom values
            use_defaults: Use default values for missing fields

        Returns:
            Generated configuration
        """
        template = self._templates.get(template_name)
        if not template:
            return {}

        result: dict[str, Any] = {}
        values = values or {}

        for field in template.fields:
            if field.name in values:
                result[field.name] = values[field.name]
            elif use_defaults and field.default is not None:
                result[field.name] = field.default

        # Add metadata
        result["_template"] = template_name
        result["_version"] = template.version

        return result

    def generate_json(
        self,
        template_name: str,
        values: dict[str, Any] | None = None,
        indent: int = 2,
    ) -> str:
        """Generate JSON configuration.

        Args:
            template_name: Template name
            values: Custom values
            indent: JSON indentation

        Returns:
            JSON string
        """
        config = self.generate(template_name, values)
        return json.dumps(config, indent=indent)

    def generate_yaml(
        self,
        template_name: str,
        values: dict[str, Any] | None = None,
    ) -> str:
        """Generate YAML configuration.

        Args:
            template_name: Template name
            values: Custom values

        Returns:
            YAML string
        """
        try:
            import yaml
            config = self.generate(template_name, values)
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        except ImportError:
            # Fallback to simple format
            config = self.generate(template_name, values)
            lines = []
            for key, value in config.items():
                if isinstance(value, str):
                    lines.append(f"{key}: '{value}'")
                elif isinstance(value, bool):
                    lines.append(f"{key}: {'true' if value else 'false'}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)

    def generate_markdown(
        self,
        template_name: str,
        include_defaults: bool = True,
    ) -> str:
        """Generate markdown documentation for a template.

        Args:
            template_name: Template name
            include_defaults: Include default values

        Returns:
            Markdown string
        """
        template = self._templates.get(template_name)
        if not template:
            return ""

        lines = [
            f"# {template.name} Configuration",
            "",
            template.description,
            "",
            f"**Version**: {template.version}",
            "",
        ]

        # Group fields
        for group in template.groups or ["general"]:
            group_fields = template.get_fields_by_group(group)
            if group_fields:
                lines.append(f"## {group.title()}")
                lines.append("")
                lines.append("| Field | Type | Required | Default | Description |")
                lines.append("|-------|------|----------|---------|-------------|")

                for f in group_fields:
                    default = f.get_default_display() if include_defaults else "-"
                    required = "Yes" if f.required else "No"
                    lines.append(
                        f"| `{f.name}` | {f.type.__name__} | {required} | {default} | {f.description} |"
                    )

                lines.append("")

        return "\n".join(lines)

    def generate_interactive(
        self,
        template_name: str,
        prompt_func: Callable[[str, Any], Any] | None = None,
    ) -> dict[str, Any]:
        """Generate configuration with interactive prompts.

        Args:
            template_name: Template name
            prompt_func: Custom prompt function

        Returns:
            Generated configuration
        """
        template = self._templates.get(template_name)
        if not template:
            return {}

        values: dict[str, Any] = {}
        def default_prompt(label, default):
            return input(f"{label} [{default}]: ") or default

        prompt = prompt_func or default_prompt

        for field in template.fields:
            label = field.get_label()
            if field.description:
                print(f"  # {field.description}")

            if field.choices:
                print(f"  Choices: {', '.join(map(str, field.choices))}")

            value = prompt(label, field.default)

            # Type coercion
            if field.type == bool:
                if isinstance(value, str):
                    value = value.lower() in ("true", "yes", "1", "y")
            elif field.type == int:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = field.default
            elif field.type == float:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = field.default

            values[field.name] = value

        return self.generate(template_name, values, use_defaults=False)


def get_default_template() -> ConfigTemplate:
    """Get the default configuration template.

    Returns:
        Default template
    """
    return get_default_templates()[0]


def get_default_templates() -> list[ConfigTemplate]:
    """Get all default templates.

    Returns:
        List of default templates
    """
    return [
        ConfigTemplate(
            name="default",
            type=TemplateType.FULL,
            description="Complete MC-Agent-Kit configuration",
            version="1.0",
            groups=["general", "knowledge", "launcher", "cache", "output"],
            fields=[
                # General
                TemplateField(
                    name="debug",
                    label="Debug Mode",
                    description="Enable debug logging",
                    type=bool,
                    default=False,
                    group="general",
                ),
                TemplateField(
                    name="log_level",
                    label="Log Level",
                    description="Logging level",
                    type=str,
                    default="INFO",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    group="general",
                ),

                # Knowledge
                TemplateField(
                    name="knowledge_base_path",
                    label="Knowledge Base Path",
                    description="Path to knowledge base file",
                    type=str,
                    default="data/knowledge_base.json",
                    group="knowledge",
                ),
                TemplateField(
                    name="knowledge_cache_enabled",
                    label="Enable Knowledge Cache",
                    description="Enable knowledge base caching",
                    type=bool,
                    default=True,
                    group="knowledge",
                ),

                # Launcher
                TemplateField(
                    name="game_path",
                    label="Game Path",
                    description="Path to Minecraft game",
                    type=str,
                    required=False,
                    group="launcher",
                ),
                TemplateField(
                    name="log_port",
                    label="Log Port",
                    description="Port for log capture",
                    type=int,
                    default=8080,
                    group="launcher",
                ),
                TemplateField(
                    name="launch_timeout",
                    label="Launch Timeout",
                    description="Game launch timeout in seconds",
                    type=int,
                    default=60,
                    group="launcher",
                ),

                # Cache
                TemplateField(
                    name="cache_enabled",
                    label="Enable Cache",
                    description="Enable caching system",
                    type=bool,
                    default=True,
                    group="cache",
                ),
                TemplateField(
                    name="cache_ttl",
                    label="Cache TTL",
                    description="Cache time-to-live in seconds",
                    type=int,
                    default=3600,
                    group="cache",
                ),
                TemplateField(
                    name="cache_max_size",
                    label="Max Cache Size",
                    description="Maximum cache size in MB",
                    type=int,
                    default=100,
                    group="cache",
                ),

                # Output
                TemplateField(
                    name="output_format",
                    label="Output Format",
                    description="Default output format",
                    type=str,
                    default="text",
                    choices=["text", "json"],
                    group="output",
                ),
                TemplateField(
                    name="color_output",
                    label="Color Output",
                    description="Enable colored terminal output",
                    type=bool,
                    default=True,
                    group="output",
                ),
            ],
        ),

        ConfigTemplate(
            name="minimal",
            type=TemplateType.CLI,
            description="Minimal CLI configuration",
            version="1.0",
            fields=[
                TemplateField(
                    name="debug",
                    type=bool,
                    default=False,
                ),
                TemplateField(
                    name="output_format",
                    type=str,
                    default="text",
                    choices=["text", "json"],
                ),
            ],
        ),

        ConfigTemplate(
            name="launcher",
            type=TemplateType.LAUNCHER,
            description="Launcher-specific configuration",
            version="1.0",
            groups=["paths", "settings"],
            fields=[
                TemplateField(
                    name="game_path",
                    description="Path to Minecraft executable",
                    type=str,
                    required=False,
                    group="paths",
                ),
                TemplateField(
                    name="addons_path",
                    description="Path to addons directory",
                    type=str,
                    default="addons",
                    group="paths",
                ),
                TemplateField(
                    name="log_port",
                    description="Port for log capture",
                    type=int,
                    default=8080,
                    group="settings",
                ),
                TemplateField(
                    name="auto_start_log_server",
                    description="Automatically start log server",
                    type=bool,
                    default=True,
                    group="settings",
                ),
            ],
        ),
    ]


def create_template_generator() -> TemplateGenerator:
    """Create a template generator.

    Returns:
        TemplateGenerator instance
    """
    return TemplateGenerator()
