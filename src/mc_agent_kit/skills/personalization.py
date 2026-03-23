"""
个性化适配模块

提供用户偏好记忆、项目上下文管理、常用模式学习和跨会话记忆持久化。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class PreferenceType(Enum):
    """偏好类型"""
    CODE_STYLE = "code_style"           # 代码风格
    NAMING = "naming"                   # 命名约定
    MODULE = "module"                   # 模块偏好
    PATTERN = "pattern"                 # 代码模式
    API = "api"                         # API 偏好
    LANGUAGE = "language"               # 语言偏好
    INDENTATION = "indentation"         # 缩进风格
    QUOTES = "quotes"                   # 引号风格
    BRACKETS = "brackets"               # 括号风格
    COMMENTS = "comments"               # 注释风格
    SCOPE = "scope"                     # 作用域偏好
    TEMPLATES = "templates"             # 模板偏好


class PatternFrequency(Enum):
    """模式频率"""
    RARE = "rare"           # 很少使用
    OCCASIONAL = "occasional"   # 偶尔使用
    FREQUENT = "frequent"       # 经常使用
    CONSTANT = "constant"       # 持续使用


@dataclass
class UserPreference:
    """用户偏好"""
    id: str
    preference_type: PreferenceType
    key: str
    value: Any
    confidence: float = 1.0
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    created_at: float = field(default_factory=time.time)
    source: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "preference_type": self.preference_type.value,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "created_at": self.created_at,
            "source": self.source,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreference":
        """从字典创建"""
        return cls(
            id=data["id"],
            preference_type=PreferenceType(data["preference_type"]),
            key=data["key"],
            value=data["value"],
            confidence=data.get("confidence", 1.0),
            last_used=data.get("last_used", time.time()),
            use_count=data.get("use_count", 0),
            created_at=data.get("created_at", time.time()),
            source=data.get("source", ""),
            context=data.get("context", {}),
        )


@dataclass
class ProjectContext:
    """项目上下文"""
    project_id: str
    name: str
    path: str = ""
    used_modules: set[str] = field(default_factory=set)
    used_apis: set[str] = field(default_factory=set)
    used_events: set[str] = field(default_factory=set)
    code_style: dict[str, Any] = field(default_factory=dict)
    custom_patterns: list[str] = field(default_factory=list)
    scope: str = "both"  # server, client, both
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "path": self.path,
            "used_modules": list(self.used_modules),
            "used_apis": list(self.used_apis),
            "used_events": list(self.used_events),
            "code_style": self.code_style,
            "custom_patterns": self.custom_patterns,
            "scope": self.scope,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectContext":
        """从字典创建"""
        return cls(
            project_id=data["project_id"],
            name=data["name"],
            path=data.get("path", ""),
            used_modules=set(data.get("used_modules", [])),
            used_apis=set(data.get("used_apis", [])),
            used_events=set(data.get("used_events", [])),
            code_style=data.get("code_style", {}),
            custom_patterns=data.get("custom_patterns", []),
            scope=data.get("scope", "both"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UsagePattern:
    """使用模式"""
    id: str
    pattern_name: str
    pattern_type: str
    elements: list[str]           # 模式元素（API、事件等）
    frequency: PatternFrequency
    occurrence_count: int
    first_seen: float
    last_seen: float
    contexts: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "pattern_name": self.pattern_name,
            "pattern_type": self.pattern_type,
            "elements": self.elements,
            "frequency": self.frequency.value,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "contexts": self.contexts,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsagePattern":
        """从字典创建"""
        return cls(
            id=data["id"],
            pattern_name=data["pattern_name"],
            pattern_type=data["pattern_type"],
            elements=data.get("elements", []),
            frequency=PatternFrequency(data.get("frequency", "occasional")),
            occurrence_count=data.get("occurrence_count", 0),
            first_seen=data.get("first_seen", time.time()),
            last_seen=data.get("last_seen", time.time()),
            contexts=data.get("contexts", []),
            confidence=data.get("confidence", 0.0),
        )


@dataclass
class SessionMemory:
    """会话记忆"""
    session_id: str
    user_id: str
    project_id: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    interactions: list[dict[str, Any]] = field(default_factory=list)
    preferences_learned: list[str] = field(default_factory=list)
    patterns_detected: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "interactions": self.interactions,
            "preferences_learned": self.preferences_learned,
            "patterns_detected": self.patterns_detected,
            "summary": self.summary,
        }


@dataclass
class PersonalizationResult:
    """个性化结果"""
    original: str
    adapted: str
    changes: list[dict[str, Any]]
    confidence: float
    applied_preferences: list[str]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "original": self.original,
            "adapted": self.adapted,
            "changes": self.changes,
            "confidence": self.confidence,
            "applied_preferences": self.applied_preferences,
        }


@dataclass
class PersonalizationStats:
    """个性化统计"""
    total_preferences: int = 0
    total_projects: int = 0
    total_patterns: int = 0
    sessions_recorded: int = 0
    adaptations_made: int = 0
    average_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_preferences": self.total_preferences,
            "total_projects": self.total_projects,
            "total_patterns": self.total_patterns,
            "sessions_recorded": self.sessions_recorded,
            "adaptations_made": self.adaptations_made,
            "average_confidence": self.average_confidence,
        }


class PreferenceManager:
    """偏好管理器

    管理用户偏好。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
    ) -> None:
        """初始化偏好管理器"""
        self._storage_path = storage_path or Path.home() / ".mc_agent_kit" / "personalization"
        self._preferences: dict[str, UserPreference] = {}
        self._preferences_by_type: dict[PreferenceType, list[str]] = defaultdict(list)
        self._lock = threading.RLock()

        # 加载已有偏好
        self._load_preferences()

    def record_preference(
        self,
        preference_type: PreferenceType,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> UserPreference:
        """记录偏好"""
        pref_id = self._generate_id(preference_type, key)

        with self._lock:
            # 检查是否已存在
            existing = self._preferences.get(pref_id)
            if existing:
                # 更新已有偏好
                existing.value = value
                existing.confidence = min(1.0, existing.confidence + 0.1)
                existing.use_count += 1
                existing.last_used = time.time()
                if source:
                    existing.source = source
                if context:
                    existing.context.update(context)
                self._save_preferences()
                return existing

            # 创建新偏好
            preference = UserPreference(
                id=pref_id,
                preference_type=preference_type,
                key=key,
                value=value,
                confidence=confidence,
                source=source,
                context=context or {},
            )

            self._preferences[pref_id] = preference
            self._preferences_by_type[preference_type].append(pref_id)

        self._save_preferences()
        return preference

    def get_preference(
        self,
        preference_type: PreferenceType,
        key: str,
    ) -> Optional[UserPreference]:
        """获取偏好"""
        pref_id = self._generate_id(preference_type, key)
        return self._preferences.get(pref_id)

    def get_preferences_by_type(
        self,
        preference_type: PreferenceType,
    ) -> list[UserPreference]:
        """按类型获取偏好"""
        with self._lock:
            pref_ids = self._preferences_by_type.get(preference_type, [])
            return [self._preferences[pid] for pid in pref_ids if pid in self._preferences]

    def get_all_preferences(self) -> list[UserPreference]:
        """获取所有偏好"""
        return list(self._preferences.values())

    def delete_preference(
        self,
        preference_type: PreferenceType,
        key: str,
    ) -> bool:
        """删除偏好"""
        pref_id = self._generate_id(preference_type, key)

        with self._lock:
            if pref_id in self._preferences:
                preference = self._preferences[pref_id]
                del self._preferences[pref_id]
                if pref_id in self._preferences_by_type[preference.preference_type]:
                    self._preferences_by_type[preference.preference_type].remove(pref_id)
                self._save_preferences()
                return True
            return False

    def clear_preferences(
        self,
        preference_type: Optional[PreferenceType] = None,
    ) -> int:
        """清除偏好"""
        count = 0
        with self._lock:
            if preference_type:
                pref_ids = self._preferences_by_type.get(preference_type, [])
                for pref_id in pref_ids:
                    if pref_id in self._preferences:
                        del self._preferences[pref_id]
                        count += 1
                self._preferences_by_type[preference_type] = []
            else:
                count = len(self._preferences)
                self._preferences.clear()
                self._preferences_by_type.clear()

        self._save_preferences()
        return count

    def _generate_id(
        self,
        preference_type: PreferenceType,
        key: str,
    ) -> str:
        """生成偏好 ID"""
        return f"{preference_type.value}:{key}"

    def _load_preferences(self) -> None:
        """加载已存储的偏好"""
        if not self._storage_path.exists():
            return

        pref_file = self._storage_path / "preferences.json"
        if not pref_file.exists():
            return

        try:
            with open(pref_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for pref_data in data.get("preferences", []):
                preference = UserPreference.from_dict(pref_data)
                self._preferences[preference.id] = preference
                self._preferences_by_type[preference.preference_type].append(preference.id)

        except (json.JSONDecodeError, KeyError):
            pass

    def _save_preferences(self) -> None:
        """保存偏好到存储"""
        self._storage_path.mkdir(parents=True, exist_ok=True)
        pref_file = self._storage_path / "preferences.json"

        with self._lock:
            data = {
                "preferences": [p.to_dict() for p in self._preferences.values()],
                "saved_at": time.time(),
            }

        with open(pref_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class ProjectContextManager:
    """项目上下文管理器

    管理项目上下文。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
    ) -> None:
        """初始化项目上下文管理器"""
        self._storage_path = storage_path or Path.home() / ".mc_agent_kit" / "personalization"
        self._projects: dict[str, ProjectContext] = {}
        self._current_project: Optional[ProjectContext] = None
        self._lock = threading.RLock()

        # 加载已有项目
        self._load_projects()

    def create_project(
        self,
        project_id: str,
        name: str,
        path: str = "",
    ) -> ProjectContext:
        """创建项目上下文"""
        with self._lock:
            project = ProjectContext(
                project_id=project_id,
                name=name,
                path=path,
            )
            self._projects[project_id] = project
            self._current_project = project

        self._save_projects()
        return project

    def get_project(
        self,
        project_id: str,
    ) -> Optional[ProjectContext]:
        """获取项目上下文"""
        return self._projects.get(project_id)

    def get_current_project(self) -> Optional[ProjectContext]:
        """获取当前项目"""
        return self._current_project

    def set_current_project(
        self,
        project_id: str,
    ) -> Optional[ProjectContext]:
        """设置当前项目"""
        with self._lock:
            project = self._projects.get(project_id)
            if project:
                project.access_count += 1
                project.updated_at = time.time()
                self._current_project = project
            return project

    def update_project(
        self,
        project_id: str,
        updates: dict[str, Any],
    ) -> Optional[ProjectContext]:
        """更新项目上下文"""
        with self._lock:
            project = self._projects.get(project_id)
            if not project:
                return None

            # 更新模块
            if "used_modules" in updates:
                project.used_modules.update(updates["used_modules"])

            # 更新 API
            if "used_apis" in updates:
                project.used_apis.update(updates["used_apis"])

            # 更新事件
            if "used_events" in updates:
                project.used_events.update(updates["used_events"])

            # 更新代码风格
            if "code_style" in updates:
                project.code_style.update(updates["code_style"])

            # 更新自定义模式
            if "custom_patterns" in updates:
                for pattern in updates["custom_patterns"]:
                    if pattern not in project.custom_patterns:
                        project.custom_patterns.append(pattern)

            # 更新作用域
            if "scope" in updates:
                project.scope = updates["scope"]

            project.updated_at = time.time()

        self._save_projects()
        return project

    def record_api_usage(
        self,
        api_name: str,
        module: str = "",
    ) -> None:
        """记录 API 使用"""
        if self._current_project:
            with self._lock:
                self._current_project.used_apis.add(api_name)
                if module:
                    self._current_project.used_modules.add(module)
                self._current_project.updated_at = time.time()
            self._save_projects()

    def record_event_usage(
        self,
        event_name: str,
    ) -> None:
        """记录事件使用"""
        if self._current_project:
            with self._lock:
                self._current_project.used_events.add(event_name)
                self._current_project.updated_at = time.time()
            self._save_projects()

    def get_all_projects(self) -> list[ProjectContext]:
        """获取所有项目"""
        return list(self._projects.values())

    def delete_project(
        self,
        project_id: str,
    ) -> bool:
        """删除项目"""
        with self._lock:
            if project_id in self._projects:
                del self._projects[project_id]
                if self._current_project and self._current_project.project_id == project_id:
                    self._current_project = None
                self._save_projects()
                return True
            return False

    def _load_projects(self) -> None:
        """加载已存储的项目"""
        if not self._storage_path.exists():
            return

        project_file = self._storage_path / "projects.json"
        if not project_file.exists():
            return

        try:
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for project_data in data.get("projects", []):
                project = ProjectContext.from_dict(project_data)
                self._projects[project.project_id] = project

        except (json.JSONDecodeError, KeyError):
            pass

    def _save_projects(self) -> None:
        """保存项目到存储"""
        self._storage_path.mkdir(parents=True, exist_ok=True)
        project_file = self._storage_path / "projects.json"

        with self._lock:
            data = {
                "projects": [p.to_dict() for p in self._projects.values()],
                "saved_at": time.time(),
            }

        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class PatternLearner:
    """模式学习器

    学习用户常用的代码模式。
    """

    def __init__(self) -> None:
        """初始化模式学习器"""
        self._patterns: dict[str, UsagePattern] = {}
        self._pattern_index: dict[str, list[str]] = defaultdict(list)  # element -> pattern_ids
        self._lock = threading.RLock()

    def record_usage(
        self,
        elements: list[str],
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[UsagePattern]:
        """记录使用"""
        if not elements:
            return None

        # 查找或创建模式
        pattern_key = self._create_pattern_key(elements)

        with self._lock:
            if pattern_key in self._patterns:
                # 更新已有模式
                pattern = self._patterns[pattern_key]
                pattern.occurrence_count += 1
                pattern.last_seen = time.time()

                # 更新频率
                if pattern.occurrence_count >= 20:
                    pattern.frequency = PatternFrequency.CONSTANT
                elif pattern.occurrence_count >= 10:
                    pattern.frequency = PatternFrequency.FREQUENT
                elif pattern.occurrence_count >= 5:
                    pattern.frequency = PatternFrequency.OCCASIONAL

                # 记录上下文
                if context:
                    pattern.contexts.append(context)
                    if len(pattern.contexts) > 10:
                        pattern.contexts = pattern.contexts[-10:]

                pattern.confidence = min(1.0, pattern.occurrence_count / 20)
            else:
                # 创建新模式
                pattern = UsagePattern(
                    id=pattern_key,
                    pattern_name=self._generate_pattern_name(elements),
                    pattern_type=self._determine_pattern_type(elements),
                    elements=elements,
                    frequency=PatternFrequency.RARE,
                    occurrence_count=1,
                    first_seen=time.time(),
                    last_seen=time.time(),
                    contexts=[context] if context else [],
                    confidence=0.1,
                )

                self._patterns[pattern_key] = pattern

                # 建立索引
                for element in elements:
                    self._pattern_index[element].append(pattern_key)

            return pattern

    def get_patterns(
        self,
        element: Optional[str] = None,
        min_frequency: Optional[PatternFrequency] = None,
    ) -> list[UsagePattern]:
        """获取模式"""
        with self._lock:
            patterns: list[UsagePattern] = []

            if element:
                pattern_ids = self._pattern_index.get(element, [])
                patterns = [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]
            else:
                patterns = list(self._patterns.values())

            # 过滤频率
            if min_frequency:
                frequency_order = {
                    PatternFrequency.RARE: 0,
                    PatternFrequency.OCCASIONAL: 1,
                    PatternFrequency.FREQUENT: 2,
                    PatternFrequency.CONSTANT: 3,
                }
                min_order = frequency_order[min_frequency]
                patterns = [p for p in patterns if frequency_order[p.frequency] >= min_order]

            # 按出现次数排序
            patterns.sort(key=lambda p: p.occurrence_count, reverse=True)
            return patterns

    def get_related_patterns(
        self,
        elements: list[str],
    ) -> list[UsagePattern]:
        """获取相关模式"""
        related: list[UsagePattern] = []
        seen_ids: set[str] = set()

        with self._lock:
            for element in elements:
                pattern_ids = self._pattern_index.get(element, [])
                for pattern_id in pattern_ids:
                    if pattern_id not in seen_ids and pattern_id in self._patterns:
                        related.append(self._patterns[pattern_id])
                        seen_ids.add(pattern_id)

        related.sort(key=lambda p: p.occurrence_count, reverse=True)
        return related

    def clear(self) -> None:
        """清空模式"""
        with self._lock:
            self._patterns.clear()
            self._pattern_index.clear()

    def _create_pattern_key(self, elements: list[str]) -> str:
        """创建模式键"""
        sorted_elements = sorted(elements)
        return hashlib.md5("|".join(sorted_elements).encode()).hexdigest()[:12]

    def _generate_pattern_name(self, elements: list[str]) -> str:
        """生成模式名称"""
        if len(elements) <= 3:
            return " + ".join(elements)
        return f"{elements[0]} + {len(elements) - 1} others"

    def _determine_pattern_type(self, elements: list[str]) -> str:
        """确定模式类型"""
        # 简单判断
        has_api = any(e[0].isupper() for e in elements if e)
        has_event = any(e.startswith("On") for e in elements)

        if has_event:
            return "event_pattern"
        elif has_api:
            return "api_pattern"
        else:
            return "general_pattern"


class PersonalizationEngine:
    """个性化引擎

    整合偏好管理、项目上下文和模式学习。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
    ) -> None:
        """初始化个性化引擎"""
        self._storage_path = storage_path or Path.home() / ".mc_agent_kit" / "personalization"
        self._preference_manager = PreferenceManager(self._storage_path)
        self._project_manager = ProjectContextManager(self._storage_path)
        self._pattern_learner = PatternLearner()
        self._session_memories: dict[str, SessionMemory] = {}
        self._adaptations_count = 0
        self._lock = threading.RLock()

    def record_preference(
        self,
        preference_type: PreferenceType,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "",
    ) -> UserPreference:
        """记录偏好"""
        return self._preference_manager.record_preference(
            preference_type=preference_type,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
        )

    def get_preferences(
        self,
        preference_type: Optional[PreferenceType] = None,
    ) -> list[UserPreference]:
        """获取偏好"""
        if preference_type:
            return self._preference_manager.get_preferences_by_type(preference_type)
        return self._preference_manager.get_all_preferences()

    def adapt_suggestion(
        self,
        suggestion: str,
        context: Optional[dict[str, Any]] = None,
    ) -> PersonalizationResult:
        """适配建议"""
        changes: list[dict[str, Any]] = []
        applied_preferences: list[str] = []
        adapted = suggestion

        # 获取代码风格偏好
        style_prefs = self._preference_manager.get_preferences_by_type(PreferenceType.CODE_STYLE)

        for pref in style_prefs:
            if pref.key == "indentation":
                if pref.value == "tabs" and "    " in adapted:
                    adapted = adapted.replace("    ", "\t")
                    changes.append({
                        "type": "indentation",
                        "from": "spaces",
                        "to": "tabs",
                    })
                    applied_preferences.append(pref.id)
                elif pref.value == "spaces" and "\t" in adapted:
                    adapted = adapted.replace("\t", "    ")
                    changes.append({
                        "type": "indentation",
                        "from": "tabs",
                        "to": "spaces",
                    })
                    applied_preferences.append(pref.id)

            elif pref.key == "quotes":
                if pref.value == "single":
                    adapted = self._convert_quotes(adapted, "single")
                    changes.append({
                        "type": "quotes",
                        "from": "double",
                        "to": "single",
                    })
                    applied_preferences.append(pref.id)
                elif pref.value == "double":
                    adapted = self._convert_quotes(adapted, "double")
                    changes.append({
                        "type": "quotes",
                        "from": "single",
                        "to": "double",
                    })
                    applied_preferences.append(pref.id)

        # 计算置信度
        confidence = 1.0
        if applied_preferences:
            prefs = [self._preference_manager.get_preference(
                PreferenceType(pid.split(":")[0]) if ":" in pid else PreferenceType.CODE_STYLE,
                pid.split(":")[1] if ":" in pid else ""
            ) for pid in applied_preferences]
            valid_prefs = [p for p in prefs if p]
            if valid_prefs:
                confidence = sum(p.confidence for p in valid_prefs) / len(valid_prefs)

        with self._lock:
            self._adaptations_count += 1

        return PersonalizationResult(
            original=suggestion,
            adapted=adapted,
            changes=changes,
            confidence=confidence,
            applied_preferences=applied_preferences,
        )

    def save_project_context(
        self,
        project_id: str,
        name: str,
        path: str = "",
    ) -> ProjectContext:
        """保存项目上下文"""
        project = self._project_manager.get_project(project_id)
        if project:
            return project
        return self._project_manager.create_project(project_id, name, path)

    def load_project_context(
        self,
        project_id: str,
    ) -> Optional[ProjectContext]:
        """加载项目上下文"""
        return self._project_manager.set_current_project(project_id)

    def record_usage(
        self,
        elements: list[str],
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[UsagePattern]:
        """记录使用模式"""
        # 记录到模式学习器
        pattern = self._pattern_learner.record_usage(elements, context)

        # 记录到项目上下文
        if pattern:
            for element in elements:
                if element.startswith("On"):
                    self._project_manager.record_event_usage(element)
                elif element[0].isupper() if element else False:
                    self._project_manager.record_api_usage(element)

        return pattern

    def get_common_patterns(
        self,
        limit: int = 10,
    ) -> list[UsagePattern]:
        """获取常用模式"""
        return self._pattern_learner.get_patterns(min_frequency=PatternFrequency.OCCASIONAL)[:limit]

    def get_project_recommendations(
        self,
        project_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """获取项目推荐"""
        project = None
        if project_id:
            project = self._project_manager.get_project(project_id)
        else:
            project = self._project_manager.get_current_project()

        if not project:
            return []

        recommendations: list[dict[str, Any]] = []

        # 基于已使用的 API 推荐
        for api in project.used_apis:
            related_patterns = self._pattern_learner.get_related_patterns([api])
            for pattern in related_patterns[:3]:
                if pattern.occurrence_count >= 3:
                    recommendations.append({
                        "type": "pattern",
                        "api": api,
                        "pattern": pattern.pattern_name,
                        "confidence": pattern.confidence,
                    })

        # 基于已使用的模块推荐
        for module in project.used_modules:
            recommendations.append({
                "type": "module",
                "module": module,
                "suggestion": f"继续使用 {module} 模块的相关功能",
            })

        return recommendations[:10]

    def get_stats(self) -> PersonalizationStats:
        """获取个性化统计"""
        with self._lock:
            prefs = self._preference_manager.get_all_preferences()
            projects = self._project_manager.get_all_projects()
            patterns = self._pattern_learner.get_patterns()

            avg_confidence = 0.0
            if prefs:
                avg_confidence = sum(p.confidence for p in prefs) / len(prefs)

            return PersonalizationStats(
                total_preferences=len(prefs),
                total_projects=len(projects),
                total_patterns=len(patterns),
                sessions_recorded=len(self._session_memories),
                adaptations_made=self._adaptations_count,
                average_confidence=avg_confidence,
            )

    def clear_all(self) -> None:
        """清除所有个性化数据"""
        with self._lock:
            self._preference_manager.clear_preferences()
            self._pattern_learner.clear()

            # 清除项目需要逐个删除
            for project_id in list(self._project_manager._projects.keys()):
                self._project_manager.delete_project(project_id)

            self._session_memories.clear()
            self._adaptations_count = 0

    def _convert_quotes(
        self,
        text: str,
        target_style: str,
    ) -> str:
        """转换引号风格"""
        # 简单实现，不处理字符串内的引号
        if target_style == "single":
            return text.replace('"', "'")
        else:
            return text.replace("'", '"')


# 全局实例
_engine: Optional[PersonalizationEngine] = None


def get_personalization_engine() -> PersonalizationEngine:
    """获取全局个性化引擎"""
    global _engine
    if _engine is None:
        _engine = PersonalizationEngine()
    return _engine


def record_preference(
    preference_type: PreferenceType,
    key: str,
    value: Any,
    confidence: float = 1.0,
) -> UserPreference:
    """便捷函数：记录偏好"""
    return get_personalization_engine().record_preference(
        preference_type=preference_type,
        key=key,
        value=value,
        confidence=confidence,
    )


def adapt_suggestion(
    suggestion: str,
    context: Optional[dict[str, Any]] = None,
) -> PersonalizationResult:
    """便捷函数：适配建议"""
    return get_personalization_engine().adapt_suggestion(suggestion, context)


def get_common_patterns(limit: int = 10) -> list[UsagePattern]:
    """便捷函数：获取常用模式"""
    return get_personalization_engine().get_common_patterns(limit)