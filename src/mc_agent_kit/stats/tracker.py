"""
API 使用统计追踪器

追踪和统计 API 使用情况，帮助开发者了解热门 API 和问题 API。
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ApiCategory(Enum):
    """API 类别"""
    ENTITY = "entity"
    ITEM = "item"
    BLOCK = "block"
    PLAYER = "player"
    WORLD = "world"
    UI = "ui"
    NETWORK = "network"
    EVENT = "event"
    OTHER = "other"


@dataclass
class UsageRecord:
    """使用记录"""
    api_name: str
    timestamp: str
    success: bool = True
    error_message: str | None = None
    module: str | None = None
    scope: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_name": self.api_name,
            "timestamp": self.timestamp,
            "success": self.success,
            "error_message": self.error_message,
            "module": self.module,
            "scope": self.scope,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageRecord":
        return cls(
            api_name=data["api_name"],
            timestamp=data["timestamp"],
            success=data.get("success", True),
            error_message=data.get("error_message"),
            module=data.get("module"),
            scope=data.get("scope"),
            duration_ms=data.get("duration_ms"),
        )


@dataclass
class ApiUsageStats:
    """API 使用统计"""
    api_name: str
    total_calls: int = 0
    success_count: int = 0
    error_count: int = 0
    last_used: str | None = None
    avg_duration_ms: float | None = None
    common_errors: list[str] = field(default_factory=list)
    related_apis: list[str] = field(default_factory=list)
    category: ApiCategory = ApiCategory.OTHER

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 0.0
        return self.success_count / self.total_calls

    @property
    def error_rate(self) -> float:
        """错误率"""
        return 1.0 - self.success_rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_name": self.api_name,
            "total_calls": self.total_calls,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 4),
            "error_rate": round(self.error_rate, 4),
            "last_used": self.last_used,
            "avg_duration_ms": self.avg_duration_ms,
            "common_errors": self.common_errors[:10],  # 最多 10 个常见错误
            "related_apis": self.related_apis[:10],
            "category": self.category.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiUsageStats":
        return cls(
            api_name=data["api_name"],
            total_calls=data.get("total_calls", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0),
            last_used=data.get("last_used"),
            avg_duration_ms=data.get("avg_duration_ms"),
            common_errors=data.get("common_errors", []),
            related_apis=data.get("related_apis", []),
            category=ApiCategory(data.get("category", "other")),
        )


class ApiUsageTracker:
    """
    API 使用追踪器

    追踪 API 使用情况，生成统计报告，识别热门 API 和问题 API。
    """

    def __init__(self, storage_path: str | None = None):
        """
        初始化追踪器。

        Args:
            storage_path: 统计数据存储路径
        """
        self.storage_path = storage_path
        self._stats: dict[str, ApiUsageStats] = {}
        self._records: list[UsageRecord] = []
        self._module_mapping: dict[str, str] = {}

        # 加载已保存的数据
        if storage_path and os.path.exists(storage_path):
            self.load(storage_path)

    def record(
        self,
        api_name: str,
        success: bool = True,
        error_message: str | None = None,
        module: str | None = None,
        scope: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """
        记录一次 API 调用。

        Args:
            api_name: API 名称
            success: 是否成功
            error_message: 错误信息
            module: 所属模块
            scope: 作用域
            duration_ms: 调用耗时（毫秒）
        """
        timestamp = datetime.now().isoformat()

        # 创建使用记录
        record = UsageRecord(
            api_name=api_name,
            timestamp=timestamp,
            success=success,
            error_message=error_message,
            module=module,
            scope=scope,
            duration_ms=duration_ms,
        )
        self._records.append(record)

        # 更新统计
        if api_name not in self._stats:
            self._stats[api_name] = ApiUsageStats(api_name=api_name)

        stats = self._stats[api_name]
        stats.total_calls += 1
        stats.last_used = timestamp

        if success:
            stats.success_count += 1
        else:
            stats.error_count += 1
            if error_message and error_message not in stats.common_errors:
                stats.common_errors.append(error_message)

        # 更新平均耗时
        if duration_ms is not None:
            if stats.avg_duration_ms is None:
                stats.avg_duration_ms = duration_ms
            else:
                # 简单移动平均
                stats.avg_duration_ms = (
                    stats.avg_duration_ms * (stats.total_calls - 1) + duration_ms
                ) / stats.total_calls

        # 更新模块映射
        if module:
            self._module_mapping[api_name] = module

    def get_stats(self, api_name: str) -> ApiUsageStats | None:
        """
        获取指定 API 的统计数据。

        Args:
            api_name: API 名称

        Returns:
            统计数据，如果不存在返回 None
        """
        return self._stats.get(api_name)

    def get_all_stats(self) -> dict[str, ApiUsageStats]:
        """
        获取所有 API 的统计数据。

        Returns:
            API 名称到统计数据的映射
        """
        return self._stats.copy()

    def get_hot_apis(self, limit: int = 10) -> list[ApiUsageStats]:
        """
        获取热门 API（调用次数最多）。

        Args:
            limit: 返回数量

        Returns:
            热门 API 列表
        """
        sorted_stats = sorted(
            self._stats.values(),
            key=lambda s: s.total_calls,
            reverse=True,
        )
        return sorted_stats[:limit]

    def get_problematic_apis(
        self,
        min_calls: int = 5,
        error_rate_threshold: float = 0.3,
        limit: int = 10,
    ) -> list[ApiUsageStats]:
        """
        获取问题 API（错误率高）。

        Args:
            min_calls: 最小调用次数阈值
            error_rate_threshold: 错误率阈值
            limit: 返回数量

        Returns:
            问题 API 列表
        """
        problematic = [
            stats
            for stats in self._stats.values()
            if stats.total_calls >= min_calls
            and stats.error_rate >= error_rate_threshold
        ]

        sorted_stats = sorted(
            problematic,
            key=lambda s: s.error_rate,
            reverse=True,
        )
        return sorted_stats[:limit]

    def get_recent_errors(self, limit: int = 20) -> list[UsageRecord]:
        """
        获取最近的错误记录。

        Args:
            limit: 返回数量

        Returns:
            错误记录列表
        """
        errors = [r for r in self._records if not r.success]
        return errors[-limit:]

    def get_stats_by_module(self) -> dict[str, list[ApiUsageStats]]:
        """
        按模块分组获取统计。

        Returns:
            模块名到统计列表的映射
        """
        by_module: dict[str, list[ApiUsageStats]] = {}

        for api_name, stats in self._stats.items():
            module = self._module_mapping.get(api_name, "unknown")
            if module not in by_module:
                by_module[module] = []
            by_module[module].append(stats)

        return by_module

    def get_summary(self) -> dict[str, Any]:
        """
        获取统计摘要。

        Returns:
            统计摘要
        """
        total_apis = len(self._stats)
        total_calls = sum(s.total_calls for s in self._stats.values())
        total_success = sum(s.success_count for s in self._stats.values())
        total_errors = sum(s.error_count for s in self._stats.values())

        return {
            "total_apis": total_apis,
            "total_calls": total_calls,
            "total_success": total_success,
            "total_errors": total_errors,
            "success_rate": round(total_success / total_calls, 4) if total_calls > 0 else 0,
            "hot_apis": [s.to_dict() for s in self.get_hot_apis(5)],
            "problematic_apis": [s.to_dict() for s in self.get_problematic_apis(5)],
        }

    def save(self, path: str | None = None) -> None:
        """
        保存统计数据到文件。

        Args:
            path: 保存路径，默认使用初始化时的路径
        """
        save_path = path or self.storage_path
        if not save_path:
            return

        data = {
            "stats": {name: stats.to_dict() for name, stats in self._stats.items()},
            "records": [r.to_dict() for r in self._records[-1000:]],  # 只保存最近 1000 条记录
            "module_mapping": self._module_mapping,
        }

        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        """
        从文件加载统计数据。

        Args:
            path: 加载路径
        """
        if not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self._stats = {
            name: ApiUsageStats.from_dict(stats_data)
            for name, stats_data in data.get("stats", {}).items()
        }
        self._records = [
            UsageRecord.from_dict(record_data)
            for record_data in data.get("records", [])
        ]
        self._module_mapping = data.get("module_mapping", {})

    def clear(self) -> None:
        """清空所有统计数据"""
        self._stats.clear()
        self._records.clear()
        self._module_mapping.clear()