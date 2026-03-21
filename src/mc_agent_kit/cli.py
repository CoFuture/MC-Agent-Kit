#!/usr/bin/env python3
"""
MC-Agent-Kit CLI

命令行工具，用于调用 ModSDK Skills。
"""

import argparse
import json
import sys
from typing import Any

from mc_agent_kit.skills import (
    get_registry,
    register_modsdk_skills,
)


def setup_skills() -> None:
    """注册所有 Skills"""
    register_modsdk_skills()


def print_result(result: dict[str, Any], format: str = "text") -> None:
    """打印结果

    Args:
        result: 结果字典
        format: 输出格式 (text/json)
    """
    if format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("success"):
            print(f"✅ {result.get('message', '成功')}")
            if result.get("data"):
                data = result["data"]
                if isinstance(data, list):
                    for i, item in enumerate(data, 1):
                        print(f"\n--- [{i}] ---")
                        if isinstance(item, dict):
                            for key, value in item.items():
                                if key == "code":
                                    print(f"{key}:")
                                    print(value)
                                elif isinstance(value, list) and len(value) > 5:
                                    print(f"{key}: [{len(value)} items]")
                                else:
                                    print(f"{key}: {value}")
                        else:
                            print(item)
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if key == "code":
                            print(f"\n{key}:")
                            print(value)
                        elif key == "errors":
                            print(f"\n{key}:")
                            for error in value:
                                print(f"  - {error.get('error_type')}: {error.get('message')}")
                                if error.get("suggestions"):
                                    for s in error["suggestions"][:3]:
                                        print(f"    💡 {s}")
                        elif isinstance(value, list) and len(value) > 10:
                            print(f"{key}: [{len(value)} items]")
                        else:
                            print(f"{key}: {value}")
        else:
            print(f"❌ {result.get('message', '失败')}")
            if result.get("error"):
                print(f"错误: {result['error']}")
            if result.get("suggestions"):
                print("建议:")
                for s in result["suggestions"]:
                    print(f"  • {s}")


def cmd_list(args: argparse.Namespace) -> int:
    """列出 Skills"""
    setup_skills()
    registry = get_registry()

    skills = registry.list_all()

    if args.format == "json":
        data = [s.to_dict() for s in skills]
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("已注册的 Skills:\n")
        for skill in skills:
            print(f"  📦 {skill.name}")
            print(f"     描述: {skill.description}")
            print(f"     分类: {skill.category.value}")
            print(f"     优先级: {skill.priority.name}")
            print()

    return 0


def cmd_api(args: argparse.Namespace) -> int:
    """API 搜索"""
    setup_skills()
    registry = get_registry()
    skill = registry.get("modsdk-api-search")

    if not skill:
        print("错误: API 搜索 Skill 未注册")
        return 1

    skill.initialize()

    result = skill.execute(
        query=args.query,
        name=args.name,
        module=args.module,
        scope=args.scope,
        limit=args.limit,
    )

    print_result(result.to_dict(), args.format)
    return 0 if result.success else 1


def cmd_event(args: argparse.Namespace) -> int:
    """事件搜索"""
    setup_skills()
    registry = get_registry()
    skill = registry.get("modsdk-event-search")

    if not skill:
        print("错误: 事件搜索 Skill 未注册")
        return 1

    skill.initialize()

    result = skill.execute(
        query=args.query,
        name=args.name,
        module=args.module,
        scope=args.scope,
        limit=args.limit,
    )

    print_result(result.to_dict(), args.format)
    return 0 if result.success else 1


def cmd_gen(args: argparse.Namespace) -> int:
    """代码生成"""
    setup_skills()
    registry = get_registry()
    skill = registry.get("modsdk-code-gen")

    if not skill:
        print("错误: 代码生成 Skill 未注册")
        return 1

    skill.initialize()

    # 解析参数
    params = {}
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError:
            print("错误: params 参数必须是有效的 JSON")
            return 1

    result = skill.execute(
        template=args.template,
        params=params,
        action=args.action,
        keyword=args.keyword,
    )

    print_result(result.to_dict(), args.format)
    return 0 if result.success else 1


def cmd_debug(args: argparse.Namespace) -> int:
    """调试辅助"""
    setup_skills()
    registry = get_registry()
    skill = registry.get("modsdk-debug")

    if not skill:
        print("错误: 调试辅助 Skill 未注册")
        return 1

    skill.initialize()

    # 读取日志内容
    log_content = args.log
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                log_content = f.read()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {args.file}")
            return 1

    if not log_content:
        print("错误: 请提供日志内容 (-l) 或日志文件 (-f)")
        return 1

    result = skill.execute(
        log_content=log_content,
        action=args.action,
    )

    print_result(result.to_dict(), args.format)
    return 0 if result.success else 1


def main() -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="mc-agent",
        description="MC-Agent-Kit CLI - ModSDK 开发辅助工具",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list 命令
    subparsers.add_parser("list", help="列出所有 Skills")

    # api 命令
    api_parser = subparsers.add_parser("api", help="搜索 ModSDK API")
    api_parser.add_argument("-q", "--query", help="搜索关键词")
    api_parser.add_argument("-n", "--name", help="精确匹配 API 名称")
    api_parser.add_argument("-m", "--module", help="按模块过滤")
    api_parser.add_argument("-s", "--scope", choices=["client", "server"], help="按作用域过滤")
    api_parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")

    # event 命令
    event_parser = subparsers.add_parser("event", help="搜索 ModSDK 事件")
    event_parser.add_argument("-q", "--query", help="搜索关键词")
    event_parser.add_argument("-n", "--name", help="精确匹配事件名称")
    event_parser.add_argument("-m", "--module", help="按模块过滤")
    event_parser.add_argument("-s", "--scope", choices=["client", "server"], help="按作用域过滤")
    event_parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")

    # gen 命令
    gen_parser = subparsers.add_parser("gen", help="生成 ModSDK 代码")
    gen_parser.add_argument("-t", "--template", help="模板名称")
    gen_parser.add_argument("-p", "--params", help="模板参数 (JSON 格式)")
    gen_parser.add_argument("-a", "--action", default="generate", help="操作类型")
    gen_parser.add_argument("-k", "--keyword", help="搜索关键词")

    # debug 命令
    debug_parser = subparsers.add_parser("debug", help="调试 ModSDK 错误")
    debug_parser.add_argument("-l", "--log", help="日志内容")
    debug_parser.add_argument("-f", "--file", help="日志文件路径")
    debug_parser.add_argument("-a", "--action", default="diagnose", help="操作类型")

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args)
    elif args.command == "api":
        return cmd_api(args)
    elif args.command == "event":
        return cmd_event(args)
    elif args.command == "gen":
        return cmd_gen(args)
    elif args.command == "debug":
        return cmd_debug(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
