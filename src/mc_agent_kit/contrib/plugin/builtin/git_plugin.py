"""Git operations plugin for MC-Agent-Kit.

Provides Git operations like status, commit, push, pull, branch management.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginPriority,
    PluginState,
)
from mc_agent_kit.contrib.plugin.hooks import HookType, HookPriority, register_hook


@dataclass
class GitStatus:
    """Git repository status."""
    branch: str
    is_clean: bool
    staged: list[str]
    unstaged: list[str]
    untracked: list[str]
    ahead: int
    behind: int


@dataclass
class GitLogEntry:
    """Git log entry."""
    commit_hash: str
    author: str
    date: str
    message: str


class GitPlugin(PluginBase):
    """Plugin for Git operations."""

    def __init__(self) -> None:
        """Initialize the Git plugin."""
        metadata = PluginMetadata(
            name="git-operations",
            version="1.0.0",
            description="Git operations plugin for version control",
            author="MC-Agent-Kit",
            capabilities=["git", "version-control", "commit", "push", "pull"],
            priority=PluginPriority.NORMAL,
        )
        super().__init__(metadata)
        self._repo_path: Path | None = None

    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if successful.
        """
        # Set state to LOADED
        self._state = PluginState.LOADED
        
        # Register hooks
        register_hook(
            HookType.ON_PROJECT_SAVE,
            self._on_project_save,
            HookPriority.LOW,
            self.metadata.name,
            "Auto-commit on project save",
        )
        return True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    def execute(self, **kwargs: Any) -> PluginResult:
        """Execute a Git operation.
        
        Args:
            **kwargs: Execution parameters.
                - operation: Operation to perform (status, commit, push, pull, etc.)
                - path: Repository path
                - message: Commit message (for commit operation)
                - branch: Branch name (for branch operations)
        
        Returns:
            Execution result.
        """
        operation = kwargs.get("operation", "status")
        path = Path(kwargs.get("path", "."))
        
        if not self._is_git_repo(path):
            return PluginResult(
                success=False,
                error=f"Not a Git repository: {path}",
            )
        
        self._repo_path = path
        
        operations = {
            "status": self._status,
            "commit": self._commit,
            "push": self._push,
            "pull": self._pull,
            "branch": self._branch,
            "checkout": self._checkout,
            "log": self._log,
            "diff": self._diff,
            "add": self._add,
            "init": self._init,
        }
        
        if operation not in operations:
            return PluginResult(
                success=False,
                error=f"Unknown Git operation: {operation}",
            )
        
        try:
            result = operations[operation](**kwargs)
            return PluginResult(success=True, data=result)
        except Exception as e:
            return PluginResult(success=False, error=str(e))

    def _run_git(self, *args: str, cwd: Path | None = None) -> tuple[bool, str]:
        """Run a Git command.
        
        Args:
            *args: Git command arguments.
            cwd: Working directory.
            
        Returns:
            Tuple of (success, output).
        """
        cmd = ["git"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self._repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except FileNotFoundError:
            return False, "Git not found. Please install Git."
        except Exception as e:
            return False, str(e)

    def _is_git_repo(self, path: Path) -> bool:
        """Check if path is a Git repository.
        
        Args:
            path: Path to check.
            
        Returns:
            True if it's a Git repository.
        """
        success, _ = self._run_git("rev-parse", "--git-dir", cwd=path)
        return success

    def _status(self, **kwargs: Any) -> GitStatus:
        """Get repository status.
        
        Returns:
            GitStatus object.
        """
        # Get branch
        success, branch = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if not success:
            branch = "unknown"
        
        # Get porcelain status
        success, output = self._run_git("status", "--porcelain")
        staged = []
        unstaged = []
        untracked = []
        
        if success and output:
            for line in output.split("\n"):
                if len(line) >= 2:
                    index = line[0]
                    work_tree = line[1]
                    file_path = line[3:]
                    
                    if index in "MADRC":
                        staged.append(file_path)
                    if work_tree in "MD":
                        unstaged.append(file_path)
                    if index == "?":
                        untracked.append(file_path)
        
        # Get ahead/behind
        ahead = 0
        behind = 0
        success, output = self._run_git("rev-list", "--left-right", "--count", "@{upstream}...HEAD")
        if success and output:
            parts = output.split()
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])
        
        return GitStatus(
            branch=branch,
            is_clean=len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked,
            ahead=ahead,
            behind=behind,
        )

    def _commit(self, **kwargs: Any) -> dict[str, Any]:
        """Create a commit.
        
        Returns:
            Commit info.
        """
        message = kwargs.get("message", "Auto-commit by MC-Agent-Kit")
        
        # Add all changes first
        self._run_git("add", "-A")
        
        success, output = self._run_git("commit", "-m", message)
        if not success:
            if "nothing to commit" in output:
                return {"message": "Nothing to commit", "clean": True}
            raise Exception(f"Commit failed: {output}")
        
        return {"message": "Committed successfully", "output": output}

    def _push(self, **kwargs: Any) -> dict[str, Any]:
        """Push to remote.
        
        Returns:
            Push result.
        """
        branch = kwargs.get("branch")
        args = ["push"]
        if branch:
            args.extend(["origin", branch])
        
        success, output = self._run_git(*args)
        if not success:
            raise Exception(f"Push failed: {output}")
        
        return {"message": "Pushed successfully", "output": output}

    def _pull(self, **kwargs: Any) -> dict[str, Any]:
        """Pull from remote.
        
        Returns:
            Pull result.
        """
        success, output = self._run_git("pull")
        if not success:
            raise Exception(f"Pull failed: {output}")
        
        return {"message": "Pulled successfully", "output": output}

    def _branch(self, **kwargs: Any) -> dict[str, Any]:
        """List or create branches.
        
        Returns:
            Branch info.
        """
        new_branch = kwargs.get("new_branch")
        
        if new_branch:
            success, output = self._run_git("checkout", "-b", new_branch)
            if not success:
                raise Exception(f"Branch creation failed: {output}")
            return {"message": f"Created branch: {new_branch}"}
        
        success, output = self._run_git("branch", "-a")
        if not success:
            raise Exception(f"Branch list failed: {output}")
        
        branches = [b.strip() for b in output.split("\n") if b.strip()]
        return {"branches": branches}

    def _checkout(self, **kwargs: Any) -> dict[str, Any]:
        """Checkout a branch.
        
        Returns:
            Checkout result.
        """
        branch = kwargs.get("branch")
        if not branch:
            raise Exception("Branch name required")
        
        success, output = self._run_git("checkout", branch)
        if not success:
            raise Exception(f"Checkout failed: {output}")
        
        return {"message": f"Checked out: {branch}"}

    def _log(self, **kwargs: Any) -> list[GitLogEntry]:
        """Get commit log.
        
        Returns:
            List of log entries.
        """
        count = kwargs.get("count", 10)
        
        success, output = self._run_git(
            "log", f"-{count}", "--pretty=format:%H|%an|%ad|%s", "--date=short"
        )
        if not success:
            raise Exception(f"Log failed: {output}")
        
        entries = []
        for line in output.split("\n"):
            if "|" in line:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    entries.append(GitLogEntry(
                        commit_hash=parts[0][:8],
                        author=parts[1],
                        date=parts[2],
                        message=parts[3],
                    ))
        
        return entries

    def _diff(self, **kwargs: Any) -> dict[str, Any]:
        """Get diff.
        
        Returns:
            Diff output.
        """
        staged = kwargs.get("staged", False)
        
        args = ["diff"]
        if staged:
            args.append("--staged")
        
        success, output = self._run_git(*args)
        if not success:
            return {"diff": ""}
        
        return {"diff": output}

    def _add(self, **kwargs: Any) -> dict[str, Any]:
        """Add files to staging.
        
        Returns:
            Add result.
        """
        files = kwargs.get("files", ["."])
        
        success, output = self._run_git("add", *files)
        if not success:
            raise Exception(f"Add failed: {output}")
        
        return {"message": "Files added to staging"}

    def _init(self, **kwargs: Any) -> dict[str, Any]:
        """Initialize a Git repository.
        
        Returns:
            Init result.
        """
        success, output = self._run_git("init")
        if not success:
            raise Exception(f"Init failed: {output}")
        
        return {"message": "Git repository initialized"}

    def _on_project_save(self, project_path: str, **kwargs: Any) -> None:
        """Hook callback for project save.
        
        Args:
            project_path: Path to saved project.
            **kwargs: Additional arguments.
        """
        # Check if auto-commit is enabled
        if kwargs.get("auto_commit", False):
            path = Path(project_path)
            if self._is_git_repo(path):
                self._repo_path = path
                status = self._status()
                if not status.is_clean:
                    self._commit(message=f"Auto-save: {path.name}")