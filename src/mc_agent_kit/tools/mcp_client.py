"""
MCP (Model Context Protocol) Client Module

实现 MCP 工具客户端，支持工具发现、调用和结果解析。
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from collections.abc import Coroutine

__all__ = [
    "MCPClient",
    "MCPTool",
    "MCPToolResult",
    "MCPClientConfig",
    "MCPConnectionStatus",
    "create_mcp_client",
    "call_tool_sync",
]


class MCPConnectionStatus(Enum):
    """MCP 连接状态"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPTool:
    """
    MCP 工具定义

    Attributes:
        name: 工具名称
        description: 工具描述
        input_schema: 输入参数 JSON Schema
        handler: 工具处理函数
        category: 工具类别
        tags: 工具标签
        version: 工具版本
        timeout: 执行超时时间（秒）
    """

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    handler: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]] | None = None
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    timeout: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPTool:
        """从字典创建"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            input_schema=data.get("input_schema", {}),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
            timeout=data.get("timeout", 30.0),
        )


@dataclass
class MCPToolResult:
    """
    MCP 工具执行结果

    Attributes:
        success: 是否成功
        result: 执行结果
        error: 错误信息
        execution_time: 执行时间（秒）
        tool_name: 工具名称
        metadata: 额外元数据
    """

    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    tool_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_name": self.tool_name,
            "metadata": self.metadata,
        }


@dataclass
class MCPClientConfig:
    """
    MCP 客户端配置

    Attributes:
        server_url: MCP 服务器 URL
        timeout: 默认超时时间（秒）
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        enable_cache: 是否启用结果缓存
        cache_ttl: 缓存有效期（秒）
    """

    server_url: str = ""
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_cache: bool = True
    cache_ttl: float = 300.0


class MCPClient:
    """
    MCP 客户端

    提供 MCP 工具的连接、发现和调用功能。

    Example:
        >>> client = MCPClient()
        >>> client.register_tool("read_file", handler=read_file_handler)
        >>> result = client.call_tool("read_file", {"path": "test.txt"})
    """

    def __init__(self, config: MCPClientConfig | None = None):
        """
        初始化 MCP 客户端

        Args:
            config: 客户端配置
        """
        self.config = config or MCPClientConfig()
        self._tools: dict[str, MCPTool] = {}
        self._status = MCPConnectionStatus.DISCONNECTED
        self._cache: dict[str, tuple[Any, float]] = {}
        self._stats: dict[str, dict[str, Any]] = {}

    @property
    def status(self) -> MCPConnectionStatus:
        """获取连接状态"""
        return self._status

    @property
    def tools(self) -> dict[str, MCPTool]:
        """获取已注册的工具"""
        return self._tools.copy()

    def connect(self, server_url: str | None = None) -> bool:
        """
        连接到 MCP 服务器

        Args:
            server_url: 服务器 URL（可选，覆盖配置）

        Returns:
            是否连接成功
        """
        url = server_url or self.config.server_url
        if not url:
            self._status = MCPConnectionStatus.CONNECTED
            return True

        self._status = MCPConnectionStatus.CONNECTING
        try:
            # 模拟连接过程
            # 实际实现中这里会建立 WebSocket 或 HTTP 连接
            self.config.server_url = url
            self._status = MCPConnectionStatus.CONNECTED
            return True
        except Exception:
            self._status = MCPConnectionStatus.ERROR
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self._status = MCPConnectionStatus.DISCONNECTED
        self._cache.clear()

    def register_tool(
        self,
        name: str,
        handler: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]],
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        category: str = "general",
        tags: list[str] | None = None,
        version: str = "1.0.0",
        timeout: float | None = None,
    ) -> bool:
        """
        注册工具

        Args:
            name: 工具名称
            handler: 处理函数
            description: 描述
            input_schema: 输入 Schema
            category: 类别
            tags: 标签
            version: 版本
            timeout: 超时时间

        Returns:
            是否注册成功
        """
        if name in self._tools:
            return False

        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema or {},
            handler=handler,
            category=category,
            tags=tags or [],
            version=version,
            timeout=timeout or self.config.timeout,
        )
        self._tools[name] = tool
        self._stats[name] = {
            "call_count": 0,
            "success_count": 0,
            "error_count": 0,
            "total_time": 0.0,
        }
        return True

    def unregister_tool(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            是否注销成功
        """
        if name not in self._tools:
            return False
        del self._tools[name]
        if name in self._stats:
            del self._stats[name]
        return True

    def get_tool(self, name: str) -> MCPTool | None:
        """
        获取工具定义

        Args:
            name: 工具名称

        Returns:
            工具定义或 None
        """
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[MCPTool]:
        """
        列出工具

        Args:
            category: 按类别过滤

        Returns:
            工具列表
        """
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def search_tools(self, query: str) -> list[MCPTool]:
        """
        搜索工具

        Args:
            query: 搜索关键词

        Returns:
            匹配的工具列表
        """
        query_lower = query.lower()
        results = []
        for tool in self._tools.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
                or query_lower in " ".join(tool.tags).lower()
            ):
                results.append(tool)
        return results

    def call_tool(
        self,
        name: str,
        args: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> MCPToolResult:
        """
        调用工具（同步）

        Args:
            name: 工具名称
            args: 调用参数
            use_cache: 是否使用缓存

        Returns:
            执行结果
        """
        args = args or {}

        # 检查工具是否存在
        tool = self._tools.get(name)
        if not tool:
            return MCPToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                tool_name=name,
            )

        # 检查缓存
        if use_cache and self.config.enable_cache:
            cache_key = self._get_cache_key(name, args)
            cached = self._cache.get(cache_key)
            if cached:
                result, timestamp = cached
                if time.time() - timestamp < self.config.cache_ttl:
                    return MCPToolResult(
                        success=True,
                        result=result,
                        tool_name=name,
                        metadata={"cached": True},
                    )

        # 执行工具
        start_time = time.time()
        try:
            if tool.handler is None:
                return MCPToolResult(
                    success=False,
                    error=f"Tool '{name}' has no handler",
                    tool_name=name,
                )

            result = tool.handler(**args)
            execution_time = time.time() - start_time

            # 更新统计
            self._update_stats(name, True, execution_time)

            # 更新缓存
            if use_cache and self.config.enable_cache:
                self._cache[cache_key] = (result, time.time())

            return MCPToolResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=name,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(name, False, execution_time)
            return MCPToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=name,
            )

    async def call_tool_async(
        self,
        name: str,
        args: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> MCPToolResult:
        """
        调用工具（异步）

        Args:
            name: 工具名称
            args: 调用参数
            use_cache: 是否使用缓存

        Returns:
            执行结果
        """
        args = args or {}

        tool = self._tools.get(name)
        if not tool:
            return MCPToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                tool_name=name,
            )

        # 检查缓存
        if use_cache and self.config.enable_cache:
            cache_key = self._get_cache_key(name, args)
            cached = self._cache.get(cache_key)
            if cached:
                result, timestamp = cached
                if time.time() - timestamp < self.config.cache_ttl:
                    return MCPToolResult(
                        success=True,
                        result=result,
                        tool_name=name,
                        metadata={"cached": True},
                    )

        start_time = time.time()
        try:
            if tool.handler is None:
                return MCPToolResult(
                    success=False,
                    error=f"Tool '{name}' has no handler",
                    tool_name=name,
                )

            # 支持异步和同步处理器
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**args)
            else:
                result = tool.handler(**args)

            execution_time = time.time() - start_time

            self._update_stats(name, True, execution_time)

            if use_cache and self.config.enable_cache:
                self._cache[cache_key] = (result, time.time())

            return MCPToolResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=name,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(name, False, execution_time)
            return MCPToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=name,
            )

    def _get_cache_key(self, name: str, args: dict[str, Any]) -> str:
        """生成缓存键"""
        args_str = json.dumps(args, sort_keys=True)
        return f"{name}:{args_str}"

    def _update_stats(self, name: str, success: bool, execution_time: float) -> None:
        """更新统计信息"""
        if name not in self._stats:
            self._stats[name] = {
                "call_count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_time": 0.0,
            }
        self._stats[name]["call_count"] += 1
        self._stats[name]["total_time"] += execution_time
        if success:
            self._stats[name]["success_count"] += 1
        else:
            self._stats[name]["error_count"] += 1

    def get_stats(self, name: str | None = None) -> dict[str, Any]:
        """
        获取统计信息

        Args:
            name: 工具名称（可选，获取单个工具统计）

        Returns:
            统计信息
        """
        if name:
            return self._stats.get(name, {})
        return self._stats.copy()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()


def create_mcp_client(
    server_url: str = "",
    timeout: float = 30.0,
    enable_cache: bool = True,
) -> MCPClient:
    """
    创建 MCP 客户端

    Args:
        server_url: 服务器 URL
        timeout: 超时时间
        enable_cache: 是否启用缓存

    Returns:
        MCP 客户端实例
    """
    config = MCPClientConfig(
        server_url=server_url,
        timeout=timeout,
        enable_cache=enable_cache,
    )
    return MCPClient(config)


def call_tool_sync(
    client: MCPClient,
    name: str,
    args: dict[str, Any] | None = None,
) -> MCPToolResult:
    """
    同步调用工具的便捷函数

    Args:
        client: MCP 客户端
        name: 工具名称
        args: 调用参数

    Returns:
        执行结果
    """
    return client.call_tool(name, args)