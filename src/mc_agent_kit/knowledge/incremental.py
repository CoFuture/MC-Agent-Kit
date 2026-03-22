"""
知识库增量更新模块

支持文档变更检测和增量向量化。
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DocumentChange:
    """文档变更记录"""

    path: str
    change_type: str  # "added", "modified", "deleted"
    old_hash: str | None = None
    new_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeReport:
    """变更报告"""

    added: list[DocumentChange] = field(default_factory=list)
    modified: list[DocumentChange] = field(default_factory=list)
    deleted: list[DocumentChange] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted)

    @property
    def has_changes(self) -> bool:
        return self.total_changes > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "added": [{"path": c.path, "hash": c.new_hash} for c in self.added],
            "modified": [{"path": c.path, "old_hash": c.old_hash, "new_hash": c.new_hash} for c in self.modified],
            "deleted": [{"path": c.path, "hash": c.old_hash} for c in self.deleted],
            "total_changes": self.total_changes,
        }


class IncrementalUpdater:
    """
    增量更新器

    检测文档变更，支持增量更新向量索引。

    使用示例:
        updater = IncrementalUpdater(state_dir="./data/state")

        # 检测变更
        changes = updater.detect_changes("./docs")

        # 应用变更
        if changes.has_changes:
            updater.apply_changes(changes, vector_store)
    """

    STATE_FILE = "document_state.json"

    def __init__(self, state_dir: str = "./data/state"):
        """
        初始化增量更新器

        Args:
            state_dir: 状态文件目录
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, str] = {}  # path -> hash
        self._load_state()

    def _state_path(self) -> Path:
        """获取状态文件路径"""
        return self.state_dir / self.STATE_FILE

    def _load_state(self) -> None:
        """加载已有状态"""
        state_file = self._state_path()
        if state_file.exists():
            try:
                with open(state_file, encoding="utf-8") as f:
                    self._state = json.load(f)
                logger.info(f"加载了 {len(self._state)} 个文档状态")
            except Exception as e:
                logger.warning(f"加载状态失败: {e}")
                self._state = {}

    def _save_state(self) -> None:
        """保存状态"""
        state_file = self._state_path()
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(self._state)} 个文档状态")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()

    def _compute_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        content = file_path.read_text(encoding="utf-8")
        return self._compute_hash(content)

    def detect_changes(
        self,
        docs_path: str,
        extensions: list[str] | None = None,
    ) -> ChangeReport:
        """
        检测文档变更

        Args:
            docs_path: 文档目录路径
            extensions: 文件扩展名列表，默认 [".md", ".txt"]

        Returns:
            变更报告
        """
        extensions = extensions or [".md", ".txt"]
        docs_dir = Path(docs_path)

        report = ChangeReport()

        # 扫描当前文件
        current_files: dict[str, str] = {}

        for ext in extensions:
            for file_path in docs_dir.rglob(f"*{ext}"):
                try:
                    file_hash = self._compute_file_hash(file_path)
                    relative_path = str(file_path.relative_to(docs_dir))
                    current_files[relative_path] = file_hash
                except Exception as e:
                    logger.warning(f"处理文件失败: {file_path}, 错误: {e}")

        # 检测新增和修改
        for path, new_hash in current_files.items():
            old_hash = self._state.get(path)

            if old_hash is None:
                # 新增
                report.added.append(DocumentChange(
                    path=path,
                    change_type="added",
                    new_hash=new_hash,
                ))
            elif old_hash != new_hash:
                # 修改
                report.modified.append(DocumentChange(
                    path=path,
                    change_type="modified",
                    old_hash=old_hash,
                    new_hash=new_hash,
                ))

        # 检测删除
        for path in self._state:
            if path not in current_files:
                report.deleted.append(DocumentChange(
                    path=path,
                    change_type="deleted",
                    old_hash=self._state[path],
                ))

        logger.info(f"变更检测完成: 新增 {len(report.added)}, 修改 {len(report.modified)}, 删除 {len(report.deleted)}")

        return report

    def apply_changes(
        self,
        changes: ChangeReport,
        docs_path: str,
        vector_store,  # VectorStore 实例
    ) -> int:
        """
        应用变更到向量存储

        Args:
            changes: 变更报告
            docs_path: 文档目录路径
            vector_store: 向量存储实例

        Returns:
            实际更新的文档数量
        """
        docs_dir = Path(docs_path)
        updated_count = 0

        # 处理删除
        if changes.deleted:
            delete_ids = [c.path for c in changes.deleted]
            vector_store.delete_documents(delete_ids)

            for c in changes.deleted:
                self._state.pop(c.path, None)

            updated_count += len(changes.deleted)

        # 处理新增和修改
        docs_to_add = []

        for c in changes.added + changes.modified:
            file_path = docs_dir / c.path
            try:
                content = file_path.read_text(encoding="utf-8")

                # 创建文档对象
                from mc_agent_kit.retrieval.vector_store import Document
                doc = Document(
                    id=c.path,
                    content=content,
                    metadata={
                        "source": c.path,
                        "content_hash": c.new_hash,
                    },
                )
                docs_to_add.append(doc)

                # 更新状态
                self._state[c.path] = c.new_hash

            except Exception as e:
                logger.warning(f"读取文件失败: {c.path}, 错误: {e}")

        # 批量添加到向量存储
        if docs_to_add:
            added = vector_store.add_documents(docs_to_add)
            updated_count += added

        # 保存状态
        self._save_state()

        logger.info(f"应用变更完成: 更新了 {updated_count} 个文档")

        return updated_count

    def get_document_state(self, path: str) -> str | None:
        """获取文档状态"""
        return self._state.get(path)

    def get_all_states(self) -> dict[str, str]:
        """获取所有文档状态"""
        return self._state.copy()

    def clear_state(self) -> None:
        """清空状态"""
        self._state.clear()
        self._save_state()

    def rebuild_state(self, docs_path: str, extensions: list[str] | None = None) -> int:
        """
        重建状态（从头开始）

        Args:
            docs_path: 文档目录路径
            extensions: 文件扩展名列表

        Returns:
            文档数量
        """
        self._state.clear()

        extensions = extensions or [".md", ".txt"]
        docs_dir = Path(docs_path)

        count = 0
        for ext in extensions:
            for file_path in docs_dir.rglob(f"*{ext}"):
                try:
                    file_hash = self._compute_file_hash(file_path)
                    relative_path = str(file_path.relative_to(docs_dir))
                    self._state[relative_path] = file_hash
                    count += 1
                except Exception as e:
                    logger.warning(f"处理文件失败: {file_path}, 错误: {e}")

        self._save_state()
        logger.info(f"重建状态完成: {count} 个文档")

        return count


def create_incremental_updater(state_dir: str = "./data/state") -> IncrementalUpdater:
    """
    创建增量更新器的便捷函数

    Args:
        state_dir: 状态文件目录

    Returns:
        初始化好的增量更新器
    """
    return IncrementalUpdater(state_dir)
