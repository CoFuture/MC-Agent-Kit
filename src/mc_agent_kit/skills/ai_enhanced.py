"""
AI Agent 能力增强模块

提供多轮对话支持、代码上下文理解、智能推荐等功能。
"""

from __future__ import annotations

import ast
import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ConversationRole(Enum):
    """对话角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(Enum):
    """意图类型"""
    SEARCH_API = "search_api"
    SEARCH_EVENT = "search_event"
    CREATE_PROJECT = "create_project"
    CREATE_ENTITY = "create_entity"
    CREATE_ITEM = "create_item"
    DIAGNOSE_ERROR = "diagnose_error"
    GENERATE_CODE = "generate_code"
    GET_EXAMPLE = "get_example"
    EXPLAIN_CODE = "explain_code"
    UNKNOWN = "unknown"


@dataclass
class ConversationMessage:
    """对话消息"""
    role: ConversationRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    messages: list[ConversationMessage] = field(default_factory=list)
    intent_history: list[IntentType] = field(default_factory=list)
    entities: dict[str, Any] = field(default_factory=dict)  # 提取的实体
    current_topic: str = ""
    search_history: list[dict[str, Any]] = field(default_factory=list)
    code_context: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: ConversationRole, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加消息"""
        self.messages.append(
            ConversationMessage(
                role=role,
                content=content,
                metadata=metadata or {},
            )
        )

    def get_recent_messages(self, count: int = 5) -> list[ConversationMessage]:
        """获取最近的消息"""
        return self.messages[-count:] if self.messages else []

    def get_user_intent_history(self) -> list[IntentType]:
        """获取用户意图历史"""
        return [msg.metadata.get("intent") for msg in self.messages if msg.role == ConversationRole.USER and msg.metadata.get("intent")]


@dataclass
class IntentRecognitionResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float
    entities: dict[str, Any]
    context_needed: bool  # 是否需要上下文


@dataclass
class CodeContextInfo:
    """代码上下文信息"""
    file_path: str
    language: str
    imports: list[str]
    classes: list[dict[str, Any]]
    functions: list[dict[str, Any]]
    variables: list[str]
    events_used: list[str]
    apis_used: list[str]
    complexity_score: float
    issues: list[dict[str, Any]]


class IntentRecognizer:
    """意图识别器

    识别用户输入的意图，提取关键实体。

    使用示例:
        recognizer = IntentRecognizer()
        result = recognizer.recognize("如何创建一个自定义实体")
        # result.intent == IntentType.SEARCH_API
        # result.entities == {"keyword": "实体", "action": "创建"}
    """

    def __init__(self) -> None:
        """初始化意图识别器"""
        # 意图关键词映射
        self._intent_keywords: dict[IntentType, list[tuple[str, float]]] = {
            IntentType.SEARCH_API: [
                ("api", 0.9), ("接口", 0.9), ("方法", 0.8), ("函数", 0.8),
                ("查找", 0.7), ("搜索", 0.7), ("找", 0.6), ("search", 0.9),
            ],
            IntentType.SEARCH_EVENT: [
                ("事件", 0.9), ("event", 0.9), ("监听", 0.8), ("回调", 0.7),
                ("触发", 0.6), ("注册事件", 0.9),
            ],
            IntentType.CREATE_PROJECT: [
                ("创建项目", 1.0), ("新建项目", 1.0), ("初始化项目", 1.0),
                ("create project", 0.9), ("新项目", 0.8),
            ],
            IntentType.CREATE_ENTITY: [
                ("创建实体", 1.0), ("新建实体", 1.0), ("自定义实体", 0.9),
                ("create entity", 0.9), ("怪物", 0.7), ("生物", 0.7),
            ],
            IntentType.CREATE_ITEM: [
                ("创建物品", 1.0), ("新建物品", 1.0), ("自定义物品", 0.9),
                ("create item", 0.9), ("道具", 0.7),
            ],
            IntentType.DIAGNOSE_ERROR: [
                ("报错", 0.9), ("错误", 0.8), ("异常", 0.8), ("error", 0.9),
                ("诊断", 0.9), ("debug", 0.9), ("修复", 0.7), ("问题", 0.6),
            ],
            IntentType.GENERATE_CODE: [
                ("生成代码", 1.0), ("写代码", 0.9), ("帮我写", 0.8),
                ("generate", 0.9), ("实现", 0.7),
            ],
            IntentType.GET_EXAMPLE: [
                ("示例", 0.9), ("例子", 0.9), ("example", 0.9),
                ("怎么写", 0.8), ("如何实现", 0.7),
            ],
            IntentType.EXPLAIN_CODE: [
                ("解释", 0.9), ("说明", 0.8), ("什么意思", 0.8),
                ("explain", 0.9), ("理解", 0.7),
            ],
        }

        # 实体提取模式
        self._entity_patterns = {
            "api_name": r"[A-Z][a-zA-Z]+",  # API 名称通常是 CamelCase
            "event_name": r"On[A-Z][a-zA-Z]+",  # 事件名通常以 On 开头
            "entity_name": r"[a-z_]+",  # 实体名通常是 snake_case
            "module": r"实体|物品|方块|UI|网络|存档",
        }

    def recognize(self, text: str, context: ConversationContext | None = None) -> IntentRecognitionResult:
        """识别意图

        Args:
            text: 用户输入
            context: 对话上下文（可选）

        Returns:
            IntentRecognitionResult: 识别结果
        """
        text_lower = text.lower()
        scores: dict[IntentType, float] = {}

        # 计算各意图得分
        for intent, keywords in self._intent_keywords.items():
            score = 0.0
            for keyword, weight in keywords:
                if keyword in text_lower:
                    score = max(score, weight)
            if score > 0:
                scores[intent] = score

        # 确定最佳意图
        if not scores:
            return IntentRecognitionResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=self._extract_entities(text),
                context_needed=False,
            )

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]

        # 提取实体
        entities = self._extract_entities(text)

        # 结合上下文判断
        context_needed = self._needs_context(best_intent, context)

        return IntentRecognitionResult(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
            context_needed=context_needed,
        )

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """提取实体

        Args:
            text: 用户输入

        Returns:
            dict: 提取的实体
        """
        entities: dict[str, Any] = {}

        # 提取 API 名称（CamelCase）
        import re
        api_matches = re.findall(r'\b([A-Z][a-zA-Z]{2,})\b', text)
        if api_matches:
            entities["api_names"] = api_matches

        # 提取事件名称（OnXxx）
        event_matches = re.findall(r'\b(On[A-Z][a-zA-Z]*)\b', text)
        if event_matches:
            entities["event_names"] = event_matches

        # 提取关键词
        entities["keyword"] = text

        # 提取作用域
        if "服务端" in text or "server" in text.lower():
            entities["scope"] = "server"
        elif "客户端" in text or "client" in text.lower():
            entities["scope"] = "client"

        return entities

    def _needs_context(self, intent: IntentType, context: ConversationContext | None) -> bool:
        """判断是否需要上下文

        Args:
            intent: 意图
            context: 上下文

        Returns:
            bool: 是否需要上下文
        """
        # 这些意图通常需要上下文
        context_intents = {
            IntentType.EXPLAIN_CODE,
            IntentType.DIAGNOSE_ERROR,
            IntentType.GENERATE_CODE,
        }
        return intent in context_intents and context is not None


class ConversationManager:
    """对话管理器

    管理多轮对话，维护上下文。

    使用示例:
        manager = ConversationManager()
        session = manager.create_session()
        session.add_message(ConversationRole.USER, "如何创建实体?")
        intent = manager.process_message(session, "创建一个攻击型的怪物")
    """

    def __init__(self, max_sessions: int = 100, session_timeout: float = 3600) -> None:
        """初始化对话管理器

        Args:
            max_sessions: 最大会话数
            session_timeout: 会话超时时间（秒）
        """
        self._sessions: OrderedDict[str, ConversationContext] = OrderedDict()
        self._max_sessions = max_sessions
        self._session_timeout = session_timeout
        self._lock = threading.Lock()
        self._intent_recognizer = IntentRecognizer()

    def create_session(self) -> ConversationContext:
        """创建新会话

        Returns:
            ConversationContext: 新会话
        """
        import uuid
        session_id = str(uuid.uuid4())[:8]

        with self._lock:
            # 清理过期会话
            self._cleanup_expired_sessions()

            # 限制会话数
            while len(self._sessions) >= self._max_sessions:
                self._sessions.popitem(last=False)

            session = ConversationContext(session_id=session_id)
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> ConversationContext | None:
        """获取会话

        Args:
            session_id: 会话ID

        Returns:
            ConversationContext | None: 会话或None
        """
        with self._lock:
            return self._sessions.get(session_id)

    def process_message(
        self,
        session: ConversationContext,
        message: str,
    ) -> IntentRecognitionResult:
        """处理消息

        Args:
            session: 会话
            message: 用户消息

        Returns:
            IntentRecognitionResult: 意图识别结果
        """
        # 识别意图
        result = self._intent_recognizer.recognize(message, session)

        # 添加消息到会话
        session.add_message(
            ConversationRole.USER,
            message,
            metadata={"intent": result.intent, "entities": result.entities},
        )

        # 更新会话实体
        session.entities.update(result.entities)

        # 更新意图历史
        session.intent_history.append(result.intent)

        return result

    def add_assistant_response(
        self,
        session: ConversationContext,
        response: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """添加助手响应

        Args:
            session: 会话
            response: 响应内容
            metadata: 元数据
        """
        session.add_message(ConversationRole.ASSISTANT, response, metadata)

    def _cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        current_time = time.time()
        expired = [
            sid for sid, session in self._sessions.items()
            if session.messages and (current_time - session.messages[-1].timestamp > self._session_timeout)
        ]
        for sid in expired:
            del self._sessions[sid]

    def get_session_count(self) -> int:
        """获取会话数"""
        with self._lock:
            return len(self._sessions)


class CodeContextAnalyzer:
    """代码上下文分析器

    使用 AST 分析 Python 代码，提取上下文信息。

    使用示例:
        analyzer = CodeContextAnalyzer()
        info = analyzer.analyze("path/to/code.py")
        print(info.apis_used)  # ['GetConfig', 'ListenEvent']
    """

    def __init__(self) -> None:
        """初始化代码分析器"""
        # ModSDK 常用 API 列表
        self._modsdk_apis = {
            "GetConfig", "SetConfig", "GetEngineType", "CreateEngineEntity",
            "DestroyEntity", "GetEntity", "SetEntityPos", "GetEntityPos",
            "CreateItem", "DestroyItem", "GetItem", "SetInvItemNum",
            "CreateBlock", "DestroyBlock", "GetBlock", "SetBlock",
            "ListenEvent", "CancelListen", "NotifyToClient", "NotifyToServer",
            "GetPlayerName", "GetPlayerUID", "SetPlayerGameMode",
            "BroadcastToAllClient", "CreateTimer", "DestroyTimer",
        }

        # ModSDK 常用事件列表
        self._modsdk_events = {
            "OnServerStart", "OnServerStop", "OnClientLoadClientScriptSuccess",
            "OnAddServerPlayer", "OnDelServerPlayer", "OnAddClientPlayer",
            "OnDelClientPlayer", "OnServerChat", "OnClientChat",
            "OnEntityCreated", "OnEntityDestroyed", "OnEntityHurt",
            "OnEntityDie", "OnPlayerAttack", "OnPlayerMove",
            "OnBlockActivated", "OnBlockBroken", "OnBlockPlaced",
            "OnItemUsed", "OnItemStartUse", "OnItemStopUse",
        }

    def analyze(self, code: str, file_path: str = "<unknown>") -> CodeContextInfo:
        """分析代码

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            CodeContextInfo: 代码上下文信息
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return CodeContextInfo(
                file_path=file_path,
                language="python",
                imports=[],
                classes=[],
                functions=[],
                variables=[],
                events_used=[],
                apis_used=[],
                complexity_score=0.0,
                issues=[{"type": "syntax_error", "message": "代码存在语法错误"}],
            )

        # 提取信息
        imports = self._extract_imports(tree)
        classes = self._extract_classes(tree)
        functions = self._extract_functions(tree)
        variables = self._extract_variables(tree)
        apis_used = self._extract_apis(tree)
        events_used = self._extract_events(tree)
        complexity = self._calculate_complexity(tree)
        issues = self._detect_issues(tree)

        return CodeContextInfo(
            file_path=file_path,
            language="python",
            imports=imports,
            classes=classes,
            functions=functions,
            variables=variables,
            events_used=events_used,
            apis_used=apis_used,
            complexity_score=complexity,
            issues=issues,
        )

    def analyze_file(self, file_path: str | Path) -> CodeContextInfo:
        """分析文件

        Args:
            file_path: 文件路径

        Returns:
            CodeContextInfo: 代码上下文信息
        """
        path = Path(file_path)
        if not path.exists():
            return CodeContextInfo(
                file_path=str(path),
                language="python",
                imports=[],
                classes=[],
                functions=[],
                variables=[],
                events_used=[],
                apis_used=[],
                complexity_score=0.0,
                issues=[{"type": "file_not_found", "message": f"文件不存在: {path}"}],
            )

        code = path.read_text(encoding="utf-8")
        return self.analyze(code, str(path))

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """提取导入"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _extract_classes(self, tree: ast.AST) -> list[dict[str, Any]]:
        """提取类"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "methods": methods,
                    "bases": [ast.unparse(base) for base in node.bases],
                })
        return classes

    def _extract_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """提取函数"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                functions.append({
                    "name": node.name,
                    "args": args,
                    "docstring": ast.get_docstring(node) or "",
                })
        return functions

    def _extract_variables(self, tree: ast.AST) -> list[str]:
        """提取变量"""
        variables = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.add(target.id)
        return list(variables)

    def _extract_apis(self, tree: ast.AST) -> list[str]:
        """提取使用的 API"""
        apis = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr in self._modsdk_apis:
                        apis.add(func.attr)
                elif isinstance(func, ast.Name):
                    if func.id in self._modsdk_apis:
                        apis.add(func.id)
        return list(apis)

    def _extract_events(self, tree: ast.AST) -> list[str]:
        """提取使用的事件"""
        events = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str) and node.value in self._modsdk_events:
                    events.add(node.value)
            elif isinstance(node, ast.Str):  # Python < 3.8 兼容
                if node.s in self._modsdk_events:
                    events.add(node.s)
        return list(events)

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """计算圈复杂度"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return float(complexity)

    def _detect_issues(self, tree: ast.AST) -> list[dict[str, Any]]:
        """检测问题"""
        issues = []

        for node in ast.walk(tree):
            # 检测裸 except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({
                    "type": "bare_except",
                    "message": "使用裸 except，应该指定异常类型",
                    "line": node.lineno,
                })

            # 检测全局变量
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # 简单判断：模块级别的赋值可能是全局变量
                        pass

        return issues


class SmartRecommender:
    """智能推荐器

    基于上下文和相似度提供推荐。

    使用示例:
        recommender = SmartRecommender()
        recommendations = recommender.recommend_apis(context, query="创建实体")
    """

    def __init__(self) -> None:
        """初始化推荐器"""
        self._cache: dict[str, Any] = {}
        self._lock = threading.Lock()

    def recommend_apis(
        self,
        context: ConversationContext | None,
        query: str,
        available_apis: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """推荐 API

        Args:
            context: 对话上下文
            query: 查询
            available_apis: 可用 API 列表
            limit: 返回数量限制

        Returns:
            list: 推荐 API 列表
        """
        recommendations = []

        # 基于关键词的简单匹配
        # 实际应用中可以使用向量相似度
        api_keywords = {
            "CreateEngineEntity": ["创建", "实体", "create", "entity", "生成", "怪物"],
            "DestroyEntity": ["删除", "销毁", "实体", "destroy", "remove"],
            "GetEntity": ["获取", "实体", "get", "查询"],
            "SetEntityPos": ["设置", "位置", "移动", "实体", "position", "move"],
            "CreateItem": ["创建", "物品", "item", "道具"],
            "GetConfig": ["获取", "配置", "config", "设置"],
            "ListenEvent": ["监听", "事件", "listen", "event", "注册"],
            "NotifyToClient": ["通知", "客户端", "同步", "notify", "client"],
            "NotifyToServer": ["通知", "服务端", "同步", "notify", "server"],
        }

        query_lower = query.lower()
        scores: dict[str, float] = {}

        for api, keywords in api_keywords.items():
            score = sum(1.0 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[api] = score

        # 结合上下文
        if context and context.entities:
            # 如果有作用域信息，提升相关 API 分数
            scope = context.entities.get("scope")
            if scope == "server":
                for api in ["NotifyToClient", "GetConfig", "CreateEngineEntity"]:
                    scores[api] = scores.get(api, 0) + 0.5
            elif scope == "client":
                for api in ["NotifyToServer", "ListenEvent"]:
                    scores[api] = scores.get(api, 0) + 0.5

        # 排序返回
        sorted_apis = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for api, score in sorted_apis[:limit]:
            recommendations.append({
                "api": api,
                "score": score,
                "reason": f"基于关键词匹配" if score >= 1.0 else "基于上下文推断",
            })

        return recommendations

    def recommend_events(
        self,
        context: ConversationContext | None,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """推荐事件

        Args:
            context: 对话上下文
            query: 查询
            limit: 返回数量限制

        Returns:
            list: 推荐事件列表
        """
        recommendations = []

        event_keywords = {
            "OnServerStart": ["服务端", "启动", "开始", "server", "start", "初始化"],
            "OnServerStop": ["服务端", "停止", "关闭", "server", "stop"],
            "OnAddServerPlayer": ["玩家", "加入", "进入", "服务端", "player", "join"],
            "OnDelServerPlayer": ["玩家", "离开", "退出", "服务端", "player", "leave"],
            "OnServerChat": ["聊天", "消息", "服务端", "chat", "message"],
            "OnEntityCreated": ["实体", "创建", "生成", "entity", "created"],
            "OnEntityDestroyed": ["实体", "销毁", "删除", "entity", "destroyed"],
            "OnEntityHurt": ["实体", "受伤", "伤害", "entity", "hurt", "damage"],
            "OnEntityDie": ["实体", "死亡", "entity", "die", "death"],
            "OnPlayerAttack": ["玩家", "攻击", "点击", "player", "attack"],
            "OnBlockActivated": ["方块", "交互", "点击", "block", "activate"],
            "OnBlockBroken": ["方块", "破坏", "block", "break"],
            "OnBlockPlaced": ["方块", "放置", "block", "place"],
            "OnItemUsed": ["物品", "使用", "item", "use"],
        }

        query_lower = query.lower()
        scores: dict[str, float] = {}

        for event, keywords in event_keywords.items():
            score = sum(1.0 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[event] = score

        sorted_events = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for event, score in sorted_events[:limit]:
            recommendations.append({
                "event": event,
                "score": score,
                "reason": f"基于关键词匹配",
            })

        return recommendations


def create_conversation_manager(
    max_sessions: int = 100,
    session_timeout: float = 3600,
) -> ConversationManager:
    """创建对话管理器

    Args:
        max_sessions: 最大会话数
        session_timeout: 会话超时时间

    Returns:
        ConversationManager 实例
    """
    return ConversationManager(max_sessions, session_timeout)


def create_code_analyzer() -> CodeContextAnalyzer:
    """创建代码分析器

    Returns:
        CodeContextAnalyzer 实例
    """
    return CodeContextAnalyzer()


def create_smart_recommender() -> SmartRecommender:
    """创建智能推荐器

    Returns:
        SmartRecommender 实例
    """
    return SmartRecommender()


# 全局实例
_conversation_manager: ConversationManager | None = None
_code_analyzer: CodeContextAnalyzer | None = None
_smart_recommender: SmartRecommender | None = None


def get_conversation_manager() -> ConversationManager:
    """获取全局对话管理器"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


def get_code_analyzer() -> CodeContextAnalyzer:
    """获取全局代码分析器"""
    global _code_analyzer
    if _code_analyzer is None:
        _code_analyzer = CodeContextAnalyzer()
    return _code_analyzer


def get_smart_recommender() -> SmartRecommender:
    """获取全局智能推荐器"""
    global _smart_recommender
    if _smart_recommender is None:
        _smart_recommender = SmartRecommender()
    return _smart_recommender