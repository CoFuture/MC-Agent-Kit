"""
对话体验增强模块

提供情感分析、个性化响应、对话历史可视化、对话摘要增强等功能。
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class SentimentType(Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    EXCITED = "excited"
    CURIOUS = "curious"


class PersonalityType(Enum):
    """个性化类型"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    CONCISE = "concise"
    VERBOSE = "verbose"


class VisualizationType(Enum):
    """可视化类型"""
    TIMELINE = "timeline"
    TOPIC_FLOW = "topic_flow"
    INTENT_DISTRIBUTION = "intent_distribution"
    SENTIMENT_TREND = "sentiment_trend"
    SUMMARY_CARD = "summary_card"


@dataclass
class SentimentResult:
    """情感分析结果"""
    sentiment: SentimentType
    confidence: float
    intensity: float  # 0.0 - 1.0
    keywords: list[str] = field(default_factory=list)
    aspects: dict[str, float] = field(default_factory=dict)  # 方面 -> 情感分数

    def to_dict(self) -> dict[str, Any]:
        return {
            "sentiment": self.sentiment.value,
            "confidence": self.confidence,
            "intensity": self.intensity,
            "keywords": self.keywords,
            "aspects": self.aspects,
        }


@dataclass
class PersonalizationConfig:
    """个性化配置"""
    personality: PersonalityType = PersonalityType.FRIENDLY
    verbosity: str = "medium"  # brief, medium, detailed
    code_style_preference: str = "modsdk_best_practice"
    language_preference: str = "zh_CN"
    show_explanations: bool = True
    show_examples: bool = True
    max_response_length: int = 2000
    preferred_response_format: str = "markdown"  # markdown, text, json

    def to_dict(self) -> dict[str, Any]:
        return {
            "personality": self.personality.value,
            "verbosity": self.verbosity,
            "code_style_preference": self.code_style_preference,
            "language_preference": self.language_preference,
            "show_explanations": self.show_explanations,
            "show_examples": self.show_examples,
            "max_response_length": self.max_response_length,
            "preferred_response_format": self.preferred_response_format,
        }


@dataclass
class ConversationVisualization:
    """对话可视化数据"""
    visualization_type: VisualizationType
    data: dict[str, Any]
    title: str
    description: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "visualization_type": self.visualization_type.value,
            "data": self.data,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp,
        }


@dataclass
class EnhancedConversationSummary:
    """增强对话摘要"""
    session_id: str
    message_count: int
    duration: float
    main_topics: list[str]
    main_intents: list[str]
    entities_mentioned: dict[str, Any]
    key_points: list[str]
    sentiment_summary: dict[str, Any]
    interaction_quality: float  # 0.0 - 1.0
    user_engagement: float  # 0.0 - 1.0
    suggestions: list[str] = field(default_factory=list)
    follow_up_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "message_count": self.message_count,
            "duration": self.duration,
            "main_topics": self.main_topics,
            "main_intents": self.main_intents,
            "entities_mentioned": self.entities_mentioned,
            "key_points": self.key_points,
            "sentiment_summary": self.sentiment_summary,
            "interaction_quality": self.interaction_quality,
            "user_engagement": self.user_engagement,
            "suggestions": self.suggestions,
            "follow_up_actions": self.follow_up_actions,
        }


class SentimentAnalyzer:
    """情感分析器

    分析用户消息的情感和情绪。

    使用示例:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("这个功能太棒了！")
        print(result.sentiment)  # SentimentType.POSITIVE
    """

    def __init__(self) -> None:
        """初始化情感分析器"""
        # 情感关键词映射
        self._sentiment_keywords: dict[SentimentType, dict[str, float]] = {
            SentimentType.POSITIVE: {
                "好": 0.8, "棒": 0.9, "优秀": 0.9, "完美": 1.0,
                "感谢": 0.7, "谢谢": 0.7, "厉害": 0.8, "赞": 0.9,
                "解决了": 0.8, "成功了": 0.8, "好的": 0.6, "可以": 0.5,
                "excellent": 0.9, "great": 0.8, "good": 0.7, "nice": 0.7,
                "thanks": 0.7, "perfect": 1.0, "awesome": 0.9,
            },
            SentimentType.NEGATIVE: {
                "不好": 0.7, "差": 0.8, "糟糕": 0.9, "失败": 0.9,
                "错误": 0.7, "问题": 0.5, "不行": 0.7, "无效": 0.7,
                "不能": 0.5, "不": 0.4, "难": 0.5, "麻烦": 0.6,
                "bad": 0.7, "error": 0.7, "fail": 0.8, "wrong": 0.7,
                "problem": 0.5, "issue": 0.5, "not work": 0.7,
            },
            SentimentType.FRUSTRATED: {
                "烦": 0.8, "气死": 0.9, "为什么": 0.5, "怎么回事": 0.6,
                "不行啊": 0.7, "又": 0.4, "还是": 0.3, "一直": 0.3,
                "frustrated": 0.9, "annoying": 0.8, "why": 0.4,
            },
            SentimentType.CONFUSED: {
                "不懂": 0.8, "不明白": 0.8, "什么意思": 0.8, "怎么": 0.5,
                "如何": 0.4, "困惑": 0.9, "不理解": 0.8, "不清楚": 0.7,
                "confused": 0.9, "don't understand": 0.9, "what": 0.4,
            },
            SentimentType.EXCITED: {
                "太棒了": 1.0, "太好": 0.9, "终于": 0.7, "成功了": 0.8,
                "实现了": 0.7, "可以了": 0.6, "做到了": 0.8,
                "excited": 0.9, "amazing": 0.9, "wow": 0.8,
            },
            SentimentType.CURIOUS: {
                "好奇": 0.8, "想知道": 0.7, "有没有": 0.4, "是否": 0.3,
                "能不能": 0.5, "可能": 0.4, "想看看": 0.6,
                "curious": 0.8, "wonder": 0.6, "interesting": 0.7,
            },
        }

        # 方面关键词
        self._aspect_keywords: dict[str, list[str]] = {
            "code_quality": ["代码", "质量", "优化", "性能", "效率", "code"],
            "documentation": ["文档", "说明", "教程", "文档", "doc"],
            "usability": ["使用", "操作", "界面", "交互", "易用", "use"],
            "functionality": ["功能", "实现", "特性", "能力", "function"],
            "error_handling": ["错误", "异常", "报错", "问题", "error"],
        }

    def analyze(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
    ) -> SentimentResult:
        """分析文本情感

        Args:
            text: 要分析的文本
            context: 上下文信息（可选）

        Returns:
            SentimentResult: 情感分析结果
        """
        text_lower = text.lower()

        # 计算各情感得分
        scores: dict[SentimentType, float] = {}
        matched_keywords: list[str] = []

        for sentiment, keywords in self._sentiment_keywords.items():
            score = 0.0
            for keyword, weight in keywords.items():
                if keyword in text_lower:
                    score = max(score, weight)
                    matched_keywords.append(keyword)
            if score > 0:
                scores[sentiment] = score

        # 确定主要情感
        if not scores:
            sentiment = SentimentType.NEUTRAL
            confidence = 0.5
            intensity = 0.0
        else:
            sentiment = max(scores, key=scores.get)
            confidence = scores[sentiment]
            intensity = confidence

        # 分析方面情感
        aspects = self._analyze_aspects(text_lower)

        return SentimentResult(
            sentiment=sentiment,
            confidence=confidence,
            intensity=intensity,
            keywords=list(set(matched_keywords)),
            aspects=aspects,
        )

    def _analyze_aspects(self, text: str) -> dict[str, float]:
        """分析各方面的情感"""
        aspects: dict[str, float] = {}

        for aspect, keywords in self._aspect_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    aspects[aspect] = aspects.get(aspect, 0.5) + 0.1

        # 归一化
        for aspect in aspects:
            aspects[aspect] = min(aspects[aspect], 1.0)

        return aspects

    def analyze_conversation_trend(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """分析对话情感趋势"""
        trend: list[SentimentResult] = []

        for msg in messages:
            if msg.get("role") == "user":
                result = self.analyze(msg.get("content", ""))
                trend.append(result)

        if not trend:
            return {"trend": [], "summary": "无数据"}

        # 统计情感分布
        distribution: dict[SentimentType, int] = {}
        for result in trend:
            distribution[result.sentiment] = distribution.get(result.sentiment, 0) + 1

        # 计算平均强度
        avg_intensity = sum(r.intensity for r in trend) / len(trend)

        # 确定趋势方向
        if len(trend) >= 2:
            first_half = trend[:len(trend) // 2]
            second_half = trend[len(trend) // 2:]
            first_avg = sum(r.confidence for r in first_half) / len(first_half)
            second_avg = sum(r.confidence for r in second_half) / len(second_half)
            direction = "improving" if second_avg > first_avg else "declining"
        else:
            direction = "stable"

        return {
            "trend": [r.to_dict() for r in trend],
            "distribution": {s.value: c for s, c in distribution.items()},
            "average_intensity": avg_intensity,
            "direction": direction,
            "dominant_sentiment": max(distribution, key=distribution.get).value,
        }


class PersonalizationEngine:
    """个性化引擎

    根据用户偏好和历史生成个性化响应。

    使用示例:
        engine = PersonalizationEngine()
        config = engine.get_or_create_config("user_123")
        response = engine.personalize_response("这是原始响应", config)
    """

    def __init__(self) -> None:
        """初始化个性化引擎"""
        self._configs: OrderedDict[str, PersonalizationConfig] = OrderedDict()
        self._max_configs = 100
        self._lock = threading.Lock()

        # 响应模板
        self._response_templates: dict[PersonalityType, dict[str, str]] = {
            PersonalityType.FORMAL: {
                "greeting": "您好，有什么可以帮助您的？",
                "success": "操作已成功完成。",
                "error": "抱歉，操作过程中出现了问题。",
                "clarification": "请提供更多详细信息。",
            },
            PersonalityType.CASUAL: {
                "greeting": "嘿，有什么需要帮忙的吗？",
                "success": "搞定！",
                "error": "哎呀，有点问题...",
                "clarification": "能再说详细点吗？",
            },
            PersonalityType.TECHNICAL: {
                "greeting": "请描述您的技术需求。",
                "success": "执行成功。返回结果如下：",
                "error": "错误代码：{code}。详细信息：{detail}",
                "clarification": "需要更多参数信息。",
            },
            PersonalityType.FRIENDLY: {
                "greeting": "你好呀！今天想做什么呢？😊",
                "success": "太好了，已经帮你搞定啦！✨",
                "error": "抱歉抱歉，出了点小问题，我们再试试？",
                "clarification": "嗯...能再多告诉我一点吗？🤔",
            },
            PersonalityType.CONCISE: {
                "greeting": "请输入需求。",
                "success": "完成。",
                "error": "失败。",
                "clarification": "需要更多信息。",
            },
            PersonalityType.VERBOSE: {
                "greeting": "您好！我是您的助手，随时准备为您提供帮助。请告诉我您今天需要什么帮助？",
                "success": "恭喜！操作已经成功完成。如果您还需要其他帮助，请随时告诉我。",
                "error": "非常抱歉，在执行操作时遇到了一些问题。让我们一起来解决这个问题。",
                "clarification": "为了更好地帮助您，我需要了解更多细节。请您详细描述一下。",
            },
        }

    def get_or_create_config(
        self,
        user_id: str,
        initial_config: Optional[PersonalizationConfig] = None,
    ) -> PersonalizationConfig:
        """获取或创建用户配置"""
        with self._lock:
            if user_id in self._configs:
                return self._configs[user_id]

            config = initial_config or PersonalizationConfig()
            self._configs[user_id] = config

            # 清理旧配置
            while len(self._configs) > self._max_configs:
                self._configs.popitem(last=False)

            return config

    def update_config(
        self,
        user_id: str,
        **kwargs: Any,
    ) -> PersonalizationConfig:
        """更新用户配置"""
        config = self.get_or_create_config(user_id)

        with self._lock:
            for key, value in kwargs.items():
                if hasattr(config, key):
                    if isinstance(value, str) and key == "personality":
                        try:
                            value = PersonalityType(value)
                        except ValueError:
                            continue
                    setattr(config, key, value)

        return config

    def personalize_response(
        self,
        response: str,
        config: PersonalizationConfig,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """个性化响应"""
        # 根据详细程度调整
        if config.verbosity == "brief":
            response = self._make_brief(response)
        elif config.verbosity == "detailed":
            response = self._make_detailed(response, context)

        # 根据最大长度截断
        if len(response) > config.max_response_length:
            response = response[:config.max_response_length - 3] + "..."

        return response

    def get_template(
        self,
        config: PersonalizationConfig,
        template_key: str,
    ) -> str:
        """获取响应模板"""
        templates = self._response_templates.get(config.personality, {})
        return templates.get(template_key, "")

    def _make_brief(self, text: str) -> str:
        """简化文本"""
        # 移除多余的换行和空格
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return " ".join(lines[:3])

    def _make_detailed(
        self,
        text: str,
        context: Optional[dict[str, Any]],
    ) -> str:
        """扩展文本"""
        if not context:
            return text

        additions = []

        if context.get("related_apis"):
            additions.append(f"\n\n相关 API: {', '.join(context['related_apis'][:5])}")

        if context.get("examples"):
            additions.append("\n\n示例代码:\n```python\n" + context["examples"][0] + "\n```")

        return text + "".join(additions)

    def learn_from_feedback(
        self,
        user_id: str,
        feedback: dict[str, Any],
    ) -> None:
        """从反馈学习"""
        # 根据用户反馈调整配置
        if feedback.get("too_verbose"):
            self.update_config(user_id, verbosity="brief")
        elif feedback.get("too_brief"):
            self.update_config(user_id, verbosity="detailed")

        if feedback.get("preferred_style"):
            self.update_config(user_id, personality=feedback["preferred_style"])


class ConversationVisualizer:
    """对话可视化器

    生成对话可视化数据。

    使用示例:
        visualizer = ConversationVisualizer()
        timeline = visualizer.create_timeline(messages)
        flow = visualizer.create_topic_flow(messages)
    """

    def create_timeline(
        self,
        messages: list[dict[str, Any]],
    ) -> ConversationVisualization:
        """创建时间线可视化"""
        timeline_data: list[dict[str, Any]] = []

        for i, msg in enumerate(messages):
            entry = {
                "index": i,
                "role": msg.get("role", "unknown"),
                "timestamp": msg.get("timestamp", time.time()),
                "content_preview": msg.get("content", "")[:50] + "...",
                "intent": msg.get("intent"),
                "topic": msg.get("topic"),
            }
            timeline_data.append(entry)

        return ConversationVisualization(
            visualization_type=VisualizationType.TIMELINE,
            data={"timeline": timeline_data},
            title="对话时间线",
            description="显示对话消息的时间顺序",
        )

    def create_topic_flow(
        self,
        messages: list[dict[str, Any]],
    ) -> ConversationVisualization:
        """创建话题流可视化"""
        transitions: list[dict[str, Any]] = []
        current_topic = None

        for msg in messages:
            topic = msg.get("topic")
            if topic and topic != current_topic:
                if current_topic:
                    transitions.append({
                        "from": current_topic,
                        "to": topic,
                        "message_index": messages.index(msg),
                    })
                current_topic = topic

        # 统计话题分布
        topic_counts: dict[str, int] = {}
        for msg in messages:
            topic = msg.get("topic")
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return ConversationVisualization(
            visualization_type=VisualizationType.TOPIC_FLOW,
            data={
                "transitions": transitions,
                "distribution": topic_counts,
            },
            title="话题流向",
            description="显示对话中话题的变化",
        )

    def create_intent_distribution(
        self,
        messages: list[dict[str, Any]],
    ) -> ConversationVisualization:
        """创建意图分布可视化"""
        intent_counts: dict[str, int] = {}

        for msg in messages:
            intent = msg.get("intent")
            if intent:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

        total = sum(intent_counts.values()) if intent_counts else 1
        percentages = {
            intent: count / total * 100
            for intent, count in intent_counts.items()
        }

        return ConversationVisualization(
            visualization_type=VisualizationType.INTENT_DISTRIBUTION,
            data={
                "counts": intent_counts,
                "percentages": percentages,
            },
            title="意图分布",
            description="显示对话中各意图的比例",
        )

    def create_sentiment_trend(
        self,
        sentiment_results: list[dict[str, Any]],
    ) -> ConversationVisualization:
        """创建情感趋势可视化"""
        trend_data: list[dict[str, Any]] = []

        for i, result in enumerate(sentiment_results):
            trend_data.append({
                "index": i,
                "sentiment": result.get("sentiment", "neutral"),
                "confidence": result.get("confidence", 0.5),
                "intensity": result.get("intensity", 0.5),
            })

        return ConversationVisualization(
            visualization_type=VisualizationType.SENTIMENT_TREND,
            data={"trend": trend_data},
            title="情感趋势",
            description="显示对话中用户情感的变化",
        )

    def create_summary_card(
        self,
        summary: EnhancedConversationSummary,
    ) -> ConversationVisualization:
        """创建摘要卡片可视化"""
        return ConversationVisualization(
            visualization_type=VisualizationType.SUMMARY_CARD,
            data={
                "session_id": summary.session_id,
                "message_count": summary.message_count,
                "duration": f"{summary.duration:.1f}s",
                "main_topics": summary.main_topics,
                "main_intents": summary.main_intents,
                "interaction_quality": f"{summary.interaction_quality * 100:.0f}%",
                "user_engagement": f"{summary.user_engagement * 100:.0f}%",
                "key_points": summary.key_points,
                "suggestions": summary.suggestions,
            },
            title="对话摘要卡片",
            description="对话的关键信息摘要",
        )


class EnhancedConversationManager:
    """增强对话管理器

    整合情感分析、个性化和可视化功能。

    使用示例:
        manager = EnhancedConversationManager()
        sentiment = manager.analyze_sentiment("这个功能太棒了！")
        config = manager.get_user_config("user_123")
    """

    def __init__(self) -> None:
        """初始化增强对话管理器"""
        self._sentiment_analyzer = SentimentAnalyzer()
        self._personalization_engine = PersonalizationEngine()
        self._visualizer = ConversationVisualizer()
        self._sentiment_history: dict[str, list[SentimentResult]] = {}
        self._lock = threading.Lock()

    def analyze_sentiment(
        self,
        text: str,
        session_id: Optional[str] = None,
    ) -> SentimentResult:
        """分析情感"""
        result = self._sentiment_analyzer.analyze(text)

        if session_id:
            with self._lock:
                if session_id not in self._sentiment_history:
                    self._sentiment_history[session_id] = []
                self._sentiment_history[session_id].append(result)

        return result

    def get_user_config(
        self,
        user_id: str,
        initial_config: Optional[PersonalizationConfig] = None,
    ) -> PersonalizationConfig:
        """获取用户配置"""
        return self._personalization_engine.get_or_create_config(user_id, initial_config)

    def update_user_config(
        self,
        user_id: str,
        **kwargs: Any,
    ) -> PersonalizationConfig:
        """更新用户配置"""
        return self._personalization_engine.update_config(user_id, **kwargs)

    def personalize_response(
        self,
        response: str,
        user_id: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """个性化响应"""
        config = self.get_user_config(user_id)
        return self._personalization_engine.personalize_response(response, config, context)

    def get_response_template(
        self,
        user_id: str,
        template_key: str,
    ) -> str:
        """获取响应模板"""
        config = self.get_user_config(user_id)
        return self._personalization_engine.get_template(config, template_key)

    def create_visualization(
        self,
        visualization_type: VisualizationType,
        data: Any,
    ) -> ConversationVisualization:
        """创建可视化"""
        if visualization_type == VisualizationType.TIMELINE:
            return self._visualizer.create_timeline(data)
        elif visualization_type == VisualizationType.TOPIC_FLOW:
            return self._visualizer.create_topic_flow(data)
        elif visualization_type == VisualizationType.INTENT_DISTRIBUTION:
            return self._visualizer.create_intent_distribution(data)
        elif visualization_type == VisualizationType.SENTIMENT_TREND:
            return self._visualizer.create_sentiment_trend(data)
        else:
            return ConversationVisualization(
                visualization_type=visualization_type,
                data=data,
                title="自定义可视化",
            )

    def generate_enhanced_summary(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
        base_summary: Optional[dict[str, Any]] = None,
    ) -> EnhancedConversationSummary:
        """生成增强摘要"""
        # 计算情感摘要
        sentiment_results = self._sentiment_history.get(session_id, [])
        sentiment_trend = self._sentiment_analyzer.analyze_conversation_trend(messages)

        # 计算交互质量
        interaction_quality = self._calculate_interaction_quality(messages, sentiment_results)

        # 计算用户参与度
        user_engagement = self._calculate_user_engagement(messages)

        # 生成建议
        suggestions = self._generate_suggestions(messages, sentiment_trend)

        # 生成后续行动
        follow_up_actions = self._generate_follow_up_actions(messages)

        return EnhancedConversationSummary(
            session_id=session_id,
            message_count=len(messages),
            duration=messages[-1].get("timestamp", time.time()) - messages[0].get("timestamp", time.time()) if messages else 0,
            main_topics=base_summary.get("main_topics", []) if base_summary else [],
            main_intents=base_summary.get("main_intents", []) if base_summary else [],
            entities_mentioned=base_summary.get("entities_mentioned", {}) if base_summary else {},
            key_points=base_summary.get("key_points", []) if base_summary else [],
            sentiment_summary=sentiment_trend,
            interaction_quality=interaction_quality,
            user_engagement=user_engagement,
            suggestions=suggestions,
            follow_up_actions=follow_up_actions,
        )

    def _calculate_interaction_quality(
        self,
        messages: list[dict[str, Any]],
        sentiment_results: list[SentimentResult],
    ) -> float:
        """计算交互质量"""
        if not messages:
            return 0.0

        # 基于情感和响应质量计算
        positive_count = sum(1 for r in sentiment_results if r.sentiment == SentimentType.POSITIVE)
        negative_count = sum(1 for r in sentiment_results if r.sentiment in [SentimentType.NEGATIVE, SentimentType.FRUSTRATED])

        total = len(sentiment_results) if sentiment_results else 1
        quality = (positive_count - negative_count * 0.5) / total

        return max(0.0, min(1.0, quality + 0.5))

    def _calculate_user_engagement(self, messages: list[dict[str, Any]]) -> float:
        """计算用户参与度"""
        if not messages:
            return 0.0

        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return 0.0

        # 基于消息长度和频率计算
        avg_length = sum(len(m.get("content", "")) for m in user_messages) / len(user_messages)
        engagement = min(avg_length / 100, 1.0)

        return engagement

    def _generate_suggestions(
        self,
        messages: list[dict[str, Any]],
        sentiment_trend: dict[str, Any],
    ) -> list[str]:
        """生成建议"""
        suggestions = []

        if sentiment_trend.get("direction") == "declining":
            suggestions.append("考虑调整对话策略，用户似乎遇到了困难")

        if sentiment_trend.get("dominant_sentiment") == "frustrated":
            suggestions.append("用户可能感到沮丧，建议提供更详细的指导")

        if sentiment_trend.get("dominant_sentiment") == "confused":
            suggestions.append("用户似乎有些困惑，建议提供更多示例")

        return suggestions

    def _generate_follow_up_actions(self, messages: list[dict[str, Any]]) -> list[str]:
        """生成后续行动"""
        actions = []

        # 检查未完成的意图
        intents = [m.get("intent") for m in messages if m.get("intent")]

        if "diagnose_error" in intents:
            actions.append("检查错误是否已解决")

        if "generate_code" in intents:
            actions.append("验证生成的代码是否正常工作")

        if "create_entity" in intents or "create_item" in intents:
            actions.append("确认实体/物品是否正确创建")

        return actions[:5]  # 最多 5 个

    def get_sentiment_stats(self, session_id: str) -> dict[str, Any]:
        """获取情感统计"""
        results = self._sentiment_history.get(session_id, [])
        if not results:
            return {"total": 0, "distribution": {}}

        distribution: dict[SentimentType, int] = {}
        for result in results:
            distribution[result.sentiment] = distribution.get(result.sentiment, 0) + 1

        return {
            "total": len(results),
            "distribution": {s.value: c for s, c in distribution.items()},
            "average_confidence": sum(r.confidence for r in results) / len(results),
            "average_intensity": sum(r.intensity for r in results) / len(results),
        }

    def record_feedback(
        self,
        user_id: str,
        feedback: dict[str, Any],
    ) -> None:
        """记录用户反馈"""
        self._personalization_engine.learn_from_feedback(user_id, feedback)


# 全局实例
_enhanced_manager: Optional[EnhancedConversationManager] = None


def get_enhanced_conversation_manager() -> EnhancedConversationManager:
    """获取全局增强对话管理器"""
    global _enhanced_manager
    if _enhanced_manager is None:
        _enhanced_manager = EnhancedConversationManager()
    return _enhanced_manager


def analyze_sentiment(text: str, session_id: Optional[str] = None) -> SentimentResult:
    """便捷函数：分析情感"""
    return get_enhanced_conversation_manager().analyze_sentiment(text, session_id)


def get_user_config(user_id: str) -> PersonalizationConfig:
    """便捷函数：获取用户配置"""
    return get_enhanced_conversation_manager().get_user_config(user_id)


def personalize_response(
    response: str,
    user_id: str,
    context: Optional[dict[str, Any]] = None,
) -> str:
    """便捷函数：个性化响应"""
    return get_enhanced_conversation_manager().personalize_response(response, user_id, context)