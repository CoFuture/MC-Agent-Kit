"""
增量学习模块

提供从对话中持续学习新知识、自动验证知识有效性、知识版本管理和知识来源追踪。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class KnowledgeType(Enum):
    """知识类型"""
    API_USAGE = "api_usage"           # API 用法
    BEST_PRACTICE = "best_practice"   # 最佳实践
    PATTERN = "pattern"               # 代码模式
    FIX = "fix"                       # 错误修复
    TIP = "tip"                       # 开发技巧
    SNIPPET = "snippet"               # 代码片段
    CONSTRAINT = "constraint"         # 约束条件
    RELATION = "relation"             # API 关系


class KnowledgeSource(Enum):
    """知识来源"""
    CONVERSATION = "conversation"     # 对话
    DOCUMENTATION = "documentation"   # 文档
    EXAMPLE_CODE = "example_code"     # 示例代码
    USER_FEEDBACK = "user_feedback"   # 用户反馈
    INFERENCE = "inference"           # 推断
    EXTERNAL = "external"             # 外部导入


class KnowledgeStatus(Enum):
    """知识状态"""
    PENDING = "pending"               # 待验证
    VERIFIED = "verified"             # 已验证
    DEPRECATED = "deprecated"         # 已废弃
    INVALID = "invalid"               # 无效
    MERGED = "merged"                 # 已合并


@dataclass
class LearnedKnowledge:
    """学习到的知识"""
    id: str
    knowledge_type: KnowledgeType
    content: str
    source: KnowledgeSource
    confidence: float = 1.0
    verified: bool = False
    status: KnowledgeStatus = KnowledgeStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    usage_count: int = 0
    feedback_score: float = 0.0
    feedback_count: int = 0
    source_conversation_id: str = ""
    source_entry_id: str = ""
    version: int = 1
    parent_id: str = ""  # 如果是更新版本，记录父知识 ID
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    related_apis: list[str] = field(default_factory=list)
    related_events: list[str] = field(default_factory=list)
    code_example: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "knowledge_type": self.knowledge_type.value,
            "content": self.content,
            "source": self.source.value,
            "confidence": self.confidence,
            "verified": self.verified,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
            "feedback_score": self.feedback_score,
            "feedback_count": self.feedback_count,
            "source_conversation_id": self.source_conversation_id,
            "source_entry_id": self.source_entry_id,
            "version": self.version,
            "parent_id": self.parent_id,
            "tags": self.tags,
            "metadata": self.metadata,
            "related_apis": self.related_apis,
            "related_events": self.related_events,
            "code_example": self.code_example,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearnedKnowledge":
        """从字典创建"""
        return cls(
            id=data["id"],
            knowledge_type=KnowledgeType(data["knowledge_type"]),
            content=data["content"],
            source=KnowledgeSource(data["source"]),
            confidence=data.get("confidence", 1.0),
            verified=data.get("verified", False),
            status=KnowledgeStatus(data.get("status", "pending")),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            usage_count=data.get("usage_count", 0),
            feedback_score=data.get("feedback_score", 0.0),
            feedback_count=data.get("feedback_count", 0),
            source_conversation_id=data.get("source_conversation_id", ""),
            source_entry_id=data.get("source_entry_id", ""),
            version=data.get("version", 1),
            parent_id=data.get("parent_id", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            related_apis=data.get("related_apis", []),
            related_events=data.get("related_events", []),
            code_example=data.get("code_example", ""),
        )


@dataclass
class ExtractionResult:
    """提取结果"""
    knowledge_list: list[LearnedKnowledge]
    extraction_time: float
    source_length: int
    success_rate: float

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_list": [k.to_dict() for k in self.knowledge_list],
            "extraction_time": self.extraction_time,
            "source_length": self.source_length,
            "success_rate": self.success_rate,
        }


@dataclass
class VerificationResult:
    """验证结果"""
    knowledge_id: str
    is_valid: bool
    confidence: float
    error_message: str = ""
    test_result: str = ""
    verified_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "error_message": self.error_message,
            "test_result": self.test_result,
            "verified_at": self.verified_at,
        }


@dataclass
class KnowledgeVersion:
    """知识版本"""
    version: int
    knowledge_id: str
    content: str
    created_at: float
    change_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "knowledge_id": self.knowledge_id,
            "content": self.content,
            "created_at": self.created_at,
            "change_description": self.change_description,
        }


class KnowledgeExtractor:
    """知识提取器

    从对话内容中提取新知识。
    """

    def __init__(self) -> None:
        """初始化知识提取器"""
        self._patterns = self._load_patterns()
        self._lock = threading.Lock()

    def extract(
        self,
        conversation: list[dict[str, Any]],
        conversation_id: str = "",
    ) -> ExtractionResult:
        """从对话中提取知识"""
        start_time = time.time()
        knowledge_list: list[LearnedKnowledge] = []

        for entry in conversation:
            role = entry.get("role", "")
            content = entry.get("content", "")
            entry_id = entry.get("id", "")

            if role == "assistant":
                # 从助手回复中提取知识
                extracted = self._extract_from_content(
                    content,
                    conversation_id,
                    entry_id,
                )
                knowledge_list.extend(extracted)

        extraction_time = time.time() - start_time
        source_length = sum(len(e.get("content", "")) for e in conversation)
        success_rate = len(knowledge_list) / max(len(conversation), 1)

        return ExtractionResult(
            knowledge_list=knowledge_list,
            extraction_time=extraction_time,
            source_length=source_length,
            success_rate=success_rate,
        )

    def extract_from_text(
        self,
        text: str,
        source_type: KnowledgeSource = KnowledgeSource.CONVERSATION,
        source_id: str = "",
    ) -> list[LearnedKnowledge]:
        """从文本中提取知识"""
        return self._extract_from_content(text, source_id, "", source_type)

    def _extract_from_content(
        self,
        content: str,
        conversation_id: str,
        entry_id: str,
        source_type: KnowledgeSource = KnowledgeSource.CONVERSATION,
    ) -> list[LearnedKnowledge]:
        """从内容中提取知识"""
        results: list[LearnedKnowledge] = []

        # 提取代码块
        code_blocks = self._extract_code_blocks(content)
        for code, language in code_blocks:
            knowledge = self._create_knowledge_from_code(
                code,
                language,
                conversation_id,
                entry_id,
                source_type,
            )
            if knowledge:
                results.append(knowledge)

        # 提取最佳实践
        practices = self._extract_best_practices(content)
        for practice in practices:
            knowledge = self._create_knowledge_from_practice(
                practice,
                conversation_id,
                entry_id,
                source_type,
            )
            results.append(knowledge)

        # 提取 API 用法
        api_usages = self._extract_api_usages(content)
        for api_usage in api_usages:
            knowledge = self._create_knowledge_from_api_usage(
                api_usage,
                conversation_id,
                entry_id,
                source_type,
            )
            results.append(knowledge)

        # 提取错误修复
        fixes = self._extract_fixes(content)
        for fix in fixes:
            knowledge = self._create_knowledge_from_fix(
                fix,
                conversation_id,
                entry_id,
                source_type,
            )
            results.append(knowledge)

        return results

    def _extract_code_blocks(
        self,
        content: str,
    ) -> list[tuple[str, str]]:
        """提取代码块"""
        import re
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        return [(code, lang or "python") for lang, code in matches]

    def _extract_best_practices(self, content: str) -> list[str]:
        """提取最佳实践"""
        import re
        patterns = [
            r'建议[：:]\s*(.+?)(?=\n|$)',
            r'最佳实践[：:]\s*(.+?)(?=\n|$)',
            r'推荐[：:]\s*(.+?)(?=\n|$)',
            r'注意[：:]\s*(.+?)(?=\n|$)',
            r'Recommended[：:]\s*(.+?)(?=\n|$)',
        ]

        results: list[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            results.extend(matches)

        return results

    def _extract_api_usages(self, content: str) -> list[dict[str, Any]]:
        """提取 API 用法"""
        import re
        # 匹配 API 调用模式
        pattern = r'\b([A-Z][a-zA-Z]{2,})\s*\(([^)]*)\)'
        matches = re.findall(pattern, content)

        results: list[dict[str, Any]] = []
        for api_name, params in matches:
            if api_name not in ["True", "False", "None", "List", "Dict"]:
                results.append({
                    "api_name": api_name,
                    "params": params,
                    "context": content,
                })

        return results

    def _extract_fixes(self, content: str) -> list[dict[str, Any]]:
        """提取错误修复"""
        import re
        patterns = [
            (r'错误[：:]\s*(.+?)(?=\n)', "error"),
            (r'修复[：:]\s*(.+?)(?=\n)', "fix"),
            (r'解决[：:]\s*(.+?)(?=\n)', "solution"),
        ]

        results: list[dict[str, Any]] = []
        for pattern, fix_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                results.append({
                    "type": fix_type,
                    "content": match,
                    "context": content,
                })

        return results

    def _create_knowledge_from_code(
        self,
        code: str,
        language: str,
        conversation_id: str,
        entry_id: str,
        source_type: KnowledgeSource,
    ) -> Optional[LearnedKnowledge]:
        """从代码创建知识"""
        if len(code.strip()) < 10:
            return None

        import re
        # 提取 API 名称
        api_matches = re.findall(r'\b([A-Z][a-zA-Z]{2,})\s*\(', code)
        related_apis = [a for a in api_matches if a not in ["True", "False", "None"]]

        # 提取事件名称
        event_matches = re.findall(r'\b(On[A-Z][a-zA-Z]*)\b', code)

        knowledge_id = self._generate_id(code)

        return LearnedKnowledge(
            id=knowledge_id,
            knowledge_type=KnowledgeType.SNIPPET,
            content=code,
            source=source_type,
            confidence=0.7,
            source_conversation_id=conversation_id,
            source_entry_id=entry_id,
            tags=[language, "code"],
            related_apis=list(set(related_apis)),
            related_events=list(set(event_matches)),
            code_example=code,
        )

    def _create_knowledge_from_practice(
        self,
        practice: str,
        conversation_id: str,
        entry_id: str,
        source_type: KnowledgeSource,
    ) -> LearnedKnowledge:
        """从最佳实践创建知识"""
        knowledge_id = self._generate_id(practice)

        return LearnedKnowledge(
            id=knowledge_id,
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            content=practice,
            source=source_type,
            confidence=0.8,
            source_conversation_id=conversation_id,
            source_entry_id=entry_id,
            tags=["practice"],
        )

    def _create_knowledge_from_api_usage(
        self,
        api_usage: dict[str, Any],
        conversation_id: str,
        entry_id: str,
        source_type: KnowledgeSource,
    ) -> LearnedKnowledge:
        """从 API 用法创建知识"""
        knowledge_id = self._generate_id(str(api_usage))

        return LearnedKnowledge(
            id=knowledge_id,
            knowledge_type=KnowledgeType.API_USAGE,
            content=f"{api_usage['api_name']}({api_usage['params']})",
            source=source_type,
            confidence=0.75,
            source_conversation_id=conversation_id,
            source_entry_id=entry_id,
            tags=["api", "usage"],
            related_apis=[api_usage["api_name"]],
        )

    def _create_knowledge_from_fix(
        self,
        fix: dict[str, Any],
        conversation_id: str,
        entry_id: str,
        source_type: KnowledgeSource,
    ) -> LearnedKnowledge:
        """从错误修复创建知识"""
        knowledge_id = self._generate_id(str(fix))

        return LearnedKnowledge(
            id=knowledge_id,
            knowledge_type=KnowledgeType.FIX,
            content=fix["content"],
            source=source_type,
            confidence=0.85,
            source_conversation_id=conversation_id,
            source_entry_id=entry_id,
            tags=["fix", fix["type"]],
        )

    def _generate_id(self, content: str) -> str:
        """生成知识 ID"""
        hash_input = f"{content}{time.time()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _load_patterns(self) -> dict[str, Any]:
        """加载提取模式"""
        return {
            "code_block": r'```(\w+)?\n(.*?)```',
            "api_call": r'\b([A-Z][a-zA-Z]{2,})\s*\(([^)]*)\)',
            "event": r'\b(On[A-Z][a-zA-Z]*)\b',
        }


class KnowledgeValidator:
    """知识验证器

    验证知识的有效性。
    """

    def __init__(self) -> None:
        """初始化知识验证器"""
        self._validation_rules = self._load_validation_rules()
        self._lock = threading.Lock()

    def validate(
        self,
        knowledge: LearnedKnowledge,
        run_tests: bool = True,
    ) -> VerificationResult:
        """验证知识"""
        is_valid = True
        error_messages: list[str] = []
        confidence = knowledge.confidence

        # 检查内容有效性
        if not knowledge.content or len(knowledge.content.strip()) < 5:
            is_valid = False
            error_messages.append("内容过短")

        # 检查知识类型
        if knowledge.knowledge_type == KnowledgeType.API_USAGE:
            api_valid = self._validate_api_usage(knowledge)
            if not api_valid:
                is_valid = False
                error_messages.append("API 用法无效")
                confidence *= 0.5

        # 检查代码示例
        if knowledge.code_example and run_tests:
            code_valid, code_error = self._validate_code(knowledge.code_example)
            if not code_valid:
                confidence *= 0.7
                error_messages.append(f"代码验证警告: {code_error}")

        # 更新置信度
        if error_messages:
            confidence = max(0.1, confidence - 0.1 * len(error_messages))

        return VerificationResult(
            knowledge_id=knowledge.id,
            is_valid=is_valid,
            confidence=confidence,
            error_message="; ".join(error_messages) if error_messages else "",
            test_result="passed" if is_valid else "failed",
        )

    def validate_batch(
        self,
        knowledge_list: list[LearnedKnowledge],
        run_tests: bool = True,
    ) -> list[VerificationResult]:
        """批量验证知识"""
        return [self.validate(k, run_tests) for k in knowledge_list]

    def _validate_api_usage(self, knowledge: LearnedKnowledge) -> bool:
        """验证 API 用法"""
        # 检查是否包含有效的 API 名称
        import re
        api_pattern = r'\b([A-Z][a-zA-Z]{2,})\s*\('
        matches = re.findall(api_pattern, knowledge.content)

        if not matches:
            return False

        # 检查 API 名称是否在相关 API 列表中
        for api in matches:
            if api in knowledge.related_apis or api in self._get_known_apis():
                return True

        return True  # 对于未知 API，暂时认为有效

    def _validate_code(self, code: str) -> tuple[bool, str]:
        """验证代码"""
        try:
            # 简单的语法检查
            compile(code, "<string>", "exec")
            return True, ""
        except SyntaxError as e:
            return False, str(e)

    def _get_known_apis(self) -> list[str]:
        """获取已知 API 列表"""
        return [
            "CreateEngineEntity",
            "DestroyEntity",
            "GetEngineEntity",
            "ListenEvent",
            "UnListenEvent",
            "CreateEngineItem",
            "CreateEngineBlock",
            "SetEngineEntityPos",
            "GetEngineEntityPos",
        ]

    def _load_validation_rules(self) -> dict[str, Any]:
        """加载验证规则"""
        return {
            "min_content_length": 5,
            "max_content_length": 10000,
            "min_confidence": 0.1,
            "required_fields": ["id", "knowledge_type", "content"],
        }


class ContinuousLearner:
    """持续学习器

    管理知识的持续学习和集成。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
    ) -> None:
        """初始化持续学习器"""
        self._storage_path = storage_path or Path.home() / ".mc_agent_kit" / "learned_knowledge"
        self._knowledge_store: dict[str, LearnedKnowledge] = {}
        self._version_history: dict[str, list[KnowledgeVersion]] = {}
        self._extractor = KnowledgeExtractor()
        self._validator = KnowledgeValidator()
        self._lock = threading.RLock()

        # 加载已有知识
        self._load_knowledge()

    def extract_knowledge(
        self,
        conversation: list[dict[str, Any]],
        conversation_id: str = "",
    ) -> list[LearnedKnowledge]:
        """从对话中提取知识"""
        result = self._extractor.extract(conversation, conversation_id)
        return result.knowledge_list

    def verify_knowledge(
        self,
        knowledge: LearnedKnowledge,
        run_tests: bool = True,
    ) -> bool:
        """验证知识"""
        result = self._validator.validate(knowledge, run_tests)

        with self._lock:
            if knowledge.id in self._knowledge_store:
                self._knowledge_store[knowledge.id].verified = result.is_valid
                self._knowledge_store[knowledge.id].confidence = result.confidence

        return result.is_valid

    def integrate_knowledge(
        self,
        knowledge: LearnedKnowledge,
        validate: bool = True,
    ) -> bool:
        """集成知识到知识库"""
        if validate:
            result = self._validator.validate(knowledge)
            if not result.is_valid:
                return False
            knowledge.confidence = result.confidence
            knowledge.verified = True
            knowledge.status = KnowledgeStatus.VERIFIED

        with self._lock:
            # 检查是否已存在类似知识
            existing = self._find_similar_knowledge(knowledge)
            if existing:
                # 更新已有知识
                self._update_knowledge(existing, knowledge)
                return True

            # 添加新知识
            knowledge.created_at = time.time()
            knowledge.updated_at = time.time()
            self._knowledge_store[knowledge.id] = knowledge

            # 记录版本
            self._record_version(knowledge)

        # 保存到存储
        self._save_knowledge()

        return True

    def get_related_knowledge(
        self,
        query: str,
        knowledge_types: Optional[list[KnowledgeType]] = None,
        limit: int = 10,
    ) -> list[tuple[LearnedKnowledge, float]]:
        """获取相关知识"""
        results: list[tuple[LearnedKnowledge, float]] = []
        query_lower = query.lower()

        with self._lock:
            for knowledge in self._knowledge_store.values():
                # 过滤类型
                if knowledge_types and knowledge.knowledge_type not in knowledge_types:
                    continue

                # 过滤状态
                if knowledge.status not in (KnowledgeStatus.VERIFIED, KnowledgeStatus.PENDING):
                    continue

                # 计算相关性
                score = self._calculate_relevance(query_lower, knowledge)
                if score > 0:
                    results.append((knowledge, score))

        # 按相关性排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_knowledge_by_api(
        self,
        api_name: str,
    ) -> list[LearnedKnowledge]:
        """获取与 API 相关的知识"""
        with self._lock:
            return [
                k for k in self._knowledge_store.values()
                if api_name in k.related_apis
            ]

    def update_knowledge_usage(
        self,
        knowledge_id: str,
        feedback_score: Optional[float] = None,
    ) -> bool:
        """更新知识使用情况"""
        with self._lock:
            knowledge = self._knowledge_store.get(knowledge_id)
            if not knowledge:
                return False

            knowledge.usage_count += 1
            knowledge.updated_at = time.time()

            if feedback_score is not None:
                knowledge.feedback_count += 1
                # 计算平均反馈分数
                total_score = knowledge.feedback_score * (knowledge.feedback_count - 1)
                knowledge.feedback_score = (total_score + feedback_score) / knowledge.feedback_count

        self._save_knowledge()
        return True

    def get_stats(self) -> dict[str, Any]:
        """获取学习统计"""
        with self._lock:
            total = len(self._knowledge_store)
            type_counts: dict[str, int] = {}
            status_counts: dict[str, int] = {}
            avg_confidence = 0.0
            avg_usage = 0.0

            for knowledge in self._knowledge_store.values():
                type_name = knowledge.knowledge_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

                status_name = knowledge.status.value
                status_counts[status_name] = status_counts.get(status_name, 0) + 1

                avg_confidence += knowledge.confidence
                avg_usage += knowledge.usage_count

            if total > 0:
                avg_confidence /= total
                avg_usage /= total

            return {
                "total_knowledge": total,
                "type_distribution": type_counts,
                "status_distribution": status_counts,
                "average_confidence": avg_confidence,
                "average_usage": avg_usage,
                "verified_count": status_counts.get("verified", 0),
            }

    def _find_similar_knowledge(
        self,
        knowledge: LearnedKnowledge,
    ) -> Optional[LearnedKnowledge]:
        """查找类似知识"""
        for existing in self._knowledge_store.values():
            if existing.knowledge_type != knowledge.knowledge_type:
                continue

            # 计算内容相似度
            similarity = self._calculate_similarity(
                existing.content,
                knowledge.content,
            )

            if similarity > 0.8:
                return existing

        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单的 Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _update_knowledge(
        self,
        existing: LearnedKnowledge,
        new: LearnedKnowledge,
    ) -> None:
        """更新已有知识"""
        # 创建新版本
        existing.version += 1
        existing.content = new.content
        existing.updated_at = time.time()
        existing.confidence = max(existing.confidence, new.confidence)

        # 合并标签
        for tag in new.tags:
            if tag not in existing.tags:
                existing.tags.append(tag)

        # 合并相关 API
        for api in new.related_apis:
            if api not in existing.related_apis:
                existing.related_apis.append(api)

        # 记录版本
        self._record_version(existing)

    def _record_version(self, knowledge: LearnedKnowledge) -> None:
        """记录知识版本"""
        version = KnowledgeVersion(
            version=knowledge.version,
            knowledge_id=knowledge.id,
            content=knowledge.content,
            created_at=time.time(),
        )

        if knowledge.id not in self._version_history:
            self._version_history[knowledge.id] = []
        self._version_history[knowledge.id].append(version)

    def _calculate_relevance(
        self,
        query: str,
        knowledge: LearnedKnowledge,
    ) -> float:
        """计算相关性"""
        score = 0.0

        # 内容匹配
        if query in knowledge.content.lower():
            score += 0.5

        # 标签匹配
        for tag in knowledge.tags:
            if query in tag.lower():
                score += 0.3
                break

        # 相关 API 匹配
        for api in knowledge.related_apis:
            if query in api.lower():
                score += 0.4
                break

        # 根据使用频率调整
        if knowledge.usage_count > 0:
            score *= min(1.5, 1.0 + knowledge.usage_count * 0.1)

        # 根据置信度调整
        score *= knowledge.confidence

        return score

    def _load_knowledge(self) -> None:
        """加载已存储的知识"""
        if not self._storage_path.exists():
            return

        knowledge_file = self._storage_path / "knowledge.json"
        if not knowledge_file.exists():
            return

        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for knowledge_data in data.get("knowledge", []):
                knowledge = LearnedKnowledge.from_dict(knowledge_data)
                self._knowledge_store[knowledge.id] = knowledge

        except (json.JSONDecodeError, KeyError):
            pass

    def _save_knowledge(self) -> None:
        """保存知识到存储"""
        self._storage_path.mkdir(parents=True, exist_ok=True)
        knowledge_file = self._storage_path / "knowledge.json"

        with self._lock:
            data = {
                "knowledge": [k.to_dict() for k in self._knowledge_store.values()],
                "saved_at": time.time(),
            }

        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def rollback_knowledge(
        self,
        knowledge_id: str,
        target_version: int,
    ) -> bool:
        """回滚知识到指定版本"""
        with self._lock:
            versions = self._version_history.get(knowledge_id, [])
            target = None

            for v in versions:
                if v.version == target_version:
                    target = v
                    break

            if not target:
                return False

            knowledge = self._knowledge_store.get(knowledge_id)
            if not knowledge:
                return False

            knowledge.version = target_version
            knowledge.content = target.content
            knowledge.updated_at = time.time()

        self._save_knowledge()
        return True

    def clear(self) -> None:
        """清空知识库"""
        with self._lock:
            self._knowledge_store.clear()
            self._version_history.clear()
        self._save_knowledge()


# 全局实例
_learner: Optional[ContinuousLearner] = None


def get_continuous_learner() -> ContinuousLearner:
    """获取全局持续学习器"""
    global _learner
    if _learner is None:
        _learner = ContinuousLearner()
    return _learner


def extract_knowledge(
    conversation: list[dict[str, Any]],
    conversation_id: str = "",
) -> list[LearnedKnowledge]:
    """便捷函数：提取知识"""
    return get_continuous_learner().extract_knowledge(conversation, conversation_id)


def get_learned_knowledge(
    query: str,
    knowledge_types: Optional[list[KnowledgeType]] = None,
    limit: int = 10,
) -> list[tuple[LearnedKnowledge, float]]:
    """便捷函数：获取学习到的知识"""
    return get_continuous_learner().get_related_knowledge(query, knowledge_types, limit)