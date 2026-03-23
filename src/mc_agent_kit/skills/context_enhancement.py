"""
上下文增强模块

提供多轮对话上下文管理、上下文压缩、关键信息提取和上下文窗口优化。
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ContextPriority(Enum):
    """上下文优先级"""
    CRITICAL = 1.0     # 关键信息，必须保留
    HIGH = 0.8         # 高优先级
    MEDIUM = 0.5       # 中等优先级
    LOW = 0.3          # 低优先级
    DISCARDABLE = 0.1  # 可丢弃


class ContextType(Enum):
    """上下文类型"""
    USER_REQUEST = "user_request"       # 用户请求
    API_CALL = "api_call"               # API 调用
    CODE_SNIPPET = "code_snippet"       # 代码片段
    ERROR_MESSAGE = "error_message"     # 错误消息
    DOCUMENT_REFERENCE = "doc_ref"      # 文档引用
    ENTITY_REFERENCE = "entity_ref"     # 实体引用
    STATE_VARIABLE = "state_var"        # 状态变量
    DECISION = "decision"               # 决策
    CONSTRAINT = "constraint"           # 约束
    PREFERENCE = "preference"           # 偏好


class CompressionStrategy(Enum):
    """压缩策略"""
    SUMMARIZE = "summarize"         # 摘要压缩
    EXTRACT_KEY = "extract_key"     # 关键信息提取
    PRUNE_OLD = "prune_old"         # 删除旧信息
    MERGE_SIMILAR = "merge_similar" # 合并相似
    RANK_KEEP = "rank_keep"         # 按优先级保留


@dataclass
class ContextEntry:
    """上下文条目"""
    id: str
    content: str
    context_type: ContextType
    priority: ContextPriority
    timestamp: float = field(default_factory=time.time)
    relevance_score: float = 1.0
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)  # 引用的其他条目 ID
    source: str = ""

    def __post_init__(self) -> None:
        """后处理"""
        if self.token_count == 0:
            self.token_count = len(self.content.split())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "context_type": self.context_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "relevance_score": self.relevance_score,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "references": self.references,
            "source": self.source,
        }


@dataclass
class ContextWindow:
    """上下文窗口"""
    entries: list[ContextEntry]
    total_tokens: int
    max_tokens: int
    compression_ratio: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entries": [e.to_dict() for e in self.entries],
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "compression_ratio": self.compression_ratio,
            "entry_count": len(self.entries),
        }


@dataclass
class KeyInfo:
    """关键信息"""
    key: str
    value: Any
    info_type: str
    confidence: float = 1.0
    source_entry_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "info_type": self.info_type,
            "confidence": self.confidence,
            "source_entry_id": self.source_entry_id,
        }


@dataclass
class CompressionResult:
    """压缩结果"""
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    removed_entries: list[str]
    summarized_entries: list[ContextEntry]
    key_info_preserved: int

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "removed_entries": self.removed_entries,
            "summarized_entries": [e.to_dict() for e in self.summarized_entries],
            "key_info_preserved": self.key_info_preserved,
        }


class ContextManager:
    """上下文管理器

    管理多轮对话的上下文。

    使用示例:
        manager = ContextManager(max_tokens=4096)
        manager.add_entry("用户想创建实体", ContextType.USER_REQUEST, ContextPriority.HIGH)
        window = manager.get_context_window()
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        max_entries: int = 100,
        session_timeout: float = 3600,
    ) -> None:
        """初始化上下文管理器"""
        self._entries: OrderedDict[str, ContextEntry] = OrderedDict()
        self._max_tokens = max_tokens
        self._max_entries = max_entries
        self._session_timeout = session_timeout
        self._key_info: dict[str, KeyInfo] = {}
        self._lock = threading.RLock()
        self._current_tokens = 0
        self._session_start = time.time()

    def add_entry(
        self,
        content: str,
        context_type: ContextType,
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: Optional[dict[str, Any]] = None,
        references: Optional[list[str]] = None,
        source: str = "",
    ) -> ContextEntry:
        """添加上下文条目"""
        entry_id = self._generate_entry_id(content)

        entry = ContextEntry(
            id=entry_id,
            content=content,
            context_type=context_type,
            priority=priority,
            metadata=metadata or {},
            references=references or [],
            source=source,
        )

        with self._lock:
            # 检查是否需要压缩
            if self._current_tokens + entry.token_count > self._max_tokens:
                self._compress_context()

            self._entries[entry_id] = entry
            self._current_tokens += entry.token_count

            # 提取关键信息
            self._extract_key_info(entry)

            # 限制条目数量
            while len(self._entries) > self._max_entries:
                self._remove_oldest_discardable()

        return entry

    def get_entry(self, entry_id: str) -> Optional[ContextEntry]:
        """获取条目"""
        return self._entries.get(entry_id)

    def get_entries_by_type(
        self,
        context_type: ContextType,
    ) -> list[ContextEntry]:
        """按类型获取条目"""
        return [
            entry for entry in self._entries.values()
            if entry.context_type == context_type
        ]

    def get_entries_by_priority(
        self,
        min_priority: ContextPriority = ContextPriority.LOW,
    ) -> list[ContextEntry]:
        """按优先级获取条目"""
        return [
            entry for entry in self._entries.values()
            if entry.priority.value >= min_priority.value
        ]

    def get_context_window(
        self,
        max_tokens: Optional[int] = None,
    ) -> ContextWindow:
        """获取上下文窗口"""
        max_tokens = max_tokens or self._max_tokens

        with self._lock:
            # 按优先级和相关性排序
            sorted_entries = sorted(
                self._entries.values(),
                key=lambda e: (e.priority.value, e.relevance_score),
                reverse=True,
            )

            # 选择条目直到达到 token 限制
            selected: list[ContextEntry] = []
            total_tokens = 0

            for entry in sorted_entries:
                if total_tokens + entry.token_count <= max_tokens:
                    selected.append(entry)
                    total_tokens += entry.token_count

            compression_ratio = total_tokens / self._current_tokens if self._current_tokens > 0 else 1.0

            return ContextWindow(
                entries=selected,
                total_tokens=total_tokens,
                max_tokens=max_tokens,
                compression_ratio=compression_ratio,
            )

    def search_entries(
        self,
        query: str,
        limit: int = 10,
    ) -> list[tuple[ContextEntry, float]]:
        """搜索条目"""
        query_lower = query.lower()
        results: list[tuple[ContextEntry, float]] = []

        with self._lock:
            for entry in self._entries.values():
                score = 0.0

                # 内容匹配
                if query_lower in entry.content.lower():
                    score = 0.8

                # 元数据匹配
                for key, value in entry.metadata.items():
                    if query_lower in str(value).lower():
                        score = max(score, 0.6)
                        break

                if score > 0:
                    results.append((entry, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def update_relevance(
        self,
        entry_id: str,
        relevance_score: float,
    ) -> bool:
        """更新相关性分数"""
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry:
                entry.relevance_score = relevance_score
                return True
            return False

    def remove_entry(self, entry_id: str) -> bool:
        """删除条目"""
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry:
                self._current_tokens -= entry.token_count
                del self._entries[entry_id]
                return True
            return False

    def clear(self) -> None:
        """清空上下文"""
        with self._lock:
            self._entries.clear()
            self._key_info.clear()
            self._current_tokens = 0

    def get_key_info(self, key: str) -> Optional[KeyInfo]:
        """获取关键信息"""
        return self._key_info.get(key)

    def get_all_key_info(self) -> list[KeyInfo]:
        """获取所有关键信息"""
        return list(self._key_info.values())

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            type_counts: dict[str, int] = {}
            for entry in self._entries.values():
                type_name = entry.context_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

            return {
                "entry_count": len(self._entries),
                "total_tokens": self._current_tokens,
                "max_tokens": self._max_tokens,
                "utilization": self._current_tokens / self._max_tokens,
                "key_info_count": len(self._key_info),
                "type_distribution": type_counts,
                "session_duration": time.time() - self._session_start,
            }

    def _generate_entry_id(self, content: str) -> str:
        """生成条目 ID"""
        hash_input = f"{content}{time.time()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _extract_key_info(self, entry: ContextEntry) -> None:
        """提取关键信息"""
        content = entry.content.lower()

        # API 名称提取
        import re
        api_matches = re.findall(r'\b([A-Z][a-zA-Z]{2,})\b', entry.content)
        for api_name in api_matches:
            key = f"api:{api_name}"
            if key not in self._key_info:
                self._key_info[key] = KeyInfo(
                    key=key,
                    value=api_name,
                    info_type="api_name",
                    source_entry_id=entry.id,
                )

        # 事件名称提取
        event_matches = re.findall(r'\b(On[A-Z][a-zA-Z]*)\b', entry.content)
        for event_name in event_matches:
            key = f"event:{event_name}"
            if key not in self._key_info:
                self._key_info[key] = KeyInfo(
                    key=key,
                    value=event_name,
                    info_type="event_name",
                    source_entry_id=entry.id,
                )

        # 作用域提取
        if "服务端" in content or "server" in content:
            self._key_info["scope"] = KeyInfo(
                key="scope",
                value="server",
                info_type="scope",
                source_entry_id=entry.id,
            )
        elif "客户端" in content or "client" in content:
            self._key_info["scope"] = KeyInfo(
                key="scope",
                value="client",
                info_type="scope",
                source_entry_id=entry.id,
            )

    def _compress_context(self) -> None:
        """压缩上下文"""
        # 先删除可丢弃的低优先级条目
        while (
            self._current_tokens > self._max_tokens * 0.8
            and self._remove_oldest_discardable()
        ):
            pass

    def _remove_oldest_discardable(self) -> bool:
        """删除最旧的可丢弃条目"""
        discardable = [
            (eid, entry) for eid, entry in self._entries.items()
            if entry.priority == ContextPriority.DISCARDABLE
        ]

        if discardable:
            # 按时间排序，删除最旧的
            discardable.sort(key=lambda x: x[1].timestamp)
            entry_id, entry = discardable[0]
            self._current_tokens -= entry.token_count
            del self._entries[entry_id]
            return True

        # 如果没有可丢弃的，删除最低优先级的
        lowest_priority = min(
            self._entries.values(),
            key=lambda e: (e.priority.value, e.timestamp),
            default=None,
        )

        if lowest_priority and lowest_priority.priority != ContextPriority.CRITICAL:
            self._current_tokens -= lowest_priority.token_count
            del self._entries[lowest_priority.id]
            return True

        return False


class ContextCompressor:
    """上下文压缩器

    压缩上下文以适应 token 限制。
    """

    def __init__(
        self,
        target_ratio: float = 0.5,
        preserve_critical: bool = True,
    ) -> None:
        """初始化压缩器"""
        self._target_ratio = target_ratio
        self._preserve_critical = preserve_critical
        self._lock = threading.Lock()

    def compress(
        self,
        entries: list[ContextEntry],
        max_tokens: int,
        strategy: CompressionStrategy = CompressionStrategy.RANK_KEEP,
    ) -> CompressionResult:
        """压缩上下文"""
        if not entries:
            return CompressionResult(
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=1.0,
                removed_entries=[],
                summarized_entries=[],
                key_info_preserved=0,
            )

        original_tokens = sum(e.token_count for e in entries)
        target_tokens = int(max_tokens * self._target_ratio)

        if strategy == CompressionStrategy.RANK_KEEP:
            return self._rank_keep_compress(entries, target_tokens)
        elif strategy == CompressionStrategy.PRUNE_OLD:
            return self._prune_old_compress(entries, target_tokens)
        elif strategy == CompressionStrategy.MERGE_SIMILAR:
            return self._merge_similar_compress(entries, target_tokens)
        else:
            return self._summarize_compress(entries, target_tokens)

    def _rank_keep_compress(
        self,
        entries: list[ContextEntry],
        target_tokens: int,
    ) -> CompressionResult:
        """按优先级保留压缩"""
        # 按优先级排序
        sorted_entries = sorted(
            entries,
            key=lambda e: (e.priority.value, e.relevance_score),
            reverse=True,
        )

        kept: list[ContextEntry] = []
        removed: list[str] = []
        total_tokens = 0

        for entry in sorted_entries:
            if total_tokens + entry.token_count <= target_tokens:
                kept.append(entry)
                total_tokens += entry.token_count
            else:
                removed.append(entry.id)

        compression_ratio = total_tokens / sum(e.token_count for e in entries) if entries else 1.0

        return CompressionResult(
            original_tokens=sum(e.token_count for e in entries),
            compressed_tokens=total_tokens,
            compression_ratio=compression_ratio,
            removed_entries=removed,
            summarized_entries=kept,
            key_info_preserved=len(kept),
        )

    def _prune_old_compress(
        self,
        entries: list[ContextEntry],
        target_tokens: int,
    ) -> CompressionResult:
        """删除旧条目压缩"""
        # 按时间排序（新到旧）
        sorted_entries = sorted(
            entries,
            key=lambda e: e.timestamp,
            reverse=True,
        )

        kept: list[ContextEntry] = []
        removed: list[str] = []
        total_tokens = 0

        for entry in sorted_entries:
            # 保留关键条目
            if self._preserve_critical and entry.priority == ContextPriority.CRITICAL:
                kept.append(entry)
                total_tokens += entry.token_count
                continue

            if total_tokens + entry.token_count <= target_tokens:
                kept.append(entry)
                total_tokens += entry.token_count
            else:
                removed.append(entry.id)

        compression_ratio = total_tokens / sum(e.token_count for e in entries) if entries else 1.0

        return CompressionResult(
            original_tokens=sum(e.token_count for e in entries),
            compressed_tokens=total_tokens,
            compression_ratio=compression_ratio,
            removed_entries=removed,
            summarized_entries=kept,
            key_info_preserved=len(kept),
        )

    def _merge_similar_compress(
        self,
        entries: list[ContextEntry],
        target_tokens: int,
    ) -> CompressionResult:
        """合并相似条目压缩"""
        # 按类型分组
        groups: dict[ContextType, list[ContextEntry]] = {}
        for entry in entries:
            if entry.context_type not in groups:
                groups[entry.context_type] = []
            groups[entry.context_type].append(entry)

        merged: list[ContextEntry] = []
        removed: list[str] = []

        for context_type, group_entries in groups.items():
            if len(group_entries) > 1:
                # 合并同类型条目
                merged_content = " | ".join(e.content for e in group_entries)
                merged_entry = ContextEntry(
                    id=f"merged:{context_type.value}",
                    content=merged_content[:500],  # 限制长度
                    context_type=context_type,
                    priority=ContextPriority.MEDIUM,
                    token_count=len(merged_content[:500].split()),
                )
                merged.append(merged_entry)
                removed.extend([e.id for e in group_entries])
            else:
                merged.extend(group_entries)

        # 如果仍然超过限制，使用 rank_keep 进一步压缩
        if sum(e.token_count for e in merged) > target_tokens:
            return self._rank_keep_compress(merged, target_tokens)

        compression_ratio = sum(e.token_count for e in merged) / sum(e.token_count for e in entries) if entries else 1.0

        return CompressionResult(
            original_tokens=sum(e.token_count for e in entries),
            compressed_tokens=sum(e.token_count for e in merged),
            compression_ratio=compression_ratio,
            removed_entries=removed,
            summarized_entries=merged,
            key_info_preserved=len(merged),
        )

    def _summarize_compress(
        self,
        entries: list[ContextEntry],
        target_tokens: int,
    ) -> CompressionResult:
        """摘要压缩"""
        # 简单实现：截断内容
        kept: list[ContextEntry] = []
        removed: list[str] = []
        total_tokens = 0

        for entry in entries:
            if self._preserve_critical and entry.priority == ContextPriority.CRITICAL:
                kept.append(entry)
                total_tokens += entry.token_count
                continue

            # 截断内容
            max_entry_tokens = target_tokens // max(len(entries), 1)
            if entry.token_count > max_entry_tokens:
                truncated_content = " ".join(
                    entry.content.split()[:max_entry_tokens]
                ) + "..."
                truncated_entry = ContextEntry(
                    id=entry.id,
                    content=truncated_content,
                    context_type=entry.context_type,
                    priority=entry.priority,
                    token_count=len(truncated_content.split()),
                )
                kept.append(truncated_entry)
                total_tokens += truncated_entry.token_count
            else:
                kept.append(entry)
                total_tokens += entry.token_count

        compression_ratio = total_tokens / sum(e.token_count for e in entries) if entries else 1.0

        return CompressionResult(
            original_tokens=sum(e.token_count for e in entries),
            compressed_tokens=total_tokens,
            compression_ratio=compression_ratio,
            removed_entries=removed,
            summarized_entries=kept,
            key_info_preserved=len(kept),
        )


class KeyInfoExtractor:
    """关键信息提取器

    从上下文中提取关键信息。
    """

    def __init__(self) -> None:
        """初始化关键信息提取器"""
        self._patterns = {
            "api_name": r'\b([A-Z][a-zA-Z]{2,})\b',
            "event_name": r'\b(On[A-Z][a-zA-Z]*)\b',
            "entity_name": r'实体[：:]\s*(\w+)',
            "item_name": r'物品[：:]\s*(\w+)',
            "scope": r'(服务端|客户端|server|client)',
            "module": r'模块[：:]\s*(\w+)',
        }

    def extract(
        self,
        content: str,
        context_type: Optional[ContextType] = None,
    ) -> list[KeyInfo]:
        """提取关键信息"""
        import re
        results: list[KeyInfo] = []

        for info_type, pattern in self._patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                key = f"{info_type}:{match}"
                results.append(KeyInfo(
                    key=key,
                    value=match,
                    info_type=info_type,
                    confidence=0.8,
                ))

        return results

    def extract_from_entries(
        self,
        entries: list[ContextEntry],
    ) -> list[KeyInfo]:
        """从多个条目提取关键信息"""
        all_info: dict[str, KeyInfo] = {}

        for entry in entries:
            info_list = self.extract(entry.content, entry.context_type)
            for info in info_list:
                # 去重，保留置信度高的
                if info.key not in all_info or info.confidence > all_info[info.key].confidence:
                    all_info[info.key] = info

        return list(all_info.values())


class ContextEnhancer:
    """上下文增强器

    整合上下文管理、压缩和关键信息提取。
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        target_compression_ratio: float = 0.5,
    ) -> None:
        """初始化上下文增强器"""
        self._manager = ContextManager(max_tokens=max_tokens)
        self._compressor = ContextCompressor(target_ratio=target_compression_ratio)
        self._extractor = KeyInfoExtractor()
        self._lock = threading.RLock()

    def add_context(
        self,
        content: str,
        context_type: ContextType,
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ContextEntry:
        """添加上下文"""
        return self._manager.add_entry(
            content=content,
            context_type=context_type,
            priority=priority,
            metadata=metadata,
        )

    def get_optimized_context(
        self,
        max_tokens: Optional[int] = None,
        strategy: CompressionStrategy = CompressionStrategy.RANK_KEEP,
    ) -> ContextWindow:
        """获取优化后的上下文"""
        window = self._manager.get_context_window(max_tokens)

        if window.compression_ratio > 0.7:
            # 不需要压缩
            return window

        # 压缩
        result = self._compressor.compress(
            window.entries,
            window.max_tokens,
            strategy,
        )

        return ContextWindow(
            entries=result.summarized_entries,
            total_tokens=result.compressed_tokens,
            max_tokens=window.max_tokens,
            compression_ratio=result.compression_ratio,
        )

    def get_key_info(self) -> list[KeyInfo]:
        """获取关键信息"""
        return self._manager.get_all_key_info()

    def search_context(
        self,
        query: str,
        limit: int = 10,
    ) -> list[tuple[ContextEntry, float]]:
        """搜索上下文"""
        return self._manager.search_entries(query, limit)

    def get_context_summary(self) -> dict[str, Any]:
        """获取上下文摘要"""
        stats = self._manager.get_stats()
        key_info = self.get_key_info()

        return {
            "stats": stats,
            "key_info_count": len(key_info),
            "key_info_types": self._group_key_info_by_type(key_info),
        }

    def _group_key_info_by_type(
        self,
        key_info_list: list[KeyInfo],
    ) -> dict[str, int]:
        """按类型分组关键信息"""
        groups: dict[str, int] = {}
        for info in key_info_list:
            groups[info.info_type] = groups.get(info.info_type, 0) + 1
        return groups

    def clear(self) -> None:
        """清空上下文"""
        self._manager.clear()


# 全局实例
_enhancer: Optional[ContextEnhancer] = None


def get_context_enhancer() -> ContextEnhancer:
    """获取全局上下文增强器"""
    global _enhancer
    if _enhancer is None:
        _enhancer = ContextEnhancer()
    return _enhancer


def add_context(
    content: str,
    context_type: ContextType,
    priority: ContextPriority = ContextPriority.MEDIUM,
) -> ContextEntry:
    """便捷函数：添加上下文"""
    return get_context_enhancer().add_context(content, context_type, priority)