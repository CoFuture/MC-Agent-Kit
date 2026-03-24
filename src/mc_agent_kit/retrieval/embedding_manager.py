"""
Embedding 管理器模块

支持多种 Embedding 模型、模型切换、批量生成和缓存。
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingModelType(Enum):
    """Embedding 模型类型"""
    BGE_LARGE_ZH = "bge-large-zh"       # BGE 大模型中文
    BGE_BASE_ZH = "bge-base-zh"         # BGE 基础模型中文
    M3E_BASE = "m3e-base"               # M3E 基础模型
    M3E_LARGE = "m3e-large"             # M3E 大模型
    TEXT2VEC = "text2vec"               # Text2Vec
    OPENAI = "openai"                   # OpenAI Embedding
    AZURE = "azure"                     # Azure OpenAI
    LOCAL = "local"                     # 本地模型
    MOCK = "mock"                       # Mock 模型（测试用）


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"                         # 最近最少使用
    LFU = "lfu"                         # 最不经常使用
    FIFO = "fifo"                       # 先进先出
    TTL = "ttl"                         # 基于时间过期


@dataclass
class EmbeddingConfig:
    """Embedding 配置"""
    model_type: EmbeddingModelType = EmbeddingModelType.BGE_LARGE_ZH
    model_path: str | None = None
    dimension: int = 1024
    max_batch_size: int = 32
    normalize: bool = True
    cache_enabled: bool = True
    cache_size: int = 10000
    cache_ttl: int = 3600              # 缓存过期时间（秒）
    fallback_model: EmbeddingModelType | None = EmbeddingModelType.MOCK
    timeout: float = 30.0


@dataclass
class EmbeddingResult:
    """Embedding 结果"""
    text: str
    embedding: list[float]
    model_type: EmbeddingModelType
    dimension: int
    processing_time: float
    cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "embedding_dim": len(self.embedding),
            "model_type": self.model_type.value,
            "dimension": self.dimension,
            "processing_time": self.processing_time,
            "cached": self.cached,
            "metadata": self.metadata,
        }


@dataclass
class BatchEmbeddingResult:
    """批量 Embedding 结果"""
    results: list[EmbeddingResult]
    total_texts: int
    success_count: int
    failure_count: int
    total_time: float
    avg_time_per_text: float
    cache_hits: int
    cache_misses: int

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_texts": self.total_texts,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_time": self.total_time,
            "avg_time_per_text": self.avg_time_per_text,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }


@dataclass
class CacheEntry:
    """缓存条目"""
    text_hash: str
    embedding: list[float]
    model_type: EmbeddingModelType
    created_at: float
    last_accessed: float
    access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "text_hash": self.text_hash,
            "embedding_dim": len(self.embedding),
            "model_type": self.model_type.value,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
        }


class EmbeddingModel(ABC):
    """Embedding 模型基类"""

    def __init__(self, config: EmbeddingConfig) -> None:
        """初始化模型"""
        self.config = config

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """生成单个文本的嵌入向量"""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度"""
        pass


class MockEmbeddingModel(EmbeddingModel):
    """Mock Embedding 模型（用于测试）"""

    def embed(self, text: str) -> list[float]:
        """生成模拟嵌入向量"""
        import random
        # 基于文本生成确定性向量
        random.seed(hash(text) % (2**32))
        embedding = [random.gauss(0, 1) for _ in range(self.config.dimension)]
        if self.config.normalize:
            norm = sum(x * x for x in embedding) ** 0.5
            embedding = [x / norm for x in embedding]
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成模拟嵌入向量"""
        return [self.embed(text) for text in texts]

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.config.dimension


class LocalEmbeddingModel(EmbeddingModel):
    """本地 Embedding 模型"""

    def __init__(self, config: EmbeddingConfig) -> None:
        """初始化本地模型"""
        super().__init__(config)
        self._model: Any = None
        self._initialized = False

    def _initialize_model(self) -> None:
        """初始化模型（延迟加载）"""
        if self._initialized:
            return

        try:
            # 尝试导入 sentence-transformers
            from sentence_transformers import SentenceTransformer

            model_path = self.config.model_path or self._get_default_model_path()
            self._model = SentenceTransformer(model_path)
            self._initialized = True
            logger.info(f"本地 Embedding 模型加载成功: {model_path}")

        except ImportError:
            logger.warning("sentence-transformers 未安装，使用 Mock 模型")
            self._model = MockEmbeddingModel(self.config)
            self._initialized = True

        except Exception as e:
            logger.error(f"加载本地模型失败: {e}，使用 Mock 模型")
            self._model = MockEmbeddingModel(self.config)
            self._initialized = True

    def _get_default_model_path(self) -> str:
        """获取默认模型路径"""
        model_paths = {
            EmbeddingModelType.BGE_LARGE_ZH: "BAAI/bge-large-zh-v1.5",
            EmbeddingModelType.BGE_BASE_ZH: "BAAI/bge-base-zh-v1.5",
            EmbeddingModelType.M3E_BASE: "moka-ai/m3e-base",
            EmbeddingModelType.M3E_LARGE: "moka-ai/m3e-large",
            EmbeddingModelType.TEXT2VEC: "shibing624/text2vec-base-chinese",
        }
        return model_paths.get(self.config.model_type, "BAAI/bge-large-zh-v1.5")

    def embed(self, text: str) -> list[float]:
        """生成嵌入向量"""
        self._initialize_model()

        if hasattr(self._model, "encode"):
            embedding = self._model.encode(text, normalize_embeddings=self.config.normalize)
            return embedding.tolist()
        else:
            return self._model.embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量"""
        self._initialize_model()

        if hasattr(self._model, "encode"):
            embeddings = self._model.encode(texts, normalize_embeddings=self.config.normalize)
            return [e.tolist() for e in embeddings]
        else:
            return self._model.embed_batch(texts)

    def get_dimension(self) -> int:
        """获取向量维度"""
        self._initialize_model()

        if hasattr(self._model, "get_sentence_embedding_dimension"):
            return self._model.get_sentence_embedding_dimension()
        else:
            return self._model.get_dimension()


class EmbeddingCache:
    """Embedding 缓存

    支持多种缓存策略。
    """

    def __init__(
        self,
        max_size: int = 10000,
        ttl: int = 3600,
        strategy: CacheStrategy = CacheStrategy.LRU,
    ) -> None:
        """初始化缓存"""
        self._max_size = max_size
        self._ttl = ttl
        self._strategy = strategy
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def get(self, text_hash: str, model_type: EmbeddingModelType) -> list[float] | None:
        """获取缓存"""
        with self._lock:
            key = f"{model_type.value}:{text_hash}"
            entry = self._cache.get(key)

            if not entry:
                self._stats["misses"] += 1
                return None

            # 检查 TTL
            if time.time() - entry.created_at > self._ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # 更新访问信息
            entry.last_accessed = time.time()
            entry.access_count += 1

            # 更新 LRU 顺序
            if self._strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry.embedding

    def set(
        self,
        text_hash: str,
        embedding: list[float],
        model_type: EmbeddingModelType,
    ) -> None:
        """设置缓存"""
        with self._lock:
            key = f"{model_type.value}:{text_hash}"

            # 检查是否需要淘汰
            while len(self._cache) >= self._max_size:
                self._evict()

            entry = CacheEntry(
                text_hash=text_hash,
                embedding=embedding,
                model_type=model_type,
                created_at=time.time(),
                last_accessed=time.time(),
            )

            self._cache[key] = entry

    def _evict(self) -> None:
        """淘汰条目"""
        if not self._cache:
            return

        if self._strategy == CacheStrategy.LRU:
            # 淘汰最旧的
            self._cache.popitem(last=False)
        elif self._strategy == CacheStrategy.LFU:
            # 淘汰访问次数最少的
            min_key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
            del self._cache[min_key]
        elif self._strategy == CacheStrategy.FIFO:
            # 淘汰最早加入的
            self._cache.popitem(last=False)
        elif self._strategy == CacheStrategy.TTL:
            # 淘汰最早创建的
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]

        self._stats["evictions"] += 1

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": hit_rate,
                "strategy": self._strategy.value,
            }


class EmbeddingManager:
    """Embedding 管理器

    管理多个 Embedding 模型，支持切换和回退。

    使用示例:
        manager = EmbeddingManager()
        manager.register_model(EmbeddingModelType.BGE_LARGE_ZH, LocalEmbeddingModel(config))
        embedding = manager.embed("测试文本")
    """

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        """初始化 Embedding 管理器"""
        self.config = config or EmbeddingConfig()
        self._models: dict[EmbeddingModelType, EmbeddingModel] = {}
        self._cache: EmbeddingCache | None = None
        self._lock = threading.RLock()

        # 初始化缓存
        if self.config.cache_enabled:
            self._cache = EmbeddingCache(
                max_size=self.config.cache_size,
                ttl=self.config.cache_ttl,
            )

        # 注册 Mock 模型作为后备
        self.register_model(EmbeddingModelType.MOCK, MockEmbeddingModel(self.config))

    def register_model(
        self,
        model_type: EmbeddingModelType,
        model: EmbeddingModel,
    ) -> None:
        """注册模型"""
        with self._lock:
            self._models[model_type] = model
            logger.info(f"注册 Embedding 模型: {model_type.value}")

    def get_model(self, model_type: EmbeddingModelType | None = None) -> EmbeddingModel:
        """获取模型"""
        model_type = model_type or self.config.model_type

        model = self._models.get(model_type)
        if model:
            return model

        # 尝试回退模型
        if self.config.fallback_model:
            fallback = self._models.get(self.config.fallback_model)
            if fallback:
                logger.warning(f"模型 {model_type.value} 不可用，使用回退模型")
                return fallback

        # 返回 Mock 模型
        return self._models[EmbeddingModelType.MOCK]

    def embed(
        self,
        text: str,
        model_type: EmbeddingModelType | None = None,
    ) -> EmbeddingResult:
        """生成单个文本的嵌入向量"""
        start_time = time.time()
        model_type = model_type or self.config.model_type

        # 检查缓存
        text_hash = self._compute_hash(text)
        if self._cache:
            cached = self._cache.get(text_hash, model_type)
            if cached:
                return EmbeddingResult(
                    text=text,
                    embedding=cached,
                    model_type=model_type,
                    dimension=len(cached),
                    processing_time=time.time() - start_time,
                    cached=True,
                )

        # 生成嵌入向量
        model = self.get_model(model_type)
        embedding = model.embed(text)

        # 存入缓存
        if self._cache:
            self._cache.set(text_hash, embedding, model_type)

        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model_type=model_type,
            dimension=len(embedding),
            processing_time=time.time() - start_time,
            cached=False,
        )

    def embed_batch(
        self,
        texts: list[str],
        model_type: EmbeddingModelType | None = None,
    ) -> BatchEmbeddingResult:
        """批量生成嵌入向量"""
        start_time = time.time()
        model_type = model_type or self.config.model_type

        results: list[EmbeddingResult] = []
        cache_hits = 0
        cache_misses = 0
        success_count = 0
        failure_count = 0

        # 分离缓存命中和未命中的文本
        cached_embeddings: dict[int, list[float]] = {}
        uncached_texts: list[tuple[int, str]] = []

        for i, text in enumerate(texts):
            text_hash = self._compute_hash(text)

            if self._cache:
                cached = self._cache.get(text_hash, model_type)
                if cached:
                    cached_embeddings[i] = cached
                    cache_hits += 1
                    continue

            uncached_texts.append((i, text))
            cache_misses += 1

        # 批量生成未缓存的嵌入向量
        if uncached_texts:
            model = self.get_model(model_type)

            # 分批处理
            batch_size = self.config.max_batch_size
            for batch_start in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[batch_start:batch_start + batch_size]
                batch_texts = [t[1] for t in batch]
                batch_indices = [t[0] for t in batch]

                try:
                    embeddings = model.embed_batch(batch_texts)

                    for j, (idx, text) in enumerate(batch):
                        if j < len(embeddings):
                            embedding = embeddings[j]

                            # 存入缓存
                            if self._cache:
                                text_hash = self._compute_hash(text)
                                self._cache.set(text_hash, embedding, model_type)

                            cached_embeddings[idx] = embedding
                            success_count += 1
                        else:
                            failure_count += 1

                except Exception as e:
                    logger.error(f"批量生成嵌入向量失败: {e}")
                    failure_count += len(batch)

        # 组装结果
        for i, text in enumerate(texts):
            embedding = cached_embeddings.get(i)
            if embedding:
                results.append(EmbeddingResult(
                    text=text,
                    embedding=embedding,
                    model_type=model_type,
                    dimension=len(embedding),
                    processing_time=0,  # 批量处理，单独时间为 0
                    cached=i in [t[0] for t in uncached_texts[:cache_misses]],
                ))

        total_time = time.time() - start_time

        return BatchEmbeddingResult(
            results=results,
            total_texts=len(texts),
            success_count=success_count,
            failure_count=failure_count,
            total_time=total_time,
            avg_time_per_text=total_time / len(texts) if texts else 0,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
        )

    def get_available_models(self) -> list[EmbeddingModelType]:
        """获取可用的模型列表"""
        return list(self._models.keys())

    def switch_model(self, model_type: EmbeddingModelType) -> bool:
        """切换模型"""
        if model_type in self._models:
            self.config.model_type = model_type
            logger.info(f"切换到 Embedding 模型: {model_type.value}")
            return True
        return False

    def get_cache_stats(self) -> dict[str, Any] | None:
        """获取缓存统计"""
        if self._cache:
            return self._cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """清空缓存"""
        if self._cache:
            self._cache.clear()

    def _compute_hash(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()


# 全局实例
_manager: EmbeddingManager | None = None


def get_embedding_manager() -> EmbeddingManager:
    """获取全局 Embedding 管理器"""
    global _manager
    if _manager is None:
        _manager = EmbeddingManager()
    return _manager


def embed(text: str, model_type: EmbeddingModelType | None = None) -> list[float]:
    """便捷函数：生成嵌入向量"""
    manager = get_embedding_manager()
    result = manager.embed(text, model_type)
    return result.embedding


def embed_batch(texts: list[str], model_type: EmbeddingModelType | None = None) -> list[list[float]]:
    """便捷函数：批量生成嵌入向量"""
    manager = get_embedding_manager()
    result = manager.embed_batch(texts, model_type)
    return [r.embedding for r in result.results]