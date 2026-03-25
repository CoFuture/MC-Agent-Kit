"""
增强 CLI REPL 模块

提供交互式命令行界面，包括：
- REPL 模式增强
- 命令历史管理
- 自动补全增强
- 语法高亮
- 结构化输出
- 进度条和动画
- 工作流命令集成
"""

from __future__ import annotations

import os
import re
import shlex
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterator


class OutputFormat(Enum):
    """输出格式"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    TABLE = "table"
    ANSI = "ansi"


class ProgressState(Enum):
    """进度状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CommandHistory:
    """命令历史"""
    commands: deque = field(default_factory=lambda: deque(maxlen=1000))
    file_path: str | None = None
    current_index: int = -1
    
    def add(self, command: str) -> None:
        """添加命令"""
        if command.strip():
            self.commands.append(command)
            self.current_index = len(self.commands)
    
    def up(self) -> str | None:
        """向上导航（更早的命令）"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.commands[self.current_index]
        return None
    
    def down(self) -> str | None:
        """向下导航（更近的命令）"""
        if self.current_index < len(self.commands) - 1:
            self.current_index += 1
            return self.commands[self.current_index]
        self.current_index = len(self.commands)
        return None
    
    def search(self, pattern: str) -> list[str]:
        """搜索历史"""
        regex = re.compile(pattern, re.IGNORECASE)
        return [cmd for cmd in self.commands if regex.search(cmd)]
    
    def save(self) -> None:
        """保存历史到文件"""
        if self.file_path:
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    for cmd in self.commands:
                        f.write(cmd + "\n")
            except Exception:
                pass
    
    def load(self) -> None:
        """从文件加载历史"""
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self.commands.append(line)
            except Exception:
                pass


@dataclass
class CompletionSuggestion:
    """补全建议"""
    text: str
    display: str
    description: str = ""
    type: str = "generic"
    priority: int = 0
    
    def __lt__(self, other: CompletionSuggestion) -> bool:
        return self.priority > other.priority


@dataclass
class SyntaxToken:
    """语法令牌"""
    text: str
    token_type: str
    color: str = ""


@dataclass
class OutputBuilder:
    """输出构建器"""
    lines: list[str] = field(default_factory=list)
    format: OutputFormat = OutputFormat.TEXT
    
    def add(self, line: str) -> "OutputBuilder":
        """添加行"""
        self.lines.append(line)
        return self
    
    def add_heading(self, text: str, level: int = 1) -> "OutputBuilder":
        """添加标题"""
        if self.format == OutputFormat.MARKDOWN:
            self.lines.append(f"{'#' * level} {text}")
        elif self.format == OutputFormat.ANSI:
            self.lines.append(f"\033[1m{text}\033[0m")
        else:
            self.lines.append(text.upper())
        return self
    
    def add_code(self, code: str, language: str = "") -> "OutputBuilder":
        """添加代码"""
        if self.format == OutputFormat.MARKDOWN:
            self.lines.append(f"```{language}")
            self.lines.append(code)
            self.lines.append("```")
        elif self.format == OutputFormat.ANSI:
            self.lines.append(f"\033[36m{code}\033[0m")
        else:
            self.lines.append(code)
        return self
    
    def add_table(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> "OutputBuilder":
        """添加表格"""
        if self.format == OutputFormat.TABLE or self.format == OutputFormat.ANSI:
            # 计算列宽
            widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(widths):
                        widths[i] = max(widths[i], len(cell))
            
            # 添加表头
            header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
            self.lines.append(header_line)
            self.lines.append("-" * len(header_line))
            
            # 添加行
            for row in rows:
                self.lines.append(" | ".join(
                    cell.ljust(widths[i]) if i < len(widths) else cell
                    for i, cell in enumerate(row)
                ))
        elif self.format == OutputFormat.MARKDOWN:
            self.lines.append("| " + " | ".join(headers) + " |")
            self.lines.append("| " + " | ".join("-" * len(h) for h in headers) + " |")
            for row in rows:
                self.lines.append("| " + " | ".join(row) + " |")
        else:
            # 简单文本格式
            self.lines.append("  ".join(headers))
            self.lines.append("-" * 40)
            for row in rows:
                self.lines.append("  ".join(row))
        
        return self
    
    def add_list(self, items: list[str], ordered: bool = False) -> "OutputBuilder":
        """添加列表"""
        for i, item in enumerate(items):
            if self.format == OutputFormat.MARKDOWN:
                prefix = f"{i + 1}." if ordered else "-"
            else:
                prefix = f"{i + 1}." if ordered else "*"
            self.lines.append(f"{prefix} {item}")
        return self
    
    def build(self) -> str:
        """构建输出"""
        return "\n".join(self.lines)


@dataclass
class ProgressBar:
    """进度条"""
    total: int
    current: int = 0
    description: str = ""
    width: int = 40
    state: ProgressState = ProgressState.RUNNING
    start_time: float = field(default_factory=time.time)
    
    def update(self, amount: int = 1) -> None:
        """更新进度"""
        self.current = min(self.current + amount, self.total)
        if self.current >= self.total:
            self.state = ProgressState.COMPLETED
    
    def render(self) -> str:
        """渲染进度条"""
        if self.total == 0:
            percent = 0
        else:
            percent = self.current / self.total
        
        filled = int(self.width * percent)
        empty = self.width - filled
        
        # 选择颜色
        if self.state == ProgressState.COMPLETED:
            color = "\033[32m"  # 绿色
        elif self.state == ProgressState.FAILED:
            color = "\033[31m"  # 红色
        else:
            color = "\033[34m"  # 蓝色
        
        bar = f"{color}{'█' * filled}{'░' * empty}\033[0m"
        
        # 计算预计剩余时间
        elapsed = time.time() - self.start_time
        if percent > 0 and self.state == ProgressState.RUNNING:
            eta = elapsed / percent * (1 - percent)
            eta_str = f" ETA: {eta:.1f}s"
        else:
            eta_str = ""
        
        return f"{self.description}: [{bar}] {self.current}/{self.total} ({percent:.0%}){eta_str}"
    
    def complete(self) -> None:
        """标记完成"""
        self.current = self.total
        self.state = ProgressState.COMPLETED
    
    def fail(self) -> None:
        """标记失败"""
        self.state = ProgressState.FAILED
    
    def cancel(self) -> None:
        """标记取消"""
        self.state = ProgressState.CANCELLED


@dataclass
class Spinner:
    """旋转动画"""
    frames: list[str] = field(default_factory=lambda: ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    message: str = "Loading"
    current_frame: int = 0
    running: bool = False
    
    def next(self) -> str:
        """获取下一帧"""
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return f"\033[36m{frame}\033[0m {self.message}"
    
    def start(self) -> None:
        """开始动画"""
        self.running = True
    
    def stop(self, message: str = "Done") -> str:
        """停止动画"""
        self.running = False
        return f"\033[32m✓\033[0m {message}"


class EnhancedCompleter:
    """
    增强自动补全器
    
    提供智能命令和参数补全。
    """
    
    def __init__(self) -> None:
        self._commands: dict[str, dict[str, Any]] = {}
        self._aliases: dict[str, str] = {}
        self._options: dict[str, list[str]] = {}
    
    def register_command(
        self,
        name: str,
        description: str = "",
        subcommands: list[str] | None = None,
        options: list[str] | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        """注册命令"""
        self._commands[name] = {
            "description": description,
            "subcommands": subcommands or [],
            "options": options or [],
        }
        
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
        
        if options:
            self._options[name] = options
    
    def complete(self, text: str, cursor_pos: int) -> list[CompletionSuggestion]:
        """
        获取补全建议
        
        Args:
            text: 输入文本
            cursor_pos: 光标位置
            
        Returns:
            补全建议列表
        """
        suggestions = []
        
        # 解析当前输入
        before_cursor = text[:cursor_pos]
        parts = before_cursor.split()
        
        if not parts:
            # 空输入，列出所有命令
            for name, info in self._commands.items():
                suggestions.append(CompletionSuggestion(
                    text=name,
                    display=name,
                    description=info.get("description", ""),
                    type="command",
                    priority=10,
                ))
        elif len(parts) == 1:
            # 输入命令中，补全命令
            partial = parts[0]
            for name in self._commands:
                if name.startswith(partial):
                    suggestions.append(CompletionSuggestion(
                        text=name,
                        display=name,
                        description=self._commands[name].get("description", ""),
                        type="command",
                        priority=10,
                    ))
            # 检查别名
            for alias, cmd in self._aliases.items():
                if alias.startswith(partial):
                    suggestions.append(CompletionSuggestion(
                        text=alias,
                        display=f"{alias} (alias for {cmd})",
                        description=self._commands[cmd].get("description", ""),
                        type="alias",
                        priority=5,
                    ))
        else:
            # 已有命令，补全子命令或选项
            cmd = parts[0]
            if cmd in self._aliases:
                cmd = self._aliases[cmd]
            
            if cmd in self._commands:
                info = self._commands[cmd]
                
                # 子命令补全
                partial = parts[-1] if len(parts) > 1 else ""
                for subcmd in info.get("subcommands", []):
                    if subcmd.startswith(partial):
                        suggestions.append(CompletionSuggestion(
                            text=subcmd,
                            display=subcmd,
                            type="subcommand",
                            priority=8,
                        ))
                
                # 选项补全
                for opt in info.get("options", []):
                    if opt.startswith(partial):
                        suggestions.append(CompletionSuggestion(
                            text=opt,
                            display=opt,
                            type="option",
                            priority=6,
                        ))
        
        suggestions.sort()
        return suggestions


class SyntaxHighlighter:
    """
    语法高亮器
    
    为 Python 和命令语法提供高亮。
    """
    
    def __init__(self) -> None:
        self._python_keywords = {
            "def", "class", "if", "else", "elif", "for", "while",
            "try", "except", "finally", "with", "as", "import", "from",
            "return", "yield", "raise", "break", "continue", "pass",
            "lambda", "and", "or", "not", "in", "is", "True", "False",
            "None", "async", "await",
        }
        self._colors = {
            "keyword": "\033[35m",    # 紫色
            "string": "\033[32m",     # 绿色
            "number": "\033[33m",     # 黄色
            "comment": "\033[90m",    # 灰色
            "function": "\033[36m",   # 青色
            "operator": "\033[37m",   # 白色
            "reset": "\033[0m",
        }
    
    def highlight(self, text: str, language: str = "python") -> str:
        """
        高亮文本
        
        Args:
            text: 输入文本
            language: 语言类型
            
        Returns:
            高亮后的文本
        """
        if language == "python":
            return self._highlight_python(text)
        elif language == "command":
            return self._highlight_command(text)
        return text
    
    def _highlight_python(self, code: str) -> str:
        """高亮 Python 代码"""
        result = []
        i = 0
        
        while i < len(code):
            # 检查注释
            if code[i] == "#":
                end = code.find("\n", i)
                if end == -1:
                    end = len(code)
                result.append(f"{self._colors['comment']}{code[i:end]}{self._colors['reset']}")
                i = end
                continue
            
            # 检查字符串
            if code[i] in ('"', "'"):
                quote = code[i]
                end = i + 1
                while end < len(code):
                    if code[end] == "\\":
                        end += 2
                        continue
                    if code[end] == quote:
                        end += 1
                        break
                    end += 1
                result.append(f"{self._colors['string']}{code[i:end]}{self._colors['reset']}")
                i = end
                continue
            
            # 检查数字
            if code[i].isdigit():
                end = i
                while end < len(code) and (code[end].isdigit() or code[end] == "."):
                    end += 1
                result.append(f"{self._colors['number']}{code[i:end]}{self._colors['reset']}")
                i = end
                continue
            
            # 检查标识符和关键字
            if code[i].isalpha() or code[i] == "_":
                end = i
                while end < len(code) and (code[end].isalnum() or code[end] == "_"):
                    end += 1
                word = code[i:end]
                
                if word in self._python_keywords:
                    result.append(f"{self._colors['keyword']}{word}{self._colors['reset']}")
                elif end < len(code) and code[end] == "(":
                    result.append(f"{self._colors['function']}{word}{self._colors['reset']}")
                else:
                    result.append(word)
                i = end
                continue
            
            # 检查操作符
            if code[i] in "+-*/%=<>!&|^~":
                result.append(f"{self._colors['operator']}{code[i]}{self._colors['reset']}")
                i += 1
                continue
            
            result.append(code[i])
            i += 1
        
        return "".join(result)
    
    def _highlight_command(self, command: str) -> str:
        """高亮命令"""
        parts = command.split()
        if not parts:
            return command
        
        # 第一个词是命令，高亮为青色
        result = [f"\033[36m{parts[0]}\033[0m"]
        
        for part in parts[1:]:
            # 选项高亮为黄色
            if part.startswith("-"):
                result.append(f"\033[33m{part}\033[0m")
            else:
                result.append(part)
        
        return " ".join(result)


class EnhancedReplSession:
    """
    增强交互式 REPL 会话
    
    提供完整的交互式命令行体验。
    """
    
    def __init__(
        self,
        history_file: str | None = None,
        output_format: OutputFormat = OutputFormat.TEXT,
    ) -> None:
        self.history = CommandHistory(file_path=history_file)
        self.completer = EnhancedCompleter()
        self.highlighter = SyntaxHighlighter()
        self.output_format = output_format
        self._commands: dict[str, Callable] = {}
        self._running = False
        self._progress: ProgressBar | None = None
        self._spinner: Spinner | None = None
        
        # 加载历史
        if history_file:
            self.history.load()
        
        # 注册内置命令
        self._register_builtin_commands()
    
    def _register_builtin_commands(self) -> None:
        """注册内置命令"""
        self.completer.register_command(
            "help",
            description="显示帮助信息",
            aliases=["?", "h"],
            options=["-v", "--verbose"],
        )
        self.completer.register_command(
            "exit",
            description="退出 REPL",
            aliases=["quit", "q"],
        )
        self.completer.register_command(
            "history",
            description="查看命令历史",
            aliases=["hist"],
            options=["-c", "--clear", "-s", "--search"],
        )
        self.completer.register_command(
            "set",
            description="设置会话变量",
            subcommands=["format", "output"],
        )
        self.completer.register_command(
            "workflow",
            description="工作流管理",
            subcommands=["list", "run", "create", "status", "cancel"],
            options=["-v", "--verbose", "-j", "--json"],
        )
        self.completer.register_command(
            "diagnose",
            description="错误诊断",
            subcommands=["analyze", "suggest", "fix"],
            options=["-f", "--file", "-c", "--code"],
        )
        self.completer.register_command(
            "kb",
            description="知识库管理",
            subcommands=["search", "api", "event", "example", "build", "status"],
            options=["-l", "--limit", "-t", "--type"],
        )
    
    def register_command(self, name: str, handler: Callable) -> None:
        """注册命令处理器"""
        self._commands[name] = handler
    
    def execute(self, line: str) -> str:
        """
        执行命令
        
        Args:
            line: 命令行
            
        Returns:
            输出结果
        """
        # 添加到历史
        self.history.add(line)
        
        # 解析命令
        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()
        
        if not parts:
            return ""
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        # 处理内置命令
        if cmd in ("help", "?", "h"):
            return self._cmd_help(args)
        elif cmd in ("exit", "quit", "q"):
            self._running = False
            return "再见!"
        elif cmd in ("history", "hist"):
            return self._cmd_history(args)
        elif cmd == "set":
            return self._cmd_set(args)
        elif cmd == "workflow":
            return self._cmd_workflow(args)
        elif cmd == "diagnose":
            return self._cmd_diagnose(args)
        elif cmd == "kb":
            return self._cmd_kb(args)
        
        # 查找注册的处理器
        if cmd in self._commands:
            try:
                result = self._commands[cmd](*args)
                return self._format_output(result)
            except Exception as e:
                return f"错误: {e}"
        
        return f"未知命令: {cmd}。输入 'help' 查看可用命令。"
    
    def _cmd_help(self, args: list[str]) -> str:
        """帮助命令"""
        builder = OutputBuilder(format=self.output_format)
        
        if args:
            # 特定命令帮助
            cmd = args[0]
            builder.add_heading(f"命令: {cmd}", level=2)
            # 这里可以添加更详细的帮助信息
        else:
            builder.add_heading("MC-Agent-Kit REPL", level=1)
            builder.add("")
            builder.add("可用命令:")
            builder.add("")
            
            commands_info = [
                ("help", "显示帮助信息"),
                ("exit", "退出 REPL"),
                ("history", "查看命令历史"),
                ("set", "设置会话变量"),
                ("workflow", "工作流管理"),
                ("diagnose", "错误诊断"),
                ("kb", "知识库管理"),
            ]
            
            for cmd, desc in commands_info:
                builder.add(f"  {cmd:15} {desc}")
            
            builder.add("")
            builder.add("输入 'help <command>' 获取详细帮助。")
        
        return builder.build()
    
    def _cmd_history(self, args: list[str]) -> str:
        """历史命令"""
        builder = OutputBuilder(format=self.output_format)
        
        if "-c" in args or "--clear" in args:
            self.history.commands.clear()
            return "历史已清除"
        
        if "-s" in args or "--search" in args:
            # 搜索模式
            pattern = args[-1] if args else ""
            results = self.history.search(pattern)
            builder.add_heading(f"搜索结果: {pattern}", level=2)
            for i, cmd in enumerate(results[:20]):
                builder.add(f"  {i + 1}. {cmd}")
        else:
            builder.add_heading("命令历史", level=2)
            recent = list(self.history.commands)[-20:]
            for i, cmd in enumerate(recent):
                builder.add(f"  {i + 1}. {cmd}")
        
        return builder.build()
    
    def _cmd_set(self, args: list[str]) -> str:
        """设置命令"""
        if not args:
            return "用法: set <name> <value>"
        
        if args[0] == "format":
            if len(args) > 1:
                try:
                    self.output_format = OutputFormat(args[1])
                    return f"输出格式已设置为: {self.output_format.value}"
                except ValueError:
                    return f"无效格式。可选: {[f.value for f in OutputFormat]}"
            else:
                return f"当前格式: {self.output_format.value}"
        
        return f"未知设置项: {args[0]}"
    
    def _cmd_workflow(self, args: list[str]) -> str:
        """工作流命令"""
        if not args:
            args = ["list"]
        
        subcmd = args[0].lower()
        
        builder = OutputBuilder(format=self.output_format)
        
        if subcmd == "list":
            builder.add_heading("工作流列表", level=2)
            builder.add_table(
                ["名称", "状态", "步骤数", "创建时间"],
                [
                    ["example-workflow", "completed", "5", "2026-03-25"],
                    ["data-processing", "running", "3", "2026-03-25"],
                ]
            )
        elif subcmd == "run":
            if len(args) > 1:
                return f"运行工作流: {args[1]}"
            return "用法: workflow run <name>"
        elif subcmd == "create":
            return "创建新工作流（需要交互式输入）"
        elif subcmd == "status":
            if len(args) > 1:
                return f"工作流状态: {args[1]}"
            return "用法: workflow status <name>"
        else:
            return f"未知子命令: {subcmd}"
        
        return builder.build()
    
    def _cmd_diagnose(self, args: list[str]) -> str:
        """诊断命令"""
        if not args:
            args = ["analyze"]
        
        subcmd = args[0].lower()
        
        builder = OutputBuilder(format=self.output_format)
        
        if subcmd == "analyze":
            builder.add_heading("错误分析", level=2)
            builder.add("请提供错误日志或使用 -f 指定日志文件")
        elif subcmd == "suggest":
            builder.add_heading("修复建议", level=2)
            builder.add_list([
                "检查变量是否已定义",
                "验证参数类型",
                "确认 API 调用正确",
            ])
        elif subcmd == "fix":
            builder.add("自动修复功能需要指定错误和代码文件")
        else:
            return f"未知子命令: {subcmd}"
        
        return builder.build()
    
    def _cmd_kb(self, args: list[str]) -> str:
        """知识库命令"""
        if not args:
            args = ["status"]
        
        subcmd = args[0].lower()
        
        builder = OutputBuilder(format=self.output_format)
        
        if subcmd == "status":
            builder.add_heading("知识库状态", level=2)
            builder.add_table(
                ["指标", "值"],
                [
                    ["API 数量", "1250"],
                    ["事件数量", "350"],
                    ["示例数量", "85"],
                    ["索引大小", "12.5 MB"],
                ]
            )
        elif subcmd == "search":
            if len(args) > 1:
                return f"搜索: {args[1]}"
            return "用法: kb search <query>"
        else:
            return f"未知子命令: {subcmd}"
        
        return builder.build()
    
    def _format_output(self, result: Any) -> str:
        """格式化输出"""
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            builder = OutputBuilder(format=self.output_format)
            builder.add_heading("结果", level=2)
            for key, value in result.items():
                builder.add(f"  {key}: {value}")
            return builder.build()
        elif isinstance(result, list):
            builder = OutputBuilder(format=self.output_format)
            builder.add_list(result)
            return builder.build()
        else:
            return str(result)
    
    def start_progress(self, total: int, description: str = "") -> ProgressBar:
        """开始进度条"""
        self._progress = ProgressBar(total=total, description=description)
        return self._progress
    
    def update_progress(self, amount: int = 1) -> str:
        """更新进度"""
        if self._progress:
            self._progress.update(amount)
            return self._progress.render()
        return ""
    
    def start_spinner(self, message: str = "Loading") -> Spinner:
        """开始旋转动画"""
        self._spinner = Spinner(message=message)
        self._spinner.start()
        return self._spinner
    
    def stop_spinner(self, message: str = "Done") -> str:
        """停止旋转动画"""
        if self._spinner:
            return self._spinner.stop(message)
        return ""
    
    def run(self) -> None:
        """运行交互式会话"""
        self._running = True
        
        print("MC-Agent-Kit 增强交互式 REPL")
        print("输入 'help' 查看可用命令，'exit' 退出\n")
        
        while self._running:
            try:
                # 获取输入
                line = input("mc-agent> ")
                
                # 执行命令
                result = self.execute(line)
                
                if result:
                    print(result)
                    print()
                
            except KeyboardInterrupt:
                print("\n使用 'exit' 退出")
            except EOFError:
                print("\n再见!")
                break
        
        # 保存历史
        self.history.save()


# 便捷函数
def create_enhanced_repl(
    history_file: str | None = None,
    output_format: OutputFormat = OutputFormat.TEXT,
) -> EnhancedReplSession:
    """创建增强 REPL 会话"""
    return EnhancedReplSession(
        history_file=history_file,
        output_format=output_format,
    )


def run_interactive() -> None:
    """运行交互式会话"""
    repl = create_enhanced_repl()
    repl.run()