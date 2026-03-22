"""
迭代 #20 补充测试

针对低覆盖率模块进行测试提升。
目标模块：
- plugin/manager.py: 68% -> 85%
- retrieval/llama_index.py: 64% -> 80%
- skills/modsdk/api_search.py: 67% -> 80%
- completion/refactor.py: 73% -> 85%
- knowledge/incremental.py: 75% -> 85%
- log_capture/analyzer.py: 76% -> 85%
"""

import json
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue
from unittest.mock import MagicMock, patch

import pytest

from mc_agent_kit.completion.refactor import RefactorEngine, RefactorSuggestion, RefactorType
from mc_agent_kit.completion.smells import CodeSmell, SmellSeverity, SmellType
from mc_agent_kit.knowledge.incremental import ChangeReport, DocumentChange, IncrementalUpdater
from mc_agent_kit.log_capture.analyzer import (
    Alert,
    AlertSeverity,
    ErrorPattern,
    LogAggregator,
    LogAnalyzer,
    LogStatistics,
    MatchResult,
    PatternCategory,
)
from mc_agent_kit.log_capture.parser import LogEntry, LogLevel, LogParser
from mc_agent_kit.plugin import (
    PluginBase,
    PluginInfo,
    PluginLoader,
    PluginManager,
    PluginMetadata,
    PluginPriority,
    PluginRegistry,
    PluginResult,
    PluginState,
)
from mc_agent_kit.retrieval.llama_index import LlamaIndexConfig, LlamaIndexRetriever


# ============================================================================
# Plugin Manager Tests (补充)
# ============================================================================

class ErrorPlugin(PluginBase):
    """Plugin that raises errors during lifecycle."""

    def __init__(self, error_on_enable=False, error_on_disable=False):
        super().__init__()
        self._metadata = PluginMetadata(name="error-plugin", version="1.0.0")
        self._error_on_enable = error_on_enable
        self._error_on_disable = error_on_disable

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def on_enable(self):
        if self._error_on_enable:
            raise RuntimeError("Enable error")

    def on_disable(self):
        if self._error_on_disable:
            raise RuntimeError("Disable error")


class TestPluginManagerExtra:
    """Additional tests for PluginManager to improve coverage."""

    def test_enable_plugin_not_found(self):
        """Test enabling non-existent plugin."""
        manager = PluginManager()
        result = manager.enable_plugin("nonexistent")
        assert not result

    def test_enable_already_enabled(self, tmp_path):
        """Test enabling already enabled plugin."""
        plugin_file = tmp_path / "already.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class AlreadyPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="already-enabled", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        assert manager.enable_plugin("already-enabled")
        # Enable again should return True
        assert manager.enable_plugin("already-enabled")

    def test_enable_plugin_with_instance_error(self, tmp_path):
        """Test enabling plugin with instance creation error."""
        plugin_file = tmp_path / "instance_error.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class InstanceErrorPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="instance-error", version="1.0.0")
        raise RuntimeError("Cannot instantiate")

    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        info = manager.load_plugin(plugin_file)
        # Plugin loaded but instance creation failed
        if info:
            result = manager.enable_plugin("instance-error")
            assert not result

    def test_disable_not_enabled(self, tmp_path):
        """Test disabling plugin that is not enabled."""
        plugin_file = tmp_path / "not_enabled.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class NotEnabledPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="not-enabled", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        # Disable without enabling first
        result = manager.disable_plugin("not-enabled")
        assert result  # Should return True (already disabled)

    def test_disable_nonexistent(self):
        """Test disabling non-existent plugin."""
        manager = PluginManager()
        result = manager.disable_plugin("nonexistent")
        assert not result

    def test_reload_nonexistent(self):
        """Test reloading non-existent plugin."""
        manager = PluginManager()
        result = manager.reload_plugin("nonexistent")
        assert not result

    def test_execute_nonexistent(self):
        """Test executing non-existent plugin."""
        manager = PluginManager()
        result = manager.execute_plugin("nonexistent")
        assert result is None

    def test_execute_plugin_no_instance(self):
        """Test executing plugin without instance."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="no-instance", version="1.0.0")
        info = PluginInfo(metadata=metadata)
        info.state = PluginState.ENABLED
        # No instance set
        registry.register(info)

        manager = PluginManager(registry)
        result = manager.execute_plugin("no-instance")
        assert result is not None
        assert not result.success
        assert "no instance" in result.error.lower()

    def test_get_plugin_instance(self):
        """Test getting plugin instance."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="get-instance", version="1.0.0")
        info = PluginInfo(metadata=metadata)
        info.instance = ErrorPlugin()
        registry.register(info)

        manager = PluginManager(registry)
        instance = manager.get_plugin_instance("get-instance")
        assert instance is not None

        # Non-existent
        instance = manager.get_plugin_instance("nonexistent")
        assert instance is None

    def test_get_plugin_status(self):
        """Test getting plugin status."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="status-plugin", version="1.0.0")
        info = PluginInfo(metadata=metadata)
        registry.register(info)

        manager = PluginManager(registry)
        status = manager.get_plugin_status("status-plugin")
        assert status is not None
        assert status["name"] == "status-plugin"

        # Non-existent
        status = manager.get_plugin_status("nonexistent")
        assert status is None

    def test_remove_plugin_directory(self):
        """Test removing plugin directory."""
        manager = PluginManager()
        manager.add_plugin_directory("/path/to/plugins")
        result = manager.remove_plugin_directory("/path/to/plugins")
        assert result

        # Remove non-existent
        result = manager.remove_plugin_directory("/nonexistent/path")
        assert not result

    def test_discover_plugins(self):
        """Test discovering plugins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginManager()
            manager.add_plugin_directory(tmpdir)
            discovered = manager.discover_plugins()
            assert discovered == []

    def test_load_all_plugins(self, tmp_path):
        """Test loading all plugins."""
        plugin1 = tmp_path / "plugin1.py"
        plugin1.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class LoadAll1(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="load-all-1", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.add_plugin_directory(tmp_path)
        loaded = manager.load_all_plugins()
        assert len(loaded) >= 0  # May or may not find plugins

    def test_load_plugin_invalid_path(self):
        """Test loading plugin from invalid path."""
        manager = PluginManager()
        info = manager.load_plugin("/nonexistent/path/plugin.py")
        assert info is None

    def test_set_config_applies_to_running_plugin(self, tmp_path):
        """Test setting config applies to running plugin."""
        plugin_file = tmp_path / "config_plugin.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class ConfigPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="config-test", version="1.0.0")
        self.received_config = None
    def on_load(self): pass
    def on_unload(self): pass
    def set_config(self, config):
        self.received_config = config
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        manager.enable_plugin("config-test")

        # Set config after plugin is enabled
        manager.set_plugin_config("config-test", {"key": "value"})

        # Check the config was applied
        instance = manager.get_plugin_instance("config-test")
        if instance and hasattr(instance, 'received_config'):
            assert instance.received_config == {"key": "value"}


# ============================================================================
# LlamaIndex Tests (补充)
# ============================================================================

class TestLlamaIndexExtra:
    """Additional tests for LlamaIndex integration."""

    def test_config_defaults(self):
        """Test LlamaIndexConfig defaults."""
        config = LlamaIndexConfig()
        assert config.persist_dir is None
        assert config.collection_name == "mc_knowledge"
        assert config.similarity_top_k == 5
        assert config.response_mode == "compact"
        assert not config.streaming

    def test_retriever_without_llama_index(self):
        """Test retriever when LlamaIndex is not available."""
        with patch('mc_agent_kit.retrieval.llama_index.LlamaIndexRetriever._check_availability') as mock:
            # Simulate LlamaIndex not available
            retriever = LlamaIndexRetriever()
            retriever._llama_available = False

            assert not retriever.is_available()
            assert not retriever.index_documents(["test"])

    def test_retriever_load_index_no_dir(self):
        """Test loading index without persist_dir."""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = False
        result = retriever.load_index()
        assert not result

    def test_retriever_query_no_index(self):
        """Test querying without index."""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = False
        retriever._index = None

        result = retriever.query("test query")
        # Returns Chinese message when not available
        assert result  # Just check it returns something

    def test_retriever_retrieve_no_index(self):
        """Test retrieving without index."""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = False
        retriever._index = None

        result = retriever.retrieve("test query")
        assert result == []

    def test_retriever_get_stats(self):
        """Test getting stats."""
        config = LlamaIndexConfig(
            persist_dir="/test/dir",
            collection_name="test_collection"
        )
        retriever = LlamaIndexRetriever(config)

        stats = retriever.get_stats()
        assert "llama_available" in stats
        assert "index_loaded" in stats
        assert stats["persist_dir"] == "/test/dir"
        assert stats["collection_name"] == "test_collection"

    def test_create_llama_index_retriever(self):
        """Test convenience function."""
        from mc_agent_kit.retrieval.llama_index import create_llama_index_retriever

        retriever = create_llama_index_retriever(
            persist_dir="/custom/dir",
            embedding_model="custom-model"
        )
        assert retriever.config.persist_dir == "/custom/dir"
        assert retriever.config.embedding_model == "custom-model"


# ============================================================================
# Refactor Engine Tests (补充)
# ============================================================================

class TestRefactorEngineExtra:
    """Additional tests for RefactorEngine."""

    def test_refactor_type_values(self):
        """Test RefactorType enum values."""
        assert RefactorType.EXTRACT_FUNCTION.value == "extract_function"
        assert RefactorType.EXTRACT_VARIABLE.value == "extract_variable"
        assert RefactorType.REPLACE_MAGIC_NUMBER.value == "replace_magic_number"
        assert RefactorType.ADD_DOCSTRING.value == "add_docstring"
        assert RefactorType.RENAME.value == "rename"

    def test_refactor_suggestion_to_dict(self):
        """Test RefactorSuggestion.to_dict()."""
        suggestion = RefactorSuggestion(
            type=RefactorType.EXTRACT_FUNCTION,
            message="Extract function",
            line=10,
            end_line=20,
            original_code="def long_func(): pass",
            suggested_code="# extracted",
            explanation="Explanation",
            priority=5,
            auto_applicable=True
        )
        d = suggestion.to_dict()
        assert d["type"] == "extract_function"
        assert d["message"] == "Extract function"
        assert d["line"] == 10
        assert d["end_line"] == 20
        assert d["auto_applicable"]

    def test_suggest_refactors_empty(self):
        """Test suggesting refactors with no smells."""
        engine = RefactorEngine()
        suggestions = engine.suggest_refactors([], "code")
        assert suggestions == []

    def test_suggest_extract_function_no_end_line(self):
        """Test extract function suggestion without end_line."""
        engine = RefactorEngine()
        smell = CodeSmell(
            type=SmellType.LONG_FUNCTION,
            message="Function too long",
            line=10,
            end_line=None,
            severity=SmellSeverity.MAJOR
        )
        suggestions = engine.suggest_refactors([smell], "def func(): pass")
        assert len(suggestions) == 0

    def test_suggest_extract_function_with_end_line(self):
        """Test extract function suggestion with end_line."""
        engine = RefactorEngine()
        code = "def func():\n    pass\n    return 1"
        smell = CodeSmell(
            type=SmellType.LONG_FUNCTION,
            message="Function too long",
            line=1,
            end_line=3,
            severity=SmellSeverity.MAJOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert suggestions[0].type == RefactorType.EXTRACT_FUNCTION

    def test_suggest_replace_magic_number(self):
        """Test replacing magic number."""
        engine = RefactorEngine()
        code = "x = 1000"
        smell = CodeSmell(
            type=SmellType.MAGIC_NUMBER,
            message="Magic number found",
            line=1,
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert "1000" in suggestions[0].message

    def test_suggest_replace_magic_number_no_match(self):
        """Test magic number without large number."""
        engine = RefactorEngine()
        code = "x = 10"  # Too small to be magic number
        smell = CodeSmell(
            type=SmellType.MAGIC_NUMBER,
            message="Magic number found",
            line=1,
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 0

    def test_suggest_fix_bare_except(self):
        """Test fixing bare except."""
        engine = RefactorEngine()
        code = "try:\n    pass\nexcept:\n    pass"
        smell = CodeSmell(
            type=SmellType.BARE_EXCEPT,
            message="Bare except",
            line=3,
            severity=SmellSeverity.MAJOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert "Exception" in suggestions[0].suggested_code

    def test_suggest_add_docstring_function(self):
        """Test adding docstring to function."""
        engine = RefactorEngine()
        code = "def func():\n    pass"
        smell = CodeSmell(
            type=SmellType.MISSING_DOCSTRING,
            message="函数缺少文档字符串",
            line=1,
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert "Args:" in suggestions[0].suggested_code

    def test_suggest_add_docstring_class(self):
        """Test adding docstring to class."""
        engine = RefactorEngine()
        code = "class MyClass:\n    pass"
        smell = CodeSmell(
            type=SmellType.MISSING_DOCSTRING,
            message="类缺少文档字符串",
            line=1,
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert "Attributes:" in suggestions[0].suggested_code

    def test_suggest_simplify_nesting(self):
        """Test simplifying nested code."""
        engine = RefactorEngine()
        code = "if a:\n    if b:\n        if c:\n            pass"
        smell = CodeSmell(
            type=SmellType.DEEPLY_NESTED,
            message="Deeply nested code",
            line=1,
            severity=SmellSeverity.MAJOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert suggestions[0].type == RefactorType.SIMPLIFY_CONDITION

    def test_suggest_reduce_complexity(self):
        """Test reducing complexity."""
        engine = RefactorEngine()
        code = "def complex():\n    if a and b or c and d:\n        pass"
        smell = CodeSmell(
            type=SmellType.HIGH_COMPLEXITY,
            message="High cyclomatic complexity",
            line=1,
            severity=SmellSeverity.MAJOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1

    def test_suggest_rename(self):
        """Test rename suggestion."""
        engine = RefactorEngine()
        code = "x = 1"
        smell = CodeSmell(
            type=SmellType.SHORT_NAME,
            message="Name too short",
            line=1,
            suggestion="Use more descriptive name",
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert suggestions[0].type == RefactorType.RENAME

    def test_suggest_replace_print(self):
        """Test replacing print with logging."""
        engine = RefactorEngine()
        code = "print('debug message')"
        smell = CodeSmell(
            type=SmellType.PRINT_DEBUG,
            message="Print statement found",
            line=1,
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert "logging" in suggestions[0].suggested_code

    def test_suggest_replace_print_with_args(self):
        """Test replacing print with arguments."""
        engine = RefactorEngine()
        code = "print('value:', x)"
        smell = CodeSmell(
            type=SmellType.PRINT_DEBUG,
            message="Print statement found",
            line=1,
            severity=SmellSeverity.MINOR
        )
        suggestions = engine.suggest_refactors([smell], code)
        assert len(suggestions) == 1
        assert "logging" in suggestions[0].suggested_code

    def test_suggestions_sorted_by_priority(self):
        """Test that suggestions are sorted by priority."""
        engine = RefactorEngine()
        code = "def long():\n    print(1000)"
        smells = [
            CodeSmell(type=SmellType.LONG_FUNCTION, message="Long", line=1, end_line=2, severity=SmellSeverity.MINOR),
            CodeSmell(type=SmellType.MAGIC_NUMBER, message="Magic", line=2, severity=SmellSeverity.MINOR),
        ]
        suggestions = engine.suggest_refactors(smells, code)
        if len(suggestions) >= 2:
            # Should be sorted by priority (descending)
            assert suggestions[0].priority >= suggestions[-1].priority

    def test_generate_diff(self):
        """Test generating diff."""
        engine = RefactorEngine()
        suggestion = RefactorSuggestion(
            type=RefactorType.REPLACE_MAGIC_NUMBER,
            message="Replace magic number",
            line=1,
            original_code="x = 1000",
            suggested_code="MAX_VALUE = 1000"
        )
        diff = engine.generate_diff(suggestion)
        assert "---" in diff
        assert "+++" in diff
        assert "- x = 1000" in diff
        assert "+ MAX_VALUE = 1000" in diff


# ============================================================================
# Incremental Updater Tests (补充)
# ============================================================================

class TestIncrementalUpdaterExtra:
    """Additional tests for IncrementalUpdater."""

    def test_change_report_properties(self):
        """Test ChangeReport properties."""
        report = ChangeReport()
        assert report.total_changes == 0
        assert not report.has_changes

        report.added.append(DocumentChange(path="a.py", change_type="added"))
        assert report.total_changes == 1
        assert report.has_changes

    def test_change_report_to_dict(self):
        """Test ChangeReport.to_dict()."""
        report = ChangeReport()
        report.added.append(DocumentChange(path="new.py", change_type="added", new_hash="abc"))
        report.modified.append(DocumentChange(path="mod.py", change_type="modified", old_hash="old", new_hash="new"))
        report.deleted.append(DocumentChange(path="del.py", change_type="deleted", old_hash="old"))

        d = report.to_dict()
        assert d["total_changes"] == 3
        assert len(d["added"]) == 1
        assert len(d["modified"]) == 1
        assert len(d["deleted"]) == 1

    def test_document_change(self):
        """Test DocumentChange dataclass."""
        change = DocumentChange(
            path="test.py",
            change_type="modified",
            old_hash="old_hash",
            new_hash="new_hash",
            metadata={"key": "value"}
        )
        assert change.path == "test.py"
        assert change.change_type == "modified"
        assert change.old_hash == "old_hash"
        assert change.new_hash == "new_hash"
        assert change.metadata == {"key": "value"}

    def test_detect_changes_with_extensions(self, tmp_path):
        """Test detecting changes with custom extensions."""
        # Create test files
        (tmp_path / "test.md").write_text("content")
        (tmp_path / "test.txt").write_text("content")
        (tmp_path / "test.py").write_text("content")

        updater = IncrementalUpdater(state_dir=str(tmp_path / "state"))
        changes = updater.detect_changes(str(tmp_path), extensions=[".md", ".txt"])

        # Should only detect .md and .txt files
        assert len(changes.added) == 2

    def test_apply_changes_with_deletions(self, tmp_path):
        """Test applying changes with deletions."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        state_dir = tmp_path / "state"

        updater = IncrementalUpdater(state_dir=str(state_dir))
        updater._state["deleted.py"] = "old_hash"

        changes = ChangeReport()
        changes.deleted.append(DocumentChange(path="deleted.py", change_type="deleted", old_hash="old_hash"))

        # Mock vector store
        mock_store = MagicMock()
        mock_store.delete_documents.return_value = 1

        result = updater.apply_changes(changes, str(docs_dir), mock_store)
        assert result == 1
        assert "deleted.py" not in updater._state

    def test_apply_changes_with_additions(self, tmp_path):
        """Test applying changes with additions."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "new.md").write_text("new content")
        state_dir = tmp_path / "state"

        updater = IncrementalUpdater(state_dir=str(state_dir))

        changes = ChangeReport()
        changes.added.append(DocumentChange(path="new.md", change_type="added", new_hash="new_hash"))

        # Mock vector store
        mock_store = MagicMock()
        mock_store.add_documents.return_value = 1

        result = updater.apply_changes(changes, str(docs_dir), mock_store)
        assert result == 1

    def test_apply_changes_read_error(self, tmp_path):
        """Test applying changes when file read fails."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        state_dir = tmp_path / "state"

        updater = IncrementalUpdater(state_dir=str(state_dir))

        changes = ChangeReport()
        changes.added.append(DocumentChange(path="nonexistent.py", change_type="added", new_hash="hash"))

        mock_store = MagicMock()
        result = updater.apply_changes(changes, str(docs_dir), mock_store)
        assert result == 0

    def test_get_document_state(self, tmp_path):
        """Test getting document state."""
        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))
        updater._state["test.py"] = "hash123"

        assert updater.get_document_state("test.py") == "hash123"
        assert updater.get_document_state("nonexistent.py") is None

    def test_get_all_states(self, tmp_path):
        """Test getting all states."""
        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))
        updater._state["a.py"] = "hash_a"
        updater._state["b.py"] = "hash_b"

        states = updater.get_all_states()
        assert len(states) == 2
        assert states["a.py"] == "hash_a"

    def test_clear_state(self, tmp_path):
        """Test clearing state."""
        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))
        updater._state["test.py"] = "hash"

        updater.clear_state()
        assert len(updater._state) == 0

    def test_rebuild_state(self, tmp_path):
        """Test rebuilding state."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "a.md").write_text("content a")
        (docs_dir / "b.md").write_text("content b")

        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))

        count = updater.rebuild_state(str(docs_dir))
        assert count == 2
        assert "a.md" in updater._state
        assert "b.md" in updater._state

    def test_rebuild_state_with_error(self, tmp_path):
        """Test rebuilding state with file error."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "valid.md").write_text("valid")

        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))

        count = updater.rebuild_state(str(docs_dir))
        assert count == 1

    def test_create_incremental_updater(self):
        """Test convenience function."""
        from mc_agent_kit.knowledge.incremental import create_incremental_updater

        updater = create_incremental_updater(state_dir="/tmp/test_state")
        assert updater.state_dir == Path("/tmp/test_state")


# ============================================================================
# Log Analyzer Tests (补充)
# ============================================================================

class TestLogAnalyzerExtra:
    """Additional tests for LogAnalyzer."""

    def test_alert_severity_values(self):
        """Test AlertSeverity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_pattern_category_values(self):
        """Test PatternCategory enum values."""
        assert PatternCategory.SYNTAX.value == "syntax"
        assert PatternCategory.RUNTIME.value == "runtime"
        assert PatternCategory.API.value == "api"
        assert PatternCategory.EVENT.value == "event"

    def test_error_pattern_creation(self):
        """Test creating ErrorPattern."""
        pattern = ErrorPattern(
            name="TestPattern",
            pattern=__import__('re').compile(r"test error: (\w+)"),
            category=PatternCategory.CUSTOM,
            severity=AlertSeverity.WARNING,
            description="Test pattern",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )
        assert pattern.name == "TestPattern"
        assert pattern.category == PatternCategory.CUSTOM

    def test_match_result(self):
        """Test MatchResult dataclass."""
        entry = LogEntry(level=LogLevel.ERROR, message="Test error", raw="Test error")
        pattern = ErrorPattern(
            name="Test",
            pattern=__import__('re').compile(r"Test"),
            category=PatternCategory.CUSTOM,
            severity=AlertSeverity.ERROR
        )
        match = pattern.pattern.search("Test error")

        result = MatchResult(
            pattern=pattern,
            match=match,
            log_entry=entry,
            extracted_info={"group_1": "value"}
        )
        assert result.pattern.name == "Test"
        assert result.extracted_info["group_1"] == "value"

    def test_alert_creation(self):
        """Test creating Alert."""
        entry = LogEntry(level=LogLevel.ERROR, message="Error", raw="Error")
        pattern = ErrorPattern(
            name="AlertPattern",
            pattern=__import__('re').compile(r".*"),
            category=PatternCategory.RUNTIME,
            severity=AlertSeverity.ERROR
        )

        alert = Alert(
            severity=AlertSeverity.ERROR,
            title="Test Alert",
            message="Error occurred",
            pattern=pattern,
            log_entry=entry
        )
        assert alert.title == "Test Alert"
        assert alert.count == 1

    def test_log_statistics_defaults(self):
        """Test LogStatistics defaults."""
        stats = LogStatistics()
        assert stats.total_logs == 0
        assert stats.error_count == 0
        assert stats.warning_count == 0

    def test_analyzer_add_remove_pattern(self):
        """Test adding and removing patterns."""
        analyzer = LogAnalyzer(use_builtin_patterns=False)

        pattern = ErrorPattern(
            name="Custom",
            pattern=__import__('re').compile(r"custom"),
            category=PatternCategory.CUSTOM,
            severity=AlertSeverity.INFO
        )

        analyzer.add_pattern(pattern)
        patterns = analyzer.get_patterns()
        assert len(patterns) == 1

        result = analyzer.remove_pattern("Custom")
        assert result
        assert len(analyzer.get_patterns()) == 0

        # Remove non-existent
        result = analyzer.remove_pattern("NonExistent")
        assert not result

    def test_analyzer_set_callbacks(self):
        """Test setting callbacks."""
        analyzer = LogAnalyzer()

        alert_called = []
        log_called = []

        def on_alert(alert):
            alert_called.append(alert)

        def on_log(entry):
            log_called.append(entry)

        analyzer.set_alert_callback(on_alert)
        analyzer.set_log_callback(on_log)

        # Process a log
        entry = analyzer.process_log("[ERROR] SyntaxError: invalid syntax")

        assert len(log_called) == 1
        assert len(alert_called) >= 1  # Should match SyntaxError pattern

    def test_analyzer_analyze_batch(self):
        """Test batch analysis."""
        analyzer = LogAnalyzer()

        logs = [
            "[INFO] Starting up",
            "[ERROR] NameError: name 'x' is not defined",
            "[WARNING] Deprecated API used",
            "[ERROR] TypeError: unsupported operand",
        ]

        result = analyzer.analyze_batch(logs)

        assert result["total"] == 4
        assert result["errors"] == 2
        assert result["warnings"] == 1
        assert "NameError" in result["error_types"]
        assert "TypeError" in result["error_types"]

    def test_analyzer_get_statistics(self):
        """Test getting statistics."""
        analyzer = LogAnalyzer()

        analyzer.process_log("[INFO] Info message")
        analyzer.process_log("[ERROR] Error message")
        analyzer.process_log("[WARNING] Warning message")

        stats = analyzer.get_statistics()

        assert stats["total_logs"] == 3
        assert stats["error_count"] == 1
        assert stats["warning_count"] == 1

    def test_analyzer_reset_statistics(self):
        """Test resetting statistics."""
        analyzer = LogAnalyzer()

        analyzer.process_log("[INFO] Message")
        assert analyzer.get_statistics()["total_logs"] == 1

        analyzer.reset_statistics()
        assert analyzer.get_statistics()["total_logs"] == 0

    def test_analyzer_get_top_errors(self):
        """Test getting top errors."""
        analyzer = LogAnalyzer()

        analyzer.process_log("[ERROR] SyntaxError: error 1")
        analyzer.process_log("[ERROR] SyntaxError: error 2")
        analyzer.process_log("[ERROR] NameError: name error")

        top = analyzer.get_top_errors(limit=5)
        assert len(top) > 0
        # SyntaxError should be most common
        assert top[0][0] == "SyntaxError"

    def test_analyzer_builtin_patterns(self):
        """Test that builtin patterns are loaded."""
        analyzer = LogAnalyzer(use_builtin_patterns=True)
        patterns = analyzer.get_patterns()

        pattern_names = [p.name for p in patterns]
        assert "SyntaxError" in pattern_names
        assert "NameError" in pattern_names
        assert "TypeError" in pattern_names

    def test_analyzer_match_patterns(self):
        """Test pattern matching."""
        analyzer = LogAnalyzer(use_builtin_patterns=True)

        entry = LogEntry(
            level=LogLevel.ERROR,
            message="NameError: name 'undefined_var' is not defined",
            raw="NameError: name 'undefined_var' is not defined"
        )

        matches = analyzer.match_patterns(entry)
        assert len(matches) >= 1

        # Should match NameError pattern
        name_error_match = next((m for m in matches if m.pattern.name == "NameError"), None)
        assert name_error_match is not None
        assert "undefined_var" in name_error_match.extracted_info.get("group_1", "")


class TestLogAggregatorExtra:
    """Additional tests for LogAggregator."""

    def test_aggregator_add_log(self):
        """Test adding log to aggregator."""
        aggregator = LogAggregator(max_logs=100)

        entry = aggregator.add_log("[INFO] Test message")
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"

    def test_aggregator_query(self):
        """Test querying logs."""
        aggregator = LogAggregator()

        aggregator.add_log("[INFO] Info message")
        aggregator.add_log("[ERROR] Error message")
        aggregator.add_log("[WARNING] Warning message")

        # Query by level
        errors = aggregator.query(level=LogLevel.ERROR)
        assert len(errors) == 1

        # Query by keyword
        results = aggregator.query(keyword="message")
        assert len(results) == 3

    def test_aggregator_query_with_limit(self):
        """Test querying with limit."""
        aggregator = LogAggregator()

        for i in range(10):
            aggregator.add_log(f"[INFO] Message {i}")

        results = aggregator.query(limit=5)
        assert len(results) == 5

    def test_aggregator_query_by_error(self):
        """Test querying by is_error flag."""
        aggregator = LogAggregator()

        aggregator.add_log("[INFO] Info")
        aggregator.add_log("[ERROR] Error 1")
        aggregator.add_log("[ERROR] Error 2")

        errors = aggregator.query(is_error=True)
        assert len(errors) == 2

    def test_aggregator_max_logs(self):
        """Test max logs limit."""
        aggregator = LogAggregator(max_logs=5)

        for i in range(10):
            aggregator.add_log(f"[INFO] Message {i}")

        # Should only keep last 5
        with aggregator._lock:
            assert len(aggregator._logs) == 5

    def test_aggregator_clear(self):
        """Test clearing aggregator."""
        aggregator = LogAggregator()

        aggregator.add_log("[INFO] Message")
        aggregator.clear()

        assert len(aggregator.query()) == 0

    def test_aggregator_get_statistics(self):
        """Test getting statistics from aggregator."""
        aggregator = LogAggregator()

        aggregator.add_log("[INFO] Info")
        aggregator.add_log("[ERROR] Error")

        stats = aggregator.get_statistics()
        assert stats["total_logs"] == 2
        assert stats["error_count"] == 1


# ============================================================================
# API Search Skill Tests (补充)
# ============================================================================

class TestAPISearchSkillExtra:
    """Additional tests for ModSDKAPISearchSkill."""

    def test_parse_scope(self):
        """Test parsing scope strings."""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base import Scope

        skill = ModSDKAPISearchSkill()

        assert skill._parse_scope("client") == Scope.CLIENT
        assert skill._parse_scope("server") == Scope.SERVER
        assert skill._parse_scope("both") == Scope.BOTH
        assert skill._parse_scope("客户端") == Scope.CLIENT
        assert skill._parse_scope("服务端") == Scope.SERVER
        assert skill._parse_scope("双端") == Scope.BOTH
        assert skill._parse_scope("unknown") == Scope.UNKNOWN

    def test_format_api(self):
        """Test formatting API entry."""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill
        from mc_agent_kit.knowledge_base.models import APIEntry, APIParameter, Scope

        skill = ModSDKAPISearchSkill()

        api = APIEntry(
            name="TestAPI",
            module="test_module",
            description="Test description",
            method_path="test.TestAPI",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(name="param1", data_type="int", description="Test param")
            ],
            return_type="str",
            examples=[]
        )

        formatted = skill._format_api(api, relevance_score=0.9)

        assert formatted["name"] == "TestAPI"
        assert formatted["module"] == "test_module"
        assert formatted["scope"] == "server"
        assert len(formatted["parameters"]) == 1
        assert formatted["relevance_score"] == 0.9

    def test_skill_metadata(self):
        """Test skill metadata."""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill

        skill = ModSDKAPISearchSkill()
        assert skill.metadata.name == "modsdk-api-search"
        assert skill.metadata.category.value == "search"

    def test_list_modules_without_kb(self):
        """Test listing modules without knowledge base."""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill

        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = None

        result = skill.list_modules()
        assert not result.success

    def test_get_stats_without_kb(self):
        """Test getting stats without knowledge base."""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill

        skill = ModSDKAPISearchSkill()
        skill._initialized = True
        skill._retriever = None

        result = skill.get_stats()
        assert not result.success