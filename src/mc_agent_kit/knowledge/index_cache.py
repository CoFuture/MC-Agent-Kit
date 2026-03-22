"""
知识库索引缓存模块

实现知识库索引构建缓存，支持：
- 索引构建缓存
- 增量索引更新
- 缓存失效检测
- 缓存统计和清理
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheMetadata:
    """缓存元数据"""
    cache_version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    source_hash: str = ""
    file_count: int = 0
    total_size: int = 0
    build_time_ms: float = 0.0


@dataclass
class FileState:
    """文件状态"""
    path: str
    hash: str
    size: int
    modified_time: float


@dataclass
class IndexCacheStats:
    """索引缓存统计"""
    total_entries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_size_bytes: int = 0
    last_build_time: float = 0.0
    hit_rate: float = 0.0


class KnowledgeIndexCache:
    """
    知识库索引缓存

    缓存知识库索引构建结果，支持增量更新和失效检测。

    使用示例:
        cache = KnowledgeIndexCache(cache_dir=".cache/index")
        
        # 检查是否需要重建
        if cache.needs_rebuild(docs_dir):
            kb = build_index(docs_dir)
            cache.save(kb)
        else
            kb = cache.load()
    """

    def __init__(
        self,
        cache_dir: str = ".cache/knowledge_index",
        ttl_seconds: int | None = None,
        max_size_mb: int = 100,
    ):
        """
        初始化索引缓存。

        Args:
            cache_dir: 缓存目录
            ttl_seconds: 缓存有效期（秒），None 表示永不过期
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._metadata: CacheMetadata | None = None
        self._file_states: dict[str, FileState] = {}
        self._stats = IndexCacheStats()

    def needs_rebuild(
        self,
        source_dir: str,
        file_patterns: list[str] | None = None,
    ) -> bool:
        """
        检查是否需要重建索引。

        Args:
            source_dir: 源文档目录
            file_patterns: 文件匹配模式（如 ["*.md"]）

        Returns:
            是否需要重建
        """
        self._stats.cache_misses += 1

        # 检查缓存目录是否存在
        if not self.cache_dir.exists():
            return True

        # 检查缓存文件是否存在
        cache_file = self.cache_dir / "index.json"
        if not cache_file.exists():
            return True

        # 检查 TTL
        if self.ttl_seconds:
            metadata = self._load_metadata()
            if metadata and (time.time() - metadata.created_at) > self.ttl_seconds:
                return True

        # 加载文件状态
        self._load_file_states()

        # 检查源文件变化
        source_path = Path(source_dir)
        if not source_path.exists():
            return True

        patterns = file_patterns or ["*.md"]
        current_files = self._scan_files(source_dir, patterns)

        # 文件数量变化
        if len(current_files) != len(self._file_states):
            return True

        # 检查文件内容变化
        for file_path, state in current_files.items():
            if file_path not in self._file_states:
                return True

            cached_state = self._file_states[file_path]
            if state.hash != cached_state.hash:
                return True
            if state.size != cached_state.size:
                return True

        # 检查是否有删除的文件
        for file_path in self._file_states:
            if file_path not in current_files:
                return True

        self._stats.cache_hits += 1
        return False

    def get_incremental_changes(
        self,
        source_dir: str,
        file_patterns: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """
        获取增量变化。

        Args:
            source_dir: 源文档目录
            file_patterns: 文件匹配模式

        Returns:
            {"added": [...], "modified": [...], "deleted": [...]}
        """
        patterns = file_patterns or ["*.md"]
        current_files = self._scan_files(source_dir, patterns)
        self._load_file_states()

        changes = {
            "added": [],
            "modified": [],
            "deleted": [],
        }

        # 检查新增和修改
        for file_path, state in current_files.items():
            if file_path not in self._file_states:
                changes["added"].append(file_path)
            elif state.hash != self._file_states[file_path].hash:
                changes["modified"].append(file_path)

        # 检查删除
        for file_path in self._file_states:
            if file_path not in current_files:
                changes["deleted"].append(file_path)

        return changes

    def save(
        self,
        index_data: dict[str, Any],
        source_dir: str,
        file_patterns: list[str] | None = None,
        build_time_ms: float = 0.0,
    ) -> None:
        """
        保存索引缓存。

        Args:
            index_data: 索引数据
            source_dir: 源文档目录
            file_patterns: 文件匹配模式
            build_time_ms: 构建耗时（毫秒）
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        patterns = file_patterns or ["*.md"]
        current_files = self._scan_files(source_dir, patterns)

        # 计算源哈希
        source_hash = self._compute_source_hash(current_files)

        # 创建元数据
        self._metadata = CacheMetadata(
            source_hash=source_hash,
            file_count=len(current_files),
            total_size=sum(s.size for s in current_files.values()),
            build_time_ms=build_time_ms,
        )

        # 保存索引数据
        cache_file = self.cache_dir / "index.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False)

        # 保存元数据
        self._save_metadata()

        # 保存文件状态
        self._file_states = current_files
        self._save_file_states()

        # 更新统计
        self._stats.total_entries = len(index_data.get("apis", {})) + len(index_data.get("events", {}))
        self._stats.total_size_bytes = cache_file.stat().st_size
        self._stats.last_build_time = build_time_ms

    def load(self) -> dict[str, Any] | None:
        """
        加载索引缓存。

        Returns:
            索引数据，不存在返回 None
        """
        cache_file = self.cache_dir / "index.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def invalidate(self, source_dir: str | None = None) -> bool:
        """
        使缓存失效。

        Args:
            source_dir: 源目录（可选，用于验证）

        Returns:
            是否成功
        """
        if not self.cache_dir.exists():
            return False

        try:
            # 删除缓存文件
            for file in self.cache_dir.glob("*"):
                file.unlink()

            # 清空状态
            self._metadata = None
            self._file_states.clear()
            self._stats = IndexCacheStats()

            return True
        except Exception:
            return False

    def cleanup(self, max_age_days: int = 30) -> int:
        """
        清理过期缓存。

        Args:
            max_age_days: 最大保留天数

        Returns:
            清理的文件数
        """
        if not self.cache_dir.exists():
            return 0

        cleaned = 0
        cutoff_time = time.time() - (max_age_days * 24 * 3600)

        for file in self.cache_dir.glob("*"):
            if file.is_file() and file.stat().st_mtime < cutoff_time:
                file.unlink()
                cleaned += 1

        return cleaned

    def get_stats(self) -> IndexCacheStats:
        """
        获取缓存统计。

        Returns:
            缓存统计信息
        """
        total = self._stats.cache_hits + self._stats.cache_misses
        if total > 0:
            self._stats.hit_rate = self._stats.cache_hits / total

        return self._stats

    def get_metadata(self) -> CacheMetadata | None:
        """获取缓存元数据"""
        if not self._metadata:
            self._load_metadata()
        return self._metadata

    def _scan_files(
        self,
        source_dir: str,
        patterns: list[str],
    ) -> dict[str, FileState]:
        """扫描源文件"""
        files = {}
        source_path = Path(source_dir)

        for pattern in patterns:
            for file_path in source_path.rglob(pattern):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(source_path))
                    files[rel_path] = FileState(
                        path=rel_path,
                        hash=self._compute_file_hash(file_path),
                        size=file_path.stat().st_size,
                        modified_time=file_path.stat().st_mtime,
                    )

        return files

    def _compute_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _compute_source_hash(self, files: dict[str, FileState]) -> str:
        """计算源目录哈希"""
        hasher = hashlib.md5()
        for path in sorted(files.keys()):
            hasher.update(path.encode())
            hasher.update(files[path].hash.encode())
        return hasher.hexdigest()

    def _load_metadata(self) -> CacheMetadata | None:
        """加载元数据"""
        meta_file = self.cache_dir / "metadata.json"
        if not meta_file.exists():
            return None

        try:
            with open(meta_file, encoding="utf-8") as f:
                data = json.load(f)
            self._metadata = CacheMetadata(**data)
            return self._metadata
        except (json.JSONDecodeError, IOError, TypeError):
            return None

    def _save_metadata(self) -> None:
        """保存元数据"""
        if not self._metadata:
            return

        meta_file = self.cache_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "cache_version": self._metadata.cache_version,
                "created_at": self._metadata.created_at,
                "updated_at": self._metadata.updated_at,
                "source_hash": self._metadata.source_hash,
                "file_count": self._metadata.file_count,
                "total_size": self._metadata.total_size,
                "build_time_ms": self._metadata.build_time_ms,
            }, f, indent=2)

    def _load_file_states(self) -> None:
        """加载文件状态"""
        states_file = self.cache_dir / "file_states.json"
        if not states_file.exists():
            return

        try:
            with open(states_file, encoding="utf-8") as f:
                data = json.load(f)

            self._file_states = {
                path: FileState(**state)
                for path, state in data.items()
            }
        except (json.JSONDecodeError, IOError, TypeError):
            self._file_states = {}

    def _save_file_states(self) -> None:
        """保存文件状态"""
        states_file = self.cache_dir / "file_states.json"
        with open(states_file, "w", encoding="utf-8") as f:
            json.dump({
                path: {
                    "path": state.path,
                    "hash": state.hash,
                    "size": state.size,
                    "modified_time": state.modified_time,
                }
                for path, state in self._file_states.items()
            }, f, indent=2)


def create_index_cache(cache_dir: str = ".cache/knowledge_index") -> KnowledgeIndexCache:
    """
    创建索引缓存实例的便捷函数。

    Args:
        cache_dir: 缓存目录

    Returns:
        KnowledgeIndexCache 实例
    """
    return KnowledgeIndexCache(cache_dir=cache_dir)