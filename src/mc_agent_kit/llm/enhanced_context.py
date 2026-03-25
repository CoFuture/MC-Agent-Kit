"""
上下文管理增强模块

提供优化的上下文压缩、优先级排序、跨会话上下文和持久化。
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import ChatMessage, ChatRole


class ContextPriority(Enum):
    """上下文优先级"""
    CRITICAL = 100   # 关键信息，不可删除
    HIGH = 80        # 高优先级，尽量保留
    NORMAL = 50      # 普通优先级
    LOW = 20         # 低优先级
    DISPOSABLE = 0   # 可丢弃


class ContextCategory(Enum):
    """上下文分类"""
    SYSTEM = "system"           # 系统消息
    INSTRUCTION = "instruction"  # 指令信息
    CODE = "code"               # 代码相关
    ERROR = "error"             # 错误信息
    DECISION = "decision"       # 决策记录
    QUESTION = "question"       # 问题
    ANSWER = "answer"           # 回答
    FEEDBACK = "feedback"       # 反馈
    METADATA = "metadata"       # 元数据
    GENERAL = "general"         # 一般对话


@dataclass
class PrioritizedContextMessage:
    """带优先级的上下文消息"""
    message: ChatMessage
    priority: ContextPriority = ContextPriority.NORMAL
    category: ContextCategory = ContextCategory.GENERAL
    timestamp: float = field(default_factory=time.time)
    token_count: int = 0
    importance_score: float = 0.0
    references: list[str] = field(default_factory=list)  # 引用的其他消息 ID
    id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"msg_{int(self.timestamp * 1000)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message.to_dict(),
            "priority": self.priority.value,
            "category": self.category.value,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
            "importance_score": self.importance_score,
            "references": self.references,
            "id": self.id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrioritizedContextMessage:
        msg_data = data["message"]
        return cls(
            message=ChatMessage(
                role=ChatRole(msg_data["role"]),
                content=msg_data["content"],
            ),
            priority=ContextPriority(data["priority"]),
            category=ContextCategory(data["category"]),
            timestamp=data["timestamp"],
            token_count=data.get("token_count", 0),
            importance_score=data.get("importance_score", 0.0),
            references=data.get("references", []),
            id=data["id"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class CompressionResult:
    """压缩结果"""
    original_tokens: int = 0
    compressed_tokens: int = 0
    removed_messages: int = 0
    summary: str = ""
    preserved_ids: list[str] = field(default_factory=list)

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1 - (self.compressed_tokens / self.original_tokens)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "removed_messages": self.removed_messages,
            "summary": self.summary,
            "preserved_ids": self.preserved_ids,
            "compression_ratio": self.compression_ratio,
        }


class ContextCompressor:
    """
    上下文压缩器

    使用优化算法压缩上下文。
    """

    def __init__(
        self,
        target_ratio: float = 0.5,
        preserve_priority_threshold: ContextPriority = ContextPriority.HIGH,
    ) -> None:
        self.target_ratio = target_ratio
        self.preserve_priority_threshold = preserve_priority_threshold

    def compress(
        self,
        messages: list[PrioritizedContextMessage],
        max_tokens: int,
    ) -> tuple[list[PrioritizedContextMessage], CompressionResult]:
        """
        压缩上下文

        Args:
            messages: 消息列表
            max_tokens: 最大 token 数

        Returns:
            tuple: (压缩后的消息列表, 压缩结果)
        """
        if not messages:
            return [], CompressionResult()

        # 计算总 token 数
        total_tokens = sum(m.token_count for m in messages)

        if total_tokens <= max_tokens:
            return messages, CompressionResult(
                original_tokens=total_tokens,
                compressed_tokens=total_tokens,
            )

        # 计算重要性分数
        scored_messages = self._score_messages(messages)

        # 按优先级和重要性排序
        sorted_messages = sorted(
            scored_messages,
            key=lambda m: (m.priority.value, m.importance_score),
            reverse=True,
        )

        # 选择保留的消息
        preserved: list[PrioritizedContextMessage] = []
        preserved_tokens = 0
        preserved_ids: list[str] = []
        summary_parts: list[str] = []

        for msg in sorted_messages:
            if preserved_tokens + msg.token_count <= max_tokens:
                preserved.append(msg)
                preserved_tokens += msg.token_count
                preserved_ids.append(msg.id)
            elif msg.priority.value >= self.preserve_priority_threshold.value:
                # 高优先级消息，尝试摘要
                if len(msg.message.content) > 100:
                    summary = self._summarize_message(msg)
                    summary_parts.append(summary)
                    # 创建摘要消息
                    summary_msg = PrioritizedContextMessage(
                        message=ChatMessage(
                            role=msg.message.role,
                            content=summary,
                        ),
                        priority=msg.priority,
                        category=msg.category,
                        timestamp=msg.timestamp,
                        token_count=len(summary) // 4,
                    )
                    preserved.append(summary_msg)
                    preserved_tokens += summary_msg.token_count

        # 按时间重新排序
        preserved.sort(key=lambda m: m.timestamp)

        # 生成总体摘要
        if summary_parts:
            full_summary = "压缩摘要:\n" + "\n".join(f"- {s}" for s in summary_parts[:5])
        else:
            full_summary = ""

        return preserved, CompressionResult(
            original_tokens=total_tokens,
            compressed_tokens=preserved_tokens,
            removed_messages=len(messages) - len(preserved),
            summary=full_summary,
            preserved_ids=preserved_ids,
        )

    def _score_messages(
        self,
        messages: list[PrioritizedContextMessage],
    ) -> list[PrioritizedContextMessage]:
        """计算消息重要性分数"""
        for i, msg in enumerate(messages):
            score = 0.0

            # 基础分数：优先级
            score += msg.priority.value * 0.5

            # 类别权重
            category_weights = {
                ContextCategory.SYSTEM: 1.0,
                ContextCategory.INSTRUCTION: 0.9,
                ContextCategory.ERROR: 0.8,
                ContextCategory.DECISION: 0.7,
                ContextCategory.CODE: 0.6,
                ContextCategory.QUESTION: 0.5,
                ContextCategory.ANSWER: 0.5,
                ContextCategory.FEEDBACK: 0.4,
                ContextCategory.METADATA: 0.3,
                ContextCategory.GENERAL: 0.2,
            }
            score += category_weights.get(msg.category, 0.2) * 50

            # 位置权重（最近的消息更重要）
            position_weight = i / len(messages) if messages else 0
            score += position_weight * 20

            # 引用权重（被引用的消息更重要）
            reference_count = sum(
                1 for m in messages if msg.id in m.references
            )
            score += reference_count * 10

            # 内容特征
            content = msg.message.content.lower()
            if "重要" in content or "important" in content:
                score += 15
            if "错误" in content or "error" in content:
                score += 10
            if "决策" in content or "decision" in content:
                score += 10

            msg.importance_score = score

        return messages

    def _summarize_message(self, msg: PrioritizedContextMessage) -> str:
        """生成消息摘要"""
        content = msg.message.content

        # 提取关键句子
        sentences = content.replace("。", ".").replace("！", "!").replace("？", "?").split(".")
        key_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            # 检查是否包含关键词
            keywords = ["重要", "决策", "错误", "注意", "important", "error", "decision"]
            if any(kw in sentence.lower() for kw in keywords):
                key_sentences.append(sentence)
                if len(key_sentences) >= 3:
                    break

        if not key_sentences:
            # 取前几个句子
            key_sentences = [s.strip() for s in sentences[:2] if len(s.strip()) >= 10]

        return "。".join(key_sentences)[:200]


class CrossSessionContext:
    """
    跨会话上下文

    管理跨多个会话的持久化上下文。
    """

    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), ".context_sessions")
        self._sessions: dict[str, list[PrioritizedContextMessage]] = {}
        self._global_context: dict[str, Any] = {}
        self._lock = threading.Lock()

        os.makedirs(self.storage_dir, exist_ok=True)

    def create_session(self, session_id: str) -> None:
        """创建新会话"""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = []

    def add_message(
        self,
        session_id: str,
        message: PrioritizedContextMessage,
    ) -> None:
        """添加消息到会话"""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = []
            self._sessions[session_id].append(message)

    def get_session_messages(
        self,
        session_id: str,
    ) -> list[PrioritizedContextMessage]:
        """获取会话消息"""
        with self._lock:
            return list(self._sessions.get(session_id, []))

    def get_recent_context(
        self,
        session_id: str,
        max_messages: int = 20,
    ) -> list[PrioritizedContextMessage]:
        """获取最近的上下文"""
        messages = self.get_session_messages(session_id)
        return messages[-max_messages:] if messages else []

    def get_cross_session_context(
        self,
        session_id: str,
        include_other_sessions: bool = False,
    ) -> dict[str, Any]:
        """
        获取跨会话上下文

        Args:
            session_id: 当前会话 ID
            include_other_sessions: 是否包含其他会话的关键信息

        Returns:
            dict: 跨会话上下文
        """
        context: dict[str, Any] = {
            "current_session": [],
            "global_context": dict(self._global_context),
            "decisions": [],
            "errors": [],
        }

        # 当前会话消息
        messages = self.get_session_messages(session_id)
        context["current_session"] = [m.to_dict() for m in messages]

        if include_other_sessions:
            # 从其他会话提取关键信息
            for other_id, other_messages in self._sessions.items():
                if other_id == session_id:
                    continue

                for msg in other_messages:
                    # 提取决策
                    if msg.category == ContextCategory.DECISION:
                        context["decisions"].append({
                            "session_id": other_id,
                            "content": msg.message.content,
                            "timestamp": msg.timestamp,
                        })

                    # 提取错误
                    if msg.category == ContextCategory.ERROR:
                        context["errors"].append({
                            "session_id": other_id,
                            "content": msg.message.content,
                            "timestamp": msg.timestamp,
                        })

        return context

    def set_global_context(self, key: str, value: Any) -> None:
        """设置全局上下文"""
        with self._lock:
            self._global_context[key] = value

    def get_global_context(self, key: str) -> Any | None:
        """获取全局上下文"""
        return self._global_context.get(key)

    def save_session(self, session_id: str) -> bool:
        """保存会话到文件"""
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")

        with self._lock:
            messages = self._sessions.get(session_id, [])

        try:
            data = {
                "session_id": session_id,
                "messages": [m.to_dict() for m in messages],
                "global_context": self._global_context,
                "timestamp": time.time(),
            }

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except (IOError, json.JSONEncodeError):
            return False

    def load_session(self, session_id: str) -> bool:
        """从文件加载会话"""
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")

        if not os.path.exists(session_file):
            return False

        try:
            with open(session_file, encoding="utf-8") as f:
                data = json.load(f)

            with self._lock:
                self._sessions[session_id] = [
                    PrioritizedContextMessage.from_dict(m)
                    for m in data.get("messages", [])
                ]
                if "global_context" in data:
                    self._global_context.update(data["global_context"])

            return True
        except (json.JSONDecodeError, IOError, KeyError):
            return False

    def list_sessions(self) -> list[str]:
        """列出所有会话"""
        sessions = set(self._sessions.keys())

        # 从文件加载
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    session_id = filename[:-5]  # 去掉 .json
                    sessions.add(session_id)

        return list(sessions)

    def delete_session(self, session_id: str) -> None:
        """删除会话"""
        with self._lock:
            self._sessions.pop(session_id, None)

        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except OSError:
                pass


class ContextPersistence:
    """
    上下文持久化管理器

    提供多种存储后端的持久化支持。
    """

    def __init__(self, storage_type: str = "file", storage_path: str | None = None) -> None:
        self.storage_type = storage_type
        self.storage_path = storage_path or os.path.join(os.getcwd(), ".context_persistence")
        self._cache: dict[str, Any] = {}
        self._lock = threading.Lock()

        if storage_type == "file":
            os.makedirs(self.storage_path, exist_ok=True)

    def save(self, key: str, data: Any) -> bool:
        """保存数据"""
        with self._lock:
            self._cache[key] = data

        if self.storage_type == "file":
            return self._save_to_file(key, data)

        return True

    def load(self, key: str) -> Any | None:
        """加载数据"""
        # 先检查缓存
        with self._lock:
            if key in self._cache:
                return self._cache[key]

        # 从存储加载
        if self.storage_type == "file":
            data = self._load_from_file(key)
            if data is not None:
                with self._lock:
                    self._cache[key] = data
            return data

        return None

    def delete(self, key: str) -> bool:
        """删除数据"""
        with self._lock:
            self._cache.pop(key, None)

        if self.storage_type == "file":
            return self._delete_file(key)

        return True

    def exists(self, key: str) -> bool:
        """检查是否存在"""
        with self._lock:
            if key in self._cache:
                return True

        if self.storage_type == "file":
            file_path = os.path.join(self.storage_path, f"{key}.json")
            return os.path.exists(file_path)

        return False

    def list_keys(self) -> list[str]:
        """列出所有键"""
        keys = set(self._cache.keys())

        if self.storage_type == "file" and os.path.exists(self.storage_path):
            for filename in os.listdir(self.storage_path):
                if filename.endswith(".json"):
                    keys.add(filename[:-5])

        return list(keys)

    def _save_to_file(self, key: str, data: Any) -> bool:
        """保存到文件"""
        file_path = os.path.join(self.storage_path, f"{key}.json")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except (IOError, json.JSONEncodeError):
            return False

    def _load_from_file(self, key: str) -> Any | None:
        """从文件加载"""
        file_path = os.path.join(self.storage_path, f"{key}.json")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _delete_file(self, key: str) -> bool:
        """删除文件"""
        file_path = os.path.join(self.storage_path, f"{key}.json")

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False

        return True

    def clear(self) -> None:
        """清空所有数据"""
        with self._lock:
            self._cache.clear()

        if self.storage_type == "file" and os.path.exists(self.storage_path):
            for filename in os.listdir(self.storage_path):
                if filename.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.storage_path, filename))
                    except OSError:
                        pass


class EnhancedContextManager:
    """
    增强上下文管理器

    整合压缩、优先级、跨会话和持久化功能。
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        target_compression_ratio: float = 0.5,
        storage_dir: str | None = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.compressor = ContextCompressor(target_ratio=target_compression_ratio)
        self.cross_session = CrossSessionContext(storage_dir)
        self.persistence = ContextPersistence("file", storage_dir)

        self._current_session_id: str | None = None
        self._messages: list[PrioritizedContextMessage] = []
        self._lock = threading.Lock()

    def start_session(self, session_id: str) -> None:
        """开始新会话"""
        self._current_session_id = session_id
        self.cross_session.create_session(session_id)

        # 尝试加载之前的会话
        self.cross_session.load_session(session_id)
        self._messages = self.cross_session.get_session_messages(session_id)

    def add_message(
        self,
        message: ChatMessage,
        priority: ContextPriority = ContextPriority.NORMAL,
        category: ContextCategory = ContextCategory.GENERAL,
        metadata: dict[str, Any] | None = None,
    ) -> PrioritizedContextMessage:
        """添加消息"""
        prioritized = PrioritizedContextMessage(
            message=message,
            priority=priority,
            category=category,
            token_count=len(message.content) // 4,
            metadata=metadata or {},
        )

        with self._lock:
            self._messages.append(prioritized)

        if self._current_session_id:
            self.cross_session.add_message(self._current_session_id, prioritized)

        return prioritized

    def add_system_message(self, content: str) -> PrioritizedContextMessage:
        """添加系统消息"""
        return self.add_message(
            ChatMessage.system(content),
            priority=ContextPriority.CRITICAL,
            category=ContextCategory.SYSTEM,
        )

    def add_user_message(self, content: str) -> PrioritizedContextMessage:
        """添加用户消息"""
        return self.add_message(
            ChatMessage.user(content),
            priority=ContextPriority.NORMAL,
            category=ContextCategory.QUESTION,
        )

    def add_assistant_message(self, content: str) -> PrioritizedContextMessage:
        """添加助手消息"""
        return self.add_message(
            ChatMessage.assistant(content),
            priority=ContextPriority.NORMAL,
            category=ContextCategory.ANSWER,
        )

    def add_error_message(self, content: str) -> PrioritizedContextMessage:
        """添加错误消息"""
        return self.add_message(
            ChatMessage.system(content),
            priority=ContextPriority.HIGH,
            category=ContextCategory.ERROR,
        )

    def add_decision_message(self, content: str) -> PrioritizedContextMessage:
        """添加决策消息"""
        return self.add_message(
            ChatMessage.system(content),
            priority=ContextPriority.HIGH,
            category=ContextCategory.DECISION,
        )

    def get_messages(self) -> list[ChatMessage]:
        """获取消息列表（可能已压缩）"""
        with self._lock:
            messages = list(self._messages)

        # 检查是否需要压缩
        total_tokens = sum(m.token_count for m in messages)

        if total_tokens > self.max_tokens:
            compressed, _ = self.compressor.compress(messages, self.max_tokens)
            return [m.message for m in compressed]

        return [m.message for m in messages]

    def compress_if_needed(self) -> CompressionResult:
        """如果需要则压缩"""
        with self._lock:
            messages = list(self._messages)

        total_tokens = sum(m.token_count for m in messages)

        if total_tokens <= self.max_tokens:
            return CompressionResult(
                original_tokens=total_tokens,
                compressed_tokens=total_tokens,
            )

        compressed, result = self.compressor.compress(messages, self.max_tokens)

        with self._lock:
            self._messages = compressed

        return result

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        with self._lock:
            messages = list(self._messages)

        summary_parts = []

        # 按类别分组
        categories: dict[ContextCategory, list[str]] = {}
        for msg in messages:
            if msg.category not in categories:
                categories[msg.category] = []
            categories[msg.category].append(msg.message.content[:100])

        # 生成摘要
        if ContextCategory.DECISION in categories:
            summary_parts.append("已做决策: " + "; ".join(categories[ContextCategory.DECISION][:3]))

        if ContextCategory.ERROR in categories:
            summary_parts.append("遇到问题: " + "; ".join(categories[ContextCategory.ERROR][:3]))

        if ContextCategory.CODE in categories:
            summary_parts.append(f"代码相关: {len(categories[ContextCategory.CODE])} 条消息")

        return "\n".join(summary_parts) if summary_parts else "暂无上下文摘要"

    def save_session(self) -> bool:
        """保存当前会话"""
        if not self._current_session_id:
            return False

        return self.cross_session.save_session(self._current_session_id)

    def load_session(self, session_id: str) -> bool:
        """加载会话"""
        if self.cross_session.load_session(session_id):
            self._current_session_id = session_id
            self._messages = self.cross_session.get_session_messages(session_id)
            return True
        return False

    def clear_session(self) -> None:
        """清空当前会话"""
        with self._lock:
            self._messages.clear()

        if self._current_session_id:
            self.cross_session.delete_session(self._current_session_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            messages = list(self._messages)

        total_tokens = sum(m.token_count for m in messages)

        categories: dict[str, int] = {}
        for msg in messages:
            cat = msg.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_messages": len(messages),
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "categories": categories,
            "session_id": self._current_session_id,
        }


# 便捷函数
_enhanced_context_manager: EnhancedContextManager | None = None


def get_enhanced_context_manager(
    max_tokens: int = 4000,
    storage_dir: str | None = None,
) -> EnhancedContextManager:
    """获取增强上下文管理器单例"""
    global _enhanced_context_manager
    if _enhanced_context_manager is None:
        _enhanced_context_manager = EnhancedContextManager(max_tokens, storage_dir=storage_dir)
    return _enhanced_context_manager