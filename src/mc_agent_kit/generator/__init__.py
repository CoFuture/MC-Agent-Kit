"""
代码生成模块

提供 ModSDK 代码生成功能，基于 Jinja2 模板引擎。
"""

from .bindings import APIBindingGenerator
from .code_gen import CodeGenerator, generate_api_call, generate_event_listener
from .event_gen import EventGenerator, EventListenerConfig
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
    # 数据类
    "CodeTemplate",
    "TemplateParameter",
    "TemplateType",
    "EventListenerConfig",
    # 便捷函数
    "generate_event_listener",
    "generate_api_call",
    "load_templates_from_directory",
    # 常量
    "BUILTIN_TEMPLATES",
]
