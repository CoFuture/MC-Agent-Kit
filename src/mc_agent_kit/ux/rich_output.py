"""
Rich CLI 输出模块

使用 Rich 库提供美化的 CLI 输出，包括：
- 彩色表格和面板
- 进度条和旋转器
- 语法高亮
- 交互式输出
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

# Rich 导入（可选依赖）
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TimeElapsedColumn,
    )
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.style import Style
    from rich.color import Color

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class OutputTheme(Enum):
    """输出主题"""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    MONOKAI = "monokai"
    NORD = "nord"


@dataclass
class RichOutputConfig:
    """Rich 输出配置"""
    theme: OutputTheme = OutputTheme.DEFAULT
    show_timestamp: bool = True
    show_emoji: bool = True
    color_system: str = "auto"  # auto, standard, 256, truecolor, none
    width: int | None = None  # None = auto detect
    legacy_windows: bool = False
    force_terminal: bool = False


@dataclass
class ProgressInfo:
    """进度信息"""
    description: str
    total: int
    completed: int = 0
    status: str = ""
    start_time: float = field(default_factory=time.time)

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def eta(self) -> float:
        if self.completed == 0 or self.elapsed == 0:
            return 0.0
        rate = self.completed / self.elapsed
        remaining = self.total - self.completed
        return remaining / rate if rate > 0 else 0.0


class RichOutputManager:
    """Rich 输出管理器

    提供美化的 CLI 输出功能。

    使用示例:
        output = RichOutputManager()
        output.print_header("MC-Agent-Kit", "v1.35.0")
        output.print_success("项目创建成功")
        output.print_table([{"name": "API", "count": 100}])
    """

    def __init__(self, config: RichOutputConfig | None = None):
        """初始化输出管理器

        Args:
            config: 输出配置
        """
        self.config = config or RichOutputConfig()
        self._lock = threading.Lock()
        self._console: Any = None
        self._progress: Any = None
        self._progress_info: dict[str, ProgressInfo] = {}

        if RICH_AVAILABLE:
            self._init_console()

    def _init_console(self) -> None:
        """初始化 Rich Console"""
        if not RICH_AVAILABLE:
            return

        self._console = Console(
            color_system=self.config.color_system,
            width=self.config.width,
            legacy_windows=self.config.legacy_windows,
            force_terminal=self.config.force_terminal,
        )

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        if self.config.show_timestamp:
            return f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] "
        return ""

    def print(self, message: str, **kwargs: Any) -> None:
        """打印消息

        Args:
            message: 消息内容（支持 Rich markup）
            **kwargs: 额外参数
        """
        if RICH_AVAILABLE and self._console:
            self._console.print(message, **kwargs)
        else:
            # Fallback to plain text
            import re
            clean_message = re.sub(r'\[.*?\]', '', message)
            print(clean_message)

    def print_header(self, title: str, version: str = "", subtitle: str = "") -> None:
        """打印标题头部

        Args:
            title: 标题
            version: 版本号
            subtitle: 副标题
        """
        if RICH_AVAILABLE and self._console:
            content = f"[bold cyan]{title}[/bold cyan]"
            if version:
                content += f" [dim]v{version}[/dim]"
            if subtitle:
                content += f"\n[dim]{subtitle}[/dim]"
            panel = Panel(content, border_style="cyan", padding=(1, 2))
            self._console.print(panel)
        else:
            print(f"\n{'='*50}")
            print(f"{title} {version}")
            if subtitle:
                print(subtitle)
            print('='*50)

    def print_success(self, message: str, details: str | None = None) -> None:
        """打印成功消息

        Args:
            message: 成功消息
            details: 详细信息
        """
        timestamp = self._get_timestamp()
        emoji = "✅ " if self.config.show_emoji else ""

        if RICH_AVAILABLE and self._console:
            content = f"{timestamp}[bold green]{emoji}{message}[/bold green]"
            if details:
                content += f"\n[dim]{details}[/dim]"
            self._console.print(content)
        else:
            print(f"{emoji}{message}")
            if details:
                print(f"  {details}")

    def print_error(self, message: str, error: str | None = None, suggestions: list[str] | None = None) -> None:
        """打印错误消息

        Args:
            message: 错误消息
            error: 错误详情
            suggestions: 建议列表
        """
        timestamp = self._get_timestamp()
        emoji = "❌ " if self.config.show_emoji else ""

        if RICH_AVAILABLE and self._console:
            content = f"{timestamp}[bold red]{emoji}{message}[/bold red]"
            if error:
                content += f"\n[red]{error}[/red]"
            if suggestions:
                content += "\n[yellow]建议:[/yellow]"
                for s in suggestions:
                    content += f"\n  • {s}"
            self._console.print(content)
        else:
            print(f"{emoji}{message}")
            if error:
                print(f"  错误: {error}")
            if suggestions:
                print("建议:")
                for s in suggestions:
                    print(f"  • {s}")

    def print_warning(self, message: str, details: str | None = None) -> None:
        """打印警告消息

        Args:
            message: 警告消息
            details: 详细信息
        """
        timestamp = self._get_timestamp()
        emoji = "⚠️  " if self.config.show_emoji else ""

        if RICH_AVAILABLE and self._console:
            content = f"{timestamp}[bold yellow]{emoji}{message}[/bold yellow]"
            if details:
                content += f"\n[dim]{details}[/dim]"
            self._console.print(content)
        else:
            print(f"{emoji}{message}")
            if details:
                print(f"  {details}")

    def print_info(self, message: str, details: str | None = None) -> None:
        """打印信息消息

        Args:
            message: 信息消息
            details: 详细信息
        """
        timestamp = self._get_timestamp()
        emoji = "ℹ️  " if self.config.show_emoji else ""

        if RICH_AVAILABLE and self._console:
            content = f"{timestamp}[bold blue]{emoji}{message}[/bold blue]"
            if details:
                content += f"\n[dim]{details}[/dim]"
            self._console.print(content)
        else:
            print(f"{emoji}{message}")
            if details:
                print(f"  {details}")

    def print_table(
        self,
        data: list[dict[str, Any]],
        title: str = "",
        columns: list[str] | None = None,
        show_header: bool = True,
    ) -> None:
        """打印表格

        Args:
            data: 数据列表
            title: 表格标题
            columns: 列名列表（默认从数据推断）
            show_header: 是否显示表头
        """
        if not data:
            self.print_info("无数据")
            return

        if RICH_AVAILABLE and self._console:
            table = Table(title=title, show_header=show_header, border_style="dim")

            # 确定列名
            if columns is None:
                columns = list(data[0].keys())

            # 添加列
            for col in columns:
                table.add_column(col, style="cyan")

            # 添加行
            for row in data:
                table.add_column
                table.add_row(*[str(row.get(col, "")) for col in columns])

            self._console.print(table)
        else:
            # Fallback: 简单文本表格
            if columns is None:
                columns = list(data[0].keys())

            print(f"\n{title}" if title else "")
            print(" | ".join(columns))
            print("-" * (sum(len(c) for c in columns) + 3 * len(columns)))
            for row in data:
                print(" | ".join(str(row.get(col, "")) for col in columns))

    def print_code(self, code: str, language: str = "python", line_numbers: bool = True) -> None:
        """打印代码

        Args:
            code: 代码内容
            language: 语言类型
            line_numbers: 是否显示行号
        """
        if RICH_AVAILABLE and self._console:
            syntax = Syntax(code, language, line_numbers=line_numbers, theme="monokai")
            self._console.print(syntax)
        else:
            print(f"```{language}")
            print(code)
            print("```")

    def print_markdown(self, text: str) -> None:
        """打印 Markdown

        Args:
            text: Markdown 文本
        """
        if RICH_AVAILABLE and self._console:
            md = Markdown(text)
            self._console.print(md)
        else:
            print(text)

    def print_list(self, items: list[str], title: str = "", numbered: bool = False) -> None:
        """打印列表

        Args:
            items: 列表项
            title: 标题
            numbered: 是否编号
        """
        if title:
            self.print(f"\n[bold]{title}[/bold]")

        for i, item in enumerate(items, 1):
            if numbered:
                self.print(f"  [cyan]{i}.[/cyan] {item}")
            else:
                self.print(f"  [dim]•[/dim] {item}")

    def create_progress(self, description: str = "处理中...") -> Any:
        """创建进度条

        Args:
            description: 描述

        Returns:
            Progress 对象
        """
        if RICH_AVAILABLE:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self._console,
            )
            return progress
        return None

    def start_spinner(self, message: str = "处理中...") -> None:
        """开始旋转动画

        Args:
            message: 显示消息
        """
        if RICH_AVAILABLE and self._console:
            self._console.print(f"[dim]⏳ {message}[/dim]")

    def stop_spinner(self, success: bool = True, message: str = "") -> None:
        """停止旋转动画

        Args:
            success: 是否成功
            message: 完成消息
        """
        if success:
            self.print_success(message or "完成")
        else:
            self.print_error(message or "失败")

    def print_panel(self, content: str, title: str = "", style: str = "cyan") -> None:
        """打印面板

        Args:
            content: 内容
            title: 标题
            style: 样式
        """
        if RICH_AVAILABLE and self._console:
            panel = Panel(content, title=title, border_style=style)
            self._console.print(panel)
        else:
            if title:
                print(f"\n[{title}]")
            print(content)

    def print_rule(self, title: str = "") -> None:
        """打印分隔线

        Args:
            title: 标题
        """
        if RICH_AVAILABLE and self._console:
            self._console.rule(title)
        else:
            print(f"\n{'─' * 20} {title} {'─' * 20}")

    def print_search_results(
        self,
        results: list[dict[str, Any]],
        query: str,
        result_type: str = "API",
    ) -> None:
        """打印搜索结果

        Args:
            results: 搜索结果
            query: 查询词
            result_type: 结果类型
        """
        emoji = "🔍 " if self.config.show_emoji else ""

        if RICH_AVAILABLE and self._console:
            self._console.print(
                f"\n{emoji}[bold]搜索结果:[/bold] [cyan]{query}[/cyan] "
                f"[dim]({len(results)} 个{result_type})[/dim]"
            )
            self._console.print()

            for i, result in enumerate(results, 1):
                name = result.get("name", "Unknown")
                module = result.get("module", "")
                description = result.get("description", "")
                scope = result.get("scope", "")

                self._console.print(f"  [bold cyan]{i}. {name}[/bold cyan]")
                if module:
                    self._console.print(f"     [dim]模块:[/dim] {module}")
                if scope:
                    self._console.print(f"     [dim]作用域:[/dim] {scope}")
                if description:
                    # 截断长描述
                    desc_display = description[:100] + "..." if len(description) > 100 else description
                    self._console.print(f"     [dim]{desc_display}[/dim]")
                self._console.print()
        else:
            print(f"\n{emoji}搜索结果: {query} ({len(results)} 个{result_type})")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.get('name', 'Unknown')}")
                if result.get("module"):
                    print(f"   模块: {result['module']}")
                if result.get("scope"):
                    print(f"   作用域: {result['scope']}")
                desc = result.get("description", "")[:100]
                if desc:
                    print(f"   {desc}...")

    def print_diagnostic_results(
        self,
        issues: list[dict[str, Any]],
        summary: str = "",
    ) -> None:
        """打印诊断结果

        Args:
            issues: 问题列表
            summary: 总结
        """
        emoji = "🔍 " if self.config.show_emoji else ""

        if RICH_AVAILABLE and self._console:
            self._console.print(f"\n{emoji}[bold]诊断结果[/bold]")

            if not issues:
                self._console.print("[green]✅ 未发现问题[/green]")
                return

            for issue in issues:
                severity = issue.get("severity", "info")
                message = issue.get("message", "")

                if severity == "error":
                    style = "bold red"
                    icon = "❌"
                elif severity == "warning":
                    style = "bold yellow"
                    icon = "⚠️"
                else:
                    style = "bold blue"
                    icon = "ℹ️"

                self._console.print(f"  [{style}]{icon} {message}[/{style}]")

                if issue.get("location"):
                    self._console.print(f"     [dim]位置:[/dim] {issue['location']}")
                if issue.get("suggestion"):
                    self._console.print(f"     [dim]建议:[/dim] {issue['suggestion']}")

            if summary:
                self._console.print(f"\n[dim]{summary}[/dim]")
        else:
            print(f"\n{emoji}诊断结果")
            if not issues:
                print("✅ 未发现问题")
                return

            for issue in issues:
                print(f"  {issue.get('severity', 'info')}: {issue.get('message', '')}")

            if summary:
                print(f"\n{summary}")


def create_rich_output(config: RichOutputConfig | None = None) -> RichOutputManager:
    """创建 Rich 输出管理器

    Args:
        config: 输出配置

    Returns:
        RichOutputManager 实例
    """
    return RichOutputManager(config)


# 全局实例
_rich_output: RichOutputManager | None = None


def get_rich_output() -> RichOutputManager:
    """获取全局 Rich 输出管理器"""
    global _rich_output
    if _rich_output is None:
        _rich_output = RichOutputManager()
    return _rich_output