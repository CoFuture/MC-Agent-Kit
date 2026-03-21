"""
最佳实践推荐模块

提供 ModSDK 开发最佳实践检查和建议。
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class PracticeCategory(Enum):
    """最佳实践类别"""

    PERFORMANCE = "performance"  # 性能优化
    SECURITY = "security"  # 安全性
    MAINTAINABILITY = "maintainability"  # 可维护性
    MODSDK = "modsdk"  # ModSDK 特定
    CODING_STYLE = "coding_style"  # 编码风格
    ERROR_HANDLING = "error_handling"  # 错误处理


class PracticeSeverity(Enum):
    """实践严重程度"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


@dataclass
class BestPractice:
    """最佳实践定义"""

    id: str  # 实践 ID
    name: str  # 实践名称
    category: PracticeCategory  # 类别
    description: str  # 描述
    rationale: str  # 原因说明
    examples_good: list[str] = field(default_factory=list)  # 好的示例
    examples_bad: list[str] = field(default_factory=list)  # 坏的示例
    references: list[str] = field(default_factory=list)  # 参考资料
    severity: PracticeSeverity = PracticeSeverity.INFO  # 严重程度
    auto_fixable: bool = False  # 是否可自动修复


@dataclass
class BestPracticeResult:
    """最佳实践检查结果"""

    practice: BestPractice  # 最佳实践
    message: str  # 检查消息
    line: int  # 行号
    column: int = 0  # 列号
    code_snippet: str = ""  # 代码片段
    suggestion: str = ""  # 修复建议
    passed: bool = True  # 是否通过检查

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "practice_id": self.practice.id,
            "practice_name": self.practice.name,
            "category": self.practice.category.value,
            "message": self.message,
            "line": self.line,
            "passed": self.passed,
            "suggestion": self.suggestion,
        }


# ModSDK 最佳实践库
MODSDK_BEST_PRACTICES: list[BestPractice] = [
    # 性能优化
    BestPractice(
        id="PERF001",
        name="避免在 Tick 事件中进行昂贵操作",
        category=PracticeCategory.PERFORMANCE,
        description="Tick 事件每帧触发，应避免在其中执行耗时操作",
        rationale="Tick 事件频率高达每秒 30-60 次，在其中执行昂贵操作会导致卡顿",
        examples_good=[
            "def OnTick(args):\n    if frame_counter % 30 == 0:\n        check_status()",
        ],
        examples_bad=[
            "def OnTick(args):\n    for entity in GetPlayerList():\n        expensive_operation(entity)",
        ],
        severity=PracticeSeverity.WARNING,
    ),
    BestPractice(
        id="PERF002",
        name="使用缓存避免重复计算",
        category=PracticeCategory.PERFORMANCE,
        description="对于频繁访问但不常变化的数据，应使用缓存",
        rationale="缓存可以显著减少重复计算的开销",
        examples_good=[
            "_cache = {}\ndef get_config(key):\n    if key not in _cache:\n        _cache[key] = load_config(key)\n    return _cache[key]",
        ],
        examples_bad=[
            "def get_config(key):\n    return load_config(key)  # 每次都重新加载",
        ],
        severity=PracticeSeverity.INFO,
    ),
    BestPractice(
        id="PERF003",
        name="批量操作代替循环调用",
        category=PracticeCategory.PERFORMANCE,
        description="优先使用批量 API 而不是循环调用单个 API",
        rationale="批量操作通常有更好的性能，减少了跨语言调用的开销",
        examples_good=[
            "positions = [(x, y, z) for x, y, z in data]\nSetBlockBatch(positions)",
        ],
        examples_bad=[
            "for x, y, z in data:\n    SetBlock(x, y, z, block)",
        ],
        severity=PracticeSeverity.WARNING,
    ),
    # 安全性
    BestPractice(
        id="SEC001",
        name="验证外部输入",
        category=PracticeCategory.SECURITY,
        description="对所有来自玩家或外部数据源的数据进行验证",
        rationale="未经验证的外部输入可能导致安全问题或崩溃",
        examples_good=[
            "def handle_command(args):\n    if not isinstance(args.get('value'), int):\n        return\n    process(args['value'])",
        ],
        examples_bad=[
            "def handle_command(args):\n    process(args['value'])  # 未验证类型",
        ],
        severity=PracticeSeverity.ERROR,
    ),
    BestPractice(
        id="SEC002",
        name="限制敏感操作权限",
        category=PracticeCategory.SECURITY,
        description="敏感操作应检查玩家权限或身份",
        rationale="权限检查可以防止未授权访问",
        examples_good=[
            "def admin_command(player, cmd):\n    if not is_admin(player):\n        NotifyToClient(player, 'error', 'Permission denied')\n        return",
        ],
        examples_bad=[
            "def admin_command(player, cmd):\n    execute_admin_action(cmd)  # 未检查权限",
        ],
        severity=PracticeSeverity.CRITICAL,
    ),
    # 可维护性
    BestPractice(
        id="MAIN001",
        name="使用有意义的变量名",
        category=PracticeCategory.MAINTAINABILITY,
        description="变量名应清楚表达其用途",
        rationale="良好的命名提高代码可读性",
        examples_good=[
            "player_health = GetEntityHealth(player_id)",
            "remaining_cooldown = cooldown_time - elapsed_time",
        ],
        examples_bad=[
            "x = GetEntityHealth(y)",
            "temp = a - b",
        ],
        severity=PracticeSeverity.INFO,
    ),
    BestPractice(
        id="MAIN002",
        name="避免魔法数字",
        category=PracticeCategory.MAINTAINABILITY,
        description="使用命名常量代替硬编码的数字",
        rationale="命名常量使代码更易理解和修改",
        examples_good=[
            "MAX_PLAYERS = 100\nDEFAULT_HEALTH = 20\nif player_count > MAX_PLAYERS:",
        ],
        examples_bad=[
            "if player_count > 100:  # 100 是什么意思？",
        ],
        severity=PracticeSeverity.INFO,
    ),
    BestPractice(
        id="MAIN003",
        name="函数职责单一",
        category=PracticeCategory.MAINTAINABILITY,
        description="每个函数应该只做一件事",
        rationale="单一职责使函数更易测试和维护",
        examples_good=[
            "def calculate_damage(attacker, defender):\n    base = get_base_damage(attacker)\n    modifier = get_defense_modifier(defender)\n    return base * modifier",
        ],
        examples_bad=[
            "def attack_and_heal_and_log(attacker, defender, logger):\n    # 做了太多事情",
        ],
        severity=PracticeSeverity.WARNING,
    ),
    # ModSDK 特定
    BestPractice(
        id="MSDK001",
        name="使用正确的事件监听注册",
        category=PracticeCategory.MODSDK,
        description="使用 ListenForEvent 或 RegisterXxxEventListener 注册事件",
        rationale="正确的事件注册确保事件能够被正确触发",
        examples_good=[
            "ListenForEvent('OnScriptTickServerEvent', self, self.on_tick)\nRegisterEntityEventListener(entity_id, 'EntityHurtEvent', self, self.on_hurt)",
        ],
        examples_bad=[
            "# 直接定义函数但未注册",
            "def OnScriptTickServerEvent(args):\n    pass",
        ],
        severity=PracticeSeverity.ERROR,
    ),
    BestPractice(
        id="MSDK002",
        name="服务端/客户端代码分离",
        category=PracticeCategory.MODSDK,
        description="明确区分服务端和客户端代码",
        rationale="ModSDK 采用客户端-服务端架构，混淆可能导致同步问题",
        examples_good=[
            "# server_service.py - 服务端逻辑\n# client_ui.py - 客户端 UI\n# shared/ - 共享代码",
        ],
        examples_bad=[
            "# 在客户端代码中直接调用服务端 API",
        ],
        severity=PracticeSeverity.WARNING,
    ),
    BestPractice(
        id="MSDK003",
        name="使用 NotifyToClient/NotifyToServer 进行通信",
        category=PracticeCategory.MODSDK,
        description="客户端和服务端之间的通信使用官方 API",
        rationale="使用官方 API 确保数据正确传输",
        examples_good=[
            "# 服务端\nNotifyToClient(player_uid, 'UpdateHealthEvent', {'health': health})\n\n# 客户端\nListenForEvent('UpdateHealthEvent', self, self.on_health_update)",
        ],
        examples_bad=[
            "# 尝试直接共享变量或使用非标准方式通信",
        ],
        severity=PracticeSeverity.ERROR,
    ),
    BestPractice(
        id="MSDK004",
        name="正确处理实体 ID",
        category=PracticeCategory.MODSDK,
        description="实体 ID 是字符串类型，需要进行有效性检查",
        rationale="无效的实体 ID 可能导致 API 调用失败或崩溃",
        examples_good=[
            "def process_entity(entity_id):\n    if not entity_id or not isinstance(entity_id, str):\n        return\n    pos = GetEntityPos(entity_id)",
        ],
        examples_bad=[
            "def process_entity(entity_id):\n    pos = GetEntityPos(entity_id)  # 未检查有效性",
        ],
        severity=PracticeSeverity.WARNING,
    ),
    # 错误处理
    BestPractice(
        id="ERR001",
        name="使用 try-except 处理可能失败的 API 调用",
        category=PracticeCategory.ERROR_HANDLING,
        description="对可能失败的 API 调用进行异常处理",
        rationale="异常处理可以防止崩溃并提供错误信息",
        examples_good=[
            "try:\n    result = GetEntityPos(entity_id)\nexcept Exception as e:\n    print(f'Failed to get position: {e}')\n    return None",
        ],
        examples_bad=[
            "result = GetEntityPos(entity_id)  # 可能失败但未处理",
        ],
        severity=PracticeSeverity.WARNING,
    ),
    BestPractice(
        id="ERR002",
        name="提供有意义的错误信息",
        category=PracticeCategory.ERROR_HANDLING,
        description="错误信息应包含足够的上下文便于调试",
        rationale="好的错误信息可以加速问题定位",
        examples_good=[
            "raise ValueError(f'Invalid player_id: {player_id}, expected non-empty string')",
        ],
        examples_bad=[
            "raise ValueError('Invalid input')  # 缺少具体信息",
        ],
        severity=PracticeSeverity.INFO,
    ),
    # 编码风格
    BestPractice(
        id="STYLE001",
        name="遵循 PEP 8 编码规范",
        category=PracticeCategory.CODING_STYLE,
        description="遵循 Python 编码规范 PEP 8",
        rationale="统一的编码风格提高代码可读性",
        examples_good=[
            "def get_player_health(player_id):\n    \"\"\"Get player's current health.\"\"\"\n    return health",
        ],
        examples_bad=[
            "def GetPlayerHealth(PlayerID):\n    # 函数名应使用 snake_case",
        ],
        severity=PracticeSeverity.INFO,
    ),
    BestPractice(
        id="STYLE002",
        name="使用文档字符串",
        category=PracticeCategory.CODING_STYLE,
        description="为公共函数和类添加文档字符串",
        rationale="文档字符串提供 API 文档和使用说明",
        examples_good=[
            "def calculate_damage(attacker_id: str, defender_id: str) -> float:\n    \"\"\"Calculate damage from attacker to defender.\n\n    Args:\n        attacker_id: The entity ID of the attacker.\n        defender_id: The entity ID of the defender.\n\n    Returns:\n        The calculated damage value.\n    \"\"\"",
        ],
        examples_bad=[
            "def calculate_damage(attacker_id, defender_id):\n    return damage  # 无文档",
        ],
        severity=PracticeSeverity.INFO,
    ),
]


class BestPracticeChecker:
    """最佳实践检查器

    检查代码是否遵循 ModSDK 最佳实践。

    Example:
        >>> checker = BestPracticeChecker()
        >>> results = checker.check(code)
        >>> for r in results:
        ...     if not r.passed:
        ...         print(f"{r.practice.id}: {r.message}")
    """

    def __init__(self, practices: list[BestPractice] | None = None) -> None:
        """初始化检查器

        Args:
            practices: 自定义最佳实践列表，默认使用 ModSDK 最佳实践
        """
        self._practices = practices or MODSDK_BEST_PRACTICES
        self._practice_map: dict[str, BestPractice] = {p.id: p for p in self._practices}

    def check(self, code: str) -> list[BestPracticeResult]:
        """检查代码

        Args:
            code: 源代码

        Returns:
            检查结果列表
        """
        results: list[BestPracticeResult] = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return results

        lines = code.split("\n")

        # 运行各种检查
        results.extend(self._check_performance(code, tree, lines))
        results.extend(self._check_security(code, tree, lines))
        results.extend(self._check_modsdk(code, tree, lines))
        results.extend(self._check_error_handling(code, tree, lines))
        results.extend(self._check_style(code, tree, lines))

        return results

    def _check_performance(
        self, code: str, tree: ast.AST, lines: list[str]
    ) -> list[BestPracticeResult]:
        """检查性能相关实践"""
        results: list[BestPracticeResult] = []

        # 检查 Tick 事件中的循环
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查是否是 Tick 事件处理函数
                is_tick_handler = any(
                    name in node.name.lower()
                    for name in ("tick", "ontick", "on_tick", "on_script_tick")
                )

                if is_tick_handler:
                    # 检查是否有循环
                    for child in ast.walk(node):
                        if isinstance(child, ast.For):
                            practice = self._practice_map["PERF001"]
                            results.append(
                                BestPracticeResult(
                                    practice=practice,
                                    message="Tick 事件处理函数中包含循环，可能影响性能",
                                    line=child.lineno,
                                    code_snippet=lines[child.lineno - 1] if child.lineno <= len(lines) else "",
                                    suggestion="考虑将操作分摊到多个 Tick 中执行",
                                    passed=False,
                                )
                            )
                            break

        return results

    def _check_security(
        self, code: str, tree: ast.AST, lines: list[str]
    ) -> list[BestPracticeResult]:
        """检查安全相关实践"""
        results: list[BestPracticeResult] = []

        # 检查事件处理函数中的输入验证
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查是否处理外部输入
                if any(
                    name in node.name.lower()
                    for name in ("command", "chat", "input", "handle", "process")
                ):
                    # 检查是否有类型检查
                    has_type_check = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                if child.func.id in ("isinstance", "type"):
                                    has_type_check = True
                                    break

                    if not has_type_check and len(node.args.args) > 0:
                        practice = self._practice_map["SEC001"]
                        results.append(
                            BestPracticeResult(
                                practice=practice,
                                message=f"函数 '{node.name}' 处理外部输入但缺少类型验证",
                                line=node.lineno,
                                suggestion="添加参数类型验证",
                                passed=False,
                            )
                        )

        return results

    def _check_modsdk(
        self, code: str, tree: ast.AST, lines: list[str]
    ) -> list[BestPracticeResult]:
        """检查 ModSDK 特定实践"""
        results: list[BestPracticeResult] = []

        # 检查事件监听注册
        has_listen_for_event = False
        has_register_listener = False
        has_event_handler = False

        for i, line in enumerate(lines, 1):
            if "ListenForEvent" in line:
                has_listen_for_event = True
            if "RegisterEntityEventListener" in line or "RegisterPlayerEventListener" in line:
                has_register_listener = True

        # 检查是否有定义但未注册的事件处理函数
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if any(
                    evt in node.name
                    for evt in ("Event", "OnScript", "OnCustom")
                ):
                    has_event_handler = True
                    break

        if has_event_handler and not (has_listen_for_event or has_register_listener):
            practice = self._practice_map["MSDK001"]
            results.append(
                BestPracticeResult(
                    practice=practice,
                    message="检测到事件处理函数但未找到事件注册代码",
                    line=1,
                    suggestion="使用 ListenForEvent 或 RegisterXxxEventListener 注册事件",
                    passed=False,
                )
            )

        return results

    def _check_error_handling(
        self, code: str, tree: ast.AST, lines: list[str]
    ) -> list[BestPracticeResult]:
        """检查错误处理实践"""
        results: list[BestPracticeResult] = []

        # 检查 API 调用是否有 try-except
        api_calls = [
            "GetEntityPos",
            "SetEntityPos",
            "CreateEngineEntity",
            "DestroyEntity",
            "GetPlayerByUid",
        ]

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in api_calls:
                    # 检查是否在 try 块中（简化检查）
                    practice = self._practice_map["ERR001"]
                    # 不报告，仅记录建议

        return results

    def _check_style(
        self, code: str, tree: ast.AST, lines: list[str]
    ) -> list[BestPracticeResult]:
        """检查编码风格实践"""
        results: list[BestPracticeResult] = []

        # 检查文档字符串
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 公共函数检查文档字符串
                if not node.name.startswith("_"):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        practice = self._practice_map["STYLE002"]
                        results.append(
                            BestPracticeResult(
                                practice=practice,
                                message=f"公共函数 '{node.name}' 缺少文档字符串",
                                line=node.lineno,
                                suggestion="添加文档字符串描述函数功能",
                                passed=False,
                            )
                        )

        return results

    def get_practice(self, practice_id: str) -> BestPractice | None:
        """获取指定的最佳实践"""
        return self._practice_map.get(practice_id)

    def list_practices(self, category: PracticeCategory | None = None) -> list[BestPractice]:
        """列出最佳实践

        Args:
            category: 可选的类别过滤

        Returns:
            最佳实践列表
        """
        if category:
            return [p for p in self._practices if p.category == category]
        return self._practices

    def get_summary(self, results: list[BestPracticeResult]) -> dict:
        """获取检查结果摘要"""
        summary = {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "by_category": {},
            "by_severity": {},
        }

        for r in results:
            # 按类别统计
            cat = r.practice.category.value
            summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

            # 按严重程度统计
            sev = r.practice.severity.value
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1

        return summary