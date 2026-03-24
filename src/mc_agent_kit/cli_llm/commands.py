"""CLI commands for LLM-powered features.

Provides commands for code generation, review, diagnosis, and fix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mc_agent_kit.llm import (
    ChatMessage,
    ChatRole,
    CodeGenerationType,
    GenerationContext,
    GeneratedCode,
    get_llm_manager,
    diagnose_error,
    fix_error,
    review_code,
    LLMConfig,
)

from .config import LLMCliConfig, load_llm_cli_config
from .output import (
    CodeFormatter,
    OutputFormat,
    format_code_result,
    format_review_result,
)


def generate_command(
    prompt: str,
    generation_type: str = "custom",
    target: str = "server",
    context: dict[str, Any] | None = None,
    config: LLMCliConfig | None = None,
    stream: bool = False,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]:
    """Generate code based on natural language prompt.

    Args:
        prompt: Natural language description
        generation_type: Type of code to generate
        target: Target environment (server/client)
        context: Additional context
        config: LLM CLI configuration
        stream: Whether to stream output
        format: Output format

    Returns:
        Generation result
    """
    if config is None:
        config = load_llm_cli_config()

    # Get LLM manager
    manager = get_llm_manager()
    manager.set_default_provider(config.default_provider)

    # Build generation context
    gen_context = GenerationContext(
        project_name=context.get("project_name") if context else None,
        module_name=context.get("module_name") if context else None,
        description=prompt,
        target=target,
    )

    # Map generation type
    type_map = {
        "event_listener": CodeGenerationType.EVENT_LISTENER,
        "entity_behavior": CodeGenerationType.ENTITY_BEHAVIOR,
        "item_logic": CodeGenerationType.ITEM_LOGIC,
        "ui_screen": CodeGenerationType.UI_SCREEN,
        "network_sync": CodeGenerationType.NETWORK_SYNC,
        "config_handler": CodeGenerationType.CONFIG_HANDLER,
        "error_handler": CodeGenerationType.ERROR_HANDLER,
        "custom": CodeGenerationType.CUSTOM,
    }
    gen_type = type_map.get(generation_type, CodeGenerationType.CUSTOM)

    # Get provider config
    provider_config = config.get_provider_config(config.default_provider)
    llm_config = LLMConfig(
        provider=config.default_provider,
        model=provider_config.model or "default",
        api_key=provider_config.api_key,
        temperature=provider_config.temperature,
        max_tokens=provider_config.max_tokens,
    )

    try:
        # Build messages
        system_prompt = _get_generation_system_prompt(gen_type)
        messages = [
            ChatMessage(role=ChatRole.SYSTEM, content=system_prompt),
            ChatMessage(role=ChatRole.USER, content=_build_generation_prompt(prompt, gen_context)),
        ]

        if stream:
            # Stream response
            full_content = []
            for chunk in manager.stream(messages, llm_config):
                full_content.append(chunk.content)
                print(chunk.content, end="", flush=True)
            print()

            content = "".join(full_content)
        else:
            # Get completion
            result = manager.complete(messages, llm_config)
            content = result.content

        # Parse generated code
        code = _extract_code(content)

        return {
            "success": True,
            "code": code,
            "raw_response": content,
            "generation_type": generation_type,
            "target": target,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "code": None,
        }


def review_command(
    code: str,
    categories: list[str] | None = None,
    min_score: int = 60,
    config: LLMCliConfig | None = None,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]:
    """Review code and provide suggestions.

    Args:
        code: Code to review
        categories: Review categories
        min_score: Minimum acceptable score
        config: LLM CLI configuration
        format: Output format

    Returns:
        Review result
    """
    if config is None:
        config = load_llm_cli_config()

    # Default categories
    if categories is None:
        categories = config.code_review.categories

    try:
        # Use the review_code function from llm module
        result = review_code(
            code=code,
            min_score=min_score,
        )

        # Convert to dict
        result_dict = result.to_dict()
        result_dict["success"] = True
        return result_dict

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "score": 0,
            "grade": "F",
            "passed": False,
            "issues": [],
        }


def diagnose_command(
    error_message: str,
    code: str | None = None,
    stack_trace: str | None = None,
    config: LLMCliConfig | None = None,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]:
    """Diagnose an error and provide fix suggestions.

    Args:
        error_message: Error message
        code: Related code
        stack_trace: Stack trace
        config: LLM CLI configuration
        format: Output format

    Returns:
        Diagnosis result
    """
    if config is None:
        config = load_llm_cli_config()

    try:
        # Use the diagnose_error function from llm module
        result = diagnose_error(
            error_message=error_message,
            code=code or "",
            stack_trace=stack_trace,
        )

        # Convert to dict
        result_dict = result.to_dict()
        result_dict["success"] = True
        return result_dict

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "Unknown",
            "error_message": error_message,
            "suggestions": [],
        }


def fix_command(
    error_message: str,
    code: str,
    apply: bool = False,
    config: LLMCliConfig | None = None,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]:
    """Attempt to fix an error in code.

    Args:
        error_message: Error message
        code: Code with error
        apply: Whether to automatically apply fix
        config: LLM CLI configuration
        format: Output format

    Returns:
        Fix result
    """
    if config is None:
        config = load_llm_cli_config()

    try:
        # Use the fix_error function from llm module
        result = fix_error(
            error_message=error_message,
            code=code,
            auto_apply=apply,
        )

        # Convert to dict
        result_dict = result.to_dict()
        result_dict["success"] = True
        return result_dict

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fixed_code": None,
            "original_code": code,
        }


def _get_generation_system_prompt(gen_type: CodeGenerationType) -> str:
    """Get system prompt for code generation.

    Args:
        gen_type: Generation type

    Returns:
        System prompt
    """
    base_prompt = """你是一位资深的 Minecraft 网易版 ModSDK 开发专家。
请根据用户的需求生成高质量的 Python 代码。

注意事项：
1. ModSDK 使用 Python 2.7 语法
2. 代码需要兼容网易版我的世界
3. 添加必要的注释说明
4. 遵循最佳实践

请直接输出代码，使用 ```python 代码块包裹。"""

    type_hints = {
        CodeGenerationType.EVENT_LISTENER: "\n重点关注事件监听器的创建和回调函数的实现。",
        CodeGenerationType.ENTITY_BEHAVIOR: "\n重点关注实体行为逻辑和状态管理。",
        CodeGenerationType.ITEM_LOGIC: "\n重点关注物品的交互逻辑和属性设置。",
        CodeGenerationType.UI_SCREEN: "\n重点关注 UI 界面的创建和事件处理。",
        CodeGenerationType.NETWORK_SYNC: "\n重点关注客户端和服务端的数据同步。",
        CodeGenerationType.CONFIG_HANDLER: "\n重点关注配置文件的读取和处理。",
        CodeGenerationType.ERROR_HANDLER: "\n重点关注错误处理和异常恢复。",
        CodeGenerationType.CUSTOM: "",
    }

    return base_prompt + type_hints.get(gen_type, "")


def _build_generation_prompt(
    prompt: str,
    context: GenerationContext,
) -> str:
    """Build the generation prompt.

    Args:
        prompt: User prompt
        context: Generation context

    Returns:
        Full prompt
    """
    parts = [f"需求：{prompt}"]

    if context.project_name:
        parts.append(f"项目名称：{context.project_name}")
    if context.module_name:
        parts.append(f"模块名称：{context.module_name}")
    if context.target_environment:
        parts.append(f"运行环境：{context.target_environment}")

    return "\n".join(parts)


def _extract_code(content: str) -> str:
    """Extract code from response.

    Args:
        content: Response content

    Returns:
        Extracted code
    """
    import re

    # Try to find code block
    pattern = r"```(?:python)?\s*\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    # If no code block, return content as-is
    return content.strip()


def _format_output(
    result: dict[str, Any],
    format: OutputFormat,
    output_type: str,
) -> str:
    """Format output based on type.

    Args:
        result: Result dict
        format: Output format
        output_type: Type of output (code/review/diagnose/fix)

    Returns:
        Formatted output
    """
    if format == OutputFormat.JSON:
        return json.dumps(result, ensure_ascii=False, indent=2)

    if output_type == "code":
        return format_code_result(result, format)
    elif output_type == "review":
        return format_review_result(result, format)
    else:
        # Generic text output
        lines = []

        if result.get("success"):
            lines.append("✅ Operation completed successfully")
        else:
            lines.append(f"❌ Error: {result.get('error', 'Unknown error')}")

        for key, value in result.items():
            if key not in ("success", "error"):
                if isinstance(value, str) and len(value) > 200:
                    lines.append(f"\n{key}:\n{value}")
                elif isinstance(value, list):
                    lines.append(f"\n{key}:")
                    for item in value[:5]:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")

        return "\n".join(lines)