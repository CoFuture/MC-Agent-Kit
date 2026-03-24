"""
知识库索引构建器

扫描 ModSDK 文档目录，解析所有文档，构建知识库索引。
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any

from .models import APIEntry, EnumEntry, EventEntry, KnowledgeBase
from .parser import MarkdownParser

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """知识库索引构建器

    负责扫描文档目录，解析所有 Markdown 文档，构建结构化的知识库索引。

    使用示例:
        indexer = KnowledgeIndexer()
        kb = indexer.build("path/to/docs")
        print(kb.stats())
    """

    def __init__(self) -> None:
        self.parser = MarkdownParser()
        self.kb = KnowledgeBase()

    def build(self, docs_dir: str, output_path: str | None = None) -> KnowledgeBase:
        """构建知识库索引

        Args:
            docs_dir: 文档目录路径
            output_path: 可选的输出文件路径（JSON 格式）

        Returns:
            构建的知识库对象
        """
        docs_path = Path(docs_dir)
        if not docs_path.exists():
            raise FileNotFoundError(f"文档目录不存在: {docs_dir}")

        self.kb = KnowledgeBase(source_dir=str(docs_path))

        # 扫描所有 Markdown 文件
        md_files = list(docs_path.rglob("*.md"))
        logger.info(f"找到 {len(md_files)} 个 Markdown 文件")

        # 解析每个文件
        for md_file in md_files:
            try:
                self._process_file(md_file)
            except Exception as e:
                logger.error(f"解析文件失败 {md_file}: {e}")

        logger.info(f"知识库构建完成: {self.kb.stats()}")

        # 可选：保存到文件
        if output_path:
            self.save(output_path)

        return self.kb

    def _process_file(self, file_path: Path) -> None:
        """处理单个文档文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(f"文件编码问题，尝试其他编码: {file_path}")
            content = file_path.read_text(encoding="gbk")

        relative_path = (
            str(file_path.relative_to(self.kb.source_dir))
            if self.kb.source_dir
            else str(file_path)
        )

        entries = self.parser.parse(content, relative_path)

        for entry in entries:
            if isinstance(entry, APIEntry):
                self.kb.add_api(entry)
                logger.debug(f"添加 API: {entry.name}")
            elif isinstance(entry, EventEntry):
                self.kb.add_event(entry)
                logger.debug(f"添加事件: {entry.name}")
            elif isinstance(entry, EnumEntry):
                self.kb.add_enum(entry)
                logger.debug(f"添加枚举: {entry.name}")

    def save(self, output_path: str) -> None:
        """保存知识库到 JSON 文件

        Args:
            output_path: 输出文件路径
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(self.kb.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"知识库已保存到: {output_path}")

    def load(self, input_path: str) -> KnowledgeBase:
        """从 JSON 文件加载知识库

        Args:
            input_path: 输入文件路径

        Returns:
            加载的知识库对象
        """
        with open(input_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        self.kb = KnowledgeBase(
            version=data.get("version", "1.0.0"),
            source_dir=data.get("source_dir"),
        )

        # 加载 API
        for name, api_data in data.get("apis", {}).items():
            from .models import APIParameter, Scope

            api = APIEntry(
                name=api_data["name"],
                module=api_data["module"],
                description=api_data["description"],
                method_path=api_data.get("method_path", ""),
                scope=Scope(api_data.get("scope", "unknown")),
                parameters=[
                    APIParameter(
                        name=p["name"],
                        data_type=p["data_type"],
                        description=p["description"],
                        optional=p.get("optional", False),
                    )
                    for p in api_data.get("parameters", [])
                ],
                return_type=api_data.get("return_type"),
                return_description=api_data.get("return_description"),
                remarks=api_data.get("remarks", []),
                source_path=api_data.get("source_path"),
            )
            self.kb.add_api(api)

        # 加载事件
        for name, event_data in data.get("events", {}).items():
            from .models import EventParameter, Scope

            event = EventEntry(
                name=event_data["name"],
                module=event_data["module"],
                description=event_data["description"],
                scope=Scope(event_data.get("scope", "unknown")),
                parameters=[
                    EventParameter(
                        name=p["name"],
                        data_type=p["data_type"],
                        description=p["description"],
                        mutable=p.get("mutable", False),
                    )
                    for p in event_data.get("parameters", [])
                ],
                return_value=event_data.get("return_value"),
                remarks=event_data.get("remarks", []),
                source_path=event_data.get("source_path"),
            )
            self.kb.add_event(event)

        # 加载枚举
        for name, enum_data in data.get("enums", {}).items():
            from .models import EnumValue

            enum = EnumEntry(
                name=enum_data["name"],
                description=enum_data.get("description"),
                values=[
                    EnumValue(
                        name=v["name"],
                        value=v["value"],
                        description=v.get("description"),
                    )
                    for v in enum_data.get("values", [])
                ],
                source_path=enum_data.get("source_path"),
            )
            self.kb.add_enum(enum)

        logger.info(f"知识库已加载: {self.kb.stats()}")
        return self.kb

    def get_kb(self) -> KnowledgeBase:
        """获取当前知识库"""
        return self.kb


def build_knowledge_base(docs_dir: str, output_path: str | None = None) -> KnowledgeBase:
    """构建知识库的便捷函数

    Args:
        docs_dir: 文档目录路径
        output_path: 可选的输出文件路径

    Returns:
        构建的知识库对象
    """
    indexer = KnowledgeIndexer()
    return indexer.build(docs_dir, output_path)
