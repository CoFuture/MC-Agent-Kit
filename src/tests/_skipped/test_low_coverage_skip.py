"""Additional tests for low coverage modules."""

import time
from unittest.mock import MagicMock, patch

import pytest

from mc_agent_kit.knowledge import (
    ChangeReport,
    Document,
    DocumentChange,
    DocumentChunk,
    DocumentType,
    IncrementalUpdater,
    KnowledgeBase,
    SearchResult,
    create_knowledge_tool,
)
from mc_agent_kit.performance.batch import (
    BatchConfig,
    BatchResult,
    LogAggregator,
    LogBatchProcessor,
)
from mc_agent_kit.performance.optimization import (
    CodeGenOptimizer,
    OptimizationConfig,
    OptimizationStats,
    TemplatePool,
)


class TestCreateKnowledgeTool:
    """Tests for create_knowledge_tool function."""

    def test_create_tool(self):
        """Test creating knowledge tool."""
        kb = MagicMock(spec=KnowledgeBase)
        tool = create_knowledge_tool(kb)
        assert callable(tool)

    def test_tool_search_with_results(self):
        """Test tool search with results."""
        kb = MagicMock(spec=KnowledgeBase)
        kb.search.return_value = [
            SearchResult(
                source="test.md",
                doc_type="api",
                content="Test content here",
                score=0.95,
            )
        ]

        tool = create_knowledge_tool(kb)
        result = tool("test query")

        assert "## 结果 1" in result
        assert "test.md" in result
        assert "0.95" in result
        kb.search.assert_called_once_with("test query", doc_type="all", top_k=5)

    def test_tool_search_no_results(self):
        """Test tool search with no results."""
        kb = MagicMock(spec=KnowledgeBase)
        kb.search.return_value = []

        tool = create_knowledge_tool(kb)
        result = tool("nonexistent")

        assert result == "未找到相关内容"

    def test_tool_search_with_doc_type(self):
        """Test tool search with specific doc type."""
        kb = MagicMock(spec=KnowledgeBase)
        kb.search.return_value = []

        tool = create_knowledge_tool(kb)
        tool("query", doc_type="api", top_k=10)

        kb.search.assert_called_once_with("query", doc_type="api", top_k=10)

    def test_tool_search_multiple_results(self):
        """Test tool with multiple results."""
        kb = MagicMock(spec=KnowledgeBase)
        kb.search.return_value = [
            SearchResult(source="a.md", doc_type="api", content="A", score=0.9),
            SearchResult(source="b.md", doc_type="guide", content="B", score=0.8),
        ]

        tool = create_knowledge_tool(kb)
        result = tool("query")

        assert "## 结果 1" in result
        assert "## 结果 2" in result


class TestIncrementalUpdaterExtra:
    """Additional tests for IncrementalUpdater."""

    def test_detect_changes_with_no_state(self, tmp_path):
        """Test detecting changes without prior state."""
        updater = IncrementalUpdater(state_dir=str(tmp_path / "state"))

        # Create a file
        doc = tmp_path / "doc.md"
        doc.write_text("content")

        changes = updater.detect_changes(tmp_path)
        assert len(changes.added) == 1

    def test_detect_changes_with_existing_state(self, tmp_path):
        """Test detecting changes with existing state."""
        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))

        # Create and scan file
        doc = tmp_path / "doc.md"
        doc.write_text("content")

        # First detection - added
        changes = updater.detect_changes(tmp_path)
        assert len(changes.added) == 1

        # Update state manually (simulate apply_changes)
        updater._state[changes.added[0].path] = changes.added[0].new_hash
        updater._save_state()

        # No changes now
        changes = updater.detect_changes(tmp_path)
        assert changes.total_changes == 0

        # Modify file
        doc.write_text("modified content")
        changes = updater.detect_changes(tmp_path)
        assert len(changes.modified) == 1

    def test_detect_changes_deleted_file(self, tmp_path):
        """Test detecting deleted files."""
        state_dir = tmp_path / "state"
        updater = IncrementalUpdater(state_dir=str(state_dir))

        # Create and scan
        doc = tmp_path / "doc.md"
        doc.write_text("content")
        updater.detect_changes(tmp_path)
        updater._save_state()

        # Delete file
        doc.unlink()
        changes = updater.detect_changes(tmp_path)
        # Check if deleted changes are tracked
        assert isinstance(changes, ChangeReport)

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading state."""
        state_dir = tmp_path / "state"
        updater1 = IncrementalUpdater(state_dir=str(state_dir))

        # Create file
        doc = tmp_path / "doc.md"
        doc.write_text("content")
        changes = updater1.detect_changes(tmp_path)

        # Update state
        if changes.added:
            updater1._state[changes.added[0].path] = changes.added[0].new_hash
        updater1._save_state()

        # Load in new updater
        updater2 = IncrementalUpdater(state_dir=str(state_dir))
        assert len(updater2._state) > 0

    def test_change_report(self, tmp_path):
        """Test change report generation."""
        updater = IncrementalUpdater(state_dir=str(tmp_path / "state"))

        doc1 = tmp_path / "doc1.md"
        doc1.write_text("content1")
        doc2 = tmp_path / "doc2.md"
        doc2.write_text("content2")

        changes = updater.detect_changes(tmp_path)

        assert isinstance(changes, ChangeReport)
        assert len(changes.added) == 2


class TestCodeGenOptimizerExtra:
    """Additional tests for CodeGenOptimizer."""

    def test_generate_with_cache_disabled(self):
        """Test generation with cache disabled."""
        config = OptimizationConfig(enable_cache=False)
        optimizer = CodeGenOptimizer(config)

        call_count = 0

        def generate():
            nonlocal call_count
            call_count += 1
            return "result"

        # Should call generate every time
        result1 = optimizer.generate_with_cache("template", {"a": 1}, generate)
        result2 = optimizer.generate_with_cache("template", {"a": 1}, generate)

        assert result1 == "result"
        assert result2 == "result"
        assert call_count == 2

    def test_cache_hit(self):
        """Test cache hit."""
        optimizer = CodeGenOptimizer()

        call_count = 0

        def generate():
            nonlocal call_count
            call_count += 1
            return "cached"

        result1 = optimizer.generate_with_cache("t", {"p": 1}, generate)
        result2 = optimizer.generate_with_cache("t", {"p": 1}, generate)

        assert call_count == 1  # Only called once
        assert result1 == result2

    def test_cache_miss_different_params(self):
        """Test cache miss with different params."""
        optimizer = CodeGenOptimizer()

        call_count = 0

        def generate():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        result1 = optimizer.generate_with_cache("t", {"p": 1}, generate)
        result2 = optimizer.generate_with_cache("t", {"p": 2}, generate)

        assert call_count == 2
        assert result1 != result2

    def test_cache_ttl(self):
        """Test cache TTL."""
        config = OptimizationConfig(cache_ttl=0.1)
        optimizer = CodeGenOptimizer(config)

        call_count = 0

        def generate():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        result1 = optimizer.generate_with_cache("t", {"p": 1}, generate)
        time.sleep(0.15)
        result2 = optimizer.generate_with_cache("t", {"p": 1}, generate)

        assert call_count == 2  # Cache expired

    def test_cache_eviction(self):
        """Test cache eviction when full."""
        config = OptimizationConfig(max_cache_size=2)
        optimizer = CodeGenOptimizer(config)

        def generate():
            return "result"

        optimizer.generate_with_cache("t", {"p": 1}, generate)
        optimizer.generate_with_cache("t", {"p": 2}, generate)
        optimizer.generate_with_cache("t", {"p": 3}, generate)

        stats = optimizer.stats()
        assert stats["cache_size"] <= 2

    def test_invalidate_by_template(self):
        """Test invalidating cache by template."""
        optimizer = CodeGenOptimizer()

        def generate():
            return "result"

        optimizer.generate_with_cache("t1", {"p": 1}, generate)
        optimizer.generate_with_cache("t2", {"p": 1}, generate)

        count = optimizer.invalidate_cache("t1")
        assert count == 1

        stats = optimizer.stats()
        assert stats["cache_size"] == 1

    def test_invalidate_all(self):
        """Test invalidating all cache."""
        optimizer = CodeGenOptimizer()

        def generate():
            return "result"

        optimizer.generate_with_cache("t1", {"p": 1}, generate)
        optimizer.generate_with_cache("t2", {"p": 1}, generate)

        count = optimizer.invalidate_cache()
        assert count == 2

        stats = optimizer.stats()
        assert stats["cache_size"] == 0

    def test_preload_templates_disabled(self):
        """Test preload when disabled."""
        config = OptimizationConfig(preload_templates=False)
        optimizer = CodeGenOptimizer(config)

        result = optimizer.preload_templates(MagicMock())
        assert result == 0

    def test_preload_templates_success(self):
        """Test successful template preload."""
        optimizer = CodeGenOptimizer()
        tm = MagicMock()
        tm.list_templates.return_value = ["t1", "t2"]
        tm.get_template.return_value = "template"

        result = optimizer.preload_templates(tm)
        assert result == 2

    def test_preload_templates_exception(self):
        """Test preload with exception."""
        optimizer = CodeGenOptimizer()
        tm = MagicMock()
        tm.list_templates.side_effect = Exception("error")

        result = optimizer.preload_templates(tm)
        assert result == 0

    def test_stats_calculation(self):
        """Test stats calculation."""
        optimizer = CodeGenOptimizer()

        def generate():
            return "result"

        # First call generates and caches
        optimizer.generate_with_cache("t", {"p": 1}, generate)
        # Second call hits cache
        optimizer.generate_with_cache("t", {"p": 1}, generate)
        # Third call with different params is a miss
        optimizer.generate_with_cache("t", {"p": 2}, generate)

        stats = optimizer.stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 2
        assert stats["total_generations"] == 2  # Only for actual generation calls


class TestTemplatePool:
    """Tests for TemplatePool."""

    def test_warmup(self):
        """Test template pool warmup."""
        pool = TemplatePool()
        tm = MagicMock()
        tm.get_template.side_effect = lambda n: f"template_{n}"

        loaded = pool.warmup(tm, ["t1", "t2", "t3"])
        assert loaded == 3

    def test_warmup_with_error(self):
        """Test warmup with some errors."""
        pool = TemplatePool()
        tm = MagicMock()
        tm.get_template.side_effect = lambda n: (
            f"template_{n}" if n != "bad" else (_ for _ in ()).throw(Exception())
        )

        loaded = pool.warmup(tm, ["t1", "bad", "t2"])
        assert loaded == 2

    def test_get_existing(self):
        """Test getting existing template."""
        pool = TemplatePool()
        pool._templates["t1"] = "template1"
        pool._access_order.append("t1")

        result = pool.get("t1")
        assert result == "template1"

    def test_get_nonexistent(self):
        """Test getting nonexistent template."""
        pool = TemplatePool()
        result = pool.get("nonexistent")
        assert result is None

    def test_put_and_evict(self):
        """Test putting templates with eviction."""
        pool = TemplatePool(max_size=2)
        tm = MagicMock()

        pool.put("t1", "template1")
        pool.put("t2", "template2")
        pool.put("t3", "template3")  # Should evict t1

        assert pool.get("t1") is None
        assert pool.get("t2") is not None
        assert pool.get("t3") is not None

    def test_put_updates_order(self):
        """Test that put updates access order."""
        pool = TemplatePool(max_size=2)

        pool.put("t1", "template1")
        pool.put("t2", "template2")
        pool.put("t1", "template1_updated")  # Update existing

        assert pool.get("t1") == "template1_updated"

    def test_clear(self):
        """Test clearing pool."""
        pool = TemplatePool()
        pool.put("t1", "template1")
        pool.put("t2", "template2")

        pool.clear()

        assert pool.get("t1") is None
        assert pool.get("t2") is None

    def test_stats(self):
        """Test pool stats."""
        pool = TemplatePool(max_size=10)
        pool.put("t1", "template1")

        stats = pool.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert "t1" in stats["templates"]


class TestLogBatchProcessorExtra:
    """Additional tests for LogBatchProcessor."""

    def test_add_with_auto_flush(self):
        """Test add with auto flush."""
        processed = []

        def process_fn(logs):
            processed.extend(logs)

        config = BatchConfig(batch_size=2)
        processor = LogBatchProcessor(config=config, process_fn=process_fn)

        processor.add("log1")
        processor.add("log2")  # Should trigger flush

        assert len(processed) == 2

    def test_add_when_queue_full(self):
        """Test add when queue is full."""
        config = BatchConfig(max_queue_size=3)
        processor = LogBatchProcessor(config=config)

        assert processor.add("log1")
        assert processor.add("log2")
        assert processor.add("log3")
        assert not processor.add("log4")  # Dropped

    def test_auto_flush(self):
        """Test auto flush."""
        processor = LogBatchProcessor()

        processor.add("log1")

        # Should not flush yet
        result = processor.auto_flush()
        assert result is None

    def test_auto_flush_time_based(self):
        """Test auto flush based on time."""
        config = BatchConfig(flush_interval=0.1, batch_size=100)
        processor = LogBatchProcessor(config=config)

        processor.add("log1")
        time.sleep(0.15)

        result = processor.auto_flush()
        assert result is not None
        assert result.processed_count == 1

    def test_flush_empty_queue(self):
        """Test flushing empty queue."""
        processor = LogBatchProcessor()
        result = processor.flush()
        assert result is None

    def test_flush_with_exception(self):
        """Test flush with exception in process_fn."""
        def bad_process(logs):
            raise Exception("bad")

        processor = LogBatchProcessor(process_fn=bad_process)
        processor.add("log1")

        result = processor.flush()
        assert result is not None
        assert result.processed_count == 1

    def test_stats(self):
        """Test batch processor stats."""
        processor = LogBatchProcessor()
        processor.add("log1")
        processor.add("log2")
        processor.flush()

        stats = processor.stats()
        assert stats["total_added"] == 2
        assert stats["total_processed"] == 2
        assert stats["flush_count"] == 1


class TestLogAggregatorExtra:
    """Additional tests for LogAggregator."""

    def test_aggregate_same_logs(self):
        """Test aggregating same logs."""
        aggregator = LogAggregator()

        aggregator.add("error: connection failed")
        aggregator.add("error: connection failed")
        aggregator.add("error: connection failed")

        summary = aggregator.get_summary()
        assert len(summary) == 1
        assert summary[0]["count"] == 3

    def test_aggregate_different_logs(self):
        """Test aggregating different logs."""
        aggregator = LogAggregator()

        aggregator.add("error 1")
        aggregator.add("error 2")
        aggregator.add("error 1")

        summary = aggregator.get_summary()
        assert len(summary) == 2
        # Most frequent first
        assert summary[0]["log"] == "error 1"
        assert summary[0]["count"] == 2

    def test_expire_old(self):
        """Test expiring old entries."""
        aggregator = LogAggregator(window_seconds=0.1)

        aggregator.add("old log")
        time.sleep(0.15)
        aggregator.add("new log")

        expired = aggregator.expire_old()
        assert expired == 1

        summary = aggregator.get_summary()
        assert len(summary) == 1
        assert summary[0]["log"] == "new log"

    def test_expire_old_custom_max_age(self):
        """Test expiring with custom max age."""
        aggregator = LogAggregator()

        aggregator.add("log1")
        time.sleep(0.05)
        aggregator.add("log2")

        expired = aggregator.expire_old(max_age_seconds=0.01)
        assert expired == 1

    def test_clear(self):
        """Test clearing aggregator."""
        aggregator = LogAggregator()
        aggregator.add("log1")
        aggregator.add("log2")

        aggregator.clear()

        summary = aggregator.get_summary()
        assert len(summary) == 0

    def test_summary_duration(self):
        """Test summary duration calculation."""
        aggregator = LogAggregator()

        aggregator.add("log")
        time.sleep(0.05)
        aggregator.add("log")

        summary = aggregator.get_summary()
        assert summary[0]["duration"] >= 0.05


class TestOptimizationConfig:
    """Tests for OptimizationConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = OptimizationConfig()
        assert config.enable_cache
        assert config.cache_ttl == 3600
        assert config.preload_templates
        assert config.max_cache_size == 1000

    def test_custom_config(self):
        """Test custom configuration."""
        config = OptimizationConfig(
            enable_cache=False,
            cache_ttl=7200,
            preload_templates=False,
            max_cache_size=500,
        )
        assert not config.enable_cache
        assert config.cache_ttl == 7200


class TestOptimizationStats:
    """Tests for OptimizationStats."""

    def test_default_stats(self):
        """Test default stats."""
        stats = OptimizationStats()
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.avg_generation_time == 0.0


class TestBatchConfig:
    """Tests for BatchConfig."""

    def test_default_config(self):
        """Test default batch config."""
        config = BatchConfig()
        assert config.batch_size == 100
        assert config.flush_interval == 5.0
        assert config.max_queue_size == 10000

    def test_custom_config(self):
        """Test custom batch config."""
        config = BatchConfig(
            batch_size=50,
            flush_interval=10.0,
            max_queue_size=5000,
        )
        assert config.batch_size == 50
        assert config.flush_interval == 10.0


class TestBatchResult:
    """Tests for BatchResult."""

    def test_result_creation(self):
        """Test creating batch result."""
        result = BatchResult(
            processed_count=100,
            dropped_count=5,
            processing_time=0.5,
        )
        assert result.processed_count == 100
        assert result.dropped_count == 5
        assert result.processing_time == 0.5