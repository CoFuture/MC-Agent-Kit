"""Documentation generation module for MC-Agent-Kit.

This module provides:
- API documentation generation
- Example code generation
- Multi-language support
- Version management
"""

from mc_agent_kit.docs.generator import (
    DocGenerator,
    GeneratorConfig,
    ApiDoc,
    ApiDocField,
    ExampleDoc,
    DocVersion,
    create_doc_generator,
)
from mc_agent_kit.docs.formatter import (
    DocFormatter,
    FormatterConfig,
    OutputFormat,
    create_formatter,
)

__all__ = [
    # Generator
    "DocGenerator",
    "GeneratorConfig",
    "ApiDoc",
    "ApiDocField",
    "ExampleDoc",
    "DocVersion",
    "create_doc_generator",
    # Formatter
    "DocFormatter",
    "FormatterConfig",
    "OutputFormat",
    "create_formatter",
]