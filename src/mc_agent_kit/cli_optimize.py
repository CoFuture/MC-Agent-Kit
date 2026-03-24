"""
CLI 性能优化模块

实现 CLI 性能优化功能，包括：
- 懒加载模块
- 命令自动补全
- 启动时间优化
- 输出格式优化
"""

from __future__ import annotations
import importlib
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class LazyModule:
    """懒加载模块"""
    name: str
    import_path: str
    _module: Any = None
    _loaded: bool = False

    def get(self) -> Any:
        """获取模块（延迟加载）"""
        if not self._loaded:
            self._module = importlib.import_module(self.import_path)
            self._loaded = True
        return self._module

    @property
    def loaded(self) -> bool:
        """是否已加载"""
        return self._loaded


class LazyLoader:
    """
    懒加载器

    延迟加载 CLI 命令所需的模块，优化启动时间。

    使用示例:
        loader = LazyLoader()

        # 注册懒加载模块
        loader.register("knowledge", "mc_agent_kit.knowledge_base")
        loader.register("launcher", "mc_agent_kit.launcher")

        # 获取模块（首次调用时加载）
        kb = loader.get("knowledge")

        # 检查加载状态
        print(loader.get_loaded_modules())
    """

    def __init__(self):
        self._modules: dict[str, LazyModule] = {}
        self._load_times: dict[str, float] = {}

    def register(self, name: str, import_path: str) -> None:
        """
        注册懒加载模块。

        Args:
            name: 模块别名
            import_path: 导入路径
        """
        self._modules[name] = LazyModule(name=name, import_path=import_path)

    def get(self, name: str) -> Any:
        """
        获取模块（延迟加载）。

        Args:
            name: 模块别名

        Returns:
            模块对象

        Raises:
            KeyError: 模块未注册
        """
        if name not in self._modules:
            raise KeyError(f"模块 '{name}' 未注册")

        module = self._modules[name]

        if not module.loaded:
            start_time = time.time()
            result = module.get()
            self._load_times[name] = (time.time() - start_time) * 1000
            return result

        return module.get()

    def preload(self, names: list[str] | None = None) -> dict[str, float]:
        """
        预加载模块。

        Args:
            names: 要加载的模块名列表，None 表示全部

        Returns:
            每个模块的加载时间（毫秒）
        """
        load_times = {}
        modules_to_load = names or list(self._modules.keys())

        for name in modules_to_load:
            if name in self._modules:
                start_time = time.time()
                self._modules[name].get()
                load_times[name] = (time.time() - start_time) * 1000

        return load_times

    def is_loaded(self, name: str) -> bool:
        """检查模块是否已加载"""
        if name not in self._modules:
            return False
        return self._modules[name].loaded

    def get_loaded_modules(self) -> list[str]:
        """获取已加载的模块列表"""
        return [name for name, mod in self._modules.items() if mod.loaded]

    def get_load_times(self) -> dict[str, float]:
        """获取模块加载时间"""
        return self._load_times.copy()

    def clear(self) -> None:
        """清除所有模块缓存"""
        self._modules.clear()
        self._load_times.clear()


# 全局懒加载器实例
_lazy_loader: LazyLoader | None = None


def get_lazy_loader() -> LazyLoader:
    """获取全局懒加载器"""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = LazyLoader()
        # 注册常用模块
        _lazy_loader.register("knowledge_base", "mc_agent_kit.knowledge_base")
        _lazy_loader.register("launcher", "mc_agent_kit.launcher")
        _lazy_loader.register("log_capture", "mc_agent_kit.log_capture")
        _lazy_loader.register("scaffold", "mc_agent_kit.scaffold")
        _lazy_loader.register("skills", "mc_agent_kit.skills")
        _lazy_loader.register("autofix", "mc_agent_kit.autofix")
        _lazy_loader.register("completion", "mc_agent_kit.completion")
        _lazy_loader.register("stats", "mc_agent_kit.stats")
    return _lazy_loader


@dataclass
class CompletionSuggestion:
    """补全建议"""
    name: str
    description: str
    type: str  # command, option, argument
    aliases: list[str] | None = None


class ShellCompletion:
    """
    Shell 补全支持

    为 CLI 命令生成 shell 补全脚本和建议。

    使用示例:
        completion = ShellCompletion()

        # 获取命令补全
        suggestions = completion.get_suggestions("mc-agent", "")

        # 生成 bash 补全脚本
        script = completion.generate_bash_script("mc-agent")

        # 生成 zsh 补全脚本
        script = completion.generate_zsh_script("mc-agent")
    """

    def __init__(self):
        self._commands: dict[str, dict[str, Any]] = {}
        self._global_options: list[CompletionSuggestion] = []

    def register_command(
        self,
        name: str,
        description: str,
        subcommands: list[str] | None = None,
        options: list[dict[str, str]] | None = None,
        arguments: list[dict[str, str]] | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        """
        注册命令。

        Args:
            name: 命令名
            description: 命令描述
            subcommands: 子命令列表
            options: 选项列表
            arguments: 参数列表
            aliases: 别名列表
        """
        self._commands[name] = {
            "description": description,
            "subcommands": subcommands or [],
            "options": options or [],
            "arguments": arguments or [],
            "aliases": aliases or [],
        }

    def register_global_option(
        self,
        name: str,
        description: str,
        aliases: list[str] | None = None,
    ) -> None:
        """
        注册全局选项。

        Args:
            name: 选项名
            description: 选项描述
            aliases: 别名列表
        """
        self._global_options.append(CompletionSuggestion(
            name=name,
            description=description,
            type="option",
            aliases=aliases,
        ))



    def get_suggestions(
        self,
        prog: str,
        current: str,
        prev_word: str = "",
    ) -> list[CompletionSuggestion]:
        """
        获取补全建议。

        Args:
            prog: 程序名
            current: 当前输入
            prev_word: 前一个词

        Returns:
            补全建议列表
        """
        suggestions = []

        # 如果是选项值，不补全
        if prev_word.startswith("-"):
            return []

        # 如果当前输入以 - 开头，补全选项
        if current.startswith("-"):
            suggestions.extend(self._get_option_suggestions(current))
            return suggestions

        # 解析已输入的命令
        parts = current.split()

        if len(parts) <= 1:
            # 补全命令
            suggestions.extend(self._get_command_suggestions(parts[-1] if parts else ""))
        else:
            # 补全子命令或参数
            cmd = parts[0]
            if cmd in self._commands:
                cmd_info = self._commands[cmd]
                if cmd_info["subcommands"]:
                    # 补全子命令
                    last_part = parts[-1] if parts else ""
                    suggestions.extend([
                        CompletionSuggestion(name=sub, description="", type="subcommand")
                        for sub in cmd_info["subcommands"]
                        if sub.startswith(last_part)
                    ])

        return suggestions

    def _get_command_suggestions(self, prefix: str) -> list[CompletionSuggestion]:
        """获取命令补全建议"""
        return [
            CompletionSuggestion(
                name=name,
                description=info["description"],
                type="command",
                aliases=info.get("aliases"),
            )
            for name, info in self._commands.items()
            if name.startswith(prefix)
        ]

    def _get_option_suggestions(self, prefix: str) -> list[CompletionSuggestion]:
        """获取选项补全建议"""
        suggestions = []

        # 处理 -- 前缀
        if prefix.startswith("--"):
            name_prefix = prefix[2:]  # 移除 -- 前缀
            for opt in self._global_options:
                if opt.name.startswith(name_prefix):
                    suggestions.append(opt)
        elif prefix.startswith("-"):
            # 处理短选项
            for opt in self._global_options:
                if opt.aliases:
                    for alias in opt.aliases:
                        if alias.startswith(prefix):
                            suggestions.append(opt)
                            break
        else:
            # 无前缀，返回所有选项
            suggestions.extend(self._global_options)

        return suggestions

    def generate_bash_script(self, prog: str) -> str:
        """
        生成 bash 补全脚本。

        Args:
            prog: 程序名

        Returns:
            bash 补全脚本
        """
        commands = " ".join(self._commands.keys())
        global_opts = " ".join(f"--{opt.name}" for opt in self._global_options)

        # 使用 f-string 避免花括号转义问题
        script = f'''# Bash completion for {prog}
_{prog}_completion() {{
    local cur prev words cword
    _init_completion || return

    local commands="{commands}"
    local global_opts="{global_opts}"

    # Complete commands
    if [ ${{cword}} -eq 1 ]; then
        COMPREPLY=($(compgen -W "${{commands}}" -- "${{cur}}"))
        return
    fi

    # Complete options
    if [[ "${{cur}}" == -* ]]; then
        COMPREPLY=($(compgen -W "${{global_opts}}" -- "${{cur}}"))
        return
    fi

    # Complete subcommands
    local cmd="${{words[1]}}"
    case "${{cmd}}" in
'''

        # 添加子命令补全
        for cmd, info in self._commands.items():
            if info["subcommands"]:
                subcmds = " ".join(info["subcommands"])
                script += f'        {cmd})\n'
                script += f'            COMPREPLY=($(compgen -W "{subcmds}" -- "${{cur}}"))\n'
                script += '            return\n'

        script += f'''    esac
}}

complete -F _{prog}_completion {prog}
'''

        return script

    def generate_zsh_script(self, prog: str) -> str:
        """
        生成 zsh 补全脚本。

        Args:
            prog: 程序名

        Returns:
            zsh 补全脚本
        """
        script = f'''#compdef {prog}

_{prog}() {{
    local -a commands
    commands=(
'''

        # 添加命令
        for name, info in self._commands.items():
            desc = info["description"].replace("'", "'\\''")
            script += f"        '{name}:{desc}'\n"

        script += '''    )

    _arguments -C \\
'''

        # 添加全局选项
        for opt in self._global_options:
            desc = opt.description.replace("'", "'\\''")
            script += f"        '--{opt.name}[{desc}]' \\\n"

        script += f'''        '1: :->cmd' \\
        '*: :->args'

    case $state in
        cmd)
            _describe 'command' commands
            ;;
    esac
}}

_{prog}
'''

        return script

    def generate_fish_script(self, prog: str) -> str:
        """
        生成 fish 补全脚本。

        Args:
            prog: 程序名

        Returns:
            fish 补全脚本
        """
        lines = [f"# Fish completion for {prog}"]

        # 添加命令补全
        for name, info in self._commands.items():
            desc = info["description"].replace("'", '"')
            lines.append(f"complete -c {prog} -n '__fish_use_subcommand' -a '{name}' -d '{desc}'")

        # 添加全局选项
        for opt in self._global_options:
            desc = opt.description.replace("'", '"')
            lines.append(f"complete -c {prog} -l '{opt.name}' -d '{desc}'")

        # 添加子命令补全
        for cmd, info in self._commands.items():
            for subcmd in info["subcommands"]:
                lines.append(f"complete -c {prog} -n '__fish_seen_subcommand_from {cmd}' -a '{subcmd}'")

        return "\n".join(lines)


def create_shell_completion() -> ShellCompletion:
    """
    创建并初始化 Shell 补全支持。

    Returns:
        初始化后的 ShellCompletion 实例
    """
    completion = ShellCompletion()

    # 注册 mc-agent 命令
    completion.register_command(
        name="list",
        description="列出所有 Skills",
        options=[
            {"name": "format", "description": "输出格式 (text/json)"},
        ],
    )

    completion.register_command(
        name="api",
        description="搜索 ModSDK API",
        options=[
            {"name": "query", "description": "搜索关键词"},
            {"name": "name", "description": "精确匹配 API 名称"},
            {"name": "module", "description": "按模块过滤"},
            {"name": "scope", "description": "按作用域过滤"},
            {"name": "limit", "description": "返回结果数量"},
        ],
    )

    completion.register_command(
        name="event",
        description="搜索 ModSDK 事件",
        options=[
            {"name": "query", "description": "搜索关键词"},
            {"name": "name", "description": "精确匹配事件名称"},
            {"name": "module", "description": "按模块过滤"},
            {"name": "scope", "description": "按作用域过滤"},
            {"name": "limit", "description": "返回结果数量"},
        ],
    )

    completion.register_command(
        name="gen",
        description="生成 ModSDK 代码",
        options=[
            {"name": "template", "description": "模板名称"},
            {"name": "params", "description": "模板参数 (JSON 格式)"},
        ],
    )

    completion.register_command(
        name="debug",
        description="调试 ModSDK 错误",
        options=[
            {"name": "log", "description": "日志内容"},
            {"name": "file", "description": "日志文件路径"},
        ],
    )

    completion.register_command(
        name="create",
        description="创建 Addon 项目",
        subcommands=["project", "entity", "item", "block"],
        options=[
            {"name": "name", "description": "名称"},
            {"name": "path", "description": "目标路径"},
            {"name": "template", "description": "项目模板"},
        ],
    )

    completion.register_command(
        name="kb",
        description="知识库管理",
        subcommands=["status", "search", "api", "event"],
        options=[
            {"name": "query", "description": "搜索查询"},
            {"name": "name", "description": "API/事件名称"},
        ],
    )

    completion.register_command(
        name="run",
        description="运行游戏并加载 Addon",
        options=[
            {"name": "game-path", "description": "游戏可执行文件路径"},
            {"name": "version", "description": "游戏版本"},
            {"name": "wait", "description": "等待游戏退出"},
        ],
    )

    completion.register_command(
        name="logs",
        description="日志分析",
        subcommands=["analyze", "errors", "patterns"],
        options=[
            {"name": "file", "description": "日志文件路径"},
        ],
    )

    completion.register_command(
        name="launcher",
        description="启动器诊断",
        subcommands=["diagnose", "compare", "fix", "analyze", "tips"],
        options=[
            {"name": "addon-path", "description": "Addon 目录路径"},
            {"name": "config-path", "description": "配置文件路径"},
            {"name": "game-path", "description": "游戏路径"},
        ],
    )

    completion.register_command(
        name="stats",
        description="API 使用统计",
        subcommands=["summary", "hot", "problems", "module", "api"],
        options=[
            {"name": "api-name", "description": "API 名称"},
            {"name": "module", "description": "模块名称"},
        ],
    )

    # 全局选项
    completion.register_global_option(
        name="format",
        description="输出格式 (text/json)",
        aliases=["-f"],
    )
    completion.register_global_option(
        name="verbose",
        description="详细输出",
        aliases=["-v"],
    )
    completion.register_global_option(
        name="help",
        description="显示帮助信息",
        aliases=["-h"],
    )

    return completion


@dataclass
class CLIStartupMetrics:
    """CLI 启动性能指标"""
    total_time_ms: float = 0.0
    import_time_ms: float = 0.0
    parser_time_ms: float = 0.0
    lazy_modules: dict[str, float] = None

    def __post_init__(self):
        if self.lazy_modules is None:
            self.lazy_modules = {}


def measure_startup() -> CLIStartupMetrics:
    """
    测量 CLI 启动性能。

    Returns:
        启动性能指标
    """
    metrics = CLIStartupMetrics()
    start_time = time.time()

    # 模拟导入阶段
    import_start = time.time()
    loader = get_lazy_loader()
    metrics.import_time_ms = (time.time() - import_start) * 1000

    # 模拟解析器创建
    parser_start = time.time()
    import argparse
    argparse.ArgumentParser()
    metrics.parser_time_ms = (time.time() - parser_start) * 1000

    metrics.total_time_ms = (time.time() - start_time) * 1000
    metrics.lazy_modules = loader.get_load_times()

    return metrics


def optimize_cli_startup() -> dict[str, Any]:
    """
    优化 CLI 启动。

    Returns:
        优化建议
    """
    suggestions = []
    metrics = measure_startup()

    if metrics.total_time_ms > 200:
        suggestions.append({
            "type": "performance",
            "message": f"启动时间 {metrics.total_time_ms:.1f}ms 超过目标 200ms",
            "suggestion": "考虑使用懒加载延迟导入非必要模块",
        })

    if metrics.import_time_ms > 100:
        suggestions.append({
            "type": "import",
            "message": f"模块导入耗时 {metrics.import_time_ms:.1f}ms",
            "suggestion": "检查是否有不必要的顶层导入",
        })

    if not suggestions:
        suggestions.append({
            "type": "ok",
            "message": "CLI 启动性能良好",
            "suggestion": None,
        })

    return {
        "metrics": metrics,
        "suggestions": suggestions,
    }
