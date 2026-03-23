"""
Git Tools Module

Git 工具，提供 Git 操作功能。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

__all__ = [
    "GitTools",
    "git_status",
    "git_commit",
    "git_push",
    "git_pull",
    "git_branch",
]


class GitTools:
    """Git 工具类"""

    @staticmethod
    def status(path: str = ".") -> dict[str, Any]:
        """获取 Git 状态"""
        return git_status(path)

    @staticmethod
    def commit(message: str, path: str = ".", add_all: bool = True) -> dict[str, Any]:
        """提交更改"""
        return git_commit(message, path, add_all)

    @staticmethod
    def push(path: str = ".", remote: str = "origin", branch: str = "") -> dict[str, Any]:
        """推送到远程"""
        return git_push(path, remote, branch)

    @staticmethod
    def pull(path: str = ".", remote: str = "origin", branch: str = "") -> dict[str, Any]:
        """拉取更新"""
        return git_pull(path, remote, branch)

    @staticmethod
    def branch(path: str = ".", create: str | None = None, delete: str | None = None) -> dict[str, Any]:
        """分支操作"""
        return git_branch(path, create, delete)


def _run_git_command(args: list[str], cwd: str = ".") -> dict[str, Any]:
    """
    执行 Git 命令

    Args:
        args: Git 命令参数
        cwd: 工作目录

    Returns:
        命令结果
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=60,
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out",
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Git command not found",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def git_status(path: str = ".") -> dict[str, Any]:
    """
    获取 Git 状态

    Args:
        path: 仓库路径

    Returns:
        状态信息
    """
    try:
        repo_path = Path(path)

        # 检查是否是 Git 仓库
        if not (repo_path / ".git").exists():
            return {
                "success": False,
                "error": "Not a git repository",
            }

        # 获取状态
        result = _run_git_command(["status", "--porcelain"], cwd=path)

        if not result["success"]:
            return result

        # 解析状态
        changes = []
        for line in result["stdout"].split("\n"):
            if line:
                status = line[:2]
                file_path = line[3:]
                changes.append({
                    "status": status.strip(),
                    "file": file_path,
                    "is_staged": status[0] != " " and status[0] != "?",
                    "is_untracked": status == "??",
                })

        # 获取分支
        branch_result = _run_git_command(["branch", "--show-current"], cwd=path)
        current_branch = branch_result["stdout"] if branch_result["success"] else "unknown"

        # 获取远程
        remote_result = _run_git_command(["remote", "-v"], cwd=path)
        remotes = {}
        if remote_result["success"] and remote_result["stdout"]:
            for line in remote_result["stdout"].split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remote_name = parts[0]
                        remote_url = parts[1]
                        remotes[remote_name] = remote_url

        return {
            "success": True,
            "branch": current_branch,
            "remotes": remotes,
            "changes": changes,
            "staged_count": sum(1 for c in changes if c["is_staged"]),
            "untracked_count": sum(1 for c in changes if c["is_untracked"]),
            "is_clean": len(changes) == 0,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def git_commit(message: str, path: str = ".", add_all: bool = True) -> dict[str, Any]:
    """
    提交更改

    Args:
        message: 提交信息
        path: 仓库路径
        add_all: 是否添加所有更改

    Returns:
        提交结果
    """
    try:
        repo_path = Path(path)

        if not (repo_path / ".git").exists():
            return {
                "success": False,
                "error": "Not a git repository",
            }

        if not message:
            return {
                "success": False,
                "error": "Commit message is required",
            }

        # 添加所有更改
        if add_all:
            add_result = _run_git_command(["add", "-A"], cwd=path)
            if not add_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to add changes: {add_result['stderr']}",
                }

        # 提交
        commit_result = _run_git_command(["commit", "-m", message], cwd=path)

        if not commit_result["success"]:
            if "nothing to commit" in commit_result["stdout"]:
                return {
                    "success": True,
                    "message": "Nothing to commit",
                    "is_clean": True,
                }
            return {
                "success": False,
                "error": commit_result["stderr"],
            }

        # 获取提交 hash
        hash_result = _run_git_command(["rev-parse", "HEAD"], cwd=path)
        commit_hash = hash_result["stdout"] if hash_result["success"] else ""

        return {
            "success": True,
            "message": message,
            "commit_hash": commit_hash,
            "output": commit_result["stdout"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def git_push(path: str = ".", remote: str = "origin", branch: str = "") -> dict[str, Any]:
    """
    推送到远程

    Args:
        path: 仓库路径
        remote: 远程名称
        branch: 分支名称

    Returns:
        推送结果
    """
    try:
        repo_path = Path(path)

        if not (repo_path / ".git").exists():
            return {
                "success": False,
                "error": "Not a git repository",
            }

        # 获取当前分支
        if not branch:
            branch_result = _run_git_command(["branch", "--show-current"], cwd=path)
            if branch_result["success"]:
                branch = branch_result["stdout"]
            else:
                branch = "main"

        # 推送
        push_result = _run_git_command(["push", remote, branch], cwd=path)

        if not push_result["success"]:
            return {
                "success": False,
                "error": push_result["stderr"],
                "stdout": push_result["stdout"],
            }

        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "output": push_result["stdout"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def git_pull(path: str = ".", remote: str = "origin", branch: str = "") -> dict[str, Any]:
    """
    拉取更新

    Args:
        path: 仓库路径
        remote: 远程名称
        branch: 分支名称

    Returns:
        拉取结果
    """
    try:
        repo_path = Path(path)

        if not (repo_path / ".git").exists():
            return {
                "success": False,
                "error": "Not a git repository",
            }

        # 获取当前分支
        if not branch:
            branch_result = _run_git_command(["branch", "--show-current"], cwd=path)
            if branch_result["success"]:
                branch = branch_result["stdout"]
            else:
                branch = "main"

        # 拉取
        pull_result = _run_git_command(["pull", remote, branch], cwd=path)

        if not pull_result["success"]:
            return {
                "success": False,
                "error": pull_result["stderr"],
                "stdout": pull_result["stdout"],
            }

        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "output": pull_result["stdout"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def git_branch(
    path: str = ".",
    create: str | None = None,
    delete: str | None = None,
) -> dict[str, Any]:
    """
    分支操作

    Args:
        path: 仓库路径
        create: 创建新分支
        delete: 删除分支

    Returns:
        操作结果
    """
    try:
        repo_path = Path(path)

        if not (repo_path / ".git").exists():
            return {
                "success": False,
                "error": "Not a git repository",
            }

        # 创建分支
        if create:
            result = _run_git_command(["checkout", "-b", create], cwd=path)
            if not result["success"]:
                return {
                    "success": False,
                    "error": result["stderr"],
                }
            return {
                "success": True,
                "action": "created",
                "branch": create,
            }

        # 删除分支
        if delete:
            result = _run_git_command(["branch", "-D", delete], cwd=path)
            if not result["success"]:
                return {
                    "success": False,
                    "error": result["stderr"],
                }
            return {
                "success": True,
                "action": "deleted",
                "branch": delete,
            }

        # 列出分支
        result = _run_git_command(["branch", "-a"], cwd=path)

        if not result["success"]:
            return {
                "success": False,
                "error": result["stderr"],
            }

        branches = []
        current_branch = None

        for line in result["stdout"].split("\n"):
            line = line.strip()
            if not line:
                continue

            is_current = line.startswith("*")
            if is_current:
                current_branch = line[1:].strip()
                line = current_branch

            is_remote = line.startswith("remotes/")
            branch_name = line.replace("remotes/", "") if is_remote else line

            branches.append({
                "name": branch_name,
                "is_current": is_current,
                "is_remote": is_remote,
            })

        return {
            "success": True,
            "branches": branches,
            "current_branch": current_branch,
            "count": len(branches),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }