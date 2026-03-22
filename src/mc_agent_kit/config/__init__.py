"""Configuration management module for MC-Agent-Kit.

This module provides:
- Configuration file management
- Template generation
- Validation and migration
- Environment variable support
- Hot reload
"""

from mc_agent_kit.config.manager import (
    ConfigManager,
    ConfigSource,
    ConfigValue,
    ManagerConfig,
    create_config_manager,
)
from mc_agent_kit.config.validator import (
    ConfigValidator,
    ValidationResult,
    ValidationError,
    ValidationWarning,
    ValidationLevel,
    SchemaField,
    ConfigSchema,
    create_validator,
    get_default_schema,
)
from mc_agent_kit.config.templates import (
    ConfigTemplate,
    TemplateGenerator,
    TemplateField,
    TemplateType,
    create_template_generator,
    get_default_template,
)

__all__ = [
    # Manager
    "ConfigManager",
    "ConfigSource",
    "ConfigValue",
    "ManagerConfig",
    "create_config_manager",
    # Validator
    "ConfigValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "ValidationLevel",
    "SchemaField",
    "ConfigSchema",
    "create_validator",
    "get_default_schema",
    # Templates
    "ConfigTemplate",
    "TemplateGenerator",
    "TemplateField",
    "TemplateType",
    "create_template_generator",
    "get_default_template",
]