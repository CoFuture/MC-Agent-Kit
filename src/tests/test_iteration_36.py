"""Tests for iteration #36 - CLI enhancement and user experience optimization.

This test file covers:
- CLI REPL functionality
- Command history
- Colored output and progress bars
- Command aliases
- Configuration management
- Configuration validation
- Configuration templates
- Documentation generation
"""

import pytest
from pathlib import Path
import tempfile
import os
import sys

# Import CLI modules
from mc_agent_kit.cli_enhanced.repl import (
    CLIRepl,
    ReplConfig,
    ReplCommand,
    ReplResult,
    ReplState,
    create_repl,
)
from mc_agent_kit.cli_enhanced.history import (
    CommandHistory,
    HistoryEntry,
    HistoryConfig,
    create_history,
)
from mc_agent_kit.cli_enhanced.output import (
    ColoredOutput,
    OutputConfig,
    ProgressBar,
    ProgressConfig,
    Spinner,
    SpinnerConfig,
    Color,
    Style,
    create_output,
    create_progress_bar,
    create_spinner,
)
from mc_agent_kit.cli_enhanced.aliases import (
    CommandAlias,
    AliasManager,
    AliasConfig,
    create_alias_manager,
    get_builtin_aliases,
)

# Import Config modules
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

# Import Docs modules
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


# =============================================================================
# CLI REPL Tests
# =============================================================================

class TestReplConfig:
    """Test ReplConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = ReplConfig()
        assert config.prompt == "mc-agent> "
        assert config.continue_prompt == "... "
        assert config.max_history == 1000
        assert config.enable_multi_line is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ReplConfig(
            prompt=">>> ",
            welcome_message="Welcome!",
            case_insensitive=False,
        )
        assert config.prompt == ">>> "
        assert config.welcome_message == "Welcome!"
        assert config.case_insensitive is False


class TestReplCommand:
    """Test ReplCommand dataclass."""

    def test_command_creation(self):
        """Test command creation."""
        cmd = ReplCommand(
            name="test",
            description="Test command",
            usage="test [args]",
            aliases=["t"],
        )
        assert cmd.name == "test"
        assert cmd.description == "Test command"
        assert cmd.aliases == ["t"]

    def test_command_help(self):
        """Test command help generation."""
        cmd = ReplCommand(
            name="test",
            description="Test command",
            usage="test [args]",
            aliases=["t"],
        )
        help_text = cmd.get_help()
        assert "test" in help_text
        assert "Test command" in help_text
        assert "t" in help_text


class TestReplResult:
    """Test ReplResult dataclass."""

    def test_success_result(self):
        """Test successful result."""
        result = ReplResult(success=True, output="OK")
        assert result.success is True
        assert result.output == "OK"
        assert result.error == ""

    def test_error_result(self):
        """Test error result."""
        result = ReplResult(success=False, error="Failed")
        assert result.success is False
        assert result.error == "Failed"


class TestCLIRepl:
    """Test CLI REPL functionality."""

    def test_create_repl(self):
        """Test REPL creation."""
        repl = create_repl()
        assert repl is not None
        assert "help" in repl.list_commands()
        assert "exit" in repl.list_commands()

    def test_register_command(self):
        """Test command registration."""
        repl = create_repl()

        def handler(args, session):
            return ReplResult(success=True)

        cmd = ReplCommand(name="custom", handler=handler)
        repl.register_command(cmd)

        assert "custom" in repl.list_commands()
        assert repl.get_command("custom") is not None

    def test_get_command(self):
        """Test getting command by name or alias."""
        repl = create_repl()

        cmd = repl.get_command("help")
        assert cmd is not None
        assert cmd.name == "help"

        # Test alias
        cmd = repl.get_command("?")
        assert cmd is not None

    def test_execute_help(self):
        """Test executing help command."""
        repl = create_repl()
        result = repl.execute("help")
        assert result.success is True
        assert "Available commands" in result.output

    def test_execute_unknown_command(self):
        """Test executing unknown command."""
        repl = create_repl()
        result = repl.execute("nonexistent")
        assert result.success is False
        assert "Unknown command" in result.error

    def test_execute_exit(self):
        """Test executing exit command."""
        repl = create_repl()
        result = repl.execute("exit")
        assert result.success is True
        assert result.exit is True

    def test_execute_set_get(self):
        """Test set and get commands."""
        repl = create_repl()
        result = repl.execute("set test value123")
        assert result.success is True

        result = repl.execute("get test")
        assert result.success is True
        assert "value123" in result.output

    def test_parse_input(self):
        """Test input parsing."""
        repl = create_repl()

        cmd, args = repl.parse_input("command arg1 arg2")
        assert cmd == "command"
        assert args == ["arg1", "arg2"]

        cmd, args = repl.parse_input("")
        assert cmd == ""
        assert args == []


# =============================================================================
# Command History Tests
# =============================================================================

class TestHistoryEntry:
    """Test HistoryEntry dataclass."""

    def test_entry_creation(self):
        """Test entry creation."""
        entry = HistoryEntry(
            command="test command",
            exit_code=0,
            duration_ms=100.0,
        )
        assert entry.command == "test command"
        assert entry.exit_code == 0
        assert entry.duration_ms == 100.0

    def test_entry_to_dict(self):
        """Test entry to dictionary conversion."""
        entry = HistoryEntry(command="test")
        data = entry.to_dict()
        assert data["command"] == "test"
        assert "timestamp" in data

    def test_entry_from_dict(self):
        """Test entry from dictionary conversion."""
        data = {"command": "test", "exit_code": 1}
        entry = HistoryEntry.from_dict(data)
        assert entry.command == "test"
        assert entry.exit_code == 1


class TestHistoryConfig:
    """Test HistoryConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = HistoryConfig()
        assert config.max_entries == 1000
        assert config.save_immediately is True
        assert config.deduplicate is True


class TestCommandHistory:
    """Test CommandHistory functionality."""

    def test_create_history(self):
        """Test history creation."""
        history = create_history()
        assert history is not None
        assert history.count == 0

    def test_add_entry(self):
        """Test adding entries."""
        history = create_history()
        entry = history.add("test command", exit_code=0)
        assert entry.command == "test command"
        assert history.count == 1

    def test_get_last(self):
        """Test getting last entries."""
        history = create_history()
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")

        last = history.get_last(2)
        assert len(last) == 2
        assert last[0].command == "cmd2"
        assert last[1].command == "cmd3"

    def test_search(self):
        """Test searching history."""
        history = create_history()
        history.add("create project test")
        history.add("kb search entity")
        history.add("create entity mob")

        results = history.search("create")
        assert len(results) == 2

        results = history.search("entity")
        assert len(results) == 2

    def test_search_regex(self):
        """Test regex search."""
        history = create_history()
        history.add("create project test")
        history.add("create item item1")

        results = history.search(r"project\s+\w+", regex=True)
        assert len(results) == 1

    def test_save_load(self):
        """Test save and load."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            history = create_history(HistoryConfig(history_file=temp_path))
            history.add("test command")
            history.save()

            # Load in new instance
            history2 = create_history(HistoryConfig(history_file=temp_path))
            history2.load()
            assert history2.count == 1
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_clear(self):
        """Test clearing history."""
        history = create_history()
        history.add("cmd1")
        history.add("cmd2")

        cleared = history.clear()
        assert cleared == 2
        assert history.count == 0


# =============================================================================
# Colored Output Tests
# =============================================================================

class TestColor:
    """Test Color enum."""

    def test_color_values(self):
        """Test color values."""
        assert Color.RED.value == "31"
        assert Color.GREEN.value == "32"
        assert Color.BLUE.value == "34"


class TestStyle:
    """Test Style enum."""

    def test_style_values(self):
        """Test style values."""
        assert Style.BOLD.value == "1"
        assert Style.UNDERLINE.value == "4"
        assert Style.RESET.value == "0"


class TestColoredOutput:
    """Test ColoredOutput functionality."""

    def test_create_output(self):
        """Test output creation."""
        output = create_output()
        assert output is not None

    def test_colorize(self):
        """Test colorizing text."""
        output = create_output(OutputConfig(force_color=True))
        colored = output.colorize("test", Color.RED)
        assert "\033[" in colored  # ANSI escape code

    def test_colorize_no_color(self):
        """Test colorizing without color."""
        output = create_output(OutputConfig(use_color=False))
        colored = output.colorize("test", Color.RED)
        assert colored == "test"

    def test_print_methods(self):
        """Test print methods."""
        output = create_output(OutputConfig(use_color=False))

        # These should not raise
        output.success("Success message")
        output.error("Error message")
        output.warning("Warning message")
        output.info("Info message")


class TestProgressBar:
    """Test ProgressBar functionality."""

    def test_create_progress_bar(self):
        """Test progress bar creation."""
        bar = create_progress_bar()
        assert bar is not None
        assert bar._current == 0

    def test_update(self):
        """Test progress bar update."""
        bar = create_progress_bar(ProgressConfig(total=10))
        bar.update(5)
        assert bar._current == 5

    def test_set_progress(self):
        """Test setting progress directly."""
        bar = create_progress_bar(ProgressConfig(total=100))
        bar.set_progress(75)
        assert bar._current == 75

    def test_complete(self):
        """Test completing progress bar."""
        bar = create_progress_bar(ProgressConfig(total=10))
        bar.complete()
        assert bar._current == 10

    def test_context_manager(self):
        """Test context manager usage."""
        with create_progress_bar(ProgressConfig(total=5)) as bar:
            bar.update(3)
            assert bar._current == 3


class TestSpinner:
    """Test Spinner functionality."""

    def test_create_spinner(self):
        """Test spinner creation."""
        spinner = create_spinner()
        assert spinner is not None

    def test_spin(self):
        """Test spinning."""
        spinner = create_spinner()
        frame1 = spinner.spin()
        frame2 = spinner.spin()
        assert frame1 != frame2 or len(spinner._frames) == 1

    def test_update_message(self):
        """Test updating spinner message."""
        spinner = create_spinner()
        spinner.update("Loading...")
        assert spinner.config.message == "Loading..."


# =============================================================================
# Command Aliases Tests
# =============================================================================

class TestCommandAlias:
    """Test CommandAlias dataclass."""

    def test_alias_creation(self):
        """Test alias creation."""
        alias = CommandAlias(
            name="s",
            command="kb search $@",
            description="Search shortcut",
        )
        assert alias.name == "s"
        assert alias.command == "kb search $@"

    def test_expand_simple(self):
        """Test simple expansion."""
        alias = CommandAlias(name="s", command="kb search $@")
        expanded = alias.expand(["entity"])
        # $@ is replaced with all args, no additional append
        assert "kb search" in expanded
        assert "entity" in expanded

    def test_expand_positional(self):
        """Test positional argument expansion."""
        alias = CommandAlias(
            name="test",
            command="cmd $1 $2",
            arguments=["arg1", "arg2"],
        )
        expanded = alias.expand(["value1", "value2"])
        assert expanded == "cmd value1 value2"

    def test_to_dict(self):
        """Test to dictionary conversion."""
        alias = CommandAlias(name="test", command="cmd")
        data = alias.to_dict()
        assert data["name"] == "test"
        assert data["command"] == "cmd"


class TestAliasManager:
    """Test AliasManager functionality."""

    def test_create_manager(self):
        """Test manager creation."""
        manager = create_alias_manager()
        assert manager is not None

    def test_get_builtin_aliases(self):
        """Test getting built-in aliases."""
        aliases = get_builtin_aliases()
        assert len(aliases) > 0
        names = [a.name for a in aliases]
        assert "s" in names
        assert "api" in names

    def test_register_alias(self):
        """Test registering alias."""
        manager = create_alias_manager()
        alias = CommandAlias(name="custom", command="custom command")
        result = manager.register(alias)
        assert result is True
        assert manager.is_alias("custom")

    def test_expand_alias(self):
        """Test expanding alias."""
        manager = create_alias_manager()
        expanded = manager.expand("s", ["test"])
        assert expanded is not None
        assert "kb search" in expanded

    def test_list_aliases(self):
        """Test listing aliases."""
        manager = create_alias_manager()
        aliases = manager.list_aliases()
        assert len(aliases) > 0


# =============================================================================
# Configuration Manager Tests
# =============================================================================

class TestConfigValue:
    """Test ConfigValue dataclass."""

    def test_value_creation(self):
        """Test value creation."""
        value = ConfigValue(
            key="test.key",
            value="test_value",
            source=ConfigSource.FILE,
        )
        # Key is normalized (dots remain, slashes/hyphens become underscores)
        assert value.key == "test.key"
        assert value.value == "test_value"
        assert value.source == ConfigSource.FILE


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_create_manager(self):
        """Test manager creation."""
        manager = create_config_manager()
        assert manager is not None

    def test_set_default(self):
        """Test setting default value."""
        manager = create_config_manager()
        manager.set_default("test.key", "default_value")
        value = manager.get("test.key")
        assert value == "default_value"

    def test_set_get(self):
        """Test set and get."""
        manager = create_config_manager()
        manager.set("test.key", "value")
        assert manager.get("test.key") == "value"

    def test_get_with_default(self):
        """Test get with default value."""
        manager = create_config_manager()
        value = manager.get("nonexistent", "default")
        assert value == "default"

    def test_environment_override(self):
        """Test environment variable override."""
        os.environ["MC_AGENT_TEST_KEY"] = "env_value"
        try:
            manager = create_config_manager()
            value = manager.get("test.key")
            assert value == "env_value"
        finally:
            del os.environ["MC_AGENT_TEST_KEY"]

    def test_type_coercion(self):
        """Test type coercion."""
        manager = create_config_manager()
        manager.set("test.int", "42")
        value = manager.get("test.int", coerce_type=int)
        assert value == 42

    def test_save_load_file(self):
        """Test save and load file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            manager = create_config_manager(ManagerConfig(config_file=temp_path))
            manager.set("test.key", "value")
            manager.save_file()

            # Load in new instance
            manager2 = create_config_manager(ManagerConfig(config_file=temp_path))
            manager2.load_file()
            assert manager2.get("test.key") == "value"
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_change_callback(self):
        """Test change callback."""
        manager = create_config_manager()
        changes = []

        def callback(key, old, new):
            changes.append((key, old, new))

        manager.on_change("test.key", callback)
        manager.set("test.key", "new_value")

        assert len(changes) == 1
        assert changes[0][0] == "test.key"


# =============================================================================
# Configuration Validator Tests
# =============================================================================

class TestValidationError:
    """Test ValidationError dataclass."""

    def test_error_creation(self):
        """Test error creation."""
        error = ValidationError(
            key="test",
            message="Test error",
            level=ValidationLevel.ERROR,
        )
        assert error.key == "test"
        assert error.message == "Test error"


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        """Test valid result."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.has_errors is False

    def test_add_error(self):
        """Test adding error."""
        result = ValidationResult(valid=True)
        result.add_error("key", "Error message")
        assert result.has_errors is True
        assert result.valid is False

    def test_add_warning(self):
        """Test adding warning."""
        result = ValidationResult(valid=True)
        result.add_warning("key", "Warning message")
        assert result.has_warnings is True
        assert result.valid is True


class TestSchemaField:
    """Test SchemaField dataclass."""

    def test_field_validation_type(self):
        """Test type validation."""
        field = SchemaField(name="test", type=int)
        result = field.validate("not_int")
        assert result.has_errors is True

    def test_field_validation_required(self):
        """Test required validation."""
        field = SchemaField(name="test", required=True)
        result = field.validate(None)
        assert result.has_errors is True

    def test_field_validation_range(self):
        """Test range validation."""
        field = SchemaField(name="test", type=int, min_value=0, max_value=100)
        result = field.validate(150)
        assert result.has_errors is True

    def test_field_validation_enum(self):
        """Test enum validation."""
        field = SchemaField(name="test", enum=["a", "b", "c"])
        result = field.validate("d")
        assert result.has_errors is True


class TestConfigValidator:
    """Test ConfigValidator functionality."""

    def test_create_validator(self):
        """Test validator creation."""
        validator = create_validator()
        assert validator is not None

    def test_validate_valid_config(self):
        """Test validating valid config."""
        validator = create_validator()
        config = {"debug": True, "log_port": 8080}
        result = validator.validate(config)
        assert result.valid is True

    def test_validate_invalid_config(self):
        """Test validating invalid config."""
        validator = create_validator()
        config = {"log_port": "not_int"}
        result = validator.validate(config)
        assert result.has_errors is True


# =============================================================================
# Configuration Templates Tests
# =============================================================================

class TestTemplateField:
    """Test TemplateField dataclass."""

    def test_field_creation(self):
        """Test field creation."""
        field = TemplateField(
            name="test",
            label="Test Field",
            type=str,
            default="default",
        )
        assert field.name == "test"
        assert field.get_label() == "Test Field"

    def test_get_default_display(self):
        """Test default display."""
        field = TemplateField(name="bool", type=bool, default=True)
        assert field.get_default_display() == "true"


class TestConfigTemplate:
    """Test ConfigTemplate dataclass."""

    def test_template_creation(self):
        """Test template creation."""
        template = ConfigTemplate(
            name="test",
            type=TemplateType.CLI,
            description="Test template",
        )
        assert template.name == "test"
        assert template.type == TemplateType.CLI

    def test_get_fields_by_group(self):
        """Test getting fields by group."""
        template = ConfigTemplate(
            name="test",
            type=TemplateType.CLI,
            fields=[
                TemplateField(name="f1", group="group1"),
                TemplateField(name="f2", group="group2"),
            ],
            groups=["group1", "group2"],
        )
        fields = template.get_fields_by_group("group1")
        assert len(fields) == 1


class TestTemplateGenerator:
    """Test TemplateGenerator functionality."""

    def test_create_generator(self):
        """Test generator creation."""
        generator = create_template_generator()
        assert generator is not None

    def test_list_templates(self):
        """Test listing templates."""
        generator = create_template_generator()
        templates = generator.list_templates()
        assert len(templates) > 0

    def test_generate(self):
        """Test generating configuration."""
        generator = create_template_generator()
        config = generator.generate("default")
        assert "_template" in config
        assert "_version" in config

    def test_generate_json(self):
        """Test generating JSON."""
        generator = create_template_generator()
        json_str = generator.generate_json("minimal")
        assert "_template" in json_str


# =============================================================================
# Documentation Generator Tests
# =============================================================================

class TestApiDoc:
    """Test ApiDoc dataclass."""

    def test_doc_creation(self):
        """Test doc creation."""
        doc = ApiDoc(
            name="test_function",
            description="Test function",
            parameters=[ApiDocField(name="param1", type="str")],
        )
        assert doc.name == "test_function"
        assert len(doc.parameters) == 1


class TestExampleDoc:
    """Test ExampleDoc dataclass."""

    def test_example_creation(self):
        """Test example creation."""
        example = ExampleDoc(
            title="Test Example",
            code="print('hello')",
            difficulty="beginner",
        )
        assert example.title == "Test Example"
        assert example.difficulty == "beginner"


class TestDocGenerator:
    """Test DocGenerator functionality."""

    def test_create_generator(self):
        """Test generator creation."""
        generator = create_doc_generator()
        assert generator is not None

    def test_register_api(self):
        """Test registering API doc."""
        generator = create_doc_generator()
        doc = ApiDoc(name="test", description="Test")
        generator.register_api(doc)
        assert "test" in generator._api_docs

    def test_register_example(self):
        """Test registering example."""
        generator = create_doc_generator()
        example = ExampleDoc(title="Test", code="code")
        generator.register_example(example)
        assert len(generator._examples) == 1

    def test_generate_markdown(self):
        """Test generating markdown."""
        generator = create_doc_generator()
        doc = ApiDoc(name="test_func", description="Test function")
        generator.register_api(doc)

        md = generator.generate_markdown()
        assert "test_func" in md
        assert "Test function" in md

    def test_generate_json(self):
        """Test generating JSON."""
        generator = create_doc_generator()
        json_str = generator.generate_json()
        assert "version" in json_str


# =============================================================================
# Documentation Formatter Tests
# =============================================================================

class TestDocFormatter:
    """Test DocFormatter functionality."""

    def test_create_formatter(self):
        """Test formatter creation."""
        formatter = create_formatter()
        assert formatter is not None

    def test_format_markdown(self):
        """Test formatting as markdown."""
        formatter = create_formatter(FormatterConfig(format=OutputFormat.MARKDOWN))
        data = {
            "version": "1.0",
            "apis": {
                "test": {
                    "name": "test",
                    "description": "Test API",
                }
            },
        }
        md = formatter.format(data)
        assert "# API Documentation" in md
        assert "test" in md

    def test_format_json(self):
        """Test formatting as JSON."""
        formatter = create_formatter(FormatterConfig(format=OutputFormat.JSON))
        data = {"test": "value"}
        json_str = formatter.format(data)
        assert "test" in json_str
        assert "value" in json_str


# =============================================================================
# Integration Tests
# =============================================================================

class TestIteration36Integration:
    """Integration tests for iteration #36."""

    def test_cli_modules_import(self):
        """Test CLI modules import."""
        from mc_agent_kit import cli_enhanced
        assert hasattr(cli_enhanced, 'repl')
        assert hasattr(cli_enhanced, 'history')
        assert hasattr(cli_enhanced, 'output')
        assert hasattr(cli_enhanced, 'aliases')

    def test_config_modules_import(self):
        """Test config modules import."""
        from mc_agent_kit import config
        assert hasattr(config, 'manager')
        assert hasattr(config, 'validator')
        assert hasattr(config, 'templates')

    def test_docs_modules_import(self):
        """Test docs modules import."""
        from mc_agent_kit import docs
        assert hasattr(docs, 'generator')
        assert hasattr(docs, 'formatter')

    def test_full_workflow(self):
        """Test full workflow with all components."""
        # Create REPL
        repl = create_repl()
        assert repl is not None

        # Create history
        history = create_history()
        history.add("test command")

        # Create output
        output = create_output()
        assert output is not None

        # Create config manager
        config_mgr = create_config_manager()
        config_mgr.set("test.key", "value")

        # Create validator
        validator = create_validator()
        result = validator.validate({"debug": True})

        # Create template generator
        template_gen = create_template_generator()
        config = template_gen.generate("minimal")

        # Create doc generator
        doc_gen = create_doc_generator()
        doc_gen.register_api(ApiDoc(name="test", description="Test"))
        md = doc_gen.generate_markdown()

        # All should succeed
        assert True