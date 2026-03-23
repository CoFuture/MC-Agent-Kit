"""
智能推荐增强模块

提供基于上下文的代码推荐、API 使用建议、最佳实践推荐等功能。
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RecommendationType(Enum):
    """推荐类型"""
    CODE = "code"
    API = "api"
    BEST_PRACTICE = "best_practice"
    ERROR_PREVENTION = "error_prevention"
    LEARNING_PATH = "learning_path"
    OPTIMIZATION = "optimization"
    SECURITY = "security"


class RecommendationPriority(Enum):
    """推荐优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Recommendation:
    """推荐项"""
    recommendation_id: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    source: str = "internal"
    related_items: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "context": self.context,
            "confidence": self.confidence,
            "source": self.source,
            "related_items": self.related_items,
            "tags": self.tags,
            "created_at": self.created_at,
        }


@dataclass
class RecommendationConfig:
    """推荐配置"""
    enabled_types: list[RecommendationType] = field(default_factory=lambda: list(RecommendationType))
    min_confidence: float = 0.5
    max_recommendations: int = 10
    context_window: int = 5  # 上下文窗口大小
    enable_learning: bool = True
    enable_personalization: bool = True
    preferred_tags: list[str] = field(default_factory=list)
    excluded_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled_types": [t.value for t in self.enabled_types],
            "min_confidence": self.min_confidence,
            "max_recommendations": self.max_recommendations,
            "context_window": self.context_window,
            "enable_learning": self.enable_learning,
            "enable_personalization": self.enable_personalization,
            "preferred_tags": self.preferred_tags,
            "excluded_tags": self.excluded_tags,
        }


@dataclass
class LearningPath:
    """学习路径"""
    path_id: str
    title: str
    description: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: str  # e.g., "2 hours"
    steps: list[dict[str, Any]] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "steps": self.steps,
            "prerequisites": self.prerequisites,
            "outcomes": self.outcomes,
            "tags": self.tags,
        }


class ContextAnalyzer:
    """上下文分析器

    分析当前代码和对话上下文，为推荐提供依据。

    使用示例:
        analyzer = ContextAnalyzer()
        context = analyzer.analyze_code(code)
    """

    def __init__(self) -> None:
        """初始化上下文分析器"""
        # ModSDK API 分类
        self._api_categories: dict[str, list[str]] = {
            "entity": ["CreateEngineEntity", "GetEngineType", "SetEntityPos"],
            "item": ["CreateItem", "RegisterItem", "SetItemDurability"],
            "block": ["CreateBlock", "SetBlockState", "GetBlockPos"],
            "event": ["ListenEvent", "TriggerEvent", "CancelEvent"],
            "network": ["SendPacket", "ReceivePacket", "SyncData"],
            "ui": ["CreateUI", "ShowUI", "UpdateUI"],
        }

        # 常见错误模式
        self._error_patterns: dict[str, str] = {
            "KeyError": "字典键不存在",
            "AttributeError": "属性不存在",
            "TypeError": "类型错误",
            "ImportError": "导入错误",
            "NameError": "名称未定义",
        }

        # 最佳实践规则
        self._best_practices: list[dict[str, Any]] = [
            {
                "id": "bp_001",
                "pattern": r"def\s+\w+\s*\([^)]*\)\s*:",
                "description": "函数应该有文档字符串",
                "suggestion": "为函数添加 docstring 说明功能和参数",
                "priority": RecommendationPriority.MEDIUM,
            },
            {
                "id": "bp_002",
                "pattern": r"try\s*:",
                "description": "异常处理应该具体",
                "suggestion": "避免使用裸 except，指定具体的异常类型",
                "priority": RecommendationPriority.HIGH,
            },
            {
                "id": "bp_003",
                "pattern": r"import\s+mod\.common",
                "description": "导入应该按需",
                "suggestion": "只导入需要的函数，而不是整个模块",
                "priority": RecommendationPriority.LOW,
            },
        ]

    def analyze_code(self, code: str) -> dict[str, Any]:
        """分析代码"""
        import re

        result: dict[str, Any] = {
            "apis_used": [],
            "events_used": [],
            "complexity": 0,
            "issues": [],
            "suggestions": [],
        }

        # 检测使用的 API
        for category, apis in self._api_categories.items():
            for api in apis:
                if api in code:
                    result["apis_used"].append({"name": api, "category": category})

        # 检测事件
        event_pattern = r'(On[A-Z][a-zA-Z]+)'
        events = re.findall(event_pattern, code)
        result["events_used"] = [{"name": e} for e in events]

        # 计算复杂度（简化）
        result["complexity"] = code.count("\n") // 10 + code.count("if ") + code.count("for ")

        # 检查潜在问题
        if "eval(" in code or "exec(" in code:
            result["issues"].append({
                "type": "security",
                "message": "避免使用 eval/exec，存在安全风险",
            })

        if "import *" in code:
            result["issues"].append({
                "type": "style",
                "message": "避免使用通配符导入",
            })

        return result

    def analyze_context(
        self,
        conversation_history: list[dict[str, Any]],
        current_intent: Optional[str] = None,
    ) -> dict[str, Any]:
        """分析对话上下文"""
        context: dict[str, Any] = {
            "topics": [],
            "recent_apis": [],
            "recent_errors": [],
            "user_level": "intermediate",
        }

        # 分析最近的消息
        recent = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history

        for msg in recent:
            content = msg.get("content", "")
            if "API" in content or "api" in content:
                context["recent_apis"].append(content[:100])
            if "error" in content.lower() or "错误" in content:
                context["recent_errors"].append(content[:100])

        # 推断用户水平
        if len(conversation_history) < 3:
            context["user_level"] = "beginner"
        elif any("advanced" in msg.get("content", "").lower() for msg in conversation_history):
            context["user_level"] = "advanced"

        return context


class RecommendationEngine:
    """推荐引擎

    根据上下文生成推荐。

    使用示例:
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(context)
    """

    def __init__(self) -> None:
        """初始化推荐引擎"""
        self._context_analyzer = ContextAnalyzer()
        self._recommendation_history: OrderedDict[str, Recommendation] = OrderedDict()
        self._max_history = 100
        self._lock = threading.Lock()

        # 内置推荐模板
        self._builtin_recommendations = self._create_builtin_recommendations()

    def _create_builtin_recommendations(self) -> list[Recommendation]:
        """创建内置推荐"""
        import uuid

        return [
            # API 使用建议
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.API,
                priority=RecommendationPriority.HIGH,
                title="使用 CreateEngineEntity 创建实体",
                description="CreateEngineEntity 是 ModSDK 中创建实体的标准 API",
                content="""from mod.common import CreateEngineEntity, GetEngineType

# 获取引擎类型
engine_type = GetEngineType()

# 创建实体
entity_id = CreateEngineEntity(
    engine_type,
    "my_entity",
    (x, y, z),
    dimension
)""",
                tags=["entity", "api", "beginner"],
            ),
            # 最佳实践
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.BEST_PRACTICE,
                priority=RecommendationPriority.MEDIUM,
                title="使用异常处理保护关键代码",
                description="在调用 ModSDK API 时应该使用异常处理",
                content="""try:
    entity_id = CreateEngineEntity(...)
    if entity_id:
        print(f"创建成功：{entity_id}")
    else:
        print("创建失败")
except Exception as e:
    print(f"错误：{e}")""",
                tags=["error_handling", "best_practice"],
            ),
            # 错误预防
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.ERROR_PREVENTION,
                priority=RecommendationPriority.HIGH,
                title="检查实体 ID 是否有效",
                description="CreateEngineEntity 可能返回 None，使用前应该检查",
                content="""entity_id = CreateEngineEntity(...)
if entity_id is None:
    print("创建失败，请检查参数")
    return

# 确保 entity_id 有效后再使用
SetEntityPos(entity_id, (x, y, z))""",
                tags=["error_prevention", "entity"],
            ),
            # 性能优化
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.OPTIMIZATION,
                priority=RecommendationPriority.MEDIUM,
                title="缓存频繁使用的 API 结果",
                description="避免重复调用获取相同数据的 API",
                content="""# 缓存引擎类型
_engine_type = None

def get_engine_type():
    global _engine_type
    if _engine_type is None:
        _engine_type = GetEngineType()
    return _engine_type""",
                tags=["optimization", "performance"],
            ),
            # 安全建议
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.SECURITY,
                priority=RecommendationPriority.CRITICAL,
                title="避免使用 eval 和 exec",
                description="eval 和 exec 可能执行恶意代码，应该避免使用",
                content="""# ❌ 不安全
user_input = input()
eval(user_input)

# ✅ 安全
allowed_functions = {"add": lambda x, y: x + y}
result = allowed_functions.get(user_input, lambda: None)()""",
                tags=["security", "best_practice"],
            ),
        ]

    def generate_recommendations(
        self,
        context: dict[str, Any],
        config: Optional[RecommendationConfig] = None,
    ) -> list[Recommendation]:
        """生成推荐"""
        config = config or RecommendationConfig()

        recommendations: list[Recommendation] = []

        # 基于代码分析生成推荐
        if "code" in context:
            code_analysis = self._context_analyzer.analyze_code(context["code"])
            recommendations.extend(self._generate_code_recommendations(code_analysis, config))

        # 基于对话上下文生成推荐
        if "conversation_history" in context:
            recommendations.extend(
                self._generate_context_recommendations(context["conversation_history"], config)
            )

        # 基于当前意图生成推荐
        if "current_intent" in context:
            recommendations.extend(
                self._generate_intent_recommendations(context["current_intent"], config)
            )

        # 过滤和排序
        recommendations = self._filter_recommendations(recommendations, config)
        recommendations = self._sort_recommendations(recommendations)

        # 限制数量
        return recommendations[:config.max_recommendations]

    def _generate_code_recommendations(
        self,
        code_analysis: dict[str, Any],
        config: RecommendationConfig,
    ) -> list[Recommendation]:
        """基于代码分析生成推荐"""
        recommendations: list[Recommendation] = []
        import uuid

        # 基于使用的 API 生成推荐
        for api_info in code_analysis.get("apis_used", []):
            api_name = api_info.get("name", "")
            category = api_info.get("category", "")

            # 添加相关 API 推荐
            if category == "entity":
                recommendations.append(Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    recommendation_type=RecommendationType.API,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"相关 API: SetEntityPos",
                    description="创建实体后可能需要设置位置",
                    content="SetEntityPos(entity_id, (x, y, z))",
                    tags=["entity", "api"],
                ))

        # 基于问题生成推荐
        for issue in code_analysis.get("issues", []):
            issue_type = issue.get("type", "")
            message = issue.get("message", "")

            if issue_type == "security":
                recommendations.append(Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    recommendation_type=RecommendationType.SECURITY,
                    priority=RecommendationPriority.CRITICAL,
                    title="安全警告",
                    description=message,
                    content="请避免使用危险函数，参考安全最佳实践",
                    tags=["security"],
                ))

        return recommendations

    def _generate_context_recommendations(
        self,
        conversation_history: list[dict[str, Any]],
        config: RecommendationConfig,
    ) -> list[Recommendation]:
        """基于对话上下文生成推荐"""
        recommendations: list[Recommendation] = []
        import uuid

        # 如果用户多次询问错误相关
        error_count = sum(1 for msg in conversation_history if "error" in msg.get("content", "").lower())
        if error_count >= 2:
            recommendations.append(Recommendation(
                recommendation_id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.ERROR_PREVENTION,
                priority=RecommendationPriority.HIGH,
                title="错误处理建议",
                description="检测到您多次遇到错误，建议学习异常处理最佳实践",
                content="参考错误处理指南：使用 try/except 捕获具体异常",
                tags=["error_handling", "learning"],
            ))

        return recommendations

    def _generate_intent_recommendations(
        self,
        intent: str,
        config: RecommendationConfig,
    ) -> list[Recommendation]:
        """基于意图生成推荐"""
        recommendations: list[Recommendation] = []
        import uuid

        intent_map: dict[str, list[RecommendationType]] = {
            "create_entity": [RecommendationType.API, RecommendationType.BEST_PRACTICE],
            "create_item": [RecommendationType.API, RecommendationType.CODE],
            "diagnose_error": [RecommendationType.ERROR_PREVENTION, RecommendationType.BEST_PRACTICE],
            "generate_code": [RecommendationType.CODE, RecommendationType.OPTIMIZATION],
        }

        for rec_type in intent_map.get(intent, []):
            if rec_type in config.enabled_types:
                # 从内置推荐中筛选
                for builtin in self._builtin_recommendations:
                    if builtin.recommendation_type == rec_type:
                        recommendations.append(builtin)

        return recommendations

    def _filter_recommendations(
        self,
        recommendations: list[Recommendation],
        config: RecommendationConfig,
    ) -> list[Recommendation]:
        """过滤推荐"""
        filtered: list[Recommendation] = []

        for rec in recommendations:
            # 检查置信度
            if rec.confidence < config.min_confidence:
                continue

            # 检查类型
            if rec.recommendation_type not in config.enabled_types:
                continue

            # 检查标签
            if any(tag in config.excluded_tags for tag in rec.tags):
                continue

            filtered.append(rec)

        return filtered

    def _sort_recommendations(
        self,
        recommendations: list[Recommendation],
    ) -> list[Recommendation]:
        """排序推荐"""
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
            RecommendationPriority.INFO: 4,
        }

        return sorted(
            recommendations,
            key=lambda r: (priority_order.get(r.priority, 5), -r.confidence),
        )

    def get_learning_path(
        self,
        topic: str,
        user_level: str = "beginner",
    ) -> Optional[LearningPath]:
        """获取学习路径"""
        import uuid

        paths: dict[str, LearningPath] = {
            "entity": LearningPath(
                path_id=str(uuid.uuid4()),
                title="实体开发入门",
                description="学习如何创建和自定义 Minecraft 实体",
                difficulty="beginner",
                estimated_time="2 hours",
                steps=[
                    {"title": "了解实体基础", "description": "学习实体的基本概念"},
                    {"title": "创建第一个实体", "description": "使用 CreateEngineEntity API"},
                    {"title": "自定义实体行为", "description": "添加移动、攻击等行为"},
                    {"title": "实体渲染", "description": "自定义实体外观"},
                ],
                prerequisites=["Python 基础", "ModSDK 环境配置"],
                outcomes=["能创建自定义实体", "理解实体生命周期", "掌握实体 API"],
                tags=["entity", "beginner"],
            ),
            "item": LearningPath(
                path_id=str(uuid.uuid4()),
                title="物品开发入门",
                description="学习如何创建和自定义 Minecraft 物品",
                difficulty="beginner",
                estimated_time="1.5 hours",
                steps=[
                    {"title": "了解物品基础", "description": "学习物品的基本概念"},
                    {"title": "创建第一个物品", "description": "使用 CreateItem API"},
                    {"title": "物品功能", "description": "添加使用效果"},
                    {"title": "合成配方", "description": "创建物品合成配方"},
                ],
                prerequisites=["Python 基础"],
                outcomes=["能创建自定义物品", "理解物品系统", "掌握物品 API"],
                tags=["item", "beginner"],
            ),
            "advanced": LearningPath(
                path_id=str(uuid.uuid4()),
                title="高级 ModSDK 开发",
                description="深入学习 ModSDK 高级功能",
                difficulty="advanced",
                estimated_time="8 hours",
                steps=[
                    {"title": "网络同步", "description": "学习客户端 - 服务端数据同步"},
                    {"title": "自定义 UI", "description": "创建自定义界面"},
                    {"title": "性能优化", "description": "优化 Mod 性能"},
                    {"title": "调试技巧", "description": "高级调试方法"},
                ],
                prerequisites=["实体开发", "物品开发", "Python 进阶"],
                outcomes=["掌握网络编程", "能创建复杂 UI", "性能优化能力"],
                tags=["advanced", "network", "ui"],
            ),
        }

        return paths.get(topic)


class SmartRecommendationService:
    """智能推荐服务

    整合推荐引擎和学习路径功能。

    使用示例:
        service = SmartRecommendationService()
        recs = service.get_recommendations(context)
    """

    def __init__(self) -> None:
        """初始化智能推荐服务"""
        self._engine = RecommendationEngine()
        self._config = RecommendationConfig()
        self._user_feedback: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get_recommendations(
        self,
        context: dict[str, Any],
        config: Optional[RecommendationConfig] = None,
    ) -> list[Recommendation]:
        """获取推荐"""
        config = config or self._config
        return self._engine.generate_recommendations(context, config)

    def get_learning_path(
        self,
        topic: str,
        user_level: str = "beginner",
    ) -> Optional[LearningPath]:
        """获取学习路径"""
        return self._engine.get_learning_path(topic, user_level)

    def update_config(self, **kwargs: Any) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def record_feedback(
        self,
        recommendation_id: str,
        feedback: dict[str, Any],
    ) -> None:
        """记录反馈"""
        with self._lock:
            self._user_feedback[recommendation_id] = {
                **feedback,
                "timestamp": time.time(),
            }

    def get_recommendation_stats(self) -> dict[str, Any]:
        """获取推荐统计"""
        with self._lock:
            total = len(self._user_feedback)
            positive = sum(1 for f in self._user_feedback.values() if f.get("helpful", False))
            return {
                "total_feedback": total,
                "positive_feedback": positive,
                "negative_feedback": total - positive,
                "helpful_rate": positive / total if total > 0 else 0,
            }


# 全局实例
_recommendation_service: Optional[SmartRecommendationService] = None


def get_recommendation_service() -> SmartRecommendationService:
    """获取全局推荐服务"""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = SmartRecommendationService()
    return _recommendation_service


def get_recommendations(
    context: dict[str, Any],
    config: Optional[RecommendationConfig] = None,
) -> list[Recommendation]:
    """便捷函数：获取推荐"""
    return get_recommendation_service().get_recommendations(context, config)


def get_learning_path(topic: str, user_level: str = "beginner") -> Optional[LearningPath]:
    """便捷函数：获取学习路径"""
    return get_recommendation_service().get_learning_path(topic, user_level)