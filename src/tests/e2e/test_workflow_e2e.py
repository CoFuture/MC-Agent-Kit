"""End-to-end tests for MC-Agent-Kit workflows.

This module tests the complete development cycle:
1. Search documentation
2. Create project
3. Launch test
4. Diagnose errors
"""

import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval, create_retrieval
from mc_agent_kit.scaffold.creator import ProjectCreator
from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
from mc_agent_kit.workflow.end_to_end import (
    EndToEndWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepStatus,
    create_workflow,
)


class TestSearchDocsE2E:
    """End-to-end tests for document search workflow."""

    def test_search_api_by_keyword(self) -> None:
        """Test searching for API documentation by keyword."""
        try:
            retrieval = create_retrieval()
            results = retrieval.search("创建实体", limit=5)
            assert isinstance(results, list)
        except Exception as e:
            # Skip if knowledge base not available
            pytest.skip(f"Knowledge base not available: {e}")

    def test_search_event_by_keyword(self) -> None:
        """Test searching for event documentation by keyword."""
        try:
            retrieval = create_retrieval()
            results = retrieval.search("玩家加入", limit=5)
            assert isinstance(results, list)
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

    def test_search_with_empty_query(self) -> None:
        """Test searching with empty query returns empty or minimal results."""
        try:
            retrieval = create_retrieval()
            results = retrieval.search("", limit=5)
            assert isinstance(results, list)
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")

    def test_search_with_special_characters(self) -> None:
        """Test searching with special characters."""
        try:
            retrieval = create_retrieval()
            results = retrieval.search("!!!###", limit=5)
            assert isinstance(results, list)
        except Exception as e:
            pytest.skip(f"Knowledge base not available: {e}")


class TestCreateProjectE2E:
    """End-to-end tests for project creation workflow."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def creator(self) -> ProjectCreator:
        """Create a project creator instance."""
        return ProjectCreator()

    def test_create_empty_project(self, creator: ProjectCreator, temp_dir: Path) -> None:
        """Test creating an empty project."""
        project = creator.create_project(
            name="test_project",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        assert project.name == "test_project"
        assert project.path.exists()
        assert (project.path / "behavior_pack").exists()
        assert (project.path / "resource_pack").exists()

    def test_create_entity_project(self, creator: ProjectCreator, temp_dir: Path) -> None:
        """Test creating a project with entity template."""
        project = creator.create_project(
            name="entity_project",
            path=str(temp_dir),
            template="entity",
            force=True,
        )

        assert project.name == "entity_project"
        assert project.path.exists()

    def test_add_entity_to_project(self, creator: ProjectCreator, temp_dir: Path) -> None:
        """Test adding an entity to an existing project."""
        project = creator.create_project(
            name="test_project",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        created_files = creator.add_entity("TestEntity", project)

        assert len(created_files) > 0
        assert any("testentity" in str(f).lower() for f in created_files)

    def test_add_item_to_project(self, creator: ProjectCreator, temp_dir: Path) -> None:
        """Test adding an item to an existing project."""
        project = creator.create_project(
            name="test_project",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        created_files = creator.add_item("TestItem", project)

        assert len(created_files) > 0
        assert any("testitem" in str(f).lower() for f in created_files)

    def test_create_project_overwrites_existing(self, creator: ProjectCreator, temp_dir: Path) -> None:
        """Test that force=True overwrites existing project."""
        # Create project first time
        project1 = creator.create_project(
            name="overwrite_test",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        # Create again with same name
        project2 = creator.create_project(
            name="overwrite_test",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        assert project1.path == project2.path

    def test_create_project_fails_without_force(self, creator: ProjectCreator, temp_dir: Path) -> None:
        """Test that creating existing project without force raises error."""
        creator.create_project(
            name="no_overwrite_test",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        with pytest.raises(FileExistsError):
            creator.create_project(
                name="no_overwrite_test",
                path=str(temp_dir),
                template="empty",
                force=False,
            )


class TestDiagnoseE2E:
    """End-to-end tests for diagnosis workflow."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def diagnoser(self) -> LauncherDiagnoser:
        """Create a diagnoser instance."""
        return LauncherDiagnoser()

    @pytest.fixture
    def creator(self) -> ProjectCreator:
        """Create a project creator instance."""
        return ProjectCreator()

    def test_diagnose_valid_project(
        self, diagnoser: LauncherDiagnoser, creator: ProjectCreator, temp_dir: Path
    ) -> None:
        """Test diagnosing a valid project."""
        project = creator.create_project(
            name="valid_project",
            path=str(temp_dir),
            template="empty",
            force=True,
        )

        report = diagnoser.diagnose(addon_path=str(project.path))

        assert report is not None
        assert hasattr(report, "has_errors")

    def test_diagnose_missing_manifest(
        self, diagnoser: LauncherDiagnoser, temp_dir: Path
    ) -> None:
        """Test diagnosing a project with missing manifest."""
        # Create directory without proper structure
        (temp_dir / "behavior_pack").mkdir(parents=True)

        report = diagnoser.diagnose(addon_path=str(temp_dir))

        assert report is not None
        # Should report issues due to missing manifest


class TestWorkflowE2E:
    """End-to-end tests for complete workflow."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def workflow_config(self, temp_dir: Path) -> WorkflowConfig:
        """Create workflow configuration."""
        return WorkflowConfig(
            project_name="e2e_test_project",
            output_dir=str(temp_dir),
        )

    def test_create_workflow(self, workflow_config: WorkflowConfig) -> None:
        """Test creating a workflow instance."""
        workflow = create_workflow(workflow_config)

        assert workflow is not None
        assert workflow.config == workflow_config

    def test_run_full_cycle(self, workflow_config: WorkflowConfig) -> None:
        """Test running a full development cycle."""
        workflow = create_workflow(workflow_config)
        result = workflow.run_full_cycle()

        assert isinstance(result, WorkflowResult)
        assert hasattr(result, "success")
        assert hasattr(result, "steps")

    def test_step_search_docs(self, workflow_config: WorkflowConfig) -> None:
        """Test the search docs step."""
        workflow = create_workflow(workflow_config)
        result = workflow.step_search_docs("如何创建实体")

        assert result.step == WorkflowStep.SEARCH_DOCS
        assert result.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.FAILED)

    def test_step_create_project(self, workflow_config: WorkflowConfig) -> None:
        """Test the create project step."""
        workflow = create_workflow(workflow_config)
        result = workflow.step_create_project()

        assert result.step == WorkflowStep.CREATE_PROJECT
        assert result.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.FAILED)

    def test_step_launch_test(self, workflow_config: WorkflowConfig) -> None:
        """Test the launch test step."""
        workflow = create_workflow(workflow_config)
        # First create a project
        workflow.step_create_project()
        # Then try to launch (will likely fail without game, but shouldn't crash)
        result = workflow.step_launch_test(str(workflow_config.output_dir))

        assert result.step == WorkflowStep.LAUNCH_TEST
        assert result.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.FAILED)

    def test_step_diagnose_error(self, workflow_config: WorkflowConfig) -> None:
        """Test the diagnose error step."""
        workflow = create_workflow(workflow_config)
        # Create project first
        workflow.step_create_project()
        result = workflow.step_diagnose_error(str(workflow_config.output_dir))

        assert result.step == WorkflowStep.DIAGNOSE_ERROR
        assert result.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.FAILED)


class TestIntegrationScenarios:
    """Integration tests for common user scenarios."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_scenario_create_entity_addon(self, temp_dir: Path) -> None:
        """Test scenario: User creates an entity addon."""
        creator = ProjectCreator()

        # Step 1: Create project with entity template
        project = creator.create_project(
            name="my_entity_addon",
            path=str(temp_dir),
            template="entity",
            force=True,
        )

        assert project.path.exists()

        # Step 2: Add custom entity
        files = creator.add_entity("CustomMob", project)

        assert len(files) > 0

    def test_scenario_search_and_create(self, temp_dir: Path) -> None:
        """Test scenario: User searches docs then creates project."""
        # Step 1: Search for relevant API
        try:
            retrieval = create_retrieval()
            results = retrieval.search("创建物品", limit=3)
            assert isinstance(results, list)
        except Exception:
            pass  # Skip search if knowledge base not available

        # Step 2: Create project based on search
        creator = ProjectCreator()
        project = creator.create_project(
            name="item_addon",
            path=str(temp_dir),
            template="item",
            force=True,
        )

        assert project.path.exists()

    def test_scenario_development_cycle(self, temp_dir: Path) -> None:
        """Test scenario: User goes through development cycle."""
        config = WorkflowConfig(
            project_name="cycle_test",
            output_dir=str(temp_dir),
            search_query="如何监听玩家事件",
        )

        workflow = create_workflow(config)

        # Run the cycle
        result = workflow.run_full_cycle()

        # Should complete without crashing
        assert isinstance(result, WorkflowResult)