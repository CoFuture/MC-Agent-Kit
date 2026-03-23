"""
MC-Agent-Kit Builtin Tools

内置工具集，提供常用工具实现。
"""

from mc_agent_kit.tools.builtin.file_tools import (
    FileTools,
    read_file,
    write_file,
    list_files,
    delete_file,
)
from mc_agent_kit.tools.builtin.web_tools import (
    WebTools,
    http_get,
    http_post,
    fetch_url,
)
from mc_agent_kit.tools.builtin.code_tools import (
    CodeTools,
    format_code,
    lint_code,
    run_tests,
)
from mc_agent_kit.tools.builtin.search_tools import (
    SearchTools,
    search_knowledge,
    search_code,
)
from mc_agent_kit.tools.builtin.git_tools import (
    GitTools,
    git_status,
    git_commit,
    git_push,
)

__all__ = [
    # File Tools
    "FileTools",
    "read_file",
    "write_file",
    "list_files",
    "delete_file",
    # Web Tools
    "WebTools",
    "http_get",
    "http_post",
    "fetch_url",
    # Code Tools
    "CodeTools",
    "format_code",
    "lint_code",
    "run_tests",
    # Search Tools
    "SearchTools",
    "search_knowledge",
    "search_code",
    # Git Tools
    "GitTools",
    "git_status",
    "git_commit",
    "git_push",
]


def register_builtin_tools(client) -> int:
    """
    注册所有内置工具到客户端

    Args:
        client: MCP 客户端实例

    Returns:
        注册的工具数量
    """
    count = 0

    # 注册文件工具
    client.register_tool(
        "read_file",
        handler=read_file,
        description="Read file contents",
        category="file",
        tags=["file", "read", "io"],
    )
    count += 1

    client.register_tool(
        "write_file",
        handler=write_file,
        description="Write content to file",
        category="file",
        tags=["file", "write", "io"],
    )
    count += 1

    client.register_tool(
        "list_files",
        handler=list_files,
        description="List files in directory",
        category="file",
        tags=["file", "list", "directory"],
    )
    count += 1

    # 注册网络工具
    client.register_tool(
        "http_get",
        handler=http_get,
        description="Send HTTP GET request",
        category="web",
        tags=["http", "get", "network"],
    )
    count += 1

    client.register_tool(
        "http_post",
        handler=http_post,
        description="Send HTTP POST request",
        category="web",
        tags=["http", "post", "network"],
    )
    count += 1

    client.register_tool(
        "fetch_url",
        handler=fetch_url,
        description="Fetch URL content",
        category="web",
        tags=["http", "fetch", "network"],
    )
    count += 1

    # 注册代码工具
    client.register_tool(
        "format_code",
        handler=format_code,
        description="Format code using standard formatter",
        category="code",
        tags=["code", "format", "style"],
    )
    count += 1

    client.register_tool(
        "lint_code",
        handler=lint_code,
        description="Lint code for issues",
        category="code",
        tags=["code", "lint", "quality"],
    )
    count += 1

    client.register_tool(
        "run_tests",
        handler=run_tests,
        description="Run test suite",
        category="code",
        tags=["test", "pytest", "quality"],
    )
    count += 1

    # 注册搜索工具
    client.register_tool(
        "search_knowledge",
        handler=search_knowledge,
        description="Search knowledge base",
        category="search",
        tags=["search", "knowledge", "docs"],
    )
    count += 1

    client.register_tool(
        "search_code",
        handler=search_code,
        description="Search code in project",
        category="search",
        tags=["search", "code", "project"],
    )
    count += 1

    # 注册 Git 工具
    client.register_tool(
        "git_status",
        handler=git_status,
        description="Get git repository status",
        category="git",
        tags=["git", "status", "vcs"],
    )
    count += 1

    client.register_tool(
        "git_commit",
        handler=git_commit,
        description="Commit changes to git",
        category="git",
        tags=["git", "commit", "vcs"],
    )
    count += 1

    client.register_tool(
        "git_push",
        handler=git_push,
        description="Push changes to remote",
        category="git",
        tags=["git", "push", "vcs"],
    )
    count += 1

    return count