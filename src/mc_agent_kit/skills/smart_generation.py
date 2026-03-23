"""
智能代码生成增强模块

提供基于 GPT/模板的代码生成、代码质量评估、代码风格检查、GPT 集成等功能。
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class CodeStyle(Enum):
    """代码风格"""
    PEP8 = "pep8"
    GOOGLE = "google"
    NUMPY = "numpy"
    MODSDK_BEST_PRACTICE = "modsdk_best_practice"


class GenerationStrategy(Enum):
    """生成策略"""
    TEMPLATE = "template"
    LLM = "llm"
    HYBRID = "hybrid"


class CodeQualityLevel(Enum):
    """代码质量等级"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 70-89
    ACCEPTABLE = "acceptable"  # 50-69
    POOR = "poor"  # 30-49
    CRITICAL = "critical"  # 0-29


class LLMProvider(Enum):
    """LLM 提供者"""
    OPENAI = "openai"
    AZURE = "azure"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class CodeTemplate:
    """代码模板"""
    name: str
    description: str
    template: str
    parameters: dict[str, Any]
    category: str
    tags: list[str] = field(default_factory=list)
    quality_score: float = 0.9
    modsdk_compatible: bool = True
    version: str = "1.0.0"


@dataclass
class GeneratedCode:
    """生成的代码"""
    code: str
    language: str
    template_used: Optional[str]
    quality_score: float
    style_compliance: float
    modsdk_compatible: bool
    imports_needed: list[str]
    dependencies: list[str]
    warnings: list[str]
    suggestions: list[str]
    generation_time: float = 0.0
    strategy_used: GenerationStrategy = GenerationStrategy.HYBRID


@dataclass
class QualityAssessment:
    """代码质量评估结果"""
    overall_score: float
    level: CodeQualityLevel
    readability_score: float
    maintainability_score: float
    performance_score: float
    security_score: float
    modsdk_compliance_score: float
    issues: list[dict[str, Any]]
    suggestions: list[str]
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StyleCheckResult:
    """风格检查结果"""
    style: CodeStyle
    compliance_score: float
    violations: list[dict[str, Any]]
    fixes: list[dict[str, Any]]
    auto_fixable: bool = True


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 30.0


@dataclass
class GenerationRequest:
    """生成请求"""
    prompt: str
    strategy: GenerationStrategy = GenerationStrategy.HYBRID
    style: Optional[CodeStyle] = None
    context: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    quality_threshold: float = 0.7


class SmartCodeGenerator:
    """智能代码生成器

    支持基于模板和 LLM 的代码生成，提供质量评估和风格检查。

    使用示例:
        generator = SmartCodeGenerator()
        result = generator.generate(
            GenerationRequest(prompt="创建一个服务端启动事件监听器")
        )
    """

    def __init__(
        self,
        default_style: CodeStyle = CodeStyle.MODSDK_BEST_PRACTICE,
        quality_threshold: float = 0.7,
        llm_config: Optional[LLMConfig] = None,
    ) -> None:
        """初始化智能代码生成器

        Args:
            default_style: 默认代码风格
            quality_threshold: 质量阈值
            llm_config: LLM 配置
        """
        self._default_style = default_style
        self._quality_threshold = quality_threshold
        self._llm_config = llm_config or LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-model",
        )
        self._templates: dict[str, CodeTemplate] = {}
        self._cache: dict[str, GeneratedCode] = {}
        self._lock = threading.Lock()
        self._generation_stats: dict[str, Any] = {
            "total_generations": 0,
            "template_hits": 0,
            "llm_calls": 0,
            "cache_hits": 0,
        }

        # 初始化内置模板
        self._init_builtin_templates()

    def _init_builtin_templates(self) -> None:
        """初始化内置模板"""
        templates = [
            CodeTemplate(
                name="server_start_listener",
                description="服务端启动事件监听器",
                template='''from mod.common import ListenEvent

def OnServerStart(args):
    """
    服务端启动回调
    """
    print("Server started!")
    # 在此添加初始化逻辑

# 注册事件监听
ListenEvent("OnServerStart", OnServerStart)
''',
                parameters={},
                category="event_listener",
                tags=["server", "event", "startup"],
                quality_score=0.95,
            ),
            CodeTemplate(
                name="entity_create",
                description="创建自定义实体",
                template='''from mod.common import CreateEngineEntity, GetEngineType

def create_custom_entity(entity_type: str, pos: tuple, dimension: int = 0):
    """
    创建自定义实体
    
    Args:
        entity_type: 实体类型标识符
        pos: 坐标元组 (x, y, z)
        dimension: 维度ID
    
    Returns:
        实体ID或None
    """
    engine_type = GetEngineType()
    entity_id = CreateEngineEntity(engine_type, entity_type, pos, dimension)
    
    if entity_id:
        print(f"Created entity: {entity_type} with ID: {entity_id}")
        return entity_id
    else:
        print(f"Failed to create entity: {entity_type}")
        return None
''',
                parameters={"entity_type": "string", "pos": "tuple", "dimension": "int"},
                category="entity",
                tags=["entity", "create", "spawn"],
                quality_score=0.92,
            ),
            CodeTemplate(
                name="item_register",
                description="注册自定义物品",
                template='''from mod.common import ListenEvent

ITEM_ID = "custom_item_identifier"

def OnItemUsed(args):
    """
    物品使用回调
    """
    player_id = args.get("playerId")
    item_id = args.get("itemId")
    
    if item_id == ITEM_ID:
        # 在此添加物品使用逻辑
        print(f"Player {player_id} used custom item: {item_id}")

# 注册事件监听
ListenEvent("OnItemUsed", OnItemUsed)
''',
                parameters={"item_id": "string"},
                category="item",
                tags=["item", "register", "use"],
                quality_score=0.90,
            ),
            CodeTemplate(
                name="block_interactive",
                description="交互式方块",
                template='''from mod.common import ListenEvent

BLOCK_ID = "custom_block_identifier"

def OnBlockActivated(args):
    """
    方块交互回调
    """
    block_pos = args.get("blockPos")
    player_id = args.get("playerId")
    
    if args.get("blockId") == BLOCK_ID:
        # 在此添加交互逻辑
        print(f"Block at {block_pos} activated by player {player_id}")

# 注册事件监听
ListenEvent("OnBlockActivated", OnBlockActivated)
''',
                parameters={"block_id": "string"},
                category="block",
                tags=["block", "interactive", "activate"],
                quality_score=0.90,
            ),
            CodeTemplate(
                name="client_server_sync",
                description="客户端服务端数据同步",
                template='''from mod.common import ListenEvent, NotifyToClient, NotifyToServer

# 服务端代码
def sync_to_client(player_id: str, data: dict):
    """
    同步数据到客户端
    
    Args:
        player_id: 玩家ID
        data: 要同步的数据
    """
    NotifyToClient(player_id, "CustomEvent", data)

# 客户端代码
def OnCustomEvent(args):
    """
    自定义事件回调（客户端）
    """
    data = args.get("data")
    # 处理同步的数据
    print(f"Received sync data: {data}")

# 客户端注册事件监听
ListenEvent("CustomEvent", OnCustomEvent)
''',
                parameters={},
                category="network",
                tags=["sync", "client", "server", "network"],
                quality_score=0.88,
            ),
            CodeTemplate(
                name="timer_scheduler",
                description="定时器调度器",
                template='''from mod.common import CreateTimer, DestroyTimer

_timer_ids: list = []

def create_scheduled_task(delay: float, callback: callable, repeat: bool = False):
    """
    创建定时任务
    
    Args:
        delay: 延迟时间（秒）
        callback: 回调函数
        repeat: 是否重复
    
    Returns:
        定时器ID
    """
    timer_id = CreateTimer(delay, callback, repeat)
    if timer_id:
        _timer_ids.append(timer_id)
        return timer_id
    return None

def cleanup_timers():
    """清理所有定时器"""
    for timer_id in _timer_ids:
        DestroyTimer(timer_id)
    _timer_ids.clear()
''',
                parameters={"delay": "float", "callback": "callable", "repeat": "bool"},
                category="utility",
                tags=["timer", "schedule", "task"],
                quality_score=0.91,
            ),
            CodeTemplate(
                name="config_manager",
                description="配置管理器",
                template='''from mod.common import GetConfig, SetConfig
import json

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._cache: dict = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        try:
            config_str = GetConfig(self.config_path)
            if config_str:
                self._cache = json.loads(config_str)
        except Exception as e:
            print(f"Failed to load config: {e}")
            self._cache = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._cache.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self._cache[key] = value
    
    def save(self):
        """保存配置"""
        config_str = json.dumps(self._cache, ensure_ascii=False, indent=2)
        SetConfig(self.config_path, config_str)
''',
                parameters={"config_path": "string"},
                category="utility",
                tags=["config", "settings", "persistence"],
                quality_score=0.93,
            ),
            CodeTemplate(
                name="player_manager",
                description="玩家管理器",
                template='''from mod.common import ListenEvent, GetPlayerName, GetPlayerUID

class PlayerManager:
    """玩家管理器"""
    
    def __init__(self):
        self._players: dict = {}  # player_id -> player_info
    
    def OnPlayerJoin(self, args):
        """玩家加入"""
        player_id = args.get("playerId")
        if player_id:
            name = GetPlayerName(player_id)
            uid = GetPlayerUID(player_id)
            self._players[player_id] = {
                "name": name,
                "uid": uid,
                "join_time": time.time(),
            }
            print(f"Player joined: {name} ({uid})")
    
    def OnPlayerLeave(self, args):
        """玩家离开"""
        player_id = args.get("playerId")
        if player_id in self._players:
            info = self._players.pop(player_id)
            print(f"Player left: {info['name']}")
    
    def get_player(self, player_id: str) -> Optional[dict]:
        """获取玩家信息"""
        return self._players.get(player_id)
    
    def get_all_players(self) -> list:
        """获取所有在线玩家"""
        return list(self._players.keys())

# 创建全局实例
player_manager = PlayerManager()

# 注册事件监听
ListenEvent("OnAddServerPlayer", player_manager.OnPlayerJoin)
ListenEvent("OnDelServerPlayer", player_manager.OnPlayerLeave)
''',
                parameters={},
                category="player",
                tags=["player", "management", "join", "leave"],
                quality_score=0.94,
            ),
        ]

        for template in templates:
            self._templates[template.name] = template

    def register_template(self, template: CodeTemplate) -> None:
        """注册自定义模板

        Args:
            template: 代码模板
        """
        with self._lock:
            self._templates[template.name] = template

    def generate(self, request: GenerationRequest) -> GeneratedCode:
        """生成代码

        Args:
            request: 生成请求

        Returns:
            GeneratedCode: 生成的代码
        """
        start_time = time.time()
        style = request.style or self._default_style

        # 检查缓存
        cache_key = self._get_cache_key(request.prompt, request.strategy, style)
        if cache_key in self._cache:
            with self._lock:
                self._generation_stats["cache_hits"] += 1
            return self._cache[cache_key]

        # 根据策略生成
        if request.strategy == GenerationStrategy.TEMPLATE:
            result = self._generate_from_template(request.prompt, style, request.context)
        elif request.strategy == GenerationStrategy.LLM:
            result = self._generate_from_llm(request.prompt, style, request.context)
        else:  # HYBRID
            result = self._generate_hybrid(request.prompt, style, request.context)

        # 质量检查
        if result.quality_score < request.quality_threshold:
            result.warnings.append(f"代码质量分数 {result.quality_score:.2f} 低于阈值 {request.quality_threshold}")

        # 设置生成时间
        result.generation_time = time.time() - start_time
        result.strategy_used = request.strategy

        # 缓存结果
        with self._lock:
            self._cache[cache_key] = result
            self._generation_stats["total_generations"] += 1

        return result

    def _generate_from_template(
        self,
        prompt: str,
        style: CodeStyle,
        context: dict[str, Any],
    ) -> GeneratedCode:
        """从模板生成代码"""
        # 查找匹配的模板
        matched_template = self._find_matching_template(prompt)

        if matched_template:
            code = self._apply_template(matched_template, context)
            quality_score = matched_template.quality_score
            template_used = matched_template.name
            with self._lock:
                self._generation_stats["template_hits"] += 1
        else:
            # 没有匹配模板，生成基础代码
            code = self._generate_basic_code(prompt)
            quality_score = 0.5
            template_used = None

        # 风格检查和调整
        style_result = self.check_style(code, style)
        code = self._apply_style_fixes(code, style_result)

        # 质量评估
        assessment = self.assess_quality(code)

        return GeneratedCode(
            code=code,
            language="python",
            template_used=template_used,
            quality_score=assessment.overall_score,
            style_compliance=style_result.compliance_score,
            modsdk_compatible=assessment.modsdk_compliance_score >= 0.7,
            imports_needed=self._extract_imports(code),
            dependencies=[],
            warnings=[issue["message"] for issue in assessment.issues if issue.get("severity") == "warning"],
            suggestions=assessment.suggestions,
        )

    def _generate_from_llm(
        self,
        prompt: str,
        style: CodeStyle,
        context: dict[str, Any],
    ) -> GeneratedCode:
        """从 LLM 生成代码"""
        with self._lock:
            self._generation_stats["llm_calls"] += 1

        # 根据提供者选择生成方式
        if self._llm_config.provider == LLMProvider.MOCK:
            # Mock 模式，使用模板
            return self._generate_from_template(prompt, style, context)

        # 实际 LLM 调用会在这里实现
        # 目前返回模板生成的结果
        return self._generate_from_template(prompt, style, context)

    def _generate_hybrid(
        self,
        prompt: str,
        style: CodeStyle,
        context: dict[str, Any],
    ) -> GeneratedCode:
        """混合生成策略"""
        # 首先尝试模板
        result = self._generate_from_template(prompt, style, context)

        # 如果质量不够高，可以尝试其他策略
        if result.quality_score < self._quality_threshold:
            # 可以在这里添加更多增强逻辑
            pass

        return result

    def _find_matching_template(self, prompt: str) -> Optional[CodeTemplate]:
        """查找匹配的模板"""
        prompt_lower = prompt.lower()

        # 关键词匹配
        keywords_scores: dict[str, float] = {}

        for name, template in self._templates.items():
            score = 0.0

            # 检查标签匹配
            for tag in template.tags:
                if tag in prompt_lower:
                    score += 0.2

            # 检查描述匹配
            desc_words = template.description.lower().split()
            for word in desc_words:
                if word in prompt_lower:
                    score += 0.1

            # 检查名称匹配
            name_words = name.replace("_", " ").split()
            for word in name_words:
                if word in prompt_lower:
                    score += 0.3

            if score > 0:
                keywords_scores[name] = score

        if keywords_scores:
            best_name = max(keywords_scores, key=keywords_scores.get)
            if keywords_scores[best_name] >= 0.3:
                return self._templates[best_name]

        return None

    def _apply_template(
        self,
        template: CodeTemplate,
        context: dict[str, Any],
    ) -> str:
        """应用模板"""
        code = template.template

        # 简单的变量替换
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            code = code.replace(placeholder, str(value))

        return code

    def _generate_basic_code(self, prompt: str) -> str:
        """生成基础代码"""
        return f'''# Generated code based on: {prompt}
# TODO: Implement the requested functionality

def main():
    """
    Main function
    """
    pass

if __name__ == "__main__":
    main()
'''

    def _apply_style_fixes(self, code: str, style_result: StyleCheckResult) -> str:
        """应用风格修复"""
        if not style_result.auto_fixable:
            return code

        lines = code.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            fixed_line = line

            # 修复尾随空格
            fixed_line = fixed_line.rstrip()

            # 确保文件以空行结尾
            fixed_lines.append(fixed_line)

        result = "\n".join(fixed_lines)
        
        # 确保文件以空行结尾
        if not result.endswith("\n"):
            result += "\n"

        return result

    def _extract_imports(self, code: str) -> list[str]:
        """提取导入语句"""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
        except SyntaxError:
            # 正则表达式后备
            import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'
            for line in code.split("\n"):
                match = re.match(import_pattern, line.strip())
                if match:
                    imports.append(line.strip())

        return imports

    def _get_cache_key(
        self,
        prompt: str,
        strategy: GenerationStrategy,
        style: CodeStyle,
    ) -> str:
        """获取缓存键"""
        content = f"{prompt}:{strategy.value}:{style.value}"
        return hashlib.md5(content.encode()).hexdigest()

    def assess_quality(self, code: str) -> QualityAssessment:
        """评估代码质量

        Args:
            code: 代码内容

        Returns:
            QualityAssessment: 质量评估结果
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return QualityAssessment(
                overall_score=0.0,
                level=CodeQualityLevel.CRITICAL,
                readability_score=0.0,
                maintainability_score=0.0,
                performance_score=0.0,
                security_score=0.0,
                modsdk_compliance_score=0.0,
                issues=[{
                    "type": "syntax_error",
                    "message": f"语法错误: {e}",
                    "line": e.lineno or 0,
                    "severity": "critical",
                }],
                suggestions=["修复语法错误"],
            )

        issues: list[dict[str, Any]] = []

        # 计算各项分数
        readability_score = self._assess_readability(tree, code, issues)
        maintainability_score = self._assess_maintainability(tree, code, issues)
        performance_score = self._assess_performance(tree, code, issues)
        security_score = self._assess_security(tree, code, issues)
        modsdk_compliance_score = self._assess_modsdk_compliance(tree, code, issues)

        # 计算总分
        overall_score = (
            readability_score * 0.25 +
            maintainability_score * 0.25 +
            performance_score * 0.15 +
            security_score * 0.15 +
            modsdk_compliance_score * 0.20
        )

        # 确定质量等级
        if overall_score >= 0.9:
            level = CodeQualityLevel.EXCELLENT
        elif overall_score >= 0.7:
            level = CodeQualityLevel.GOOD
        elif overall_score >= 0.5:
            level = CodeQualityLevel.ACCEPTABLE
        elif overall_score >= 0.3:
            level = CodeQualityLevel.POOR
        else:
            level = CodeQualityLevel.CRITICAL

        # 生成建议
        suggestions = self._generate_suggestions(issues)

        return QualityAssessment(
            overall_score=overall_score,
            level=level,
            readability_score=readability_score,
            maintainability_score=maintainability_score,
            performance_score=performance_score,
            security_score=security_score,
            modsdk_compliance_score=modsdk_compliance_score,
            issues=issues,
            suggestions=suggestions,
            details={
                "line_count": len(code.split("\n")),
                "char_count": len(code),
            },
        )

    def _assess_readability(
        self,
        tree: ast.AST,
        code: str,
        issues: list[dict[str, Any]],
    ) -> float:
        """评估可读性"""
        score = 1.0

        lines = code.split("\n")

        # 检查行长度
        long_lines = 0
        for i, line in enumerate(lines):
            if len(line) > 100:
                long_lines += 1
                if len(line) > 120:
                    issues.append({
                        "type": "line_too_long",
                        "message": f"第 {i + 1} 行超过 120 字符",
                        "line": i + 1,
                        "severity": "warning",
                    })

        if long_lines > 0:
            score -= min(0.2, long_lines * 0.02)

        # 检查函数/类文档字符串
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append({
                        "type": "missing_docstring",
                        "message": f"{node.name} 缺少文档字符串",
                        "line": node.lineno,
                        "severity": "info",
                    })
                    score -= 0.03

        # 检查命名规范
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append({
                        "type": "naming_convention",
                        "message": f"函数名 {node.name} 不符合 snake_case 规范",
                        "line": node.lineno,
                        "severity": "warning",
                    })
                    score -= 0.05

        return max(0.0, score)

    def _assess_maintainability(
        self,
        tree: ast.AST,
        code: str,
        issues: list[dict[str, Any]],
    ) -> float:
        """评估可维护性"""
        score = 1.0

        # 检查函数复杂度
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 计算圈复杂度
                complexity = self._calculate_cyclomatic_complexity(node)

                if complexity > 10:
                    issues.append({
                        "type": "high_complexity",
                        "message": f"函数 {node.name} 复杂度过高 ({complexity})",
                        "line": node.lineno,
                        "severity": "warning",
                    })
                    score -= min(0.2, (complexity - 10) * 0.02)

                # 检查函数长度
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        issues.append({
                            "type": "function_too_long",
                            "message": f"函数 {node.name} 过长 ({func_lines} 行)",
                            "line": node.lineno,
                            "severity": "warning",
                        })
                        score -= min(0.1, (func_lines - 50) * 0.005)

        return max(0.0, score)

    def _assess_performance(
        self,
        tree: ast.AST,
        code: str,
        issues: list[dict[str, Any]],
    ) -> float:
        """评估性能"""
        score = 1.0

        # 检查循环中的低效模式
        for node in ast.walk(tree):
            # 检查字符串拼接
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Add):
                    if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                        if isinstance(node.left.value, str) and isinstance(node.right.value, str):
                            issues.append({
                                "type": "inefficient_string_concat",
                                "message": "考虑使用 f-string 或 .format() 进行字符串格式化",
                                "line": node.lineno,
                                "severity": "info",
                            })
                            score -= 0.02

        return max(0.0, score)

    def _assess_security(
        self,
        tree: ast.AST,
        code: str,
        issues: list[dict[str, Any]],
    ) -> float:
        """评估安全性"""
        score = 1.0

        dangerous_functions = {"eval", "exec", "compile", "__import__"}

        for node in ast.walk(tree):
            # 检查危险函数调用
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in dangerous_functions:
                    issues.append({
                        "type": "dangerous_function",
                        "message": f"使用了危险函数 {func_name}",
                        "line": node.lineno,
                        "severity": "warning",
                    })
                    score -= 0.2

            # 检查裸 except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append({
                    "type": "bare_except",
                    "message": "使用裸 except，应该指定异常类型",
                    "line": node.lineno,
                    "severity": "warning",
                })
                score -= 0.1

        return max(0.0, score)

    def _assess_modsdk_compliance(
        self,
        tree: ast.AST,
        code: str,
        issues: list[dict[str, Any]],
    ) -> float:
        """评估 ModSDK 合规性"""
        score = 1.0

        # ModSDK 常用 API
        modsdk_apis = {
            "ListenEvent", "CancelListen", "CreateEngineEntity",
            "DestroyEntity", "GetEntity", "SetEntityPos",
            "NotifyToClient", "NotifyToServer", "GetConfig", "SetConfig",
        }

        used_apis = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in modsdk_apis:
                    used_apis.add(func_name)

        # 检查是否有 ModSDK API 使用
        if used_apis:
            # 检查是否使用了正确的导入
            has_mod_import = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "mod" in node.module:
                        has_mod_import = True
                        break

            if not has_mod_import:
                issues.append({
                    "type": "missing_modsdk_import",
                    "message": "使用了 ModSDK API 但未导入 mod.common",
                    "line": 0,
                    "severity": "warning",
                })
                score -= 0.1

        return max(0.0, score)

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _generate_suggestions(self, issues: list[dict[str, Any]]) -> list[str]:
        """生成改进建议"""
        suggestions = []

        issue_types = {issue["type"] for issue in issues}

        if "line_too_long" in issue_types:
            suggestions.append("将长行拆分为多行，保持每行不超过 100 字符")

        if "missing_docstring" in issue_types:
            suggestions.append("为所有公共函数和类添加文档字符串")

        if "naming_convention" in issue_types:
            suggestions.append("使用 snake_case 命名函数和变量")

        if "high_complexity" in issue_types:
            suggestions.append("将复杂函数拆分为更小的函数")

        if "function_too_long" in issue_types:
            suggestions.append("将长函数拆分为多个更小的函数")

        if "dangerous_function" in issue_types:
            suggestions.append("避免使用 eval/exec 等危险函数")

        if "bare_except" in issue_types:
            suggestions.append("指定具体的异常类型而非使用裸 except")

        return suggestions

    def check_style(
        self,
        code: str,
        style: Optional[CodeStyle] = None,
    ) -> StyleCheckResult:
        """检查代码风格

        Args:
            code: 代码内容
            style: 代码风格

        Returns:
            StyleCheckResult: 风格检查结果
        """
        style = style or self._default_style

        violations: list[dict[str, Any]] = []
        fixes: list[dict[str, Any]] = []

        lines = code.split("\n")

        # 检查缩进
        for i, line in enumerate(lines):
            if line and not line[0].isspace() and line[0] not in "#\n":
                # 顶级语句
                pass
            elif line.startswith(" ") and not line.startswith("    "):
                # 缩进不是 4 的倍数
                violations.append({
                    "type": "indentation",
                    "message": f"第 {i + 1} 行缩进不是 4 空格的倍数",
                    "line": i + 1,
                })
                fixes.append({
                    "line": i + 1,
                    "fix": "调整缩进为 4 空格的倍数",
                })

        # 检查尾随空格
        for i, line in enumerate(lines):
            if line.rstrip() != line:
                violations.append({
                    "type": "trailing_whitespace",
                    "message": f"第 {i + 1} 行有尾随空格",
                    "line": i + 1,
                })

        # 检查空行
        consecutive_empty = 0
        for i, line in enumerate(lines):
            if line.strip() == "":
                consecutive_empty += 1
                if consecutive_empty > 2:
                    violations.append({
                        "type": "too_many_blank_lines",
                        "message": f"第 {i + 1} 行附近有过多空行",
                        "line": i + 1,
                    })
            else:
                consecutive_empty = 0

        # 计算合规分数
        if not violations:
            compliance_score = 1.0
        else:
            compliance_score = max(0.0, 1.0 - len(violations) * 0.05)

        return StyleCheckResult(
            style=style,
            compliance_score=compliance_score,
            violations=violations,
            fixes=fixes,
            auto_fixable=True,
        )

    def get_stats(self) -> dict[str, Any]:
        """获取生成统计"""
        with self._lock:
            return dict(self._generation_stats)

    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


# 全局实例
_generator: Optional[SmartCodeGenerator] = None


def get_smart_generator() -> SmartCodeGenerator:
    """获取全局智能代码生成器"""
    global _generator
    if _generator is None:
        _generator = SmartCodeGenerator()
    return _generator


def generate_code(
    prompt: str,
    strategy: GenerationStrategy = GenerationStrategy.HYBRID,
    style: Optional[CodeStyle] = None,
) -> GeneratedCode:
    """便捷函数：生成代码

    Args:
        prompt: 生成提示
        strategy: 生成策略
        style: 代码风格

    Returns:
        GeneratedCode: 生成的代码
    """
    request = GenerationRequest(
        prompt=prompt,
        strategy=strategy,
        style=style,
    )
    return get_smart_generator().generate(request)