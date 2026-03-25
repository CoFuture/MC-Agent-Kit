"""
增强知识库 CLI 模块

提供改进的知识库命令行接口。
迭代 #71: 知识库增强与检索优化
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mc_agent_kit.knowledge.enhanced_retriever import (
    DifficultyLevel,
    EntryScope,
    EntryType,
    ExampleCategory,
    SearchFilter,
    get_retriever,
)
from mc_agent_kit.knowledge.example_library import get_example_library


def print_table(headers: list[str], rows: list[list[str]], widths: list[int] | None = None) -> None:
    """打印表格"""
    if not rows:
        print("无数据")
        return

    if widths is None:
        widths = [max(len(str(row[i])) if i < len(row) else 0 for row in [headers] + rows) for i in range(len(headers))]

    # 打印表头
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_row)
    print("-" * len(header_row))

    # 打印数据行
    for row in rows:
        print(" | ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def cmd_kb_search(args: argparse.Namespace) -> int:
    """知识库搜索"""
    retriever = get_retriever(
        index_path=args.index_path,
        example_library_path=args.example_path,
    )

    # 构建过滤器
    filters = None
    if args.type or args.module or args.scope:
        filters = SearchFilter(
            entry_type=EntryType(args.type) if args.type else None,
            module=args.module,
            scope=EntryScope(args.scope) if args.scope else None,
        )

    # 执行搜索
    report = retriever.search(args.query, filters=filters, limit=args.limit)

    if args.format == "json":
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"\n搜索: {args.query}")
        print(f"结果: {report.total_results} 条, 耗时: {report.duration_ms:.2f}ms\n")

        if report.results:
            for i, result in enumerate(report.results, 1):
                entry = result.entry
                type_icon = {
                    EntryType.API: "📦",
                    EntryType.EVENT: "⚡",
                    EntryType.EXAMPLE: "📝",
                    EntryType.GUIDE: "📖",
                }.get(entry.type, "📄")

                print(f"{i}. {type_icon} {entry.name}")
                print(f"   类型: {entry.type.value}")
                if entry.module:
                    print(f"   模块: {entry.module}")
                if entry.scope != EntryScope.UNKNOWN:
                    print(f"   作用域: {entry.scope.value}")
                print(f"   分数: {result.score:.1f}")
                print(f"   描述: {entry.description[:100]}{'...' if len(entry.description) > 100 else ''}")
                if result.matched_keywords:
                    print(f"   匹配: {', '.join(result.matched_keywords[:5])}")
                print()

            if report.suggestions:
                print("💡 建议:")
                for s in report.suggestions:
                    print(f"   - {s}")
        else:
            print("未找到相关结果")
            if report.suggestions:
                print("\n💡 建议:")
                for s in report.suggestions:
                    print(f"   - {s}")

    return 0


def cmd_kb_api(args: argparse.Namespace) -> int:
    """获取 API 详情"""
    retriever = get_retriever(
        index_path=args.index_path,
        example_library_path=args.example_path,
    )

    entry = retriever.get_api(args.name)

    if args.format == "json":
        if entry:
            print(json.dumps(entry.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": f"API '{args.name}' 未找到"}, ensure_ascii=False))
        return 0 if entry else 1

    if entry:
        print(f"\n📦 API: {entry.name}\n")
        print(f"模块: {entry.module or '未知'}")
        print(f"作用域: {entry.scope.value}")
        print(f"\n描述:")
        print(f"  {entry.description}")

        if entry.parameters:
            print(f"\n参数 ({len(entry.parameters)} 个):")
            for param in entry.parameters:
                required = "必需" if param.required else "可选"
                default = f" = {param.default}" if param.default else ""
                print(f"  - {param.name}: {param.type} [{required}]{default}")
                if param.description:
                    print(f"      {param.description}")

        if entry.return_type:
            print(f"\n返回值:")
            print(f"  类型: {entry.return_type}")
            if entry.return_description:
                print(f"  说明: {entry.return_description}")

        if entry.code_blocks:
            print(f"\n代码示例:")
            for i, block in enumerate(entry.code_blocks, 1):
                print(f"\n  示例 {i} ({block.language}):")
                for line in block.code.split("\n")[:10]:
                    print(f"    {line}")
                if len(block.code.split("\n")) > 10:
                    print(f"    ... (共 {len(block.code.split(chr(10)))} 行)")

        # 相关示例
        examples = retriever.get_examples_by_api(args.name)
        if examples:
            print(f"\n相关示例 ({len(examples)} 个):")
            for ex in examples[:3]:
                print(f"  - {ex.name}: {ex.metadata.title}")

        return 0
    else:
        print(f"❌ API '{args.name}' 未找到")
        return 1


def cmd_kb_event(args: argparse.Namespace) -> int:
    """获取事件详情"""
    retriever = get_retriever(
        index_path=args.index_path,
        example_library_path=args.example_path,
    )

    entry = retriever.get_event(args.name)

    if args.format == "json":
        if entry:
            print(json.dumps(entry.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": f"事件 '{args.name}' 未找到"}, ensure_ascii=False))
        return 0 if entry else 1

    if entry:
        print(f"\n⚡ 事件: {entry.name}\n")
        print(f"模块: {entry.module or '未知'}")
        print(f"作用域: {entry.scope.value}")
        print(f"\n描述:")
        print(f"  {entry.description}")

        if entry.parameters:
            print(f"\n参数 ({len(entry.parameters)} 个):")
            for param in entry.parameters:
                print(f"  - {param.name}: {param.type}")
                if param.description:
                    print(f"      {param.description}")

        if entry.code_blocks:
            print(f"\n使用示例:")
            for i, block in enumerate(entry.code_blocks, 1):
                print(f"\n  示例 {i}:")
                for line in block.code.split("\n")[:10]:
                    print(f"    {line}")

        # 相关示例
        examples = retriever.get_examples_by_event(args.name)
        if examples:
            print(f"\n相关示例 ({len(examples)} 个):")
            for ex in examples[:3]:
                print(f"  - {ex.name}: {ex.metadata.title}")

        return 0
    else:
        print(f"❌ 事件 '{args.name}' 未找到")
        return 1


def cmd_kb_example(args: argparse.Namespace) -> int:
    """获取示例详情"""
    retriever = get_retriever(
        index_path=args.index_path,
        example_library_path=args.example_path,
    )

    example = retriever.get_example(args.name)

    if args.format == "json":
        if example:
            print(json.dumps(example.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": f"示例 '{args.name}' 未找到"}, ensure_ascii=False))
        return 0 if example else 1

    if example:
        meta = example.metadata
        print(f"\n📝 示例: {meta.name}\n")
        print(f"标题: {meta.title}")
        print(f"分类: {meta.category.value}")
        print(f"难度: {meta.difficulty.value}")
        print(f"\n描述:")
        print(f"  {meta.description}")

        if meta.prerequisites:
            print(f"\n前置要求:")
            for pre in meta.prerequisites:
                print(f"  - {pre}")

        print(f"\n代码:")
        for i, block in enumerate(example.code_blocks, 1):
            if len(example.code_blocks) > 1:
                print(f"\n--- 代码块 {i} ({block.language}) ---")
            for line in block.code.split("\n"):
                print(f"  {line}")

        if example.explanation:
            print(f"\n说明:")
            print(f"  {example.explanation}")

        if example.tips:
            print(f"\n💡 提示:")
            for tip in example.tips:
                print(f"  - {tip}")

        if example.warnings:
            print(f"\n⚠️ 警告:")
            for warn in example.warnings:
                print(f"  - {warn}")

        if meta.apis_used:
            print(f"\n使用的 API:")
            for api in meta.apis_used:
                print(f"  - {api}")

        if meta.events_used:
            print(f"\n使用的事件:")
            for event in meta.events_used:
                print(f"  - {event}")

        return 0
    else:
        print(f"❌ 示例 '{args.name}' 未找到")
        return 1


def cmd_kb_list(args: argparse.Namespace) -> int:
    """列出知识库内容"""
    retriever = get_retriever(
        index_path=args.index_path,
        example_library_path=args.example_path,
    )

    if args.type == "apis":
        entries = retriever.list_apis(module=args.module, limit=args.limit)
        if args.format == "json":
            print(json.dumps([e.to_dict() for e in entries], ensure_ascii=False, indent=2))
        else:
            print(f"\nAPI 列表 ({len(entries)} 个):\n")
            headers = ["名称", "模块", "作用域", "描述"]
            rows = [[e.name, e.module or "-", e.scope.value, e.description[:50]] for e in entries]
            print_table(headers, rows, [25, 15, 10, 50])

    elif args.type == "events":
        entries = retriever.list_events(module=args.module, limit=args.limit)
        if args.format == "json":
            print(json.dumps([e.to_dict() for e in entries], ensure_ascii=False, indent=2))
        else:
            print(f"\n事件列表 ({len(entries)} 个):\n")
            headers = ["名称", "模块", "作用域", "描述"]
            rows = [[e.name, e.module or "-", e.scope.value, e.description[:50]] for e in entries]
            print_table(headers, rows, [30, 15, 10, 50])

    elif args.type == "examples":
        category = ExampleCategory(args.category) if args.category else None
        difficulty = DifficultyLevel(args.difficulty) if args.difficulty else None
        examples = retriever.list_examples(category=category, difficulty=difficulty, limit=args.limit)
        if args.format == "json":
            print(json.dumps([e.to_dict() for e in examples], ensure_ascii=False, indent=2))
        else:
            print(f"\n示例列表 ({len(examples)} 个):\n")
            headers = ["名称", "标题", "分类", "难度"]
            rows = [[e.name, e.metadata.title, e.metadata.category.value, e.metadata.difficulty.value] for e in examples]
            print_table(headers, rows, [25, 35, 15, 12])

    elif args.type == "modules":
        stats = retriever.get_stats()
        by_module = stats.get("by_module", {})
        if args.format == "json":
            print(json.dumps(by_module, ensure_ascii=False, indent=2))
        else:
            print(f"\n模块列表 ({len(by_module)} 个):\n")
            headers = ["模块", "条目数"]
            rows = [[m, str(c)] for m, c in sorted(by_module.items(), key=lambda x: -x[1])]
            print_table(headers, rows, [30, 10])

    return 0


def cmd_kb_status(args: argparse.Namespace) -> int:
    """知识库状态"""
    retriever = get_retriever(
        index_path=args.index_path,
        example_library_path=args.example_path,
    )

    stats = retriever.get_stats()

    if args.format == "json":
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print("\n📊 知识库状态\n")
        print("=" * 50)
        print(f"总条目数: {stats.get('total_entries', 0)}")
        print()

        by_type = stats.get("by_type", {})
        if by_type:
            print("按类型统计:")
            for type_name, count in sorted(by_type.items(), key=lambda x: -x[1]):
                icon = {"api": "📦", "event": "⚡", "example": "📝", "guide": "📖"}.get(type_name, "📄")
                print(f"  {icon} {type_name}: {count}")
            print()

        by_module = stats.get("by_module", {})
        if by_module:
            print("按模块统计:")
            for module, count in sorted(by_module.items(), key=lambda x: -x[1])[:10]:
                print(f"  - {module}: {count}")
            print()

        example_stats = stats.get("example_library", {})
        if example_stats:
            print("示例库统计:")
            print(f"  总示例数: {example_stats.get('total_examples', 0)}")
            print(f"  索引 API 数: {example_stats.get('total_apis_indexed', 0)}")
            print(f"  索引事件数: {example_stats.get('total_events_indexed', 0)}")

        print("=" * 50)

    return 0


def cmd_kb_categories(args: argparse.Namespace) -> int:
    """列出分类"""
    library = get_example_library()
    library.load()

    categories = library.get_categories()

    if args.format == "json":
        print(json.dumps([c.value for c in categories], ensure_ascii=False, indent=2))
    else:
        print("\n示例分类:\n")
        for cat in categories:
            examples = library.list_examples(category=cat, limit=100)
            count = len(examples)
            print(f"  - {cat.value}: {count} 个示例")

    return 0


def create_kb_parser() -> argparse.ArgumentParser:
    """创建知识库命令解析器"""
    parser = argparse.ArgumentParser(
        prog="mc-kb",
        description="MC-Agent-Kit 知识库管理工具",
    )

    parser.add_argument(
        "--index-path",
        help="索引文件路径",
    )
    parser.add_argument(
        "--example-path",
        help="示例库路径",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索知识库")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("--type", choices=["api", "event", "example", "guide"], help="条目类型过滤")
    search_parser.add_argument("--module", help="模块过滤")
    search_parser.add_argument("--scope", choices=["client", "server", "both"], help="作用域过滤")
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="结果数量限制")

    # api 命令
    api_parser = subparsers.add_parser("api", help="获取 API 详情")
    api_parser.add_argument("name", help="API 名称")

    # event 命令
    event_parser = subparsers.add_parser("event", help="获取事件详情")
    event_parser.add_argument("name", help="事件名称")

    # example 命令
    example_parser = subparsers.add_parser("example", help="获取示例详情")
    example_parser.add_argument("name", help="示例名称")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出知识库内容")
    list_parser.add_argument("type", choices=["apis", "events", "examples", "modules"], help="列出类型")
    list_parser.add_argument("--module", help="模块过滤")
    list_parser.add_argument("--category", help="示例分类过滤")
    list_parser.add_argument("--difficulty", help="示例难度过滤")
    list_parser.add_argument("--limit", "-l", type=int, default=50, help="结果数量限制")

    # status 命令
    status_parser = subparsers.add_parser("status", help="知识库状态")

    # categories 命令
    categories_parser = subparsers.add_parser("categories", help="列出示例分类")

    return parser


def kb_main() -> int:
    """知识库命令主入口"""
    parser = create_kb_parser()
    args = parser.parse_args()

    if args.command == "search":
        return cmd_kb_search(args)
    elif args.command == "api":
        return cmd_kb_api(args)
    elif args.command == "event":
        return cmd_kb_event(args)
    elif args.command == "example":
        return cmd_kb_example(args)
    elif args.command == "list":
        return cmd_kb_list(args)
    elif args.command == "status":
        return cmd_kb_status(args)
    elif args.command == "categories":
        return cmd_kb_categories(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(kb_main())