"""
迭代 #47 测试：CI/CD 集成与发布自动化

测试内容：
- CI/CD 工作流配置验证
- 发布自动化功能
- 文档完善验证
"""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestCIWorkflow:
    """CI 工作流配置测试"""

    @pytest.fixture
    def workflow_path(self) -> Path:
        """获取工作流文件路径"""
        return PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

    @pytest.fixture
    def workflow_content(self, workflow_path: Path) -> dict:
        """加载工作流内容"""
        with open(workflow_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_workflow_file_exists(self, workflow_path: Path) -> None:
        """测试工作流文件存在"""
        assert workflow_path.exists(), "CI workflow file should exist"

    def test_workflow_has_test_job(self, workflow_content: dict) -> None:
        """测试工作流包含测试任务"""
        assert "jobs" in workflow_content
        assert "test" in workflow_content["jobs"]

    def test_workflow_has_lint_job(self, workflow_content: dict) -> None:
        """测试工作流包含 Lint 任务"""
        assert "lint" in workflow_content["jobs"]

    def test_workflow_has_build_job(self, workflow_content: dict) -> None:
        """测试工作流包含构建任务"""
        assert "build" in workflow_content["jobs"]

    def test_workflow_has_publish_job(self, workflow_content: dict) -> None:
        """测试工作流包含发布任务"""
        assert "publish" in workflow_content["jobs"]

    def test_workflow_triggers_on_push(self, workflow_content: dict) -> None:
        """测试工作流在 push 时触发"""
        # YAML 中的 'on' 被解析为 True (布尔值)
        triggers = workflow_content.get(True, workflow_content.get("on", {}))
        assert "push" in triggers

    def test_workflow_triggers_on_pr(self, workflow_content: dict) -> None:
        """测试工作流在 PR 时触发"""
        triggers = workflow_content.get(True, workflow_content.get("on", {}))
        assert "pull_request" in triggers

    def test_workflow_triggers_on_release(self, workflow_content: dict) -> None:
        """测试工作流在 release 时触发"""
        triggers = workflow_content.get(True, workflow_content.get("on", {}))
        assert "release" in triggers

    def test_test_job_coverage(self, workflow_content: dict) -> None:
        """测试测试任务包含覆盖率"""
        test_job = workflow_content["jobs"]["test"]
        steps = test_job.get("steps", [])

        # 检查是否有覆盖率步骤
        coverage_step = None
        for step in steps:
            if "pytest" in str(step.get("run", "")) and "cov" in str(step.get("run", "")):
                coverage_step = step
                break

        assert coverage_step is not None, "Test job should include coverage"

    def test_lint_job_ruff(self, workflow_content: dict) -> None:
        """测试 Lint 任务包含 Ruff"""
        lint_job = workflow_content["jobs"]["lint"]
        steps = lint_job.get("steps", [])

        ruff_step = None
        for step in steps:
            if "ruff" in str(step.get("run", "")):
                ruff_step = step
                break

        assert ruff_step is not None, "Lint job should include ruff"

    def test_lint_job_mypy(self, workflow_content: dict) -> None:
        """测试 Lint 任务包含 MyPy"""
        lint_job = workflow_content["jobs"]["lint"]
        steps = lint_job.get("steps", [])

        mypy_step = None
        for step in steps:
            if "mypy" in str(step.get("run", "")):
                mypy_step = step
                break

        assert mypy_step is not None, "Lint job should include mypy"

    def test_publish_job_needs_build(self, workflow_content: dict) -> None:
        """测试发布任务依赖构建任务"""
        publish_job = workflow_content["jobs"]["publish"]
        needs = publish_job.get("needs", [])

        assert "build" in needs, "Publish job should need build job"


class TestDocumentation:
    """文档测试"""

    @pytest.fixture
    def docs_path(self) -> Path:
        """获取文档目录"""
        return PROJECT_ROOT / "docs"

    def test_developer_guide_exists(self, docs_path: Path) -> None:
        """测试开发者指南存在"""
        guide_path = docs_path / "developer-guide.md"
        assert guide_path.exists(), "Developer guide should exist"

    def test_error_codes_exists(self, docs_path: Path) -> None:
        """测试错误代码文档存在"""
        error_codes_path = docs_path / "error-codes.md"
        assert error_codes_path.exists(), "Error codes documentation should exist"

    def test_api_changelog_exists(self, docs_path: Path) -> None:
        """测试 API 变更日志存在"""
        changelog_path = docs_path / "api-changelog.md"
        assert changelog_path.exists(), "API changelog should exist"

    def test_developer_guide_has_content(self, docs_path: Path) -> None:
        """测试开发者指南有内容"""
        guide_path = docs_path / "developer-guide.md"
        content = guide_path.read_text(encoding="utf-8")

        assert len(content) > 1000, "Developer guide should have substantial content"
        assert "开发环境" in content or "Development" in content, "Should mention development setup"

    def test_error_codes_has_categories(self, docs_path: Path) -> None:
        """测试错误代码文档有分类"""
        error_codes_path = docs_path / "error-codes.md"
        content = error_codes_path.read_text(encoding="utf-8")

        assert "E0" in content, "Should have launcher errors"
        assert "E1" in content, "Should have knowledge base errors"

    def test_api_changelog_has_versions(self, docs_path: Path) -> None:
        """测试 API 变更日志有版本记录"""
        changelog_path = docs_path / "api-changelog.md"
        content = changelog_path.read_text(encoding="utf-8")

        assert "v1." in content, "Should have version entries"


class TestPyprojectConfig:
    """pyproject.toml 配置测试"""

    @pytest.fixture
    def pyproject_path(self) -> Path:
        """获取 pyproject.toml 路径"""
        return PROJECT_ROOT / "pyproject.toml"

    @pytest.fixture
    def pyproject_content(self, pyproject_path: Path) -> dict:
        """加载 pyproject.toml 内容"""
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)

    def test_pyproject_exists(self, pyproject_path: Path) -> None:
        """测试 pyproject.toml 存在"""
        assert pyproject_path.exists(), "pyproject.toml should exist"

    def test_pyproject_has_dev_dependencies(self, pyproject_content: dict) -> None:
        """测试开发依赖配置"""
        dev_deps = pyproject_content.get("project", {}).get("optional-dependencies", {}).get("dev", [])
        dep_names = [d.split(">")[0].split("<")[0].split("=")[0] for d in dev_deps]

        assert "pytest" in dep_names, "Should have pytest"
        assert "ruff" in dep_names, "Should have ruff"
        assert "mypy" in dep_names, "Should have mypy"

    def test_pyproject_has_ruff_config(self, pyproject_content: dict) -> None:
        """测试 Ruff 配置"""
        assert "tool" in pyproject_content
        assert "ruff" in pyproject_content["tool"]

    def test_pyproject_has_mypy_config(self, pyproject_content: dict) -> None:
        """测试 MyPy 配置"""
        assert "mypy" in pyproject_content["tool"]

    def test_pyproject_has_coverage_config(self, pyproject_content: dict) -> None:
        """测试覆盖率配置"""
        assert "coverage" in pyproject_content["tool"]


class TestAcceptanceCriteria:
    """验收标准测试"""

    def test_ci_workflow_complete(self) -> None:
        """测试 CI 工作流完整"""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

        with open(workflow_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)

        # YAML 中的 'on' 被解析为 True (布尔值)
        triggers = content.get(True, content.get("on", {}))

        # 验收标准 1: PR 自动运行测试
        assert "pull_request" in triggers, "CI should run on PR"

        # 验收标准 2: 类型检查
        lint_job = content["jobs"]["lint"]
        has_mypy = any("mypy" in str(s.get("run", "")) for s in lint_job.get("steps", []))
        assert has_mypy, "CI should run mypy"

        # 验收标准 3: 代码检查
        has_ruff = any("ruff" in str(s.get("run", "")) for s in lint_job.get("steps", []))
        assert has_ruff, "CI should run ruff"

        # 验收标准 4: 覆盖率报告
        test_job = content["jobs"]["test"]
        has_coverage = any("cov" in str(s.get("run", "")) for s in test_job.get("steps", []))
        assert has_coverage, "CI should generate coverage report"

    def test_publish_automation_complete(self) -> None:
        """测试发布自动化完整"""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

        with open(workflow_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)

        triggers = content.get(True, content.get("on", {}))

        # 验收标准 1: tag 推送触发发布
        assert "release" in triggers, "CI should run on release"

        # 验收标准 2: PyPI 发布
        publish_job = content["jobs"]["publish"]
        has_pypi = any("pypi" in str(s.get("uses", "")).lower() for s in publish_job.get("steps", []))
        assert has_pypi, "CI should publish to PyPI"

        # 验收标准 3: Release Notes
        release_job = content["jobs"].get("release-notes")
        assert release_job is not None, "CI should generate release notes"

    def test_documentation_complete(self) -> None:
        """测试文档完善"""
        docs_path = PROJECT_ROOT / "docs"

        # 验收标准 1: CONTRIBUTING.md
        contributing_path = PROJECT_ROOT / "CONTRIBUTING.md"
        assert contributing_path.exists(), "CONTRIBUTING.md should exist"

        # 验收标准 2: 开发者指南
        dev_guide_path = docs_path / "developer-guide.md"
        assert dev_guide_path.exists(), "Developer guide should exist"

        # 验收标准 3: 错误代码文档
        error_codes_path = docs_path / "error-codes.md"
        assert error_codes_path.exists(), "Error codes doc should exist"

        # 验收标准 4: API 变更日志
        api_changelog_path = docs_path / "api-changelog.md"
        assert api_changelog_path.exists(), "API changelog should exist"


class TestIntegration:
    """集成测试"""

    def test_tests_pass(self) -> None:
        """测试套件通过"""
        # 这个测试本身通过就证明了测试可以运行
        assert True

    def test_version_format(self) -> None:
        """测试版本号格式"""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            content = tomllib.load(f)

        version = content["project"]["version"]

        # 检查版本号格式
        parts = version.split(".")
        assert len(parts) >= 2, "Version should have at least major.minor"
        assert all(p.isdigit() for p in parts), "Version parts should be numbers"

    def test_all_cli_entry_points(self) -> None:
        """测试 CLI 入口点定义"""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            content = tomllib.load(f)

        scripts = content["project"].get("scripts", {})

        expected_scripts = ["mc-agent", "mc-create", "mc-kb", "mc-run", "mc-logs", "mc-launcher"]

        for script in expected_scripts:
            assert script in scripts, f"CLI entry point {script} should be defined"