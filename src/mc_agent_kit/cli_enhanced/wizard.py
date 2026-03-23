"""
交互式 CLI 向导模块

提供交互式向导功能，引导用户完成常见任务。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class WizardStepType(Enum):
    """向导步骤类型"""
    TEXT = "text"           # 文本输入
    SELECT = "select"       # 单选
    MULTI_SELECT = "multi"  # 多选
    CONFIRM = "confirm"     # 确认
    NUMBER = "number"       # 数字输入
    PATH = "path"           # 路径输入
    PASSWORD = "password"   # 密码输入


class WizardScenario(Enum):
    """预定义向导场景"""
    PROJECT_CREATE = "project_create"
    ENTITY_CREATE = "entity_create"
    ITEM_CREATE = "item_create"
    BLOCK_CREATE = "block_create"
    CONFIG_SETUP = "config_setup"
    DIAGNOSE = "diagnose"
    DEPLOY = "deploy"


@dataclass
class WizardOption:
    """选项定义"""
    value: str
    label: str
    description: str = ""
    disabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "label": self.label,
            "description": self.description,
            "disabled": self.disabled,
        }


@dataclass
class WizardStep:
    """向导步骤"""
    id: str
    title: str
    description: str = ""
    step_type: WizardStepType = WizardStepType.TEXT
    options: list[WizardOption] = field(default_factory=list)
    default: Any = None
    required: bool = True
    validation: Callable[[Any], bool] | None = None
    validation_message: str = ""
    placeholder: str = ""
    help_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "step_type": self.step_type.value,
            "options": [o.to_dict() for o in self.options],
            "default": self.default,
            "required": self.required,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
        }


@dataclass
class WizardResult:
    """向导结果"""
    scenario: str
    success: bool
    answers: dict[str, Any]
    cancelled: bool = False
    current_step: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "success": self.success,
            "answers": self.answers,
            "cancelled": self.cancelled,
            "current_step": self.current_step,
            "error": self.error,
        }


@dataclass
class WizardDefinition:
    """向导定义"""
    id: str
    name: str
    description: str
    steps: list[WizardStep]
    on_complete: Callable[[dict[str, Any]], dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
        }


class InteractiveWizard:
    """
    交互式 CLI 向导

    支持多种输入类型和验证，可扩展自定义场景。

    使用示例:
        wizard = InteractiveWizard()
        
        # 使用预定义场景
        result = wizard.run_scenario(WizardScenario.PROJECT_CREATE)
        
        # 自定义向导
        wizard.add_step(WizardStep(id="name", title="项目名称", step_type=WizardStepType.TEXT))
        result = wizard.run()
    """

    def __init__(self) -> None:
        self._steps: list[WizardStep] = []
        self._scenarios: dict[str, WizardDefinition] = {}
        self._current_step: int = 0
        self._answers: dict[str, Any] = {}
        self._cancelled: bool = False

        # 注册内置场景
        self._register_builtin_scenarios()

    def _register_builtin_scenarios(self) -> None:
        """注册内置向导场景"""
        # 项目创建向导
        self.register_scenario(WizardDefinition(
            id=WizardScenario.PROJECT_CREATE.value,
            name="创建项目",
            description="交互式创建新的 ModSDK 项目",
            steps=[
                WizardStep(
                    id="project_name",
                    title="项目名称",
                    description="输入项目名称",
                    step_type=WizardStepType.TEXT,
                    placeholder="my-addon",
                    required=True,
                    validation=lambda x: len(x) > 0 and x.replace("_", "").replace("-", "").isalnum(),
                    validation_message="项目名称只能包含字母、数字、下划线和连字符",
                ),
                WizardStep(
                    id="project_type",
                    title="项目类型",
                    description="选择项目类型",
                    step_type=WizardStepType.SELECT,
                    options=[
                        WizardOption("empty", "空项目", "只有基础结构"),
                        WizardOption("entity", "实体项目", "包含实体开发模板"),
                        WizardOption("item", "物品项目", "包含物品开发模板"),
                        WizardOption("block", "方块项目", "包含方块开发模板"),
                        WizardOption("full", "完整项目", "包含实体、物品、方块模板"),
                    ],
                    default="empty",
                ),
                WizardStep(
                    id="output_dir",
                    title="输出目录",
                    description="选择项目创建位置",
                    step_type=WizardStepType.PATH,
                    default=".",
                ),
                WizardStep(
                    id="author",
                    title="作者",
                    description="输入作者名称",
                    step_type=WizardStepType.TEXT,
                    required=False,
                ),
                WizardStep(
                    id="description",
                    title="描述",
                    description="输入项目描述",
                    step_type=WizardStepType.TEXT,
                    required=False,
                ),
                WizardStep(
                    id="confirm",
                    title="确认创建",
                    description="确认创建项目？",
                    step_type=WizardStepType.CONFIRM,
                    default=True,
                ),
            ],
        ))

        # 实体创建向导
        self.register_scenario(WizardDefinition(
            id=WizardScenario.ENTITY_CREATE.value,
            name="创建实体",
            description="交互式创建自定义实体",
            steps=[
                WizardStep(
                    id="entity_name",
                    title="实体名称",
                    description="输入实体名称（英文标识符）",
                    step_type=WizardStepType.TEXT,
                    placeholder="frost_ghost",
                    required=True,
                ),
                WizardStep(
                    id="entity_type",
                    title="实体类型",
                    description="选择实体行为类型",
                    step_type=WizardStepType.SELECT,
                    options=[
                        WizardOption("passive", "被动型", "不会主动攻击"),
                        WizardOption("neutral", "中立型", "受到攻击后反击"),
                        WizardOption("hostile", "敌对型", "主动攻击玩家"),
                    ],
                    default="passive",
                ),
                WizardStep(
                    id="health",
                    title="生命值",
                    description="设置实体生命值",
                    step_type=WizardStepType.NUMBER,
                    default=20,
                ),
                WizardStep(
                    id="spawn_egg",
                    title="生成蛋",
                    description="是否创建生成蛋",
                    step_type=WizardStepType.CONFIRM,
                    default=True,
                ),
            ],
        ))

        # 物品创建向导
        self.register_scenario(WizardDefinition(
            id=WizardScenario.ITEM_CREATE.value,
            name="创建物品",
            description="交互式创建自定义物品",
            steps=[
                WizardStep(
                    id="item_name",
                    title="物品名称",
                    description="输入物品名称（英文标识符）",
                    step_type=WizardStepType.TEXT,
                    required=True,
                ),
                WizardStep(
                    id="item_type",
                    title="物品类型",
                    description="选择物品类型",
                    step_type=WizardStepType.SELECT,
                    options=[
                        WizardOption("consumable", "消耗品", "可食用/使用"),
                        WizardOption("tool", "工具", "耐久度工具"),
                        WizardOption("weapon", "武器", "攻击用武器"),
                        WizardOption("armor", "护甲", "防具"),
                        WizardOption("material", "材料", "合成材料"),
                    ],
                    default="consumable",
                ),
                WizardStep(
                    id="max_stack",
                    title="最大堆叠",
                    description="设置最大堆叠数量",
                    step_type=WizardStepType.NUMBER,
                    default=64,
                ),
            ],
        ))

        # 配置设置向导
        self.register_scenario(WizardDefinition(
            id=WizardScenario.CONFIG_SETUP.value,
            name="配置设置",
            description="交互式配置 MC-Agent-Kit",
            steps=[
                WizardStep(
                    id="game_path",
                    title="游戏路径",
                    description="设置 Minecraft 游戏安装路径",
                    step_type=WizardStepType.PATH,
                    required=True,
                ),
                WizardStep(
                    id="addon_path",
                    title="Addon 路径",
                    description="设置 Addon 开发目录",
                    step_type=WizardStepType.PATH,
                    required=True,
                ),
                WizardStep(
                    id="kb_path",
                    title="知识库路径",
                    description="设置知识库目录（可选）",
                    step_type=WizardStepType.PATH,
                    required=False,
                ),
                WizardStep(
                    id="auto_launch",
                    title="自动启动",
                    description="代码生成后是否自动启动游戏测试",
                    step_type=WizardStepType.CONFIRM,
                    default=False,
                ),
                WizardStep(
                    id="log_level",
                    title="日志级别",
                    description="设置日志输出级别",
                    step_type=WizardStepType.SELECT,
                    options=[
                        WizardOption("debug", "DEBUG", "详细调试信息"),
                        WizardOption("info", "INFO", "一般信息"),
                        WizardOption("warning", "WARNING", "警告信息"),
                        WizardOption("error", "ERROR", "仅错误信息"),
                    ],
                    default="info",
                ),
            ],
        ))

        # 诊断向导
        self.register_scenario(WizardDefinition(
            id=WizardScenario.DIAGNOSE.value,
            name="问题诊断",
            description="交互式诊断问题",
            steps=[
                WizardStep(
                    id="issue_type",
                    title="问题类型",
                    description="选择遇到的问题类型",
                    step_type=WizardStepType.SELECT,
                    options=[
                        WizardOption("launch", "启动失败", "游戏无法启动"),
                        WizardOption("load", "加载失败", "Addon 无法加载"),
                        WizardOption("runtime", "运行时错误", "游戏内报错"),
                        WizardOption("behavior", "行为异常", "实体/物品行为不正确"),
                        WizardOption("other", "其他问题", "其他类型问题"),
                    ],
                ),
                WizardStep(
                    id="error_message",
                    title="错误信息",
                    description="粘贴错误信息（可选）",
                    step_type=WizardStepType.TEXT,
                    required=False,
                ),
                WizardStep(
                    id="log_file",
                    title="日志文件",
                    description="提供日志文件路径（可选）",
                    step_type=WizardStepType.PATH,
                    required=False,
                ),
            ],
        ))

    def register_scenario(self, definition: WizardDefinition) -> None:
        """注册向导场景"""
        self._scenarios[definition.id] = definition

    def get_scenario(self, scenario_id: str) -> WizardDefinition | None:
        """获取向导场景"""
        return self._scenarios.get(scenario_id)

    def list_scenarios(self) -> list[WizardDefinition]:
        """列出所有场景"""
        return list(self._scenarios.values())

    def add_step(self, step: WizardStep) -> None:
        """添加步骤"""
        self._steps.append(step)

    def clear_steps(self) -> None:
        """清空步骤"""
        self._steps.clear()

    def run_scenario(self, scenario: WizardScenario | str) -> WizardResult:
        """运行预定义场景"""
        scenario_id = scenario.value if isinstance(scenario, WizardScenario) else scenario
        definition = self._scenarios.get(scenario_id)
        
        if not definition:
            return WizardResult(
                scenario=scenario_id,
                success=False,
                answers={},
                error=f"Scenario not found: {scenario_id}",
            )

        self._steps = definition.steps.copy()
        return self.run(definition.id)

    def run(self, scenario_id: str = "custom") -> WizardResult:
        """
        运行向导

        这是一个模拟实现，实际使用时需要与前端/终端交互。
        返回的结果可以用于后续处理。
        """
        self._current_step = 0
        self._answers = {}
        self._cancelled = False

        # 模拟向导流程
        # 实际实现需要与用户交互
        for i, step in enumerate(self._steps):
            self._current_step = i
            
            # 使用默认值
            if step.default is not None:
                self._answers[step.id] = step.default
            elif not step.required:
                self._answers[step.id] = None
            else:
                # 必填但没有默认值，标记为需要输入
                self._answers[step.id] = None

        return WizardResult(
            scenario=scenario_id,
            success=True,
            answers=self._answers,
            current_step=self._current_step,
        )

    def run_with_answers(
        self,
        scenario: WizardScenario | str,
        answers: dict[str, Any],
    ) -> WizardResult:
        """
        使用预设答案运行向导

        用于程序化调用或测试。
        """
        scenario_id = scenario.value if isinstance(scenario, WizardScenario) else scenario
        definition = self._scenarios.get(scenario_id)
        
        if not definition:
            return WizardResult(
                scenario=scenario_id,
                success=False,
                answers=answers,
                error=f"Scenario not found: {scenario_id}",
            )

        # 验证答案
        validated_answers: dict[str, Any] = {}
        errors: list[str] = []

        for step in definition.steps:
            if step.id in answers:
                value = answers[step.id]
                if step.validation and not step.validation(value):
                    errors.append(f"Invalid value for '{step.id}': {step.validation_message}")
                else:
                    validated_answers[step.id] = value
            elif step.required and step.default is None:
                errors.append(f"Required field missing: {step.id}")
            elif step.default is not None:
                validated_answers[step.id] = step.default

        if errors:
            return WizardResult(
                scenario=scenario_id,
                success=False,
                answers=validated_answers,
                error="; ".join(errors),
            )

        # 执行完成回调
        if definition.on_complete:
            try:
                result = definition.on_complete(validated_answers)
                validated_answers.update(result)
            except Exception as e:
                return WizardResult(
                    scenario=scenario_id,
                    success=False,
                    answers=validated_answers,
                    error=str(e),
                )

        return WizardResult(
            scenario=scenario_id,
            success=True,
            answers=validated_answers,
        )

    def validate_step(self, step: WizardStep, value: Any) -> tuple[bool, str]:
        """验证步骤输入"""
        if step.required and value is None:
            return False, "此字段为必填项"
        
        if step.validation and value is not None:
            if not step.validation(value):
                return False, step.validation_message
        
        return True, ""

    def get_step(self, index: int) -> WizardStep | None:
        """获取步骤"""
        if 0 <= index < len(self._steps):
            return self._steps[index]
        return None

    def get_progress(self) -> tuple[int, int]:
        """获取进度"""
        return self._current_step, len(self._steps)


# 便捷函数
def create_wizard() -> InteractiveWizard:
    """创建向导实例"""
    return InteractiveWizard()


def run_project_wizard(answers: dict[str, Any] | None = None) -> WizardResult:
    """运行项目创建向导"""
    wizard = InteractiveWizard()
    if answers:
        return wizard.run_with_answers(WizardScenario.PROJECT_CREATE, answers)
    return wizard.run_scenario(WizardScenario.PROJECT_CREATE)


def run_entity_wizard(answers: dict[str, Any] | None = None) -> WizardResult:
    """运行实体创建向导"""
    wizard = InteractiveWizard()
    if answers:
        return wizard.run_with_answers(WizardScenario.ENTITY_CREATE, answers)
    return wizard.run_scenario(WizardScenario.ENTITY_CREATE)


def run_config_wizard(answers: dict[str, Any] | None = None) -> WizardResult:
    """运行配置设置向导"""
    wizard = InteractiveWizard()
    if answers:
        return wizard.run_with_answers(WizardScenario.CONFIG_SETUP, answers)
    return wizard.run_scenario(WizardScenario.CONFIG_SETUP)