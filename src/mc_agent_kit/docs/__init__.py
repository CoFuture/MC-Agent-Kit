"""Documentation generation module for MC-Agent-Kit.

This module provides:
- API documentation generation
- Example code generation
- Multi-language support
- Version management
- Documentation templates
- Code examples library
"""

from mc_agent_kit.docs.examples import (
    ExampleCategory,
    CodeExample,
    get_examples_by_category,
    get_all_examples,
    get_example_by_name,
    search_examples,
    BASIC_EXAMPLES,
    ENTITY_EXAMPLES,
    UI_EXAMPLES,
    PERFORMANCE_EXAMPLES,
)
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
from mc_agent_kit.docs.templates import (
    TemplateType,
    DocTemplate,
    get_template,
    render_template,
    create_api_doc,
    create_user_guide,
    create_example_doc,
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
    # Templates
    "TemplateType",
    "DocTemplate",
    "get_template",
    "render_template",
    "create_api_doc",
    "create_user_guide",
    "create_example_doc",
    # Examples
    "ExampleCategory",
    "CodeExample",
    "get_examples_by_category",
    "get_all_examples",
    "get_example_by_name",
    "search_examples",
    "BASIC_EXAMPLES",
    "ENTITY_EXAMPLES",
    "UI_EXAMPLES",
    "PERFORMANCE_EXAMPLES",
]
