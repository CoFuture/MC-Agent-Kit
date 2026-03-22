"""Documentation generation module for MC-Agent-Kit.

This module provides:
- API documentation generation
- Example code generation
- Multi-language support
- Version management
"""

from mc_agent_kit.docs.formatter import (
    DocFormatter,
    FormatterConfig,
    OutputFormat,
    create_formatter,
)
from mc_agent_kit.docs.generator import (
    ApiDoc,
    ApiDocField,
    DocGenerator,
    DocVersion,
    ExampleDoc,
    GeneratorConfig,
    create_doc_generator,
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
