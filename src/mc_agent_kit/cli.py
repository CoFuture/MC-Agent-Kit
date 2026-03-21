#!/usr/bin/env python3
"""
MC-Agent-Kit CLI

命令行工具，用于调用 ModSDK Skills 和自动修复功能。
"""

import argparse
import json
import sys
from typing import Any

from mc_agent_kit.autofix import (
    AutoFixer,
    ErrorDiagnoser,
)
from mc_agent_kit.completion import (
    BestPracticeChecker,
    CodeCompleter,
    RefactorEngine,
    SmellDetector,
)
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


def cmd_complete(args: argparse.Namespace) -> int:
    """代码补全"""
    completer = CodeCompleter()

    # 读取代码
    code = args.code
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {args.file}")
            return 1

    if not code:
        print("错误: 请提供代码内容 (-c) 或代码文件 (-f)")
        return 1

    result = completer.complete(
        code=code,
        cursor_line=args.line,
        cursor_column=args.column,
        prefix=args.prefix,
    )

    if args.format == "json":
        data = {
            "items": [
                {
                    "text": item.text,
                    "kind": item.kind.value,
                    "detail": item.detail,
                    "documentation": item.documentation,
                }
                for item in result.items
            ]
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if result.items:
            print(f"补全建议 ({len(result.items)} 个):\n")
            for item in result.items:
                print(f"  📝 {item.text}")
                print(f"     类型: {item.kind.value}")
                if item.detail:
                    print(f"     详情: {item.detail}")
                print()
        else:
            print("没有找到补全建议")

    return 0


def cmd_refactor(args: argparse.Namespace) -> int:
    """代码重构"""
    detector = SmellDetector()
    engine = RefactorEngine()

    # 读取代码
    code = args.code
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {args.file}")
            return 1

    if not code:
        print("错误: 请提供代码内容 (-c) 或代码文件 (-f)")
        return 1

    if args.action == "detect":
        # 检测代码异味
        smells = detector.detect(code)

        if args.format == "json":
            data = {
                "smells": [
                    {
                        "type": smell.smell_type.value,
                        "severity": smell.severity.value,
                        "message": smell.message,
                        "line": smell.line,
                    }
                    for smell in smells
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if smells:
                print(f"检测到 {len(smells)} 个代码异味:\n")
                for smell in smells:
                    print(f"  ⚠️ {smell.smell_type.value}: {smell.message}")
                    print(f"     严重程度: {smell.severity.value}")
                    if smell.line:
                        print(f"     位置: 第 {smell.line} 行")
                    print()
            else:
                print("✅ 未检测到代码异味")

    elif args.action == "suggest":
        # 生成重构建议
        smells = detector.detect(code)
        suggestions = engine.suggest(code, smells)

        if args.format == "json":
            data = {
                "suggestions": [
                    {
                        "type": sug.refactor_type.value,
                        "description": sug.description,
                        "line": sug.line,
                        "auto_fixable": sug.auto_fixable,
                    }
                    for sug in suggestions
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if suggestions:
                print(f"生成 {len(suggestions)} 个重构建议:\n")
                for sug in suggestions:
                    print(f"  💡 {sug.refactor_type.value}: {sug.description}")
                    if sug.line:
                        print(f"     位置: 第 {sug.line} 行")
                    print(f"     可自动修复: {'是' if sug.auto_fixable else '否'}")
                    print()
            else:
                print("✅ 无需重构")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """最佳实践检查"""
    checker = BestPracticeChecker()

    # 读取代码
    code = args.code
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {args.file}")
            return 1

    if not code:
        print("错误: 请提供代码内容 (-c) 或代码文件 (-f)")
        return 1

    if args.action == "check":
        # 检查最佳实践
        results = checker.check(code)

        if args.format == "json":
            data = {
                "results": [
                    {
                        "practice_id": r.practice.id,
                        "practice_name": r.practice.name,
                        "passed": r.passed,
                        "message": r.message,
                        "line": r.line,
                    }
                    for r in results
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            passed = [r for r in results if r.passed]
            failed = [r for r in results if not r.passed]

            print("最佳实践检查结果:\n")
            print(f"  ✅ 通过: {len(passed)}")
            print(f"  ❌ 未通过: {len(failed)}")

            if failed:
                print("\n未通过的项目:\n")
                for r in failed:
                    print(f"  ❌ {r.practice.name}")
                    print(f"     消息: {r.message}")
                    if r.line:
                        print(f"     位置: 第 {r.line} 行")
                    print()

    elif args.action == "list":
        # 列出所有最佳实践
        practices = checker.list_practices()

        if args.format == "json":
            data = {
                "practices": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "category": p.category.value,
                        "description": p.description,
                    }
                    for p in practices
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"最佳实践列表 ({len(practices)} 条):\n")
            for p in practices:
                print(f"  📋 {p.id}: {p.name}")
                print(f"     分类: {p.category.value}")
                print(f"     描述: {p.description}")
                print()

    return 0


def cmd_autofix(args: argparse.Namespace) -> int:
    """自动修复错误"""
    fixer = AutoFixer()
    diagnoser = ErrorDiagnoser()

    # 读取代码
    code = args.code
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            print(f"错误: 文件不存在: {args.file}")
            return 1

    if not code:
        print("错误: 请提供代码内容 (-c) 或代码文件 (-f)")
        return 1

    # 读取错误日志
    error_log = args.error
    if args.error_file:
        try:
            with open(args.error_file, encoding="utf-8") as f:
                error_log = f.read()
        except FileNotFoundError:
            print(f"错误: 错误日志文件不存在: {args.error_file}")
            return 1

    if args.action == "diagnose":
        # 诊断错误
        diagnosis = diagnoser.diagnose(error_log)

        if args.format == "json":
            data = {
                "error_type": diagnosis.error_info.error_type.value,
                "message": diagnosis.error_info.message,
                "suggestions": [
                    {
                        "description": s.description,
                        "confidence": s.confidence.value,
                        "auto_fixable": s.auto_fixable,
                    }
                    for s in diagnosis.suggestions
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("错误诊断结果:\n")
            print(f"  类型: {diagnosis.error_info.error_type.value}")
            print(f"  消息: {diagnosis.error_info.message}")
            print("\n修复建议:\n")
            for s in diagnosis.suggestions:
                print(f"  💡 {s.description}")
                print(f"     信心: {s.confidence.value}")
                print(f"     可自动修复: {'是' if s.auto_fixable else '否'}")
                print()

    elif args.action == "fix":
        # 自动修复
        result = fixer.fix_from_error_log(code, error_log)

        if args.format == "json":
            data = {
                "status": result.status.value,
                "message": result.message,
                "fixed_code": result.fixed_code,
                "replacements": [
                    {
                        "start_line": r.start_line,
                        "end_line": r.end_line,
                        "original": r.original,
                        "replacement": r.replacement,
                    }
                    for r in result.replacements
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("自动修复结果:\n")
            print(f"  状态: {result.status.value}")
            print(f"  消息: {result.message}")

            if result.replacements:
                print(f"\n应用的修复 ({len(result.replacements)} 个):\n")
                for r in result.replacements:
                    print(f"  第 {r.start_line} 行:")
                    print(f"    - {r.original}")
                    print(f"    + {r.replacement}")
                    print()

            if result.fixed_code != code:
                print("\n修复后代码:\n")
                print(result.fixed_code)

    elif args.action == "preview":
        # 预览修复
        diagnosis = diagnoser.diagnose(error_log)
        diff = fixer.preview_fix(code, diagnosis)

        if args.format == "json":
            data = {"diff": diff}
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("修复预览 (diff):\n")
            print(diff)

    return 0


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

    # complete 命令
    complete_parser = subparsers.add_parser("complete", help="代码补全")
    complete_parser.add_argument("-c", "--code", help="代码内容")
    complete_parser.add_argument("-f", "--file", help="代码文件路径")
    complete_parser.add_argument("-l", "--line", type=int, default=1, help="光标行号")
    complete_parser.add_argument("-C", "--column", type=int, default=0, help="光标列号")
    complete_parser.add_argument("-p", "--prefix", help="补全前缀")

    # refactor 命令
    refactor_parser = subparsers.add_parser("refactor", help="代码重构")
    refactor_parser.add_argument("-c", "--code", help="代码内容")
    refactor_parser.add_argument("-f", "--file", help="代码文件路径")
    refactor_parser.add_argument("-a", "--action", choices=["detect", "suggest"], default="detect", help="操作类型")

    # check 命令
    check_parser = subparsers.add_parser("check", help="最佳实践检查")
    check_parser.add_argument("-c", "--code", help="代码内容")
    check_parser.add_argument("-f", "--file", help="代码文件路径")
    check_parser.add_argument("-a", "--action", choices=["check", "list"], default="check", help="操作类型")

    # autofix 命令
    autofix_parser = subparsers.add_parser("autofix", help="自动修复错误")
    autofix_parser.add_argument("-c", "--code", help="代码内容")
    autofix_parser.add_argument("-f", "--file", help="代码文件路径")
    autofix_parser.add_argument("-e", "--error", help="错误日志内容")
    autofix_parser.add_argument("-E", "--error-file", help="错误日志文件路径")
    autofix_parser.add_argument("-a", "--action", choices=["diagnose", "fix", "preview"], default="diagnose", help="操作类型")

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
    elif args.command == "complete":
        return cmd_complete(args)
    elif args.command == "refactor":
        return cmd_refactor(args)
    elif args.command == "check":
        return cmd_check(args)
    elif args.command == "autofix":
        return cmd_autofix(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
