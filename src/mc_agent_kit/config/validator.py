"""Configuration validator for MC-Agent-Kit.

This module provides configuration validation with:
- Schema-based validation
- Custom validation rules
- Migration support
- Detailed error messages
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationLevel(Enum):
    """Validation message level."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """A validation error."""
    key: str
    message: str
    level: ValidationLevel = ValidationLevel.ERROR
    suggestion: str = ""
    value: Any = None
    expected: str = ""


@dataclass
class ValidationWarning:
    """A validation warning."""
    key: str
    message: str
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Result of validation."""
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if there are errors."""
        return any(e.level == ValidationLevel.ERROR for e in self.errors)

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0

    def add_error(
        self,
        key: str,
        message: str,
        suggestion: str = "",
        value: Any = None,
        expected: str = "",
    ) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(
            key=key,
            message=message,
            suggestion=suggestion,
            value=value,
            expected=expected,
        ))
        self.valid = False

    def add_warning(self, key: str, message: str, suggestion: str = "") -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationWarning(
            key=key,
            message=message,
            suggestion=suggestion,
        ))

    def merge(self, other: ValidationResult) -> None:
        """Merge another result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.valid:
            self.valid = False


@dataclass
class SchemaField:
    """A field in the configuration schema."""
    name: str
    type: type | tuple[type, ...] = str
    required: bool = False
    default: Any = None
    description: str = ""
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[Any] | None = None
    custom_validator: Callable[[Any], bool] | None = None
    custom_message: str = ""
    deprecated: bool = False
    replacement: str = ""

    def validate(self, value: Any) -> ValidationResult:
        """Validate a value against this field.

        Args:
            value: Value to validate

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Check required
        if value is None:
            if self.required:
                result.add_error(
                    key=self.name,
                    message=f"Required field '{self.name}' is missing",
                    suggestion="Add this field to your configuration",
                )
            return result

        # Check type
        if not isinstance(value, self.type):
            type_name = getattr(self.type, "__name__", str(self.type))
            result.add_error(
                key=self.name,
                message=f"Invalid type for '{self.name}': expected {type_name}",
                value=repr(value),
                expected=type_name,
            )
            return result

        # Check min/max value
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                result.add_error(
                    key=self.name,
                    message=f"Value for '{self.name}' is below minimum",
                    value=value,
                    expected=f">= {self.min_value}",
                )
            if self.max_value is not None and value > self.max_value:
                result.add_error(
                    key=self.name,
                    message=f"Value for '{self.name}' exceeds maximum",
                    value=value,
                    expected=f"<= {self.max_value}",
                )

        # Check min/max length
        if isinstance(value, (str, list, dict)):
            length = len(value)
            if self.min_length is not None and length < self.min_length:
                result.add_error(
                    key=self.name,
                    message=f"Length of '{self.name}' is below minimum",
                    value=length,
                    expected=f">= {self.min_length}",
                )
            if self.max_length is not None and length > self.max_length:
                result.add_error(
                    key=self.name,
                    message=f"Length of '{self.name}' exceeds maximum",
                    value=length,
                    expected=f"<= {self.max_length}",
                )

        # Check pattern
        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value):
                result.add_error(
                    key=self.name,
                    message=f"Value for '{self.name}' doesn't match pattern",
                    value=value,
                    expected=self.pattern,
                )

        # Check enum
        if self.enum is not None and value not in self.enum:
            result.add_error(
                key=self.name,
                message=f"Invalid value for '{self.name}'",
                value=value,
                expected=f"one of: {', '.join(map(str, self.enum))}",
            )

        # Custom validator
        if self.custom_validator and not self.custom_validator(value):
            message = self.custom_message or f"Invalid value for '{self.name}'"
            result.add_error(
                key=self.name,
                message=message,
                value=value,
            )

        # Deprecated warning
        if self.deprecated:
            suggestion = f"Use '{self.replacement}' instead" if self.replacement else "This field will be removed"
            result.add_warning(
                key=self.name,
                message=f"Field '{self.name}' is deprecated",
                suggestion=suggestion,
            )

        return result


@dataclass
class ConfigSchema:
    """Configuration schema definition."""
    name: str
    version: str = "1.0"
    description: str = ""
    fields: list[SchemaField] = field(default_factory=list)

    def get_field(self, name: str) -> SchemaField | None:
        """Get a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def validate(self, config: dict[str, Any]) -> ValidationResult:
        """Validate a configuration.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Validate each field
        for field in self.fields:
            value = config.get(field.name)
            field_result = field.validate(value)
            result.merge(field_result)

        # Check for unknown fields
        known_fields = {f.name for f in self.fields}
        for key in config:
            if key not in known_fields:
                result.add_warning(
                    key=key,
                    message=f"Unknown field '{key}'",
                    suggestion="Check for typos or remove this field",
                )

        return result


class ConfigValidator:
    """Configuration validator.

    Features:
    - Schema-based validation
    - Custom validation rules
    - Migration support
    - Detailed error messages
    """

    def __init__(self) -> None:
        """Initialize validator."""
        self._schemas: dict[str, ConfigSchema] = {}
        self._migrations: dict[str, list[Callable[[dict], dict]]] = {}

        # Register default schema
        self.register_schema(get_default_schema())

    def register_schema(self, schema: ConfigSchema) -> None:
        """Register a configuration schema.

        Args:
            schema: Schema to register
        """
        self._schemas[schema.name] = schema

    def get_schema(self, name: str) -> ConfigSchema | None:
        """Get a registered schema.

        Args:
            name: Schema name

        Returns:
            Schema or None
        """
        return self._schemas.get(name)

    def validate(
        self,
        config: dict[str, Any],
        schema_name: str = "default",
    ) -> ValidationResult:
        """Validate configuration against a schema.

        Args:
            config: Configuration dictionary
            schema_name: Schema name

        Returns:
            ValidationResult
        """
        schema = self._schemas.get(schema_name)
        if not schema:
            result = ValidationResult(valid=False)
            result.add_error(
                key="",
                message=f"Unknown schema: {schema_name}",
            )
            return result

        return schema.validate(config)

    def register_migration(
        self,
        schema_name: str,
        from_version: str,
        migrator: Callable[[dict], dict],
    ) -> None:
        """Register a migration function.

        Args:
            schema_name: Schema name
            from_version: Version to migrate from
            migrator: Migration function
        """
        key = f"{schema_name}:{from_version}"
        if key not in self._migrations:
            self._migrations[key] = []
        self._migrations[key].append(migrator)

    def migrate(
        self,
        config: dict[str, Any],
        schema_name: str = "default",
    ) -> dict[str, Any]:
        """Migrate configuration to latest version.

        Args:
            config: Configuration dictionary
            schema_name: Schema name

        Returns:
            Migrated configuration
        """
        version = config.get("version", "1.0")
        result = config.copy()

        while True:
            key = f"{schema_name}:{version}"
            migrators = self._migrations.get(key, [])

            if not migrators:
                break

            for migrator in migrators:
                result = migrator(result)

            # Update version after migration
            if "version" in result:
                version = result["version"]
            else:
                break

        return result

    def apply_defaults(
        self,
        config: dict[str, Any],
        schema_name: str = "default",
    ) -> dict[str, Any]:
        """Apply schema defaults to configuration.

        Args:
            config: Configuration dictionary
            schema_name: Schema name

        Returns:
            Configuration with defaults applied
        """
        schema = self._schemas.get(schema_name)
        if not schema:
            return config

        result = config.copy()
        for field in schema.fields:
            if field.name not in result and field.default is not None:
                result[field.name] = field.default

        return result


def get_default_schema() -> ConfigSchema:
    """Get the default MC-Agent-Kit configuration schema.

    Returns:
        Default schema
    """
    return ConfigSchema(
        name="default",
        version="1.0",
        description="MC-Agent-Kit default configuration",
        fields=[
            SchemaField(
                name="knowledge_base_path",
                type=str,
                required=False,
                default="data/knowledge_base.json",
                description="Path to knowledge base file",
            ),
            SchemaField(
                name="game_path",
                type=str,
                required=False,
                description="Path to Minecraft game executable",
            ),
            SchemaField(
                name="log_port",
                type=int,
                required=False,
                default=8080,
                min_value=1024,
                max_value=65535,
                description="Port for log capture server",
            ),
            SchemaField(
                name="cache_enabled",
                type=bool,
                required=False,
                default=True,
                description="Enable caching",
            ),
            SchemaField(
                name="cache_ttl",
                type=int,
                required=False,
                default=3600,
                min_value=0,
                description="Cache TTL in seconds",
            ),
            SchemaField(
                name="debug",
                type=bool,
                required=False,
                default=False,
                description="Enable debug mode",
            ),
            SchemaField(
                name="output_format",
                type=str,
                required=False,
                default="text",
                enum=["text", "json"],
                description="Output format",
            ),
            SchemaField(
                name="color_output",
                type=bool,
                required=False,
                default=True,
                description="Enable colored output",
            ),
        ],
    )


def create_validator() -> ConfigValidator:
    """Create a configuration validator.

    Returns:
        ConfigValidator instance
    """
    return ConfigValidator()
