"""
智能对话增强模块

提供上下文感知对话、多轮对话记忆、对话历史检索、对话主题跟踪等功能。
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class ConversationRole(Enum):
    """对话角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(Enum):
    """意图类型"""
    SEARCH_API = "search_api"
    SEARCH_EVENT = "search_event"
    CREATE_PROJECT = "create_project"
    CREATE_ENTITY = "create_entity"
    CREATE_ITEM = "create_item"
    DIAGNOSE_ERROR = "diagnose_error"
    GENERATE_CODE = "generate_code"
    GET_EXAMPLE = "get_example"
    EXPLAIN_CODE = "explain_code"
    FIX_CODE = "fix_code"
    TEST_CODE = "test_code"
    UNKNOWN = "unknown"


class TopicCategory(Enum):
    """话题类别"""
    ENTITY = "entity"
    ITEM = "item"
    BLOCK = "block"
    UI = "ui"
    NETWORK = "network"
    EVENT = "event"
    API = "api"
    ERROR = "error"
    PROJECT = "project"
    GENERAL = "general"


class ConversationState(Enum):
    """对话状态"""
    ACTIVE = "active"
    IDLE = "idle"
    ENDED = "ended"


@dataclass
class ConversationMessage:
    """对话消息"""
    role: ConversationRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    intent: Optional[IntentType] = None
    entities: dict[str, Any] = field(default_factory=dict)
    topic: Optional[TopicCategory] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "intent": self.intent.value if self.intent else None,
            "entities": self.entities,
            "topic": self.topic.value if self.topic else None,
        }


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    messages: list[ConversationMessage] = field(default_factory=list)
    intent_history: list[IntentType] = field(default_factory=list)
    entities: dict[str, Any] = field(default_factory=dict)
    current_topic: Optional[TopicCategory] = None
    topic_history: list[TopicCategory] = field(default_factory=list)
    search_history: list[dict[str, Any]] = field(default_factory=list)
    code_context: dict[str, Any] = field(default_factory=dict)
    state: ConversationState = ConversationState.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(
        self,
        role: ConversationRole,
        content: str,
        intent: Optional[IntentType] = None,
        entities: Optional[dict[str, Any]] = None,
        topic: Optional[TopicCategory] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ConversationMessage:
        """添加消息"""
        message = ConversationMessage(
            role=role,
            content=content,
            intent=intent,
            entities=entities or {},
            topic=topic or self.current_topic,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.last_activity = time.time()

        # 更新意图历史
        if intent:
            self.intent_history.append(intent)

        # 更新话题
        if topic and topic != self.current_topic:
            if self.current_topic:
                self.topic_history.append(self.current_topic)
            self.current_topic = topic

        # 更新实体
        if entities:
            self.entities.update(entities)

        return message

    def get_recent_messages(self, count: int = 5) -> list[ConversationMessage]:
        """获取最近的消息"""
        return self.messages[-count:] if self.messages else []

    def get_messages_by_role(self, role: ConversationRole) -> list[ConversationMessage]:
        """按角色获取消息"""
        return [msg for msg in self.messages if msg.role == role]

    def get_messages_by_topic(self, topic: TopicCategory) -> list[ConversationMessage]:
        """按话题获取消息"""
        return [msg for msg in self.messages if msg.topic == topic]

    def get_user_intent_history(self) -> list[IntentType]:
        """获取用户意图历史"""
        return [
            msg.intent for msg in self.messages
            if msg.role == ConversationRole.USER and msg.intent
        ]

    def get_topic_distribution(self) -> dict[TopicCategory, int]:
        """获取话题分布"""
        distribution: dict[TopicCategory, int] = {}
        for msg in self.messages:
            if msg.topic:
                distribution[msg.topic] = distribution.get(msg.topic, 0) + 1
        return distribution

    def get_conversation_duration(self) -> float:
        """获取对话持续时间（秒）"""
        if not self.messages:
            return 0.0
        return self.last_activity - self.created_at

    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self.messages)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "intent_history": [i.value for i in self.intent_history],
            "entities": self.entities,
            "current_topic": self.current_topic.value if self.current_topic else None,
            "topic_history": [t.value for t in self.topic_history],
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "duration": self.get_conversation_duration(),
        }


@dataclass
class IntentRecognitionResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float
    entities: dict[str, Any]
    context_needed: bool
    topic: Optional[TopicCategory] = None
    related_intents: list[IntentType] = field(default_factory=list)


@dataclass
class ConversationSummary:
    """对话摘要"""
    session_id: str
    message_count: int
    duration: float
    main_topics: list[TopicCategory]
    main_intents: list[IntentType]
    entities_mentioned: dict[str, Any]
    key_points: list[str]
    state: ConversationState


class IntentRecognizer:
    """意图识别器

    识别用户输入的意图，提取关键实体。

    使用示例:
        recognizer = IntentRecognizer()
        result = recognizer.recognize("如何创建一个自定义实体")
    """

    def __init__(self) -> None:
        """初始化意图识别器"""
        # 意图关键词映射
        self._intent_keywords: dict[IntentType, list[tuple[str, float]]] = {
            IntentType.SEARCH_API: [
                ("api", 0.9), ("接口", 0.9), ("方法", 0.8), ("函数", 0.8),
                ("查找", 0.7), ("搜索", 0.7), ("找", 0.6), ("search", 0.9),
            ],
            IntentType.SEARCH_EVENT: [
                ("事件", 0.9), ("event", 0.9), ("监听", 0.8), ("回调", 0.7),
                ("触发", 0.6), ("注册事件", 0.9),
            ],
            IntentType.CREATE_PROJECT: [
                ("创建项目", 1.0), ("新建项目", 1.0), ("初始化项目", 1.0),
                ("create project", 0.9), ("新项目", 0.8),
            ],
            IntentType.CREATE_ENTITY: [
                ("创建实体", 1.0), ("新建实体", 1.0), ("自定义实体", 0.9),
                ("create entity", 0.9), ("怪物", 0.7), ("生物", 0.7),
            ],
            IntentType.CREATE_ITEM: [
                ("创建物品", 1.0), ("新建物品", 1.0), ("自定义物品", 0.9),
                ("create item", 0.9), ("道具", 0.7),
            ],
            IntentType.DIAGNOSE_ERROR: [
                ("报错", 0.9), ("错误", 0.8), ("异常", 0.8), ("error", 0.9),
                ("诊断", 0.9), ("debug", 0.9), ("修复", 0.7), ("问题", 0.6),
            ],
            IntentType.GENERATE_CODE: [
                ("生成代码", 1.0), ("写代码", 0.9), ("帮我写", 0.8),
                ("generate", 0.9), ("实现", 0.7),
            ],
            IntentType.GET_EXAMPLE: [
                ("示例", 0.9), ("例子", 0.9), ("example", 0.9),
                ("怎么写", 0.8), ("如何实现", 0.7),
            ],
            IntentType.EXPLAIN_CODE: [
                ("解释", 0.9), ("说明", 0.8), ("什么意思", 0.8),
                ("explain", 0.9), ("理解", 0.7),
            ],
            IntentType.FIX_CODE: [
                ("修复代码", 1.0), ("改正", 0.9), ("修改错误", 0.9),
                ("fix", 0.9), ("改正错误", 0.8),
            ],
            IntentType.TEST_CODE: [
                ("测试", 0.9), ("test", 0.9), ("单元测试", 1.0),
                ("测试用例", 0.9), ("验证", 0.7),
            ],
        }

        # 话题关键词映射
        self._topic_keywords: dict[TopicCategory, list[str]] = {
            TopicCategory.ENTITY: ["实体", "entity", "怪物", "生物", "npc", "mob"],
            TopicCategory.ITEM: ["物品", "item", "道具", "装备", "武器"],
            TopicCategory.BLOCK: ["方块", "block", "方块实体"],
            TopicCategory.UI: ["ui", "界面", "ui界面", "屏幕", "screen", "gui"],
            TopicCategory.NETWORK: ["网络", "network", "同步", "客户端", "服务端", "client", "server"],
            TopicCategory.EVENT: ["事件", "event", "监听", "回调"],
            TopicCategory.API: ["api", "接口", "方法", "函数"],
            TopicCategory.ERROR: ["错误", "error", "异常", "报错", "exception"],
            TopicCategory.PROJECT: ["项目", "project", "工程", "模块"],
        }

    def recognize(
        self,
        text: str,
        context: Optional[ConversationContext] = None,
    ) -> IntentRecognitionResult:
        """识别意图

        Args:
            text: 用户输入
            context: 对话上下文（可选）

        Returns:
            IntentRecognitionResult: 识别结果
        """
        text_lower = text.lower()
        scores: dict[IntentType, float] = {}

        # 计算各意图得分
        for intent, keywords in self._intent_keywords.items():
            score = 0.0
            for keyword, weight in keywords:
                if keyword in text_lower:
                    score = max(score, weight)
            if score > 0:
                scores[intent] = score

        # 确定最佳意图
        if not scores:
            return IntentRecognitionResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=self._extract_entities(text),
                context_needed=False,
                topic=self._detect_topic(text),
            )

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]

        # 提取实体
        entities = self._extract_entities(text)

        # 检测话题
        topic = self._detect_topic(text)

        # 结合上下文判断
        context_needed = self._needs_context(best_intent, context)

        # 查找相关意图
        related_intents = self._find_related_intents(best_intent, scores)

        return IntentRecognitionResult(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
            context_needed=context_needed,
            topic=topic,
            related_intents=related_intents,
        )

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """提取实体"""
        import re
        entities: dict[str, Any] = {}

        # 提取 API 名称（CamelCase）
        api_matches = re.findall(r'\b([A-Z][a-zA-Z]{2,})\b', text)
        if api_matches:
            entities["api_names"] = api_matches

        # 提取事件名称（OnXxx）
        event_matches = re.findall(r'\b(On[A-Z][a-zA-Z]*)\b', text)
        if event_matches:
            entities["event_names"] = event_matches

        # 提取关键词
        entities["keyword"] = text

        # 提取作用域
        if "服务端" in text or "server" in text.lower():
            entities["scope"] = "server"
        elif "客户端" in text or "client" in text.lower():
            entities["scope"] = "client"

        return entities

    def _detect_topic(self, text: str) -> Optional[TopicCategory]:
        """检测话题"""
        text_lower = text.lower()

        for topic, keywords in self._topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return topic

        return None

    def _needs_context(
        self,
        intent: IntentType,
        context: Optional[ConversationContext],
    ) -> bool:
        """判断是否需要上下文"""
        # 这些意图通常需要上下文
        context_intents = {
            IntentType.EXPLAIN_CODE,
            IntentType.DIAGNOSE_ERROR,
            IntentType.GENERATE_CODE,
            IntentType.FIX_CODE,
        }
        return intent in context_intents and context is not None

    def _find_related_intents(
        self,
        best_intent: IntentType,
        scores: dict[IntentType, float],
    ) -> list[IntentType]:
        """查找相关意图"""
        related = []
        for intent, score in scores.items():
            if intent != best_intent and score > 0.5:
                related.append(intent)
        return related[:3]  # 最多返回 3 个相关意图


class TopicTracker:
    """话题跟踪器

    跟踪对话中的话题变化。

    使用示例:
        tracker = TopicTracker()
        tracker.update_topic(context, "实体创建")
        print(tracker.get_topic_summary(context))
    """

    def __init__(self) -> None:
        """初始化话题跟踪器"""
        self._topic_transitions: dict[tuple[TopicCategory, TopicCategory], int] = {}
        self._lock = threading.Lock()

    def update_topic(
        self,
        context: ConversationContext,
        new_topic: Optional[TopicCategory],
    ) -> None:
        """更新话题"""
        if not new_topic:
            return

        with self._lock:
            # 记录话题转换
            if context.current_topic and context.current_topic != new_topic:
                transition = (context.current_topic, new_topic)
                self._topic_transitions[transition] = self._topic_transitions.get(transition, 0) + 1

    def get_topic_summary(
        self,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """获取话题摘要"""
        distribution = context.get_topic_distribution()

        return {
            "current_topic": context.current_topic.value if context.current_topic else None,
            "topic_history": [t.value for t in context.topic_history],
            "topic_distribution": {t.value: c for t, c in distribution.items()},
            "topic_count": len(distribution),
        }

    def predict_next_topic(
        self,
        current_topic: Optional[TopicCategory],
    ) -> Optional[TopicCategory]:
        """预测下一个话题"""
        if not current_topic:
            return None

        with self._lock:
            # 查找最可能的下一个话题
            max_count = 0
            next_topic = None

            for (from_topic, to_topic), count in self._topic_transitions.items():
                if from_topic == current_topic and count > max_count:
                    max_count = count
                    next_topic = to_topic

            return next_topic


class ConversationMemory:
    """对话记忆

    管理多轮对话的记忆和历史检索。
    """

    def __init__(
        self,
        max_history: int = 100,
        session_timeout: float = 3600,
    ) -> None:
        """初始化对话记忆

        Args:
            max_history: 最大历史记录数
            session_timeout: 会话超时时间（秒）
        """
        self._sessions: OrderedDict[str, ConversationContext] = OrderedDict()
        self._max_history = max_history
        self._session_timeout = session_timeout
        self._lock = threading.Lock()
        self._intent_recognizer = IntentRecognizer()
        self._topic_tracker = TopicTracker()

    def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ConversationContext:
        """创建新会话"""
        import uuid
        sid = session_id or str(uuid.uuid4())[:8]

        with self._lock:
            # 清理过期会话
            self._cleanup_expired_sessions()

            # 限制会话数
            while len(self._sessions) >= self._max_history:
                self._sessions.popitem(last=False)

            session = ConversationContext(
                session_id=sid,
                metadata=metadata or {},
            )
            self._sessions[sid] = session
            return session

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """获取会话"""
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
    ) -> ConversationContext:
        """获取或创建会话"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        return self.create_session(session_id)

    def process_message(
        self,
        session: ConversationContext,
        message: str,
        role: ConversationRole = ConversationRole.USER,
    ) -> IntentRecognitionResult:
        """处理消息"""
        if role == ConversationRole.USER:
            # 识别意图
            result = self._intent_recognizer.recognize(message, session)

            # 添加消息到会话
            session.add_message(
                role=role,
                content=message,
                intent=result.intent,
                entities=result.entities,
                topic=result.topic,
            )

            # 更新话题跟踪
            self._topic_tracker.update_topic(session, result.topic)

            return result
        else:
            # 助手消息
            session.add_message(role=role, content=message)
            return IntentRecognitionResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                context_needed=False,
            )

    def add_assistant_response(
        self,
        session: ConversationContext,
        response: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """添加助手响应"""
        session.add_message(
            role=ConversationRole.ASSISTANT,
            content=response,
            metadata=metadata,
        )

    def search_history(
        self,
        query: str,
        session: Optional[ConversationContext] = None,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        """搜索历史记录"""
        results: list[ConversationMessage] = []
        query_lower = query.lower()

        sessions_to_search = [session] if session else list(self._sessions.values())

        for sess in sessions_to_search:
            for msg in sess.messages:
                if query_lower in msg.content.lower():
                    results.append(msg)
                    if len(results) >= limit:
                        return results

        return results

    def get_context_window(
        self,
        session: ConversationContext,
        window_size: int = 5,
    ) -> list[ConversationMessage]:
        """获取上下文窗口"""
        return session.get_recent_messages(window_size)

    def get_conversation_summary(
        self,
        session: ConversationContext,
    ) -> ConversationSummary:
        """获取对话摘要"""
        # 统计主要话题
        topic_dist = session.get_topic_distribution()
        main_topics = sorted(topic_dist.keys(), key=lambda t: topic_dist[t], reverse=True)[:3]

        # 统计主要意图
        intent_counts: dict[IntentType, int] = {}
        for intent in session.intent_history:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        main_intents = sorted(intent_counts.keys(), key=lambda i: intent_counts[i], reverse=True)[:3]

        # 提取关键点
        key_points = []
        for msg in session.messages:
            if msg.role == ConversationRole.USER and msg.intent:
                key_points.append(f"{msg.intent.value}: {msg.content[:50]}...")

        return ConversationSummary(
            session_id=session.session_id,
            message_count=session.get_message_count(),
            duration=session.get_conversation_duration(),
            main_topics=main_topics,
            main_intents=main_intents,
            entities_mentioned=dict(session.entities),
            key_points=key_points[:5],
            state=session.state,
        )

    def _cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        current_time = time.time()
        expired = [
            sid for sid, session in self._sessions.items()
            if current_time - session.last_activity > self._session_timeout
        ]
        for sid in expired:
            del self._sessions[sid]

    def get_session_count(self) -> int:
        """获取会话数"""
        with self._lock:
            return len(self._sessions)

    def get_all_sessions(self) -> list[ConversationContext]:
        """获取所有会话"""
        with self._lock:
            return list(self._sessions.values())


class SmartConversationManager:
    """智能对话管理器

    整合意图识别、话题跟踪和对话记忆。
    """

    def __init__(
        self,
        max_sessions: int = 100,
        session_timeout: float = 3600,
    ) -> None:
        """初始化智能对话管理器"""
        self._memory = ConversationMemory(max_sessions, session_timeout)
        self._intent_recognizer = IntentRecognizer()
        self._topic_tracker = TopicTracker()
        self._lock = threading.Lock()

    def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ConversationContext:
        """创建新会话"""
        return self._memory.create_session(session_id, metadata)

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """获取会话"""
        return self._memory.get_session(session_id)

    def process_user_message(
        self,
        session: ConversationContext,
        message: str,
    ) -> IntentRecognitionResult:
        """处理用户消息"""
        return self._memory.process_message(session, message, ConversationRole.USER)

    def add_assistant_response(
        self,
        session: ConversationContext,
        response: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """添加助手响应"""
        self._memory.add_assistant_response(session, response, metadata)

    def get_context(self, session: ConversationContext) -> dict[str, Any]:
        """获取对话上下文"""
        return {
            "session_id": session.session_id,
            "recent_messages": [m.to_dict() for m in session.get_recent_messages(5)],
            "entities": session.entities,
            "current_topic": session.current_topic.value if session.current_topic else None,
            "intent_history": [i.value for i in session.intent_history[-5:]],
            "topic_summary": self._topic_tracker.get_topic_summary(session),
        }

    def search_history(
        self,
        query: str,
        session: Optional[ConversationContext] = None,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        """搜索历史记录"""
        return self._memory.search_history(query, session, limit)

    def get_summary(self, session: ConversationContext) -> ConversationSummary:
        """获取对话摘要"""
        return self._memory.get_conversation_summary(session)

    def predict_next_intent(
        self,
        session: ConversationContext,
    ) -> Optional[IntentType]:
        """预测下一个意图"""
        history = session.get_user_intent_history()
        if not history:
            return None

        # 简单的马尔可夫链预测
        intent_transitions: dict[tuple[IntentType, IntentType], int] = {}
        for i in range(len(history) - 1):
            transition = (history[i], history[i + 1])
            intent_transitions[transition] = intent_transitions.get(transition, 0) + 1

        last_intent = history[-1]
        max_count = 0
        next_intent = None

        for (from_intent, to_intent), count in intent_transitions.items():
            if from_intent == last_intent and count > max_count:
                max_count = count
                next_intent = to_intent

        return next_intent

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "session_count": self._memory.get_session_count(),
            "sessions": [s.to_dict() for s in self._memory.get_all_sessions()],
        }


# 全局实例
_manager: Optional[SmartConversationManager] = None


def get_conversation_manager() -> SmartConversationManager:
    """获取全局对话管理器"""
    global _manager
    if _manager is None:
        _manager = SmartConversationManager()
    return _manager


def create_session(
    session_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ConversationContext:
    """便捷函数：创建会话"""
    return get_conversation_manager().create_session(session_id, metadata)


def process_message(
    session: ConversationContext,
    message: str,
) -> IntentRecognitionResult:
    """便捷函数：处理消息"""
    return get_conversation_manager().process_user_message(session, message)