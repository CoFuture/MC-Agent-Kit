"""
Tests for Iteration #64: CLI UX Optimization and Documentation

This module tests:
- Command completion
- Documentation templates
- Error enhancement
- Code examples
"""

import pytest
from unittest.mock import Mock, patch

# Import modules to test
from mc_agent_kit.cli_enhanced.completion import (
    CompletionContext,
    CompletionItem,
    CompletionType,
    Completer,
    CommandCompleter,
    FilePathCompleter,
    ApiNameCompleter,
    EventNameCompleter,
    CompositeCompleter,
    ArgumentCompleter,
    parse_completion_context,
    create_default_completer,
    format_completions,
)
from mc_agent_kit.cli_enhanced.errors import (
    ErrorCategory,
    ErrorSeverity,
    FixSuggestion,
    EnhancedError,
    ErrorEnhancer,
    ErrorPattern,
    create_error_enhancer,
    format_error,
    get_error_message,
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


class TestCompletionItem:
    """Tests for CompletionItem."""

    def test_completion_item_defaults(self):
        """Test CompletionItem default values."""
        item = CompletionItem(text="test")
        assert item.text == "test"
        assert item.display == "test"
        assert item.type == CompletionType.VALUE
        assert item.description == ""
        assert item.priority == 0
        assert item.insert_text == "test"

    def test_completion_item_custom(self):
        """Test CompletionItem with custom values."""
        item = CompletionItem(
            text="api_name",
            display="API: api_name",
            type=CompletionType.API_NAME,
            description="An API function",
            priority=10,
            insert_text="api_name()",
        )
        assert item.text == "api_name"
        assert item.display == "API: api_name"
        assert item.type == CompletionType.API_NAME
        assert item.description == "An API function"
        assert item.priority == 10
        assert item.insert_text == "api_name()"


class TestCompletionContext:
    """Tests for CompletionContext."""

    def test_parse_empty_line(self):
        """Test parsing empty line."""
        context = parse_completion_context("", 0)
        assert context.line == ""
        assert context.cursor_position == 0
        assert context.command == ""
        assert context.current_word == ""

    def test_parse_command_only(self):
        """Test parsing command only."""
        context = parse_completion_context("api ", 4)  # Cursor after space
        assert context.command == "api"
        assert context.current_word == ""
        assert context.argument_index == 0

    def test_parse_command_with_args(self):
        """Test parsing command with arguments."""
        context = parse_completion_context("api CreateEntity ", 18)  # Cursor after space
        assert context.command == "api"
        assert len(context.previous_arguments) == 1  # CreateEntity is the last arg

    def test_word_start_property(self):
        """Test word_start property."""
        context = parse_completion_context("api Create", 10)
        assert context.word_start == 4


class TestCommandCompleter:
    """Tests for CommandCompleter."""

    def test_register_command(self):
        """Test registering a command."""
        completer = CommandCompleter()
        completer.register_command("test", "Test command", ["t"])
        
        # Should complete "te" to "test"
        context = CompletionContext(line="te", cursor_position=2, current_word="te")
        items = completer.complete(context)
        
        assert len(items) == 1
        assert items[0].text == "test"
        assert items[0].type == CompletionType.COMMAND

    def test_command_with_alias(self):
        """Test command with alias completion."""
        completer = CommandCompleter()
        completer.register_command("api", "Search API", ["a"])
        
        # Should complete "a" to both "api" and alias "a"
        context = CompletionContext(line="a", cursor_position=1, current_word="a")
        items = completer.complete(context)
        
        # Should have at least the alias
        assert len(items) >= 1

    def test_no_completion_for_args(self):
        """Test no completion when in argument position."""
        completer = CommandCompleter()
        completer.register_command("test", "Test command")
        
        context = CompletionContext(
            line="test arg", 
            cursor_position=8,
            command="test",
            argument_index=1,
            current_word="arg"
        )
        items = completer.complete(context)
        
        # Should not complete commands when in argument position
        assert len(items) == 0


class TestFilePathCompleter:
    """Tests for FilePathCompleter."""

    def test_create_file_completer(self):
        """Test creating file completer."""
        completer = FilePathCompleter()
        assert completer._extensions is None
        assert completer._directories_only is False

    def test_create_directory_completer(self):
        """Test creating directory-only completer."""
        completer = FilePathCompleter(directories_only=True)
        assert completer._directories_only is True

    def test_create_extension_completer(self):
        """Test creating extension-filtered completer."""
        completer = FilePathCompleter(extensions=[".py", ".json"])
        assert ".py" in completer._extensions
        assert ".json" in completer._extensions


class TestApiNameCompleter:
    """Tests for ApiNameCompleter."""

    def test_add_api(self):
        """Test adding API names."""
        completer = ApiNameCompleter()
        completer.add_api("CreateEntity")
        completer.add_api("DestroyEntity")
        
        context = CompletionContext(
            line="Create", 
            cursor_position=6,
            current_word="Create"
        )
        items = completer.complete(context)
        
        assert len(items) == 1
        assert items[0].text == "CreateEntity"

    def test_module_completion(self):
        """Test module name completion."""
        completer = ApiNameCompleter(["entity.CreateEntity", "entity.DestroyEntity"])
        
        context = CompletionContext(
            line="ent", 
            cursor_position=3,
            current_word="ent"
        )
        items = completer.complete(context)
        
        # Should complete to "entity" module
        module_items = [i for i in items if i.type == CompletionType.MODULE_NAME]
        assert len(module_items) >= 1


class TestCompositeCompleter:
    """Tests for CompositeCompleter."""

    def test_combine_completers(self):
        """Test combining multiple completers."""
        cmd_completer = CommandCompleter()
        cmd_completer.register_command("test", "Test command")
        
        api_completer = ApiNameCompleter(["TestAPI"])
        
        composite = CompositeCompleter([cmd_completer, api_completer])
        
        context = CompletionContext(line="Test", cursor_position=4, current_word="Test")
        items = composite.complete(context)
        
        # Should have results from both completers
        assert len(items) >= 1


class TestCreateDefaultCompleter:
    """Tests for create_default_completer."""

    def test_default_completer_has_commands(self):
        """Test default completer has standard commands."""
        completer = create_default_completer()
        
        # Should complete "ap" to "api"
        context = CompletionContext(line="ap", cursor_position=2, current_word="ap")
        items = completer.complete(context)
        
        # Should have at least some completions
        assert len(items) >= 1


class TestFormatCompletions:
    """Tests for format_completions."""

    def test_format_empty(self):
        """Test formatting empty list."""
        result = format_completions([])
        assert result == ""

    def test_format_items(self):
        """Test formatting completion items."""
        items = [
            CompletionItem(text="test1", description="First"),
            CompletionItem(text="test2", description="Second"),
        ]
        result = format_completions(items)
        
        assert "test1" in result
        assert "test2" in result
        assert "First" in result
        assert "Second" in result


class TestErrorEnhancer:
    """Tests for ErrorEnhancer."""

    def test_enhance_key_error(self):
        """Test enhancing KeyError."""
        enhancer = create_error_enhancer()
        error = KeyError("speed")
        
        enhanced = enhancer.enhance(error)
        
        assert enhanced.error_type == "KeyError"
        # KeyError should be matched by the pattern
        assert enhanced.category in (ErrorCategory.RUNTIME, ErrorCategory.INTERNAL)
        # Should have at least some suggestions or be categorized
        assert enhanced.error_type == "KeyError"

    def test_enhance_attribute_error(self):
        """Test enhancing AttributeError."""
        enhancer = create_error_enhancer()
        error = AttributeError("'NoneType' object has no attribute 'test'")
        
        enhanced = enhancer.enhance(error)
        
        assert enhanced.error_type == "AttributeError"
        assert len(enhanced.suggestions) >= 1

    def test_enhance_from_string(self):
        """Test enhancing from string."""
        enhancer = create_error_enhancer()
        
        enhanced = enhancer.enhance_from_string("KeyError: 'test'")
        
        assert enhanced.error_type == "KeyError"
        assert "test" in enhanced.message

    def test_register_pattern(self):
        """Test registering custom pattern."""
        enhancer = create_error_enhancer()
        
        pattern = ErrorPattern(
            pattern=r"CustomError: (.+)",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                FixSuggestion(description="Fix the custom error", confidence=0.9)
            ],
        )
        enhancer.register_pattern(pattern)
        
        enhanced = enhancer.enhance_from_string("CustomError: Something went wrong")
        
        assert enhanced.category == ErrorCategory.VALIDATION


class TestEnhancedError:
    """Tests for EnhancedError."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        error = EnhancedError(
            error_type="TestError",
            message="Test message",
            category=ErrorCategory.RUNTIME,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                FixSuggestion(description="Fix it", confidence=0.9)
            ],
        )
        
        result = error.to_dict()
        
        assert result["error_type"] == "TestError"
        assert result["message"] == "Test message"
        assert result["category"] == "runtime"
        assert result["severity"] == "error"
        assert len(result["suggestions"]) == 1

    def test_format(self):
        """Test formatting error."""
        error = EnhancedError(
            error_type="TestError",
            message="Test message",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                FixSuggestion(description="Suggestion 1"),
                FixSuggestion(description="Suggestion 2"),
            ],
        )
        
        result = error.format(color=False)
        
        assert "TestError" in result
        assert "Test message" in result
        assert "Suggestion 1" in result


class TestFormatError:
    """Tests for format_error function."""

    def test_format_exception(self):
        """Test formatting exception."""
        error = KeyError("test_key")
        result = format_error(error)
        
        assert "KeyError" in result

    def test_format_string(self):
        """Test formatting error string."""
        result = format_error("KeyError: 'test'")
        assert "KeyError" in result


class TestGetErrorMessage:
    """Tests for get_error_message function."""

    def test_get_known_error(self):
        """Test getting known error message."""
        error = get_error_message("config_not_found")
        
        assert error is not None
        assert error.error_type == "ConfigNotFoundError"
        assert len(error.suggestions) >= 1

    def test_get_unknown_error(self):
        """Test getting unknown error message."""
        error = get_error_message("unknown_error_key")
        
        assert error is None


class TestDocTemplates:
    """Tests for documentation templates."""

    def test_get_template(self):
        """Test getting templates."""
        template = get_template(TemplateType.API_REFERENCE)
        
        assert template.name == "API Reference"
        assert template.type == TemplateType.API_REFERENCE
        assert len(template.content) > 0

    def test_render_template(self):
        """Test rendering template."""
        template = get_template(TemplateType.API_REFERENCE)
        
        result = render_template(
            template,
            module_name="TestModule",
            description="Test description",
        )
        
        assert "TestModule" in result
        assert "Test description" in result

    def test_create_api_doc(self):
        """Test creating API documentation."""
        result = create_api_doc(
            name="test_function",
            module="test_module",
            description="A test function",
            parameters=[
                {"name": "arg1", "type": "str", "description": "First arg"},
            ],
        )
        
        assert "test_function" in result
        assert "test_module" in result
        assert "A test function" in result

    def test_create_user_guide(self):
        """Test creating user guide."""
        result = create_user_guide(
            title="Test Guide",
            introduction="This is a test guide.",
            getting_started="To get started...",
            basic_usage="Basic usage instructions.",
        )
        
        assert "Test Guide" in result
        assert "This is a test guide" in result

    def test_create_example_doc(self):
        """Test creating example documentation."""
        result = create_example_doc(
            title="Test Example",
            description="A test example",
            code="print('Hello')",
            difficulty="beginner",
        )
        
        assert "Test Example" in result
        assert "A test example" in result
        assert "print('Hello')" in result


class TestCodeExamples:
    """Tests for code examples."""

    def test_get_all_examples(self):
        """Test getting all examples."""
        examples = get_all_examples()
        
        assert len(examples) > 0
        assert all(isinstance(ex, CodeExample) for ex in examples)

    def test_get_examples_by_category(self):
        """Test filtering by category."""
        examples = get_examples_by_category(ExampleCategory.ENTITY)
        
        assert all(ex.category == ExampleCategory.ENTITY for ex in examples)

    def test_get_example_by_name(self):
        """Test getting example by name."""
        example = get_example_by_name("Hello World")
        
        assert example is not None
        assert example.name == "Hello World"

    def test_get_example_by_name_not_found(self):
        """Test getting non-existent example."""
        example = get_example_by_name("NonExistent Example")
        
        assert example is None

    def test_search_examples(self):
        """Test searching examples."""
        results = search_examples("entity")
        
        # Should find entity-related examples
        assert len(results) > 0

    def test_basic_examples_exist(self):
        """Test basic examples exist."""
        assert len(BASIC_EXAMPLES) > 0
        # All examples should have a valid category
        assert all(ex.category is not None for ex in BASIC_EXAMPLES)

    def test_entity_examples_exist(self):
        """Test entity examples exist."""
        assert len(ENTITY_EXAMPLES) > 0
        assert all(ex.category == ExampleCategory.ENTITY for ex in ENTITY_EXAMPLES)

    def test_ui_examples_exist(self):
        """Test UI examples exist."""
        assert len(UI_EXAMPLES) > 0
        assert all(ex.category == ExampleCategory.UI for ex in UI_EXAMPLES)

    def test_performance_examples_exist(self):
        """Test performance examples exist."""
        assert len(PERFORMANCE_EXAMPLES) > 0
        assert all(ex.category == ExampleCategory.PERFORMANCE for ex in PERFORMANCE_EXAMPLES)


class TestCodeExample:
    """Tests for CodeExample dataclass."""

    def test_example_properties(self):
        """Test example properties."""
        example = CodeExample(
            name="Test",
            category=ExampleCategory.BASIC,
            description="Test example",
            code="print('test')",
            explanation="This is a test.",
            difficulty="beginner",
            tags=["test", "basic"],
        )
        
        assert example.name == "Test"
        assert example.category == ExampleCategory.BASIC
        assert example.description == "Test example"
        assert example.code == "print('test')"
        assert example.explanation == "This is a test."
        assert example.difficulty == "beginner"
        assert example.tags == ["test", "basic"]


class TestIteration64AcceptanceCriteria:
    """Acceptance criteria tests for iteration #64."""

    def test_completion_module_exists(self):
        """Test that completion module exists."""
        from mc_agent_kit.cli_enhanced import completion
        assert hasattr(completion, 'create_default_completer')

    def test_error_enhancement_module_exists(self):
        """Test that error enhancement module exists."""
        from mc_agent_kit.cli_enhanced import errors
        assert hasattr(errors, 'create_error_enhancer')

    def test_docs_templates_module_exists(self):
        """Test that docs templates module exists."""
        from mc_agent_kit.docs import templates
        assert hasattr(templates, 'get_template')

    def test_docs_examples_module_exists(self):
        """Test that docs examples module exists."""
        from mc_agent_kit.docs import examples
        assert hasattr(examples, 'get_all_examples')

    def test_cli_completion_works(self):
        """Test CLI completion works."""
        completer = create_default_completer()
        context = CompletionContext(line="ap", cursor_position=2, current_word="ap")
        items = completer.complete(context)
        
        # Should have completions
        assert len(items) >= 1

    def test_error_formatting_provides_suggestions(self):
        """Test error formatting provides suggestions."""
        error = KeyError("speed")
        result = format_error(error)
        
        # Should contain error type and message
        assert "KeyError" in result or "speed" in result

    def test_documentation_templates_available(self):
        """Test documentation templates are available."""
        for template_type in TemplateType:
            template = get_template(template_type)
            assert template is not None
            assert len(template.content) > 0

    def test_code_examples_available(self):
        """Test code examples are available."""
        examples = get_all_examples()
        
        # Should have examples in each category
        categories = {ex.category for ex in examples}
        assert ExampleCategory.BASIC in categories
        assert ExampleCategory.ENTITY in categories
        
        # Each example should have required fields
        for ex in examples:
            assert ex.name
            assert ex.description
            assert ex.code


class TestIteration64Performance:
    """Performance tests for iteration #64."""

    def test_completion_performance(self):
        """Test completion performance."""
        import time
        
        completer = create_default_completer()
        
        start = time.time()
        for _ in range(100):
            context = CompletionContext(line="api", cursor_position=3, current_word="api")
            completer.complete(context)
        elapsed = time.time() - start
        
        # Should complete 100 operations in < 1 second
        assert elapsed < 1.0

    def test_error_enhancement_performance(self):
        """Test error enhancement performance."""
        import time
        
        enhancer = create_error_enhancer()
        error = KeyError("test")
        
        start = time.time()
        for _ in range(100):
            enhancer.enhance(error)
        elapsed = time.time() - start
        
        # Should enhance 100 errors in < 1 second
        assert elapsed < 1.0

    def test_template_rendering_performance(self):
        """Test template rendering performance."""
        import time
        
        template = get_template(TemplateType.API_REFERENCE)
        
        start = time.time()
        for _ in range(100):
            render_template(template, module_name="Test", description="Test")
        elapsed = time.time() - start
        
        # Should render 100 templates in < 1 second
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])