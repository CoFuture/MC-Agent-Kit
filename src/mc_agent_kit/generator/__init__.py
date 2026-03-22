"""
代码生成模块

提供 ModSDK 代码生成功能，基于 Jinja2 模板引擎。
"""

from .bindings import APIBindingGenerator
from .code_gen import CodeGenerator, generate_api_call, generate_event_listener
from .enhanced_templates import (
    BLOCK_LOGIC_TEMPLATE,
    DATA_SYNC_TEMPLATE,
    ENTITY_BEHAVIOR_TEMPLATE,
    ENHANCED_TEMPLATES,
    ITEM_LOGIC_TEMPLATE,
)
from .event_gen import EventGenerator, EventListenerConfig
from .quality_checker import (
    CodeQualityChecker,
    QualityCheckConfig,
    QualityIssue,
    QualityIssueCategory,
    QualityIssueSeverity,
    QualityReport,
    check_code_quality,
    validate_generated_code,
)
from .template_loader import TemplateLoader, load_templates_from_directory
from .templates import (
    BUILTIN_TEMPLATES,
    CodeTemplate,
    TemplateManager,
    TemplateParameter,
    TemplateType,
)

__all__ = [
    # 核心类
    "CodeGenerator",
    "TemplateManager",
    "TemplateLoader",
    "APIBindingGenerator",
    "EventGenerator",
    "CodeQualityChecker",
    # 数据类
    "CodeTemplate",
    "TemplateParameter",
    "TemplateType",
    "EventListenerConfig",
    "QualityReport",
    "QualityIssue",
    "QualityIssueSeverity",
    "QualityIssueCategory",
    "QualityCheckConfig",
    # 便捷函数
    "generate_event_listener",
    "generate_api_call",
    "load_templates_from_directory",
    "check_code_quality",
    "validate_generated_code",
    # 常量
    "BUILTIN_TEMPLATES",
    "ENHANCED_TEMPLATES",
    # 增强模板
    "ENTITY_BEHAVIOR_TEMPLATE",
    "ITEM_LOGIC_TEMPLATE",
    "BLOCK_LOGIC_TEMPLATE",
    "DATA_SYNC_TEMPLATE",
]
