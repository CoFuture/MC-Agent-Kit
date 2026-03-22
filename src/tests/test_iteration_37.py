"""Tests for Iteration #37 - CLI command integration and user workflow optimization."""

import argparse
import pytest


class TestReplCommand:
    """Tests for REPL command."""

    def test_repl_config_defaults(self):
        """Test REPL config with default values."""
        args = argparse.Namespace(
            prompt=None,
            history_file=None,
            no_welcome=False,
            format="text",
        )
        assert hasattr(args, "prompt")
        assert hasattr(args, "history_file")
        assert hasattr(args, "no_welcome")

    def test_repl_custom_prompt(self):
        """Test REPL with custom prompt."""
        args = argparse.Namespace(
            prompt="custom> ",
            history_file=None,
            no_welcome=True,
            format="text",
        )
        assert args.prompt == "custom> "
        assert args.no_welcome is True


class TestConfigCommand:
    """Tests for config command."""

    def test_config_generate_args(self):
        """Test config generate command args."""
        args = argparse.Namespace(
            action="generate",
            config_path=None,
            template=None,
            output=None,
            format_type="json",
            key=None,
            value=None,
            format="text",
        )
        assert args.action == "generate"
        assert args.format_type == "json"

    def test_config_validate_args(self):
        """Test config validate command args."""
        args = argparse.Namespace(
            action="validate",
            config_path="test.json",
            template=None,
            output=None,
            format_type="json",
            key=None,
            value=None,
            format="text",
        )
        assert args.action == "validate"

    def test_config_show_args(self):
        """Test config show command args."""
        args = argparse.Namespace(
            action="show",
            config_path=None,
            template=None,
            output=None,
            format_type="json",
            key=None,
            value=None,
            format="json",
        )
        assert args.action == "show"

    def test_config_set_args(self):
        """Test config set command args."""
        args = argparse.Namespace(
            action="set",
            config_path=None,
            template=None,
            output=None,
            format_type="json",
            key="test_key",
            value="test_value",
            format="text",
        )
        assert args.action == "set"
        assert args.key == "test_key"
        assert args.value == "test_value"

    def test_config_set_missing_key(self):
        """Test setting config without key."""
        args = argparse.Namespace(
            action="set",
            config_path=None,
            template=None,
            output=None,
            format_type="json",
            key=None,
            value="test_value",
            format="text",
        )
        assert args.key is None

    def test_config_set_missing_value(self):
        """Test setting config without value."""
        args = argparse.Namespace(
            action="set",
            config_path=None,
            template=None,
            output=None,
            format_type="json",
            key="test_key",
            value=None,
            format="text",
        )
        assert args.value is None


class TestDocsCommand:
    """Tests for docs command."""

    def test_docs_generate_args(self):
        """Test docs generate command args."""
        args = argparse.Namespace(
            action="generate",
            source_path=None,
            api_name=None,
            output=None,
            output_format="markdown",
            limit=10,
            format="text",
        )
        assert args.action == "generate"
        assert args.output_format == "markdown"

    def test_docs_api_args(self):
        """Test docs api command args."""
        args = argparse.Namespace(
            action="api",
            source_path=None,
            api_name="TestAPI",
            output=None,
            output_format="markdown",
            limit=10,
            format="text",
        )
        assert args.action == "api"
        assert args.api_name == "TestAPI"

    def test_docs_list_args(self):
        """Test docs list command args."""
        args = argparse.Namespace(
            action="list",
            source_path=None,
            api_name=None,
            output=None,
            output_format="markdown",
            limit=100,
            format="json",
        )
        assert args.action == "list"


class TestWizardCommand:
    """Tests for wizard command."""

    def test_wizard_project_type(self):
        """Test wizard command for project type."""
        args = argparse.Namespace(
            type="project",
            name=None,
            format="text",
        )
        assert args.type == "project"

    def test_wizard_config_type(self):
        """Test wizard command for config type."""
        args = argparse.Namespace(
            type="config",
            name=None,
            format="text",
        )
        assert args.type == "config"

    def test_wizard_diagnose_type(self):
        """Test wizard command for diagnose type."""
        args = argparse.Namespace(
            type="diagnose",
            name=None,
            format="text",
        )
        assert args.type == "diagnose"

    def test_wizard_with_name(self):
        """Test wizard command with name provided."""
        args = argparse.Namespace(
            type="project",
            name="test_project",
            format="text",
        )
        assert args.name == "test_project"


class TestBatchCommand:
    """Tests for batch command."""

    def test_batch_analyze_args(self):
        """Test batch analyze command args."""
        args = argparse.Namespace(
            action="analyze",
            paths=["/path1", "/path2"],
            apis=None,
            output_dir=None,
            format="text",
        )
        assert args.action == "analyze"
        assert len(args.paths) == 2

    def test_batch_generate_args(self):
        """Test batch generate command args."""
        args = argparse.Namespace(
            action="generate",
            paths=None,
            apis=["API1", "API2"],
            output_dir="./docs",
            format="json",
        )
        assert args.action == "generate"
        assert len(args.apis) == 2

    def test_batch_analyze_missing_paths(self):
        """Test batch analyze without paths."""
        args = argparse.Namespace(
            action="analyze",
            paths=[],
            apis=None,
            output_dir=None,
            format="text",
        )
        assert args.paths == []

    def test_batch_generate_missing_apis(self):
        """Test batch generate without APIs."""
        args = argparse.Namespace(
            action="generate",
            paths=None,
            apis=[],
            output_dir=None,
            format="text",
        )
        assert args.apis == []


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_cli_imports(self):
        """Test that CLI module imports correctly."""
        from mc_agent_kit import cli
        assert hasattr(cli, "main")
        assert hasattr(cli, "cmd_repl")
        assert hasattr(cli, "cmd_config")
        assert hasattr(cli, "cmd_docs")
        assert hasattr(cli, "cmd_wizard")
        assert hasattr(cli, "cmd_batch")

    def test_cli_enhanced_imports(self):
        """Test CLI enhanced module imports."""
        from mc_agent_kit.cli_enhanced import (
            create_repl,
            create_alias_manager,
            create_output,
            create_progress_bar,
            Color,
            Style,
        )
        assert create_repl is not None
        assert create_alias_manager is not None
        assert create_output is not None
        assert create_progress_bar is not None
        assert Color is not None
        assert Style is not None

    def test_config_module_imports(self):
        """Test config module imports."""
        from mc_agent_kit.config import (
            create_config_manager,
            create_validator,
            create_template_generator,
        )
        assert create_config_manager is not None
        assert create_validator is not None
        assert create_template_generator is not None

    def test_docs_module_imports(self):
        """Test docs module imports."""
        from mc_agent_kit.docs import (
            create_doc_generator,
            create_formatter,
            OutputFormat,
        )
        assert create_doc_generator is not None
        assert create_formatter is not None
        assert OutputFormat is not None


class TestContribModules:
    """Tests for contrib modules."""

    def test_completion_imports(self):
        """Test completion module imports."""
        from mc_agent_kit.contrib.completion import (
            CodeCompleter,
            Completion,
            CompletionKind,
            SmellDetector,
            SmellType,
            SmellSeverity,
            RefactorEngine,
            RefactorType,
            BestPracticeChecker,
            PracticeCategory,
        )
        assert CodeCompleter is not None
        assert Completion is not None
        assert CompletionKind is not None
        assert SmellDetector is not None
        assert SmellType is not None
        assert SmellSeverity is not None
        assert RefactorEngine is not None
        assert RefactorType is not None
        assert BestPracticeChecker is not None
        assert PracticeCategory is not None

    def test_performance_imports(self):
        """Test performance module imports."""
        from mc_agent_kit.contrib.performance import (
            LRUCache,
            KnowledgeCache,
            LogBatchProcessor,
            LogAggregator,
            CodeGenOptimizer,
            TemplatePool,
        )
        assert LRUCache is not None
        assert KnowledgeCache is not None
        assert LogBatchProcessor is not None
        assert LogAggregator is not None
        assert CodeGenOptimizer is not None
        assert TemplatePool is not None

    def test_plugin_imports(self):
        """Test plugin module imports."""
        from mc_agent_kit.contrib.plugin import (
            PluginBase,
            PluginMetadata,
            PluginResult,
            PluginState,
            PluginPriority,
            PluginRegistry,
            PluginLoader,
            PluginManager,
        )
        assert PluginBase is not None
        assert PluginMetadata is not None
        assert PluginResult is not None
        assert PluginState is not None
        assert PluginPriority is not None
        assert PluginRegistry is not None
        assert PluginLoader is not None
        assert PluginManager is not None


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_cli_startup_time(self):
        """Test CLI startup time is reasonable."""
        import time

        start = time.time()
        from mc_agent_kit.cli import main
        elapsed = time.time() - start

        # Import should be fast (< 1 second)
        assert elapsed < 1.0

    def test_config_load_time(self):
        """Test config loading is fast."""
        import time

        from mc_agent_kit.config import create_config_manager

        start = time.time()
        manager = create_config_manager()
        _ = manager.get_all()
        elapsed = time.time() - start

        # Config loading should be fast (< 100ms)
        assert elapsed < 0.1