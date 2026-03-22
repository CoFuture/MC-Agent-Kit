"""
用户体验优化模块

提供友好的 CLI 输出、错误消息增强和使用提示
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(Enum):
    """消息类型"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class OutputFormat(Enum):
    """输出格式"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class UserMessage:
    """用户消息"""
    type: MessageType
    title: str
    content: str = ""
    details: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    code_example: str | None = None
    learn_more: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_text(self) -> str:
        """转换为文本格式"""
        lines = []

        # 图标
        icons = {
            MessageType.SUCCESS: "✅",
            MessageType.ERROR: "❌",
            MessageType.WARNING: "⚠️",
            MessageType.INFO: "ℹ️",
            MessageType.HINT: "💡",
        }
        icon = icons.get(self.type, "")

        # 标题
        lines.append(f"{icon} {self.title}")

        # 内容
        if self.content:
            lines.append(f"   {self.content}")

        # 详情
        if self.details:
            lines.append("")
            for detail in self.details:
                lines.append(f"   • {detail}")

        # 建议
        if self.suggestions:
            lines.append("")
            lines.append("   建议:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"     {i}. {suggestion}")

        # 代码示例
        if self.code_example:
            lines.append("")
            lines.append("   示例:")
            for line in self.code_example.split("\n"):
                lines.append(f"     {line}")

        # 了解更多
        if self.learn_more:
            lines.append(f"\n   📚 了解更多: {self.learn_more}")

        return "\n".join(lines)

    def to_json(self) -> dict[str, Any]:
        """转换为 JSON 格式"""
        return {
            "type": self.type.value,
            "title": self.title,
            "content": self.content,
            "details": self.details,
            "suggestions": self.suggestions,
            "code_example": self.code_example,
            "learn_more": self.learn_more,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = []

        # 标题
        type_emoji = {
            MessageType.SUCCESS: "✅",
            MessageType.ERROR: "❌",
            MessageType.WARNING: "⚠️",
            MessageType.INFO: "ℹ️",
            MessageType.HINT: "💡",
        }
        lines.append(f"## {type_emoji.get(self.type, '')} {self.title}")

        # 内容
        if self.content:
            lines.append(f"\n{self.content}")

        # 详情
        if self.details:
            lines.append("\n**详情:**")
            for detail in self.details:
                lines.append(f"- {detail}")

        # 建议
        if self.suggestions:
            lines.append("\n**建议:**")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"{i}. {suggestion}")

        # 代码示例
        if self.code_example:
            lines.append("\n**示例:**")
            lines.append(f"```python\n{self.code_example}\n```")

        # 了解更多
        if self.learn_more:
            lines.append(f"\n📚 **了解更多:** {self.learn_more}")

        return "\n".join(lines)


class UserMessageBuilder:
    """
    用户消息构建器

    提供流式 API 构建用户友好的消息
    """

    def __init__(self, msg_type: MessageType, title: str):
        self._message = UserMessage(type=msg_type, title=title)

    def content(self, content: str) -> "UserMessageBuilder":
        """设置内容"""
        self._message.content = content
        return self

    def detail(self, detail: str) -> "UserMessageBuilder":
        """添加详情"""
        self._message.details.append(detail)
        return self

    def details(self, details: list[str]) -> "UserMessageBuilder":
        """设置详情列表"""
        self._message.details = details
        return self

    def suggestion(self, suggestion: str) -> "UserMessageBuilder":
        """添加建议"""
        self._message.suggestions.append(suggestion)
        return self

    def suggestions(self, suggestions: list[str]) -> "UserMessageBuilder":
        """设置建议列表"""
        self._message.suggestions = suggestions
        return self

    def code(self, code: str) -> "UserMessageBuilder":
        """设置代码示例"""
        self._message.code_example = code
        return self

    def learn_more(self, url: str) -> "UserMessageBuilder":
        """设置了解更多链接"""
        self._message.learn_more = url
        return self

    def build(self) -> UserMessage:
        """构建消息"""
        return self._message


class UserExperienceEnhancer:
    """
    用户体验增强器

    提供各种场景下的友好消息生成
    """

    @staticmethod
    def success(message: str) -> UserMessageBuilder:
        """创建成功消息"""
        return UserMessageBuilder(MessageType.SUCCESS, message)

    @staticmethod
    def error(message: str) -> UserMessageBuilder:
        """创建错误消息"""
        return UserMessageBuilder(MessageType.ERROR, message)

    @staticmethod
    def warning(message: str) -> UserMessageBuilder:
        """创建警告消息"""
        return UserMessageBuilder(MessageType.WARNING, message)

    @staticmethod
    def info(message: str) -> UserMessageBuilder:
        """创建信息消息"""
        return UserMessageBuilder(MessageType.INFO, message)

    @staticmethod
    def hint(message: str) -> UserMessageBuilder:
        """创建提示消息"""
        return UserMessageBuilder(MessageType.HINT, message)

    # 预定义消息模板

    @classmethod
    def project_created(cls, project_path: str) -> UserMessage:
        """项目创建成功消息"""
        return (
            cls.success("项目创建成功")
            .content(f"已在 {project_path} 创建新项目")
            .detail("包含 behavior_pack 和 resource_pack 目录")
            .detail("已生成基础配置文件 manifest.json")
            .suggestion("使用 mc-create entity <name> 添加实体")
            .suggestion("使用 mc-create item <name> 添加物品")
            .build()
        )

    @classmethod
    def entity_created(cls, entity_name: str, entity_path: str) -> UserMessage:
        """实体创建成功消息"""
        return (
            cls.success(f"实体 '{entity_name}' 创建成功")
            .content(f"文件位置: {entity_path}")
            .detail("已生成实体定义文件 (.json)")
            .detail("已生成实体逻辑脚本 (.py)")
            .detail("已生成实体几何模型 (.geo.json)")
            .code(f"""# 在 main.py 中注册实体
from mod.common.mod import Mod
mod = Mod()

@mod.on_server_start
def on_server_start():
    from mod.common.entity import CreateEngineEntity
    entity_id = CreateEngineEntity("{entity_name}", (0, 64, 0))
    print(f"实体创建成功: {{entity_id}}")
""")
            .build()
        )

    @classmethod
    def search_result(cls, query: str, api_count: int, event_count: int) -> UserMessage:
        """搜索结果消息"""
        return (
            cls.info(f"搜索结果: '{query}'")
            .content(f"找到 {api_count} 个 API, {event_count} 个事件")
            .suggestion("使用 mc-kb api <name> 查看 API 详情")
            .suggestion("使用 mc-kb event <name> 查看事件详情")
            .build()
        )

    @classmethod
    def diagnostic_issue(cls, issue_type: str, message: str, suggestion: str) -> UserMessage:
        """诊断问题消息"""
        return (
            cls.error(f"发现 {issue_type} 问题")
            .content(message)
            .suggestion(suggestion)
            .build()
        )

    @classmethod
    def memory_issue(cls, issue_type: str, details: str) -> UserMessage:
        """内存问题消息"""
        suggestions = {
            "texture": "考虑压缩纹理或使用更小的分辨率",
            "model": "减少模型面数或骨骼数量",
            "script": "优化代码，避免内存泄漏",
        }
        return (
            cls.warning(f"发现内存问题: {issue_type}")
            .content(details)
            .suggestion(suggestions.get(issue_type, "检查资源文件"))
            .learn_more("docs/user/memory-optimization.md")
            .build()
        )

    @classmethod
    def api_not_found(cls, api_name: str) -> UserMessage:
        """API 未找到消息"""
        return (
            cls.warning(f"API '{api_name}' 未找到")
            .content("可能是 API 名称错误或不在当前版本中")
            .suggestion("检查 API 名称拼写")
            .suggestion("使用 mc-kb search <keyword> 搜索相关 API")
            .suggestion("查看 API 文档确认版本兼容性")
            .build()
        )

    @classmethod
    def config_invalid(cls, config_path: str, errors: list[str]) -> UserMessage:
        """配置无效消息"""
        return (
            cls.error("配置文件无效")
            .content(f"文件: {config_path}")
            .details(errors[:5])  # 最多显示 5 个错误
            .suggestion("检查 JSON 语法是否正确")
            .suggestion("确保必填字段已填写")
            .suggestion("使用 mc-agent config validate 验证配置")
            .build()
        )

    @classmethod
    def game_launch_failed(cls, reason: str) -> UserMessage:
        """游戏启动失败消息"""
        return (
            cls.error("游戏启动失败")
            .content(reason)
            .suggestion("检查游戏路径是否正确")
            .suggestion("确保 Addon 结构完整")
            .suggestion("运行 mc-agent launcher diagnose 诊断问题")
            .build()
        )


class CLIOutputFormatter:
    """
    CLI 输出格式化器

    提供统一的 CLI 输出格式化方法
    """

    @staticmethod
    def format_table(
        headers: list[str],
        rows: list[list[str]],
        title: str | None = None,
    ) -> str:
        """
        格式化表格输出

        Args:
            headers: 表头
            rows: 数据行
            title: 标题（可选）

        Returns:
            格式化的表格字符串
        """
        lines = []

        if title:
            lines.append(f"\n{title}")
            lines.append("=" * len(title))

        # 计算列宽
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 表头
        header_line = " | ".join(
            h.ljust(col_widths[i]) for i, h in enumerate(headers)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # 数据行
        for row in rows:
            row_line = " | ".join(
                str(cell).ljust(col_widths[i]) if i < len(col_widths) else ""
                for i, cell in enumerate(row)
            )
            lines.append(row_line)

        return "\n".join(lines)

    @staticmethod
    def format_list(
        items: list[Any],
        title: str | None = None,
        numbered: bool = False,
    ) -> str:
        """
        格式化列表输出

        Args:
            items: 列表项
            title: 标题（可选）
            numbered: 是否编号

        Returns:
            格式化的列表字符串
        """
        lines = []

        if title:
            lines.append(f"\n{title}")
            lines.append("-" * len(title))

        for i, item in enumerate(items, 1):
            if numbered:
                lines.append(f"  {i}. {item}")
            else:
                lines.append(f"  • {item}")

        return "\n".join(lines)

    @staticmethod
    def format_key_value(
        data: dict[str, Any],
        title: str | None = None,
    ) -> str:
        """
        格式化键值对输出

        Args:
            data: 键值对数据
            title: 标题（可选）

        Returns:
            格式化的键值对字符串
        """
        lines = []

        if title:
            lines.append(f"\n{title}")
            lines.append("-" * len(title))

        max_key_len = max(len(str(k)) for k in data.keys())

        for key, value in data.items():
            key_str = str(key).ljust(max_key_len)
            if isinstance(value, list):
                lines.append(f"  {key_str}: [{len(value)} items]")
            elif isinstance(value, dict):
                lines.append(f"  {key_str}: {{...}}")
            else:
                lines.append(f"  {key_str}: {value}")

        return "\n".join(lines)


# 便捷函数
def success(title: str) -> UserMessageBuilder:
    """创建成功消息构建器"""
    return UserExperienceEnhancer.success(title)


def error(title: str) -> UserMessageBuilder:
    """创建错误消息构建器"""
    return UserExperienceEnhancer.error(title)


def warning(title: str) -> UserMessageBuilder:
    """创建警告消息构建器"""
    return UserExperienceEnhancer.warning(title)


def info(title: str) -> UserMessageBuilder:
    """创建信息消息构建器"""
    return UserExperienceEnhancer.info(title)


def hint(title: str) -> UserMessageBuilder:
    """创建提示消息构建器"""
    return UserExperienceEnhancer.hint(title)
