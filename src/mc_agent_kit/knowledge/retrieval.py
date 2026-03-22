"""
知识检索集成模块

将解析器集成到 KnowledgeBase，支持代码示例搜索。
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mc_agent_kit.knowledge.parsers import CodeExample, CodeExtractor, MarkdownParser
from mc_agent_kit.retrieval.hybrid_search import HybridSearchEngine


@dataclass
class SearchResult:
    """搜索结果"""
    type: str  # api, event, example, guide
    name: str
    description: str
    content: str
    score: float
    source: str = ""
    module: str = ""
    scope: str = ""
    code_examples: list[str] = field(default_factory=list)
    related_apis: list[str] = field(default_factory=list)
    related_events: list[str] = field(default_factory=list)


@dataclass
class CodeExampleSearchResult:
    """代码示例搜索结果"""
    example: CodeExample
    score: float
    matched_apis: list[str] = field(default_factory=list)
    matched_events: list[str] = field(default_factory=list)


class KnowledgeRetrieval:
    """
    知识检索集成类

    提供统一的检索接口，支持：
    - API/事件文档检索
    - 代码示例搜索
    - 混合检索
    """

    def __init__(self, knowledge_base_path: str | None = None):
        """
        初始化知识检索器。

        Args:
            knowledge_base_path: 知识库 JSON 文件路径
        """
        self.knowledge_base_path = knowledge_base_path
        self._api_index: dict[str, Any] = {}
        self._event_index: dict[str, Any] = {}
        self._example_index: dict[str, CodeExample] = {}
        self._hybrid_engine: HybridSearchEngine | None = None
        self._parser = MarkdownParser()
        self._extractor = CodeExtractor()
        self._loaded = False

    def load(self, path: str | None = None) -> None:
        """
        加载知识库索引。

        Args:
            path: 知识库文件路径（可选，覆盖初始化时设置的路径）
        """
        path = path or self.knowledge_base_path
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"知识库文件不存在: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # 加载 API 索引
        for api in data.get("apis", []):
            self._api_index[api["name"]] = api

        # 加载事件索引
        for event in data.get("events", []):
            self._event_index[event["name"]] = event

        # 加载代码示例索引
        for example in data.get("examples", []):
            self._example_index[example["id"]] = CodeExample(
                id=example["id"],
                code=example.get("code", ""),
                language=example.get("language", "python"),
                source=example.get("source", ""),
                description=example.get("description", ""),
                api_names=example.get("api_calls", example.get("api_names", [])),
                event_names=example.get("event_names", []),
                tags=example.get("tags", []),
            )

        self._loaded = True

    def build_from_docs(self, docs_path: str, output_path: str | None = None) -> dict[str, int]:
        """
        从文档目录构建知识库索引。

        Args:
            docs_path: 文档目录路径
            output_path: 输出文件路径（可选）

        Returns:
            统计信息 {"apis": count, "events": count, "examples": count}
        """
        stats = {"apis": 0, "events": 0, "examples": 0}

        docs_dir = Path(docs_path)
        if not docs_dir.exists():
            raise FileNotFoundError(f"文档目录不存在: {docs_path}")

        # 遍历文档
        for md_file in docs_dir.rglob("*.md"):
            try:
                with open(md_file, encoding="utf-8") as f:
                    content = f.read()

                # 解析文档
                parsed = self._parser.parse(content)

                # 提取 API/事件信息
                if parsed.doc_type == "api":
                    for api in parsed.apis:
                        self._api_index[api.name] = {
                            "name": api.name,
                            "description": api.description,
                            "module": api.module,
                            "scope": api.scope,
                            "parameters": [
                                {"name": p.name, "type": p.data_type, "description": p.description}
                                for p in api.parameters
                            ],
                            "return_type": api.return_type,
                            "return_description": api.return_description,
                            "source": str(md_file),
                        }
                        stats["apis"] += 1

                elif parsed.doc_type == "event":
                    for event in parsed.events:
                        self._event_index[event.name] = {
                            "name": event.name,
                            "description": event.description,
                            "module": event.module,
                            "scope": event.scope,
                            "parameters": [
                                {"name": p.name, "type": p.data_type, "description": p.description}
                                for p in event.parameters
                            ],
                            "source": str(md_file),
                        }
                        stats["events"] += 1

                # 提取代码示例
                examples = self._extractor.extract(content)
                for ex in examples:
                    self._example_index[ex.id] = ex
                    stats["examples"] += 1

            except Exception:
                continue

        self._loaded = True

        # 保存索引
        if output_path:
            self.save(output_path)

        return stats

    def save(self, path: str) -> None:
        """
        保存知识库索引到文件。

        Args:
            path: 输出文件路径
        """
        data = {
            "apis": list(self._api_index.values()),
            "events": list(self._event_index.values()),
            "examples": [
                {
                    "id": ex.id,
                    "code": ex.code,
                    "language": ex.language,
                    "description": ex.description,
                    "api_calls": ex.api_names,
                    "event_names": ex.event_names,
                    "tags": ex.tags,
                }
                for ex in self._example_index.values()
            ],
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        搜索知识库。

        Args:
            query: 搜索查询
            search_type: 搜索类型 (api/event/example/all)
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        if not self._loaded:
            raise RuntimeError("知识库未加载，请先调用 load() 方法")

        results = []
        query_lower = query.lower()

        # 搜索 API
        if search_type in ("api", "all"):
            for name, api in self._api_index.items():
                score = self._calculate_score(query_lower, api)
                if score > 0:
                    results.append(SearchResult(
                        type="api",
                        name=api["name"],
                        description=api.get("description", ""),
                        content=self._format_api_content(api),
                        score=score,
                        source=api.get("source", ""),
                        module=api.get("module", ""),
                        scope=api.get("scope", ""),
                        code_examples=api.get("code_examples", []),
                    ))

        # 搜索事件
        if search_type in ("event", "all"):
            for name, event in self._event_index.items():
                score = self._calculate_score(query_lower, event)
                if score > 0:
                    results.append(SearchResult(
                        type="event",
                        name=event["name"],
                        description=event.get("description", ""),
                        content=self._format_event_content(event),
                        score=score,
                        source=event.get("source", ""),
                        module=event.get("module", ""),
                        scope=event.get("scope", ""),
                    ))

        # 搜索代码示例
        if search_type in ("example", "all"):
            for ex_id, example in self._example_index.items():
                score = self._calculate_example_score(query_lower, example)
                if score > 0:
                    results.append(SearchResult(
                        type="example",
                        name=example.description or f"示例 {ex_id}",
                        description=example.description or "",
                        content=example.code,
                        score=score,
                        code_examples=[example.code],
                        related_apis=example.api_names,
                        related_events=example.event_names,
                    ))

        # 排序并返回
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def search_code_examples(
        self,
        query: str,
        api_name: str | None = None,
        event_name: str | None = None,
        limit: int = 10,
    ) -> list[CodeExampleSearchResult]:
        """
        搜索代码示例。

        Args:
            query: 搜索查询
            api_name: 按 API 名称过滤
            event_name: 按事件名称过滤
            limit: 返回结果数量

        Returns:
            代码示例搜索结果列表
        """
        if not self._loaded:
            raise RuntimeError("知识库未加载，请先调用 load() 方法")

        results = []
        query_lower = query.lower()

        for ex_id, example in self._example_index.items():
            # 过滤条件
            if api_name and api_name not in example.api_names:
                continue
            if event_name and event_name not in example.event_names:
                continue

            # 计算分数
            score = self._calculate_example_score(query_lower, example)
            if score > 0:
                results.append(CodeExampleSearchResult(
                    example=example,
                    score=score,
                    matched_apis=[api for api in example.api_names if api.lower() in query_lower],
                    matched_events=[ev for ev in example.event_names if ev.lower() in query_lower],
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def get_api(self, name: str) -> dict[str, Any] | None:
        """
        获取指定 API 信息。

        Args:
            name: API 名称

        Returns:
            API 信息字典，不存在则返回 None
        """
        return self._api_index.get(name)

    def get_event(self, name: str) -> dict[str, Any] | None:
        """
        获取指定事件信息。

        Args:
            name: 事件名称

        Returns:
            事件信息字典，不存在则返回 None
        """
        return self._event_index.get(name)

    def get_related_examples(self, api_name: str | None = None, event_name: str | None = None) -> list[CodeExample]:
        """
        获取与 API 或事件相关的代码示例。

        Args:
            api_name: API 名称
            event_name: 事件名称

        Returns:
            代码示例列表
        """
        results = []
        for example in self._example_index.values():
            if api_name and api_name in example.api_names:
                results.append(example)
            elif event_name and event_name in example.event_names:
                results.append(example)
        return results

    def _calculate_score(self, query: str, item: dict[str, Any]) -> float:
        """计算搜索分数"""
        score = 0.0

        name = item.get("name", "").lower()
        description = item.get("description", "").lower()
        module = item.get("module", "").lower()

        # 名称完全匹配
        if query == name:
            score += 1.0
        # 名称包含查询
        elif query in name:
            score += 0.8
        # 描述包含查询
        elif query in description:
            score += 0.5
        # 模块包含查询
        elif query in module:
            score += 0.3

        return score

    def _calculate_example_score(self, query: str, example: CodeExample) -> float:
        """计算代码示例搜索分数"""
        score = 0.0

        description = (example.description or "").lower()
        code = example.code.lower()

        # 描述匹配
        if query in description:
            score += 0.8

        # 代码内容匹配
        if query in code:
            score += 0.5

        # API 调用匹配
        for api in example.api_names:
            if query in api.lower():
                score += 0.7

        # 事件名称匹配
        for event in example.event_names:
            if query in event.lower():
                score += 0.7

        # 标签匹配
        for tag in example.tags:
            if query in tag.lower():
                score += 0.4

        return score

    def _format_api_content(self, api: dict[str, Any]) -> str:
        """格式化 API 内容"""
        lines = [f"## {api['name']}"]

        if api.get("description"):
            lines.append(f"\n{api['description']}")

        if api.get("module"):
            lines.append(f"\n**模块**: {api['module']}")

        if api.get("scope"):
            lines.append(f"**作用域**: {api['scope']}")

        if api.get("parameters"):
            lines.append("\n### 参数\n")
            for p in api["parameters"]:
                lines.append(f"- `{p['name']}`: {p.get('type', 'unknown')} - {p.get('description', '')}")

        if api.get("return_type"):
            lines.append(f"\n### 返回值\n\n`{api['return_type']}`: {api.get('return_description', '')}")

        return "\n".join(lines)

    def _format_event_content(self, event: dict[str, Any]) -> str:
        """格式化事件内容"""
        lines = [f"## {event['name']}"]

        if event.get("description"):
            lines.append(f"\n{event['description']}")

        if event.get("module"):
            lines.append(f"\n**模块**: {event['module']}")

        if event.get("scope"):
            lines.append(f"**作用域**: {event['scope']}")

        if event.get("parameters"):
            lines.append("\n### 参数\n")
            for p in event["parameters"]:
                lines.append(f"- `{p['name']}`: {p.get('type', 'unknown')} - {p.get('description', '')}")

        return "\n".join(lines)

    @property
    def stats(self) -> dict[str, int]:
        """返回知识库统计信息"""
        return {
            "apis": len(self._api_index),
            "events": len(self._event_index),
            "examples": len(self._example_index),
        }


def create_retrieval(knowledge_base_path: str = "data/knowledge_base.json") -> KnowledgeRetrieval:
    """
    创建知识检索实例的便捷函数。

    Args:
        knowledge_base_path: 知识库文件路径

    Returns:
        KnowledgeRetrieval 实例
    """
    retrieval = KnowledgeRetrieval(knowledge_base_path)
    if os.path.exists(knowledge_base_path):
        retrieval.load()
    return retrieval


# ============================================================
# Iteration #31: Enhanced Knowledge Retrieval
# ============================================================

class EnhancedKnowledgeRetrieval(KnowledgeRetrieval):
    """
    增强知识检索类

    在 KnowledgeRetrieval 基础上添加：
    - 版本过滤
    - 搜索相关性优化
    - 精确匹配加分
    """

    def search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10,
        target_version: str | None = None,
    ) -> list[SearchResult]:
        """
        搜索知识库（增强版）。

        Args:
            query: 搜索查询
            search_type: 搜索类型 (api/event/example/all)
            limit: 返回结果数量
            target_version: 目标游戏版本（可选）

        Returns:
            搜索结果列表
        """
        if not self._loaded:
            raise RuntimeError("知识库未加载，请先调用 load() 方法")

        results = []
        query_lower = query.lower()

        # 搜索 API
        if search_type in ("api", "all"):
            for name, api in self._api_index.items():
                # 版本过滤
                if target_version and "version" in api:
                    compat = self._check_version_compatibility(api["version"], target_version)
                    if not compat:
                        continue

                score = self._calculate_score(query_lower, api)

                # 精确匹配加分
                if query_lower == name.lower():
                    score += 2.0
                elif query_lower in name.lower():
                    score += 1.0

                if score > 0:
                    results.append(SearchResult(
                        type="api",
                        name=api["name"],
                        description=api.get("description", ""),
                        content=self._format_api_content(api),
                        score=score,
                        source=api.get("source", ""),
                        module=api.get("module", ""),
                        scope=api.get("scope", ""),
                        code_examples=api.get("code_examples", []),
                    ))

        # 搜索事件
        if search_type in ("event", "all"):
            for name, event in self._event_index.items():
                score = self._calculate_score(query_lower, event)

                # 精确匹配加分
                if query_lower == name.lower():
                    score += 2.0

                if score > 0:
                    results.append(SearchResult(
                        type="event",
                        name=event["name"],
                        description=event.get("description", ""),
                        content=self._format_event_content(event),
                        score=score,
                        source=event.get("source", ""),
                        module=event.get("module", ""),
                        scope=event.get("scope", ""),
                    ))

        # 排序并返回
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def _check_version_compatibility(self, api_version: str, target_version: str) -> bool:
        """
        检查 API 版本兼容性。

        Args:
            api_version: API 引入版本
            target_version: 目标游戏版本

        Returns:
            是否兼容
        """
        try:
            api_parts = [int(x) for x in api_version.split(".")[:2]]
            target_parts = [int(x) for x in target_version.split(".")[:2]]

            # 目标版本 >= API 版本则兼容
            if target_parts[0] > api_parts[0]:
                return True
            elif target_parts[0] < api_parts[0]:
                return False
            else:
                return target_parts[1] >= api_parts[1]
        except (ValueError, IndexError):
            return True  # 无法解析时默认兼容
