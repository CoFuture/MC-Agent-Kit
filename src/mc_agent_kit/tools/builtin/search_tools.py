"""
Search Tools Module

搜索工具，提供知识库搜索、代码搜索等功能。
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

__all__ = [
    "SearchTools",
    "search_knowledge",
    "search_code",
    "search_files",
]


class SearchTools:
    """搜索工具类"""

    @staticmethod
    def knowledge(
        query: str,
        limit: int = 10,
        category: str | None = None,
    ) -> dict[str, Any]:
        """搜索知识库"""
        return search_knowledge(query, limit, category)

    @staticmethod
    def code(
        query: str,
        path: str = ".",
        file_pattern: str = "*.py",
    ) -> dict[str, Any]:
        """搜索代码"""
        return search_code(query, path, file_pattern)

    @staticmethod
    def files(
        query: str,
        path: str = ".",
        file_pattern: str = "*",
    ) -> dict[str, Any]:
        """搜索文件"""
        return search_files(query, path, file_pattern)


def search_knowledge(
    query: str,
    limit: int = 10,
    category: str | None = None,
) -> dict[str, Any]:
    """
    搜索知识库

    Args:
        query: 搜索查询
        limit: 结果数量限制
        category: 类别过滤

    Returns:
        搜索结果
    """
    try:
        # 尝试使用知识库模块
        try:
            from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval

            retriever = KnowledgeRetrieval()
            results = retriever.search(query, limit=limit)

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }

        except ImportError:
            # 知识库模块不可用，返回模拟结果
            return {
                "success": True,
                "query": query,
                "results": [],
                "count": 0,
                "note": "Knowledge base module not available",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def search_code(
    query: str,
    path: str = ".",
    file_pattern: str = "*.py",
) -> dict[str, Any]:
    """
    搜索代码

    Args:
        query: 搜索查询（支持正则表达式）
        path: 搜索路径
        file_pattern: 文件模式

    Returns:
        搜索结果
    """
    try:
        search_path = Path(path)

        if not search_path.exists():
            return {
                "success": False,
                "error": f"Path not found: {path}",
            }

        results = []
        pattern = re.compile(query, re.IGNORECASE)

        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append({
                                    "file": str(file_path.relative_to(search_path)),
                                    "line": line_num,
                                    "content": line.strip(),
                                    "match": pattern.search(line).group() if pattern.search(line) else None,
                                })
                except (UnicodeDecodeError, PermissionError):
                    continue

        return {
            "success": True,
            "query": query,
            "path": str(search_path.absolute()),
            "results": results[:100],  # 限制结果数量
            "count": len(results),
            "file_count": len(set(r["file"] for r in results)),
        }

    except re.error as e:
        return {
            "success": False,
            "error": f"Invalid regex pattern: {e}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def search_files(
    query: str,
    path: str = ".",
    file_pattern: str = "*",
) -> dict[str, Any]:
    """
    搜索文件

    Args:
        query: 搜索查询
        path: 搜索路径
        file_pattern: 文件模式

    Returns:
        搜索结果
    """
    try:
        search_path = Path(path)

        if not search_path.exists():
            return {
                "success": False,
                "error": f"Path not found: {path}",
            }

        results = []
        query_lower = query.lower()

        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file():
                if query_lower in file_path.name.lower():
                    stat = file_path.stat()
                    results.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(search_path)),
                        "absolute_path": str(file_path.absolute()),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "extension": file_path.suffix,
                    })

        # 按相关度排序（名称匹配度）
        results.sort(key=lambda x: x["name"].lower().find(query_lower))

        return {
            "success": True,
            "query": query,
            "path": str(search_path.absolute()),
            "results": results[:100],
            "count": len(results),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }