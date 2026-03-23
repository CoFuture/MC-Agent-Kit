"""
File Tools Module

文件操作工具，提供读取、写入、列表、删除等功能。
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

__all__ = [
    "FileTools",
    "read_file",
    "write_file",
    "list_files",
    "delete_file",
    "file_exists",
    "copy_file",
    "move_file",
    "create_directory",
]


class FileTools:
    """文件工具类"""

    @staticmethod
    def read(path: str, encoding: str = "utf-8") -> dict[str, Any]:
        """读取文件"""
        return read_file(path, encoding)

    @staticmethod
    def write(path: str, content: str, encoding: str = "utf-8") -> dict[str, Any]:
        """写入文件"""
        return write_file(path, content, encoding)

    @staticmethod
    def list_dir(path: str, pattern: str = "*") -> dict[str, Any]:
        """列出目录"""
        return list_files(path, pattern)

    @staticmethod
    def delete(path: str) -> dict[str, Any]:
        """删除文件"""
        return delete_file(path)

    @staticmethod
    def exists(path: str) -> dict[str, Any]:
        """检查文件是否存在"""
        return file_exists(path)

    @staticmethod
    def copy(src: str, dst: str) -> dict[str, Any]:
        """复制文件"""
        return copy_file(src, dst)

    @staticmethod
    def move(src: str, dst: str) -> dict[str, Any]:
        """移动文件"""
        return move_file(src, dst)

    @staticmethod
    def mkdir(path: str) -> dict[str, Any]:
        """创建目录"""
        return create_directory(path)


def read_file(path: str, encoding: str = "utf-8") -> dict[str, Any]:
    """
    读取文件内容

    Args:
        path: 文件路径
        encoding: 编码格式

    Returns:
        包含文件内容和元数据的字典
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
            }

        if not file_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path}",
            }

        with open(file_path, encoding=encoding) as f:
            content = f.read()

        stat = file_path.stat()

        return {
            "success": True,
            "content": content,
            "path": str(file_path.absolute()),
            "size": stat.st_size,
            "lines": content.count("\n") + 1,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    mode: str = "w",
) -> dict[str, Any]:
    """
    写入文件

    Args:
        path: 文件路径
        content: 文件内容
        encoding: 编码格式
        mode: 写入模式 (w: 覆盖, a: 追加)

    Returns:
        操作结果
    """
    try:
        file_path = Path(path)

        # 创建父目录
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)

        stat = file_path.stat()

        return {
            "success": True,
            "path": str(file_path.absolute()),
            "size": stat.st_size,
            "bytes_written": len(content.encode(encoding)),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def list_files(path: str, pattern: str = "*") -> dict[str, Any]:
    """
    列出目录内容

    Args:
        path: 目录路径
        pattern: 文件模式 (glob 格式)

    Returns:
        包含文件列表的字典
    """
    try:
        dir_path = Path(path)

        if not dir_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {path}",
            }

        if not dir_path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {path}",
            }

        files = []
        for item in dir_path.glob(pattern):
            stat = item.stat()
            files.append({
                "name": item.name,
                "path": str(item.absolute()),
                "is_dir": item.is_dir(),
                "is_file": item.is_file(),
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
            })

        return {
            "success": True,
            "path": str(dir_path.absolute()),
            "files": files,
            "count": len(files),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def delete_file(path: str) -> dict[str, Any]:
    """
    删除文件

    Args:
        path: 文件路径

    Returns:
        操作结果
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
            }

        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()

        return {
            "success": True,
            "path": str(file_path.absolute()),
            "was_directory": file_path.is_dir(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def file_exists(path: str) -> dict[str, Any]:
    """
    检查文件是否存在

    Args:
        path: 文件路径

    Returns:
        检查结果
    """
    try:
        file_path = Path(path)
        exists = file_path.exists()

        result = {
            "success": True,
            "path": str(file_path.absolute()),
            "exists": exists,
        }

        if exists:
            result["is_file"] = file_path.is_file()
            result["is_dir"] = file_path.is_dir()

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def copy_file(src: str, dst: str) -> dict[str, Any]:
    """
    复制文件

    Args:
        src: 源文件路径
        dst: 目标路径

    Returns:
        操作结果
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return {
                "success": False,
                "error": f"Source not found: {src}",
            }

        # 创建目标目录
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

        return {
            "success": True,
            "src": str(src_path.absolute()),
            "dst": str(dst_path.absolute()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def move_file(src: str, dst: str) -> dict[str, Any]:
    """
    移动文件

    Args:
        src: 源文件路径
        dst: 目标路径

    Returns:
        操作结果
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return {
                "success": False,
                "error": f"Source not found: {src}",
            }

        # 创建目标目录
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(src_path), str(dst_path))

        return {
            "success": True,
            "src": str(src_path.absolute()),
            "dst": str(dst_path.absolute()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def create_directory(path: str) -> dict[str, Any]:
    """
    创建目录

    Args:
        path: 目录路径

    Returns:
        操作结果
    """
    try:
        dir_path = Path(path)

        if dir_path.exists():
            return {
                "success": True,
                "path": str(dir_path.absolute()),
                "created": False,
                "message": "Directory already exists",
            }

        dir_path.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "path": str(dir_path.absolute()),
            "created": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }