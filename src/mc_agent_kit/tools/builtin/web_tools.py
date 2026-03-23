"""
Web Tools Module

网络工具，提供 HTTP 请求、URL 抓取等功能。
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any
from urllib.parse import urlencode

__all__ = [
    "WebTools",
    "http_get",
    "http_post", 
    "fetch_url",
    "download_file",
]


class WebTools:
    """网络工具类"""

    @staticmethod
    def get(url: str, headers: dict[str, str] | None = None, timeout: float = 30.0) -> dict[str, Any]:
        """发送 GET 请求"""
        return http_get(url, headers, timeout)

    @staticmethod
    def post(
        url: str,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """发送 POST 请求"""
        return http_post(url, data, json_data, headers, timeout)

    @staticmethod
    def fetch(url: str, timeout: float = 30.0) -> dict[str, Any]:
        """抓取 URL 内容"""
        return fetch_url(url, timeout)

    @staticmethod
    def download(url: str, path: str, timeout: float = 60.0) -> dict[str, Any]:
        """下载文件"""
        return download_file(url, path, timeout)


def http_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    发送 HTTP GET 请求

    Args:
        url: URL 地址
        headers: 请求头
        timeout: 超时时间

    Returns:
        响应结果
    """
    try:
        request = urllib.request.Request(url, method="GET")

        # 添加请求头
        if headers:
            for key, value in headers.items():
                request.add_header(key, value)

        # 默认 User-Agent
        if not headers or "User-Agent" not in headers:
            request.add_header("User-Agent", "MC-Agent-Kit/1.0")

        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8")
            response_headers = dict(response.headers)

            # 尝试解析 JSON
            json_data = None
            content_type = response_headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError:
                    pass

            return {
                "success": True,
                "status_code": response.status,
                "content": content,
                "json": json_data,
                "headers": response_headers,
                "url": response.url,
            }

    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP Error {e.code}: {e.reason}",
            "status_code": e.code,
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"URL Error: {e.reason}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def http_post(
    url: str,
    data: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    发送 HTTP POST 请求

    Args:
        url: URL 地址
        data: 表单数据
        json_data: JSON 数据
        headers: 请求头
        timeout: 超时时间

    Returns:
        响应结果
    """
    try:
        # 准备请求体
        body = None
        content_type = None

        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            content_type = "application/json"
        elif data is not None:
            body = urlencode(data).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"

        request = urllib.request.Request(url, data=body, method="POST")

        # 添加请求头
        if headers:
            for key, value in headers.items():
                request.add_header(key, value)

        if content_type:
            request.add_header("Content-Type", content_type)

        if not headers or "User-Agent" not in headers:
            request.add_header("User-Agent", "MC-Agent-Kit/1.0")

        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8")
            response_headers = dict(response.headers)

            json_response = None
            content_type_header = response_headers.get("Content-Type", "")
            if "application/json" in content_type_header:
                try:
                    json_response = json.loads(content)
                except json.JSONDecodeError:
                    pass

            return {
                "success": True,
                "status_code": response.status,
                "content": content,
                "json": json_response,
                "headers": response_headers,
                "url": response.url,
            }

    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP Error {e.code}: {e.reason}",
            "status_code": e.code,
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"URL Error: {e.reason}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def fetch_url(url: str, timeout: float = 30.0) -> dict[str, Any]:
    """
    抓取 URL 内容

    Args:
        url: URL 地址
        timeout: 超时时间

    Returns:
        抓取结果
    """
    try:
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "MC-Agent-Kit/1.0")

        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8")

            # 简单提取文本内容（移除 HTML 标签）
            # 实际实现中可以使用 BeautifulSoup 等库
            text = content
            if "<" in text and ">" in text:
                # 简单的 HTML 标签移除
                import re
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"\s+", " ", text).strip()

            return {
                "success": True,
                "url": response.url,
                "content": text,
                "raw_content": content,
                "status_code": response.status,
                "headers": dict(response.headers),
            }

    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP Error {e.code}: {e.reason}",
            "status_code": e.code,
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"URL Error: {e.reason}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def download_file(url: str, path: str, timeout: float = 60.0) -> dict[str, Any]:
    """
    下载文件

    Args:
        url: URL 地址
        path: 保存路径
        timeout: 超时时间

    Returns:
        下载结果
    """
    try:
        from pathlib import Path

        request = urllib.request.Request(url)
        request.add_header("User-Agent", "MC-Agent-Kit/1.0")

        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with urllib.request.urlopen(request, timeout=timeout) as response:
            with open(file_path, "wb") as f:
                f.write(response.read())

            return {
                "success": True,
                "url": response.url,
                "path": str(file_path.absolute()),
                "size": file_path.stat().st_size,
                "status_code": response.status,
            }

    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP Error {e.code}: {e.reason}",
            "status_code": e.code,
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"URL Error: {e.reason}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }