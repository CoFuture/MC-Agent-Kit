"""
多语言支持模块

提供多语言提示模板、语言自动检测、翻译集成等功能。
"""

from __future__ import annotations

import hashlib
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class LanguageCode(Enum):
    """语言代码"""
    ZH_CN = "zh_CN"  # 简体中文
    ZH_TW = "zh_TW"  # 繁体中文
    EN_US = "en_US"  # 英文
    JA_JP = "ja_JP"  # 日文
    KO_KR = "ko_KR"  # 韩文
    FR_FR = "fr_FR"  # 法文
    DE_DE = "de_DE"  # 德文
    ES_ES = "es_ES"  # 西班牙文
    PT_BR = "pt_BR"  # 葡萄牙文
    RU_RU = "ru_RU"  # 俄文


class DetectionMethod(Enum):
    """检测方法"""
    CHARSET = "charset"
    VOCABULARY = "vocabulary"
    NGRAM = "ngram"
    RULE = "rule"


@dataclass
class LanguageDetectionResult:
    """语言检测结果"""
    language: LanguageCode
    confidence: float
    method: DetectionMethod
    alternatives: list[tuple[LanguageCode, float]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language.value,
            "confidence": self.confidence,
            "method": self.method.value,
            "alternatives": [(lang.value, conf) for lang, conf in self.alternatives],
        }


@dataclass
class MultilingualTemplate:
    """多语言模板"""
    template_id: str
    translations: dict[LanguageCode, str]
    variables: list[str] = field(default_factory=list)
    description: str = ""

    def render(
        self,
        language: LanguageCode,
        **kwargs: Any,
    ) -> str:
        """渲染模板"""
        template = self.translations.get(language, self.translations.get(LanguageCode.EN_US, ""))
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "translations": {lang.value: text for lang, text in self.translations.items()},
            "variables": self.variables,
            "description": self.description,
        }


@dataclass
class TranslationResult:
    """翻译结果"""
    original_text: str
    translated_text: str
    source_language: LanguageCode
    target_language: LanguageCode
    confidence: float
    provider: str = "internal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "confidence": self.confidence,
            "provider": self.provider,
        }


@dataclass
class LanguagePreference:
    """语言偏好"""
    primary_language: LanguageCode = LanguageCode.ZH_CN
    fallback_language: LanguageCode = LanguageCode.EN_US
    auto_detect: bool = True
    translate_unknown: bool = True
    preferred_response_language: Optional[LanguageCode] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_language": self.primary_language.value,
            "fallback_language": self.fallback_language.value,
            "auto_detect": self.auto_detect,
            "translate_unknown": self.translate_unknown,
            "preferred_response_language": self.preferred_response_language.value if self.preferred_response_language else None,
        }


class LanguageDetector:
    """语言检测器

    自动检测文本语言。

    使用示例:
        detector = LanguageDetector()
        result = detector.detect("Hello world")
        print(result.language)  # LanguageCode.EN_US
    """

    def __init__(self) -> None:
        """初始化语言检测器"""
        # 字符范围映射
        self._charset_ranges: dict[LanguageCode, list[tuple[int, int]]] = {
            LanguageCode.ZH_CN: [
                (0x4E00, 0x9FFF),  # CJK Unified Ideographs
                (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
            ],
            LanguageCode.ZH_TW: [
                (0x4E00, 0x9FFF),
            ],
            LanguageCode.JA_JP: [
                (0x3040, 0x309F),  # Hiragana
                (0x30A0, 0x30FF),  # Katakana
                (0x4E00, 0x9FFF),  # Kanji
            ],
            LanguageCode.KO_KR: [
                (0xAC00, 0xD7AF),  # Hangul Syllables
                (0x1100, 0x11FF),  # Hangul Jamo
            ],
            LanguageCode.RU_RU: [
                (0x0400, 0x04FF),  # Cyrillic
            ],
        }

        # 词汇特征
        self._vocabulary_features: dict[LanguageCode, dict[str, float]] = {
            LanguageCode.ZH_CN: {
                "的": 0.9, "是": 0.8, "在": 0.7, "有": 0.7, "和": 0.6,
                "了": 0.8, "不": 0.6, "这": 0.5, "我": 0.6, "他": 0.5,
            },
            LanguageCode.EN_US: {
                "the": 0.9, "is": 0.8, "are": 0.8, "and": 0.7, "to": 0.7,
                "of": 0.7, "a": 0.6, "in": 0.6, "that": 0.5, "for": 0.5,
            },
            LanguageCode.JA_JP: {
                "は": 0.9, "の": 0.8, "に": 0.8, "が": 0.7, "を": 0.7,
                "です": 0.8, "ます": 0.7, "て": 0.6, "で": 0.6, "と": 0.5,
            },
            LanguageCode.KO_KR: {
                "은": 0.8, "는": 0.8, "이": 0.7, "가": 0.7, "을": 0.7,
                "를": 0.7, "에": 0.6, "의": 0.6, "와": 0.5, "과": 0.5,
            },
        }

        # 常见词汇
        self._common_words: dict[LanguageCode, set[str]] = {
            LanguageCode.ZH_CN: {"的", "是", "在", "有", "和", "了", "不", "这", "我", "他", "她", "它", "们", "要", "会", "能", "做", "说", "看", "去"},
            LanguageCode.EN_US: {"the", "is", "are", "and", "to", "of", "a", "in", "that", "for", "it", "with", "as", "be", "on", "at", "by", "this", "we", "you"},
            LanguageCode.JA_JP: {"は", "の", "に", "が", "を", "です", "ます", "て", "で", "と", "する", "ある", "いる", "なる", "もの", "こと", "これ", "それ", "あれ", "どこ"},
            LanguageCode.KO_KR: {"은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "하다", "있다", "없다", "되다", "이것", "그것", "저것", "우리", "그들", "사람"},
        }

    def detect(
        self,
        text: str,
        methods: Optional[list[DetectionMethod]] = None,
    ) -> LanguageDetectionResult:
        """检测语言

        Args:
            text: 要检测的文本
            methods: 检测方法列表

        Returns:
            LanguageDetectionResult: 检测结果
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language=LanguageCode.EN_US,
                confidence=0.0,
                method=DetectionMethod.RULE,
            )

        methods = methods or [DetectionMethod.CHARSET, DetectionMethod.VOCABULARY]

        scores: dict[LanguageCode, float] = {}

        if DetectionMethod.CHARSET in methods:
            charset_scores = self._detect_by_charset(text)
            for lang, score in charset_scores.items():
                scores[lang] = scores.get(lang, 0) + score * 0.6

        if DetectionMethod.VOCABULARY in methods:
            vocab_scores = self._detect_by_vocabulary(text)
            for lang, score in vocab_scores.items():
                scores[lang] = scores.get(lang, 0) + score * 0.4

        if not scores:
            return LanguageDetectionResult(
                language=LanguageCode.EN_US,
                confidence=0.5,
                method=DetectionMethod.RULE,
            )

        # 排序结果
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_lang = sorted_results[0][0]
        best_score = sorted_results[0][1]

        # 归一化置信度
        confidence = min(best_score / 1.0, 1.0)

        # 替代语言
        alternatives = [
            (lang, score / 1.0)
            for lang, score in sorted_results[1:4]
            if score > 0.1
        ]

        return LanguageDetectionResult(
            language=best_lang,
            confidence=confidence,
            method=DetectionMethod.CHARSET if DetectionMethod.CHARSET in methods else DetectionMethod.VOCABULARY,
            alternatives=alternatives,
        )

    def _detect_by_charset(self, text: str) -> dict[LanguageCode, float]:
        """通过字符集检测"""
        scores: dict[LanguageCode, float] = {}
        total_chars = len(text)

        if total_chars == 0:
            return scores

        for lang, ranges in self._charset_ranges.items():
            count = 0
            for char in text:
                code = ord(char)
                for start, end in ranges:
                    if start <= code <= end:
                        count += 1
                        break

            ratio = count / total_chars
            if ratio > 0.1:
                scores[lang] = ratio

        return scores

    def _detect_by_vocabulary(self, text: str) -> dict[LanguageCode, float]:
        """通过词汇检测"""
        scores: dict[LanguageCode, float] = {}

        # 分词（简化）
        words = set(re.findall(r'\w+', text.lower()))

        for lang, features in self._vocabulary_features.items():
            score = 0.0
            for word in words:
                if word in features:
                    score += features[word]
            if score > 0:
                scores[lang] = score / max(len(words), 1)

        return scores

    def detect_batch(
        self,
        texts: list[str],
    ) -> list[LanguageDetectionResult]:
        """批量检测"""
        return [self.detect(text) for text in texts]


class MultilingualTemplateRegistry:
    """多语言模板注册表

    管理多语言模板。

    使用示例:
        registry = MultilingualTemplateRegistry()
        template = registry.get_template("greeting", LanguageCode.ZH_CN)
    """

    def __init__(self) -> None:
        """初始化模板注册表"""
        self._templates: dict[str, MultilingualTemplate] = {}
        self._lock = threading.Lock()

        # 注册内置模板
        self._register_builtin_templates()

    def _register_builtin_templates(self) -> None:
        """注册内置模板"""
        # 问候语
        self.register(MultilingualTemplate(
            template_id="greeting",
            translations={
                LanguageCode.ZH_CN: "你好！我是 MC-Agent-Kit 助手，有什么可以帮助你的？",
                LanguageCode.EN_US: "Hello! I'm MC-Agent-Kit assistant. How can I help you?",
                LanguageCode.JA_JP: "こんにちは！MC-Agent-Kitアシスタントです。何かお手伝いしましょうか？",
                LanguageCode.KO_KR: "안녕하세요! MC-Agent-Kit 어시스턴트입니다. 무엇을 도와드릴까요?",
                LanguageCode.FR_FR: "Bonjour! Je suis l'assistant MC-Agent-Kit. Comment puis-je vous aider?",
            },
            description="问候语模板",
        ))

        # 错误提示
        self.register(MultilingualTemplate(
            template_id="error_generic",
            translations={
                LanguageCode.ZH_CN: "抱歉，发生了错误：{{error_message}}",
                LanguageCode.EN_US: "Sorry, an error occurred: {{error_message}}",
                LanguageCode.JA_JP: "申し訳ありませんが、エラーが発生しました：{{error_message}}",
                LanguageCode.KO_KR: "죄송합니다. 오류가 발생했습니다: {{error_message}}",
                LanguageCode.FR_FR: "Désolé, une erreur s'est produite: {{error_message}}",
            },
            variables=["error_message"],
            description="通用错误提示模板",
        ))

        # 成功提示
        self.register(MultilingualTemplate(
            template_id="success_generic",
            translations={
                LanguageCode.ZH_CN: "操作成功完成！",
                LanguageCode.EN_US: "Operation completed successfully!",
                LanguageCode.JA_JP: "操作が正常に完了しました！",
                LanguageCode.KO_KR: "작업이 성공적으로 완료되었습니다!",
                LanguageCode.FR_FR: "Opération terminée avec succès!",
            },
            description="通用成功提示模板",
        ))

        # API 搜索结果
        self.register(MultilingualTemplate(
            template_id="api_search_result",
            translations={
                LanguageCode.ZH_CN: "找到 {{count}} 个相关的 API：\n{{results}}",
                LanguageCode.EN_US: "Found {{count}} related APIs:\n{{results}}",
                LanguageCode.JA_JP: "{{count}}件の関連APIが見つかりました：\n{{results}}",
                LanguageCode.KO_KR: "{{count}}개의 관련 API를 찾았습니다:\n{{results}}",
                LanguageCode.FR_FR: "Trouvé {{count}} API connexes:\n{{results}}",
            },
            variables=["count", "results"],
            description="API 搜索结果模板",
        ))

        # 代码生成
        self.register(MultilingualTemplate(
            template_id="code_generated",
            translations={
                LanguageCode.ZH_CN: "已为你生成代码：\n\n```{{language}}\n{{code}}\n```\n\n{{notes}}",
                LanguageCode.EN_US: "Generated code for you:\n\n```{{language}}\n{{code}}\n```\n\n{{notes}}",
                LanguageCode.JA_JP: "コードを生成しました：\n\n```{{language}}\n{{code}}\n```\n\n{{notes}}",
                LanguageCode.KO_KR: "코드가 생성되었습니다:\n\n```{{language}}\n{{code}}\n```\n\n{{notes}}",
                LanguageCode.FR_FR: "Code généré pour vous:\n\n```{{language}}\n{{code}}\n```\n\n{{notes}}",
            },
            variables=["language", "code", "notes"],
            description="代码生成模板",
        ))

        # 帮助提示
        self.register(MultilingualTemplate(
            template_id="help_prompt",
            translations={
                LanguageCode.ZH_CN: "我可以帮助你：\n1. 搜索 API 和事件\n2. 生成代码\n3. 诊断错误\n4. 创建项目\n\n请告诉我你需要什么？",
                LanguageCode.EN_US: "I can help you:\n1. Search APIs and events\n2. Generate code\n3. Diagnose errors\n4. Create projects\n\nWhat do you need?",
                LanguageCode.JA_JP: "お手伝いできること：\n1. APIとイベントの検索\n2. コードの生成\n3. エラーの診断\n4. プロジェクトの作成\n\n何が必要ですか？",
                LanguageCode.KO_KR: "도와드릴 수 있는 것:\n1. API 및 이벤트 검색\n2. 코드 생성\n3. 오류 진단\n4. 프로젝트 생성\n\n무엇이 필요하신가요?",
                LanguageCode.FR_FR: "Je peux vous aider:\n1. Rechercher des API et événements\n2. Générer du code\n3. Diagnostiquer des erreurs\n4. Créer des projets\n\nDe quoi avez-vous besoin?",
            },
            description="帮助提示模板",
        ))

        # 澄清请求
        self.register(MultilingualTemplate(
            template_id="clarification_needed",
            translations={
                LanguageCode.ZH_CN: "抱歉，我不太理解你的意思。你能再详细说明一下吗？",
                LanguageCode.EN_US: "Sorry, I don't quite understand. Could you explain in more detail?",
                LanguageCode.JA_JP: "申し訳ありませんが、よく理解できません。もう少し詳しく説明していただけますか？",
                LanguageCode.KO_KR: "죄송합니다. 잘 이해하지 못했습니다. 더 자세히 설명해 주시겠어요?",
                LanguageCode.FR_FR: "Désolé, je ne comprends pas bien. Pourriez-vous expliquer plus en détail?",
            },
            description="澄清请求模板",
        ))

        # 实体创建
        self.register(MultilingualTemplate(
            template_id="entity_created",
            translations={
                LanguageCode.ZH_CN: "实体 '{{entity_name}}' 创建成功！\n\n类型: {{entity_type}}\n行为: {{behavior}}\n\n你可以在项目中使用这个实体。",
                LanguageCode.EN_US: "Entity '{{entity_name}}' created successfully!\n\nType: {{entity_type}}\nBehavior: {{behavior}}\n\nYou can use this entity in your project.",
                LanguageCode.JA_JP: "エンティティ'{{entity_name}}'が正常に作成されました！\n\nタイプ: {{entity_type}}\n動作: {{behavior}}\n\nこのエンティティをプロジェクトで使用できます。",
                LanguageCode.KO_KR: "엔티티 '{{entity_name}}'이(가) 성공적으로 생성되었습니다!\n\n유형: {{entity_type}}\n동작: {{behavior}}\n\n프로젝트에서 이 엔티티를 사용할 수 있습니다.",
                LanguageCode.FR_FR: "L'entité '{{entity_name}}' a été créée avec succès!\n\nType: {{entity_type}}\nComportement: {{behavior}}\n\nVous pouvez utiliser cette entité dans votre projet.",
            },
            variables=["entity_name", "entity_type", "behavior"],
            description="实体创建成功模板",
        ))

    def register(self, template: MultilingualTemplate) -> None:
        """注册模板"""
        with self._lock:
            self._templates[template.template_id] = template

    def get_template(
        self,
        template_id: str,
        language: LanguageCode,
        **kwargs: Any,
    ) -> str:
        """获取并渲染模板"""
        template = self._templates.get(template_id)
        if not template:
            return f"[Missing template: {template_id}]"

        return template.render(language, **kwargs)

    def list_templates(self) -> list[str]:
        """列出所有模板"""
        return list(self._templates.keys())

    def get_template_info(self, template_id: str) -> Optional[dict[str, Any]]:
        """获取模板信息"""
        template = self._templates.get(template_id)
        return template.to_dict() if template else None


class TranslationService:
    """翻译服务

    提供文本翻译功能。

    使用示例:
        service = TranslationService()
        result = service.translate("Hello", LanguageCode.EN_US, LanguageCode.ZH_CN)
    """

    def __init__(self) -> None:
        """初始化翻译服务"""
        self._cache: OrderedDict[str, TranslationResult] = OrderedDict()
        self._max_cache_size = 1000
        self._lock = threading.Lock()

        # 内置翻译词典（常用词汇）
        self._builtin_translations: dict[tuple[str, str], str] = {
            # 英 -> 中
            ("hello", "en_zh"): "你好",
            ("help", "en_zh"): "帮助",
            ("create", "en_zh"): "创建",
            ("entity", "en_zh"): "实体",
            ("item", "en_zh"): "物品",
            ("block", "en_zh"): "方块",
            ("error", "en_zh"): "错误",
            ("success", "en_zh"): "成功",
            ("api", "en_zh"): "API",
            ("event", "en_zh"): "事件",
            # 中 -> 英
            ("你好", "zh_en"): "Hello",
            ("帮助", "zh_en"): "Help",
            ("创建", "zh_en"): "Create",
            ("实体", "zh_en"): "Entity",
            ("物品", "zh_en"): "Item",
            ("方块", "zh_en"): "Block",
            ("错误", "zh_en"): "Error",
            ("成功", "zh_en"): "Success",
        }

    def translate(
        self,
        text: str,
        source_language: LanguageCode,
        target_language: LanguageCode,
    ) -> TranslationResult:
        """翻译文本"""
        # 检查缓存
        cache_key = self._make_cache_key(text, source_language, target_language)
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        # 检查内置翻译
        builtin_result = self._try_builtin_translation(text, source_language, target_language)
        if builtin_result:
            with self._lock:
                self._cache[cache_key] = builtin_result
            return builtin_result

        # 如果没有翻译器，返回原文
        result = TranslationResult(
            original_text=text,
            translated_text=text,
            source_language=source_language,
            target_language=target_language,
            confidence=0.0,
            provider="none",
        )

        with self._lock:
            self._cache[cache_key] = result

        return result

    def _try_builtin_translation(
        self,
        text: str,
        source_language: LanguageCode,
        target_language: LanguageCode,
    ) -> Optional[TranslationResult]:
        """尝试使用内置翻译"""
        key = f"{source_language.value[:2]}_{target_language.value[:2]}"

        translation = self._builtin_translations.get((text.lower(), key))
        if translation:
            return TranslationResult(
                original_text=text,
                translated_text=translation,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0,
                provider="builtin",
            )

        return None

    def _make_cache_key(
        self,
        text: str,
        source_language: LanguageCode,
        target_language: LanguageCode,
    ) -> str:
        """生成缓存键"""
        content = f"{text}:{source_language.value}:{target_language.value}"
        return hashlib.md5(content.encode()).hexdigest()

    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


class MultilingualService:
    """多语言服务

    整合语言检测、模板管理和翻译功能。

    使用示例:
        service = MultilingualService()
        lang = service.detect_language("你好世界")
        message = service.get_message("greeting", lang.language)
    """

    def __init__(self) -> None:
        """初始化多语言服务"""
        self._detector = LanguageDetector()
        self._template_registry = MultilingualTemplateRegistry()
        self._translation_service = TranslationService()
        self._user_preferences: dict[str, LanguagePreference] = {}
        self._lock = threading.Lock()

    def detect_language(
        self,
        text: str,
        methods: Optional[list[DetectionMethod]] = None,
    ) -> LanguageDetectionResult:
        """检测语言"""
        return self._detector.detect(text, methods)

    def get_message(
        self,
        template_id: str,
        language: LanguageCode,
        **kwargs: Any,
    ) -> str:
        """获取多语言消息"""
        return self._template_registry.get_template(template_id, language, **kwargs)

    def translate(
        self,
        text: str,
        target_language: LanguageCode,
        source_language: Optional[LanguageCode] = None,
    ) -> TranslationResult:
        """翻译文本"""
        if source_language is None:
            detection = self.detect_language(text)
            source_language = detection.language

        return self._translation_service.translate(
            text,
            source_language,
            target_language,
        )

    def set_user_preference(
        self,
        user_id: str,
        preference: LanguagePreference,
    ) -> None:
        """设置用户语言偏好"""
        with self._lock:
            self._user_preferences[user_id] = preference

    def get_user_preference(self, user_id: str) -> LanguagePreference:
        """获取用户语言偏好"""
        with self._lock:
            return self._user_preferences.get(user_id, LanguagePreference())

    def auto_respond_language(
        self,
        user_id: str,
        input_text: str,
    ) -> LanguageCode:
        """自动确定响应语言"""
        preference = self.get_user_preference(user_id)

        # 如果用户指定了偏好响应语言
        if preference.preferred_response_language:
            return preference.preferred_response_language

        # 如果启用了自动检测
        if preference.auto_detect:
            detection = self.detect_language(input_text)
            if detection.confidence > 0.7:
                return detection.language

        # 返回主要语言
        return preference.primary_language

    def register_template(self, template: MultilingualTemplate) -> None:
        """注册自定义模板"""
        self._template_registry.register(template)

    def list_templates(self) -> list[str]:
        """列出所有模板"""
        return self._template_registry.list_templates()

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return [lang.value for lang in LanguageCode]


# 全局实例
_multilingual_service: Optional[MultilingualService] = None


def get_multilingual_service() -> MultilingualService:
    """获取全局多语言服务"""
    global _multilingual_service
    if _multilingual_service is None:
        _multilingual_service = MultilingualService()
    return _multilingual_service


def detect_language(text: str) -> LanguageDetectionResult:
    """便捷函数：检测语言"""
    return get_multilingual_service().detect_language(text)


def get_message(
    template_id: str,
    language: LanguageCode = LanguageCode.ZH_CN,
    **kwargs: Any,
) -> str:
    """便捷函数：获取多语言消息"""
    return get_multilingual_service().get_message(template_id, language, **kwargs)


def translate(
    text: str,
    target_language: LanguageCode,
    source_language: Optional[LanguageCode] = None,
) -> TranslationResult:
    """便捷函数：翻译文本"""
    return get_multilingual_service().translate(text, target_language, source_language)