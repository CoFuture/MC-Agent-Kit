"""Performance benchmark tests for MC-Agent-Kit.

This module provides benchmark tests for key operations:
1. Knowledge search performance
2. Project creation performance
3. Code generation performance
4. Diagnosis performance
"""

import time
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Any

import pytest

from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval, create_retrieval
from mc_agent_kit.scaffold.creator import ProjectCreator
from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
from mc_agent_kit.generator.code_gen import CodeGenerator


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""

    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    ops_per_second: float

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total: {self.total_time_ms:.2f}ms\n"
            f"  Average: {self.avg_time_ms:.2f}ms\n"
            f"  Min: {self.min_time_ms:.2f}ms\n"
            f"  Max: {self.max_time_ms:.2f}ms\n"
            f"  Ops/sec: {self.ops_per_second:.2f}"
        )


def benchmark(
    name: str,
    func: Callable[[], Any],
    iterations: int = 10,
    warmup: int = 2,
) -> BenchmarkResult:
    """Run a benchmark on a function.

    Args:
        name: Name of the benchmark
        func: Function to benchmark
        iterations: Number of iterations to run
        warmup: Number of warmup iterations

    Returns:
        Benchmark result
    """
    # Warmup
    for _ in range(warmup):
        func()

    # Benchmark
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    total_time = sum(times)
    avg_time = total_time / iterations
    min_time = min(times)
    max_time = max(times)
    ops_per_second = 1000 / avg_time if avg_time > 0 else 0

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time,
        avg_time_ms=avg_time,
        min_time_ms=min_time,
        max_time_ms=max_time,
        ops_per_second=ops_per_second,
    )


class TestKnowledgeSearchBenchmark:
    """Benchmark tests for knowledge search performance."""

    @pytest.mark.benchmark
    def test_search_single_keyword(self) -> None:
        """Benchmark single keyword search."""
        try:
            retrieval = create_retrieval()
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

        result = benchmark(
            name="search_single_keyword",
            func=lambda: retrieval.search("创建实体", limit=5),
            iterations=10,
        )

        print(f"\n{result}")
        # Should be reasonably fast
        assert result.avg_time_ms < 5000, f"Search too slow: {result.avg_time_ms}ms"

    @pytest.mark.benchmark
    def test_search_chinese_query(self) -> None:
        """Benchmark Chinese query search."""
        try:
            retrieval = create_retrieval()
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

        result = benchmark(
            name="search_chinese_query",
            func=lambda: retrieval.search("如何监听玩家加入服务器事件", limit=10),
            iterations=10,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 5000

    @pytest.mark.benchmark
    def test_search_mixed_query(self) -> None:
        """Benchmark mixed language query search."""
        try:
            retrieval = create_retrieval()
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

        result = benchmark(
            name="search_mixed_query",
            func=lambda: retrieval.search("CreateEngineEntity API", limit=5),
            iterations=10,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 5000

    @pytest.mark.benchmark
    def test_search_large_limit(self) -> None:
        """Benchmark search with large result limit."""
        try:
            retrieval = create_retrieval()
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

        result = benchmark(
            name="search_large_limit",
            func=lambda: retrieval.search("玩家", limit=50),
            iterations=5,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 10000


class TestProjectCreationBenchmark:
    """Benchmark tests for project creation performance."""

    @pytest.fixture
    def temp_dirs(self) -> list[Path]:
        """Create temporary directories for tests."""
        dirs = []
        for _ in range(15):
            tmpdir = tempfile.mkdtemp()
            dirs.append(Path(tmpdir))
        yield dirs
        # Cleanup
        for d in dirs:
            import shutil

            if d.exists():
                shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def creator(self) -> ProjectCreator:
        """Create a project creator instance."""
        return ProjectCreator()

    @pytest.mark.benchmark
    def test_create_empty_project(self, creator: ProjectCreator, temp_dirs: list[Path]) -> None:
        """Benchmark creating empty projects."""
        paths = [str(d) for d in temp_dirs[:10]]

        def create_project() -> None:
            idx = paths.index(str(temp_dirs[0])) if str(temp_dirs[0]) in paths else 0
            creator.create_project(
                name=f"bench_project_{idx}",
                path=paths[idx % len(paths)],
                template="empty",
                force=True,
            )

        result = benchmark(
            name="create_empty_project",
            func=lambda: creator.create_project(
                name="bench_test",
                path=str(temp_dirs[0]),
                template="empty",
                force=True,
            ),
            iterations=10,
        )

        print(f"\n{result}")
        # Should be fast
        assert result.avg_time_ms < 1000

    @pytest.mark.benchmark
    def test_add_entity(self, creator: ProjectCreator, temp_dirs: list[Path]) -> None:
        """Benchmark adding entity to project."""
        # First create a project
        project = creator.create_project(
            name="entity_bench",
            path=str(temp_dirs[10]),
            template="empty",
            force=True,
        )

        counter = [0]

        result = benchmark(
            name="add_entity",
            func=lambda: (
                counter.__setitem__(0, counter[0] + 1),
                creator.add_entity(f"Entity_{counter[0]}", project),
            )[-1],
            iterations=10,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 500

    @pytest.mark.benchmark
    def test_add_item(self, creator: ProjectCreator, temp_dirs: list[Path]) -> None:
        """Benchmark adding item to project."""
        # First create a project
        project = creator.create_project(
            name="item_bench",
            path=str(temp_dirs[11]),
            template="empty",
            force=True,
        )

        counter = [0]

        result = benchmark(
            name="add_item",
            func=lambda: (
                counter.__setitem__(0, counter[0] + 1),
                creator.add_item(f"Item_{counter[0]}", project),
            )[-1],
            iterations=10,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 500


class TestCodeGeneratorBenchmark:
    """Benchmark tests for code generation performance."""

    @pytest.fixture
    def generator(self) -> CodeGenerator:
        """Create a code generator instance."""
        return CodeGenerator()

    @pytest.mark.benchmark
    def test_generate_with_template(self, generator: CodeGenerator) -> None:
        """Benchmark generating code with template."""
        template = """
def on_{{event_name}}(args):
    {{callback_body}}
    pass
"""
        result = benchmark(
            name="generate_with_template",
            func=lambda: generator.generate_with_template(
                template_content=template,
                params={"event_name": "OnServerChat", "callback_body": "# Handle chat"},
            ),
            iterations=50,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 100

    @pytest.mark.benchmark
    def test_list_templates(self, generator: CodeGenerator) -> None:
        """Benchmark listing templates."""
        result = benchmark(
            name="list_templates",
            func=lambda: generator.list_templates(),
            iterations=50,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 100

    @pytest.mark.benchmark
    def test_search_templates(self, generator: CodeGenerator) -> None:
        """Benchmark searching templates."""
        result = benchmark(
            name="search_templates",
            func=lambda: generator.search_templates("entity"),
            iterations=50,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 100


class TestDiagnosisBenchmark:
    """Benchmark tests for diagnosis performance."""

    @pytest.fixture
    def diagnoser(self) -> LauncherDiagnoser:
        """Create a diagnoser instance."""
        return LauncherDiagnoser()

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_project(self, temp_dir: Path) -> Path:
        """Create a sample project for testing."""
        creator = ProjectCreator()
        project = creator.create_project(
            name="diagnose_bench",
            path=str(temp_dir),
            template="empty",
            force=True,
        )
        return project.path

    @pytest.mark.benchmark
    def test_diagnose_project(self, diagnoser: LauncherDiagnoser, sample_project: Path) -> None:
        """Benchmark diagnosing a project."""
        result = benchmark(
            name="diagnose_project",
            func=lambda: diagnoser.diagnose(addon_path=str(sample_project)),
            iterations=10,
        )

        print(f"\n{result}")
        assert result.avg_time_ms < 5000


class TestMemoryBenchmark:
    """Memory usage benchmarks (informational only)."""

    @pytest.mark.benchmark
    def test_retrieval_memory(self) -> None:
        """Test retrieval object memory footprint."""
        import sys

        try:
            retrieval = create_retrieval()
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

        size = sys.getsizeof(retrieval)

        print(f"\nRetrieval object size: {size} bytes")
        # This is informational, not a strict assertion

    @pytest.mark.benchmark
    def test_creator_memory(self) -> None:
        """Test creator object memory footprint."""
        import sys

        creator = ProjectCreator()
        size = sys.getsizeof(creator)

        print(f"\nCreator object size: {size} bytes")


class TestCompositeBenchmark:
    """Composite benchmarks that test full workflows."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.benchmark
    def test_full_workflow_benchmark(self, temp_dir: Path) -> None:
        """Benchmark the full workflow from search to diagnosis."""
        from mc_agent_kit.workflow.end_to_end import (
            WorkflowConfig,
            create_workflow,
        )

        config = WorkflowConfig(
            project_name="full_bench",
            output_dir=str(temp_dir),
        )

        def run_workflow() -> None:
            workflow = create_workflow(config)
            workflow.run_full_cycle()

        result = benchmark(
            name="full_workflow",
            func=run_workflow,
            iterations=5,
            warmup=1,
        )

        print(f"\n{result}")
        # Full workflow should complete in reasonable time
        assert result.avg_time_ms < 30000, f"Full workflow too slow: {result.avg_time_ms}ms"


@pytest.mark.benchmark
class TestBenchmarkSummary:
    """Generate benchmark summary."""

    def test_print_benchmark_summary(self) -> None:
        """Print a summary of expected performance characteristics."""
        summary = """
        MC-Agent-Kit Performance Benchmarks
        ====================================

        Expected Performance Characteristics:
        
        1. Knowledge Search:
           - Single keyword search: < 5s
           - Chinese query search: < 5s
           - Large limit search: < 10s
        
        2. Project Creation:
           - Empty project: < 1s
           - Add entity: < 500ms
           - Add item: < 500ms
        
        3. Code Generation:
           - Event listener: < 100ms
           - API call: < 100ms
        
        4. Diagnosis:
           - Project diagnosis: < 5s
        
        5. Full Workflow:
           - Complete cycle: < 30s

        Note: These are baseline expectations.
        Actual performance depends on system resources.
        """
        print(summary)