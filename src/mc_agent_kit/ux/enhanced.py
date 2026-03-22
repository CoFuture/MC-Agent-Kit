"""
UX 增强模块

提供消息本地化、消息历史记录和自定义模板功能
"""

from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from mc_agent_kit.ux.enhancer import (
    MessageType,
    UserMessage,
    UserMessageBuilder,
)
from mc_agent_kit.ux.enhancer import (
    UserExperienceEnhancer as BaseEnhancer,
)

# === 本地化支持 ===

@dataclass
class LocaleConfig:
    """本地化配置"""
    locale: str = "zh_CN"  # zh_CN, en_US
    fallback_locale: str = "en_US"


# 消息模板（支持多语言）
MESSAGE_TEMPLATES: dict[str, dict[str, str]] = {
    "zh_CN": {
        # 成功消息
        "success.project_created": "项目创建成功",
        "success.entity_created": "实体 '{name}' 创建成功",
        "success.item_created": "物品 '{name}' 创建成功",
        "success.block_created": "方块 '{name}' 创建成功",
        "success.code_generated": "代码生成成功",
        "success.test_passed": "测试通过",
        "success.fix_applied": "修复已应用",

        # 错误消息
        "error.project_failed": "项目创建失败",
        "error.api_not_found": "API '{name}' 未找到",
        "error.event_not_found": "事件 '{name}' 未找到",
        "error.config_invalid": "配置文件无效",
        "error.launch_failed": "游戏启动失败",
        "error.memory_issue": "发现内存问题",
        "error.syntax_error": "语法错误",

        # 警告消息
        "warning.deprecated_api": "API '{name}' 已弃用",
        "warning.high_memory": "内存使用过高",
        "warning.slow_query": "查询耗时过长",

        # 信息消息
        "info.search_result": "搜索结果: '{query}'",
        "info.diagnostic_complete": "诊断完成",
        "info.cache_hit": "缓存命中",

        # 提示消息
        "hint.use_search": "使用 mc-kb search <keyword> 搜索",
        "hint.check_docs": "查看文档了解更多",
        "hint.optimize_code": "考虑优化代码",
    },
    "en_US": {
        # Success messages
        "success.project_created": "Project created successfully",
        "success.entity_created": "Entity '{name}' created successfully",
        "success.item_created": "Item '{name}' created successfully",
        "success.block_created": "Block '{name}' created successfully",
        "success.code_generated": "Code generated successfully",
        "success.test_passed": "Tests passed",
        "success.fix_applied": "Fix applied",

        # Error messages
        "error.project_failed": "Failed to create project",
        "error.api_not_found": "API '{name}' not found",
        "error.event_not_found": "Event '{name}' not found",
        "error.config_invalid": "Invalid configuration file",
        "error.launch_failed": "Game launch failed",
        "error.memory_issue": "Memory issue detected",
        "error.syntax_error": "Syntax error",

        # Warning messages
        "warning.deprecated_api": "API '{name}' is deprecated",
        "warning.high_memory": "High memory usage",
        "warning.slow_query": "Slow query detected",

        # Info messages
        "info.search_result": "Search results: '{query}'",
        "info.diagnostic_complete": "Diagnostic completed",
        "info.cache_hit": "Cache hit",

        # Hint messages
        "hint.use_search": "Use mc-kb search <keyword> to search",
        "hint.check_docs": "Check documentation for more details",
        "hint.optimize_code": "Consider optimizing your code",
    },
    "ja_JP": {
        # 成功メッセージ
        "success.project_created": "プロジェクトが正常に作成されました",
        "success.entity_created": "エンティティ '{name}' が正常に作成されました",
        "success.item_created": "アイテム '{name}' が正常に作成されました",
        "success.block_created": "ブロック '{name}' が正常に作成されました",
        "success.code_generated": "コードが正常に生成されました",
        "success.test_passed": "テストに合格しました",
        "success.fix_applied": "修正が適用されました",

        # エラーメッセージ
        "error.project_failed": "プロジェクトの作成に失敗しました",
        "error.api_not_found": "API '{name}' が見つかりません",
        "error.event_not_found": "イベント '{name}' が見つかりません",
        "error.config_invalid": "設定ファイルが無効です",
        "error.launch_failed": "ゲームの起動に失敗しました",
        "error.memory_issue": "メモリの問題が検出されました",
        "error.syntax_error": "構文エラー",

        # 警告メッセージ
        "warning.deprecated_api": "API '{name}' は非推奨です",
        "warning.high_memory": "メモリ使用量が高いです",
        "warning.slow_query": "クエリが遅いです",

        # 情報メッセージ
        "info.search_result": "検索結果: '{query}'",
        "info.diagnostic_complete": "診断が完了しました",
        "info.cache_hit": "キャッシュヒット",

        # ヒントメッセージ
        "hint.use_search": "mc-kb search <keyword> を使用して検索",
        "hint.check_docs": "詳細はドキュメントを参照してください",
        "hint.optimize_code": "コードの最適化を検討してください",
    },
    "ko_KR": {
        # 성공 메시지
        "success.project_created": "프로젝트가 성공적으로 생성되었습니다",
        "success.entity_created": "엔티티 '{name}'이(가) 성공적으로 생성되었습니다",
        "success.item_created": "아이템 '{name}'이(가) 성공적으로 생성되었습니다",
        "success.block_created": "블록 '{name}'이(가) 성공적으로 생성되었습니다",
        "success.code_generated": "코드가 성공적으로 생성되었습니다",
        "success.test_passed": "테스트 통과",
        "success.fix_applied": "수정이 적용되었습니다",

        # 오류 메시지
        "error.project_failed": "프로젝트 생성 실패",
        "error.api_not_found": "API '{name}'을(를) 찾을 수 없습니다",
        "error.event_not_found": "이벤트 '{name}'을(를) 찾을 수 없습니다",
        "error.config_invalid": "구성 파일이 잘못되었습니다",
        "error.launch_failed": "게임 시작 실패",
        "error.memory_issue": "메모리 문제가 감지되었습니다",
        "error.syntax_error": "구문 오류",

        # 경고 메시지
        "warning.deprecated_api": "API '{name}'은(는) 더 이상 사용되지 않습니다",
        "warning.high_memory": "메모리 사용량이 높습니다",
        "warning.slow_query": "느린 쿼리가 감지되었습니다",

        # 정보 메시지
        "info.search_result": "검색 결과: '{query}'",
        "info.diagnostic_complete": "진단 완료",
        "info.cache_hit": "캐시 적중",

        # 힌트 메시지
        "hint.use_search": "mc-kb search <keyword>를 사용하여 검색",
        "hint.check_docs": "자세한 내용은 문서를 참조하세요",
        "hint.optimize_code": "코드 최적화를 고려하세요",
    },
}


class LocaleManager:
    """本地化管理器"""

    def __init__(self, config: LocaleConfig | None = None):
        self.config = config or LocaleConfig()
        self._custom_messages: dict[str, str] = {}

    def get(self, key: str, **kwargs: Any) -> str:
        """
        获取本地化消息

        Args:
            key: 消息键
            **kwargs: 格式化参数

        Returns:
            本地化消息
        """
        # 优先使用自定义消息
        if key in self._custom_messages:
            template = self._custom_messages[key]
        elif key in MESSAGE_TEMPLATES.get(self.config.locale, {}):
            template = MESSAGE_TEMPLATES[self.config.locale][key]
        elif key in MESSAGE_TEMPLATES.get(self.config.fallback_locale, {}):
            template = MESSAGE_TEMPLATES[self.config.fallback_locale][key]
        else:
            return key  # 返回键本身作为后备

        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def set_locale(self, locale: str) -> None:
        """设置语言"""
        self.config.locale = locale

    def register_custom_message(self, key: str, message: str) -> None:
        """注册自定义消息"""
        self._custom_messages[key] = message

    def load_custom_messages(self, path: str | Path) -> int:
        """
        从文件加载自定义消息

        Args:
            path: 消息文件路径 (JSON)

        Returns:
            加载的消息数
        """
        path = Path(path)
        if not path.exists():
            return 0

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for locale, messages in data.items():
            if locale not in MESSAGE_TEMPLATES:
                MESSAGE_TEMPLATES[locale] = {}
            for key, value in messages.items():
                MESSAGE_TEMPLATES[locale][key] = value
                count += 1

        return count


# === 消息历史记录 ===

@dataclass
class MessageHistoryEntry:
    """消息历史条目"""
    message: UserMessage
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message.to_json(),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "context": self.context,
        }


class MessageHistory:
    """消息历史记录器"""

    def __init__(self, max_entries: int = 1000):
        self._history: deque[MessageHistoryEntry] = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self._session_id: str | None = None

    def set_session(self, session_id: str) -> None:
        """设置当前会话 ID"""
        self._session_id = session_id

    def record(self, message: UserMessage, context: dict[str, Any] | None = None) -> None:
        """
        记录消息

        Args:
            message: 用户消息
            context: 上下文信息
        """
        entry = MessageHistoryEntry(
            message=message,
            session_id=self._session_id,
            context=context or {},
        )
        with self._lock:
            self._history.append(entry)

    def get_recent(self, limit: int = 10) -> list[MessageHistoryEntry]:
        """获取最近的消息"""
        with self._lock:
            return list(self._history)[-limit:]

    def get_by_type(self, msg_type: MessageType, limit: int = 10) -> list[MessageHistoryEntry]:
        """按类型获取消息"""
        with self._lock:
            entries = [e for e in self._history if e.message.type == msg_type]
            return entries[-limit:]

    def get_by_session(self, session_id: str, limit: int = 100) -> list[MessageHistoryEntry]:
        """按会话获取消息"""
        with self._lock:
            entries = [e for e in self._history if e.session_id == session_id]
            return entries[-limit:]

    def search(self, keyword: str, limit: int = 10) -> list[MessageHistoryEntry]:
        """搜索消息"""
        with self._lock:
            entries = [
                e for e in self._history
                if keyword.lower() in e.message.title.lower() or
                   keyword.lower() in e.message.content.lower()
            ]
            return entries[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            type_counts: dict[str, int] = {}
            for entry in self._history:
                t = entry.message.type.value
                type_counts[t] = type_counts.get(t, 0) + 1

            return {
                "total": len(self._history),
                "by_type": type_counts,
                "oldest": self._history[0].timestamp.isoformat() if self._history else None,
                "newest": self._history[-1].timestamp.isoformat() if self._history else None,
            }

    def clear(self) -> int:
        """清空历史"""
        with self._lock:
            count = len(self._history)
            self._history.clear()
            return count

    def export(self, path: str | Path) -> int:
        """导出历史到文件"""
        with self._lock:
            data = [e.to_dict() for e in self._history]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return len(data)


# === 自定义消息模板 ===

@dataclass
class MessageTemplate:
    """自定义消息模板"""
    id: str
    type: MessageType
    title_template: str
    content_template: str | None = None
    details_templates: list[str] = field(default_factory=list)
    suggestion_templates: list[str] = field(default_factory=list)
    code_template: str | None = None
    learn_more_url: str | None = None

    def render(self, **kwargs: Any) -> UserMessage:
        """渲染模板"""
        builder = UserMessageBuilder(self.type, self.title_template.format(**kwargs))

        if self.content_template:
            builder.content(self.content_template.format(**kwargs))

        for detail_template in self.details_templates:
            builder.detail(detail_template.format(**kwargs))

        for suggestion_template in self.suggestion_templates:
            builder.suggestion(suggestion_template.format(**kwargs))

        if self.code_template:
            builder.code(self.code_template.format(**kwargs))

        if self.learn_more_url:
            builder.learn_more(self.learn_more_url.format(**kwargs))

        return builder.build()


class TemplateRegistry:
    """消息模板注册表"""

    def __init__(self) -> None:
        self._templates: dict[str, MessageTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """加载内置模板"""
        # 工作流相关模板
        self.register(MessageTemplate(
            id="workflow.step_started",
            type=MessageType.INFO,
            title_template="步骤 {step_name} 开始执行",
            content_template="正在执行: {description}",
        ))

        self.register(MessageTemplate(
            id="workflow.step_completed",
            type=MessageType.SUCCESS,
            title_template="步骤 {step_name} 完成",
            content_template="耗时: {duration_ms}ms",
        ))

        self.register(MessageTemplate(
            id="workflow.step_failed",
            type=MessageType.ERROR,
            title_template="步骤 {step_name} 失败",
            content_template="错误: {error}",
            suggestion_templates=["检查配置是否正确", "查看日志获取详细信息"],
        ))

        self.register(MessageTemplate(
            id="workflow.step_retry",
            type=MessageType.WARNING,
            title_template="步骤 {step_name} 重试中",
            content_template="第 {attempt}/{max_retries} 次重试",
        ))

        # 诊断相关模板
        self.register(MessageTemplate(
            id="diagnostic.issue_found",
            type=MessageType.WARNING,
            title_template="发现 {issue_type} 问题",
            content_template="{description}",
            suggestion_templates=["{suggestion}"],
        ))

        self.register(MessageTemplate(
            id="diagnostic.critical",
            type=MessageType.ERROR,
            title_template="严重问题: {issue_type}",
            content_template="{description}",
            suggestion_templates=["立即修复此问题", "查看相关文档"],
        ))

        # 缓存相关模板
        self.register(MessageTemplate(
            id="cache.warmup_complete",
            type=MessageType.INFO,
            title_template="缓存预热完成",
            content_template="预热了 {count} 个条目",
        ))

        self.register(MessageTemplate(
            id="cache.hit_rate_low",
            type=MessageType.WARNING,
            title_template="缓存命中率较低",
            content_template="当前命中率: {hit_rate}%",
            suggestion_templates=["考虑增加缓存预热", "检查缓存键策略"],
        ))

    def register(self, template: MessageTemplate) -> None:
        """注册模板"""
        self._templates[template.id] = template

    def get(self, template_id: str) -> MessageTemplate | None:
        """获取模板"""
        return self._templates.get(template_id)

    def list_all(self) -> list[MessageTemplate]:
        """列出所有模板"""
        return list(self._templates.values())

    def render(self, template_id: str, **kwargs: Any) -> UserMessage | None:
        """渲染模板"""
        template = self.get(template_id)
        if template:
            return template.render(**kwargs)
        return None


# === 增强用户体验增强器 ===

class EnhancedUXManager:
    """
    增强用户体验管理器

    整合本地化、历史记录和自定义模板
    """

    def __init__(
        self,
        locale_config: LocaleConfig | None = None,
        history_max_entries: int = 1000,
    ) -> None:
        self.locale_manager = LocaleManager(locale_config)
        self.history = MessageHistory(history_max_entries)
        self.templates = TemplateRegistry()
        self._enabled = True

    def enable(self) -> None:
        """启用"""
        self._enabled = True

    def disable(self) -> None:
        """禁用"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

    def set_locale(self, locale: str) -> None:
        """设置语言"""
        self.locale_manager.set_locale(locale)

    def set_session(self, session_id: str) -> None:
        """设置会话"""
        self.history.set_session(session_id)

    def message(self, message: UserMessage, context: dict[str, Any] | None = None) -> UserMessage:
        """
        发送消息（记录历史）

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            原始消息
        """
        if self._enabled:
            self.history.record(message, context)
        return message

    def from_template(self, template_id: str, **kwargs: Any) -> UserMessage | None:
        """
        从模板创建消息

        Args:
            template_id: 模板 ID
            **kwargs: 模板参数

        Returns:
            用户消息
        """
        message = self.templates.render(template_id, **kwargs)
        if message and self._enabled:
            self.history.record(message)
        return message

    def localized(self, key: str, **kwargs: Any) -> str:
        """
        获取本地化消息

        Args:
            key: 消息键
            **kwargs: 格式化参数

        Returns:
            本地化消息
        """
        return self.locale_manager.get(key, **kwargs)

    # 便捷方法

    def success(self, key: str, **kwargs: Any) -> UserMessage:
        """创建成功消息"""
        title = self.localized(key, **kwargs)
        message = BaseEnhancer.success(title).build()
        return self.message(message)

    def error(self, key: str, **kwargs: Any) -> UserMessage:
        """创建错误消息"""
        title = self.localized(key, **kwargs)
        message = BaseEnhancer.error(title).build()
        return self.message(message)

    def warning(self, key: str, **kwargs: Any) -> UserMessage:
        """创建警告消息"""
        title = self.localized(key, **kwargs)
        message = BaseEnhancer.warning(title).build()
        return self.message(message)

    def info(self, key: str, **kwargs: Any) -> UserMessage:
        """创建信息消息"""
        title = self.localized(key, **kwargs)
        message = BaseEnhancer.info(title).build()
        return self.message(message)

    def hint(self, key: str, **kwargs: Any) -> UserMessage:
        """创建提示消息"""
        title = self.localized(key, **kwargs)
        message = BaseEnhancer.hint(title).build()
        return self.message(message)

    # 更多预定义消息模板

    @classmethod
    def workflow_started(cls, step_count: int) -> UserMessage:
        """工作流开始消息"""
        return (
            BaseEnhancer.info("工作流开始执行")
            .content(f"共 {step_count} 个步骤")
            .detail("步骤: 查文档 → 创建项目 → 启动测试 → 诊断错误")
            .build()
        )

    @classmethod
    def workflow_completed(cls, success: bool, duration_ms: int) -> UserMessage:
        """工作流完成消息"""
        if success:
            return (
                BaseEnhancer.success("工作流执行成功")
                .content(f"总耗时: {duration_ms}ms")
                .build()
            )
        else:
            return (
                BaseEnhancer.error("工作流执行失败")
                .content(f"总耗时: {duration_ms}ms")
                .suggestion("查看详细日志获取错误信息")
                .build()
            )

    @classmethod
    def workflow_paused(cls, current_step: str) -> UserMessage:
        """工作流暂停消息"""
        return (
            BaseEnhancer.warning("工作流已暂停")
            .content(f"当前步骤: {current_step}")
            .suggestion("调用 resume() 继续执行")
            .build()
        )

    @classmethod
    def workflow_resumed(cls) -> UserMessage:
        """工作流恢复消息"""
        return (
            BaseEnhancer.info("工作流已恢复")
            .content("继续执行后续步骤")
            .build()
        )

    @classmethod
    def workflow_cancelled(cls) -> UserMessage:
        """工作流取消消息"""
        return (
            BaseEnhancer.warning("工作流已取消")
            .suggestion("可以重新运行工作流")
            .build()
        )

    @classmethod
    def cache_status(cls, stats: dict[str, Any]) -> UserMessage:
        """缓存状态消息"""
        return (
            BaseEnhancer.info("缓存状态")
            .details([
                f"条目数: {stats.get('entries', 0)}/{stats.get('max_entries', 0)}",
                f"命中率: {stats.get('hit_rate', 0) * 100:.1f}%",
                f"命中: {stats.get('hits', 0)}, 未命中: {stats.get('misses', 0)}",
            ])
            .build()
        )

    @classmethod
    def progress_update(cls, step: str, percentage: float, message: str) -> UserMessage:
        """进度更新消息"""
        return (
            BaseEnhancer.info(f"[{percentage:.0f}%] {step}")
            .content(message)
            .build()
        )

    @classmethod
    def retry_attempt(cls, step: str, attempt: int, max_retries: int, delay: float) -> UserMessage:
        """重试尝试消息"""
        return (
            BaseEnhancer.warning(f"步骤 '{step}' 重试中")
            .content(f"第 {attempt}/{max_retries} 次尝试，等待 {delay:.1f}s")
            .build()
        )

    @classmethod
    def step_skipped(cls, step: str, reason: str) -> UserMessage:
        """步骤跳过消息"""
        return (
            BaseEnhancer.info(f"步骤 '{step}' 已跳过")
            .content(f"原因: {reason}")
            .build()
        )


# 全局管理器实例
_global_ux_manager: EnhancedUXManager | None = None


def get_ux_manager(
    locale: str = "zh_CN",
    history_max_entries: int = 1000,
) -> EnhancedUXManager:
    """
    获取全局 UX 管理器

    Args:
        locale: 语言
        history_max_entries: 历史最大条目数

    Returns:
        UX 管理器实例
    """
    global _global_ux_manager

    if _global_ux_manager is None:
        config = LocaleConfig(locale=locale)
        _global_ux_manager = EnhancedUXManager(
            locale_config=config,
            history_max_entries=history_max_entries,
        )

    return _global_ux_manager


def localized_message(key: str, **kwargs: Any) -> str:
    """获取本地化消息的便捷函数"""
    return get_ux_manager().localized(key, **kwargs)
