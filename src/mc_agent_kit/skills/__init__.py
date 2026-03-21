"""
MC-Agent-Kit Skills 模块

提供 AI Agent 的技能扩展接口。
"""

from .base import (
    BaseSkill,
    SkillCategory,
    SkillMetadata,
    SkillPriority,
    SkillRegistry,
    SkillResult,
    get_registry,
    get_skill,
    register_skill,
)
from .modsdk import (
    ModSDKAPISearchSkill,
    ModSDKCodeGenSkill,
    ModSDKDebugSkill,
    ModSDKEventSearchSkill,
)

__all__ = [
    # 基类和工具
    "BaseSkill",
    "SkillCategory",
    "SkillMetadata",
    "SkillPriority",
    "SkillRegistry",
    "SkillResult",
    "get_registry",
    "get_skill",
    "register_skill",
    # ModSDK Skills
    "ModSDKAPISearchSkill",
    "ModSDKCodeGenSkill",
    "ModSDKDebugSkill",
    "ModSDKEventSearchSkill",
]


def register_modsdk_skills(kb_path: str | None = None) -> None:
    """注册所有 ModSDK Skills

    Args:
        kb_path: 可选的知识库文件路径
    """
    registry = get_registry()

    # 注册 API 搜索 Skill
    api_skill = ModSDKAPISearchSkill(kb_path=kb_path)
    registry.register(api_skill)

    # 注册事件搜索 Skill
    event_skill = ModSDKEventSearchSkill(kb_path=kb_path)
    registry.register(event_skill)

    # 注册代码生成 Skill
    code_gen_skill = ModSDKCodeGenSkill()
    registry.register(code_gen_skill)

    # 注册调试辅助 Skill
    debug_skill = ModSDKDebugSkill()
    registry.register(debug_skill)
