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
from mc_agent_kit.scaffold import ProjectCreator
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
                print(f"错误：{result['error']}")
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
            print(f"     描述：{skill.description}")
            print(f"     分类：{skill.category.value}")
            print(f"     优先级：{skill.priority.name}")
            print()

    return 0


def cmd_api(args: argparse.Namespace) -> int:
    """API 搜索"""
    setup_skills()
    registry = get_registry()
    skill = registry.get("modsdk-api-search")

    if not skill:
        print("错误：API 搜索 Skill 未注册")
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
        print("错误：事件搜索 Skill 未注册")
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
        print("错误：代码生成 Skill 未注册")
        return 1

    skill.initialize()

    # 解析参数
    params = {}
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError:
            print("错误：params 参数必须是有效的 JSON")
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
        print("错误：调试辅助 Skill 未注册")
        return 1

    skill.initialize()

    # list_errors 不需要日志内容
    if args.action == "list_errors":
        result = skill.execute(action="list_errors")
        print_result(result.to_dict(), args.format)
        return 0 if result.success else 1

    # 读取日志内容
    log_content = args.log
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                log_content = f.read()
        except FileNotFoundError:
            print(f"错误：文件不存在：{args.file}")
            return 1

    if not log_content:
        print("错误：请提供日志内容 (-l) 或日志文件 (--file)")
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
            print(f"错误：文件不存在：{args.file}")
            return 1

    if not code:
        print("错误：请提供代码内容 (-c) 或代码文件 (--file)")
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
                    "text": item.label,
                    "kind": item.kind.value,
                    "detail": item.detail,
                    "documentation": item.documentation,
                }
                for item in result.completions
            ]
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if result.completions:
            print(f"补全建议 ({len(result.completions)} 个):\n")
            for item in result.completions:
                print(f"  📝 {item.label}")
                print(f"     类型：{item.kind.value}")
                if item.detail:
                    print(f"     详情：{item.detail}")
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
            print(f"错误：文件不存在：{args.file}")
            return 1

    if not code:
        print("错误：请提供代码内容 (-c) 或代码文件 (--file)")
        return 1

    if args.action == "detect":
        # 检测代码异味
        smells = detector.detect(code)

        if args.format == "json":
            data = {
                "smells": [
                    {
                        "type": smell.type.value,
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
                    print(f"  ⚠️ {smell.type.value}: {smell.message}")
                    print(f"     严重程度：{smell.severity.value}")
                    if smell.line:
                        print(f"     位置：第 {smell.line} 行")
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
                        "type": sug.type.value,
                        "description": sug.message,
                        "line": sug.line,
                        "auto_fixable": sug.auto_applicable,
                    }
                    for sug in suggestions
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if suggestions:
                print(f"生成 {len(suggestions)} 个重构建议:\n")
                for sug in suggestions:
                    print(f"  💡 {sug.type.value}: {sug.message}")
                    if sug.line:
                        print(f"     位置：第 {sug.line} 行")
                    print(f"     可自动修复：{'是' if sug.auto_applicable else '否'}")
                    print()
            else:
                print("✅ 无需重构")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """最佳实践检查"""
    checker = BestPracticeChecker()

    # list 操作不需要代码
    if args.action == "list":
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
                print(f"     分类：{p.category.value}")
                print(f"     描述：{p.description}")
                print()

        return 0

    # check 操作需要代码
    code = args.code
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                code = f.read()
        except FileNotFoundError:
            print(f"错误：文件不存在：{args.file}")
            return 1

    if not code:
        print("错误：请提供代码内容 (-c) 或代码文件 (--file)")
        return 1

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
        print(f"  ✅ 通过：{len(passed)}")
        print(f"  ❌ 未通过：{len(failed)}")

        if failed:
            print("\n未通过的项目:\n")
            for r in failed:
                print(f"  ❌ {r.practice.name}")
                print(f"     消息：{r.message}")
                if r.line:
                    print(f"     位置：第 {r.line} 行")
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
            print(f"错误：文件不存在：{args.file}")
            return 1

    if not code:
        print("错误：请提供代码内容 (-c) 或代码文件 (--file)")
        return 1

    # 读取错误日志
    error_log = args.error
    if args.error_file:
        try:
            with open(args.error_file, encoding="utf-8") as f:
                error_log = f.read()
        except FileNotFoundError:
            print(f"错误：错误日志文件不存在：{args.error_file}")
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
            print(f"  类型：{diagnosis.error_info.error_type.value}")
            print(f"  消息：{diagnosis.error_info.message}")
            print("\n修复建议:\n")
            for s in diagnosis.suggestions:
                print(f"  💡 {s.description}")
                print(f"     信心：{s.confidence.value}")
                print(f"     可自动修复：{'是' if s.auto_fixable else '否'}")
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
            print(f"  状态：{result.status.value}")
            print(f"  消息：{result.message}")

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


def cmd_create(args: argparse.Namespace) -> int:
    """项目创建"""
    creator = ProjectCreator()

    if args.type == "project":
        # 创建项目
        try:
            project = creator.create_project(
                name=args.name,
                path=args.path or ".",
                template=args.template or "empty",
                force=args.force,
            )

            if args.format == "json":
                data = {
                    "success": True,
                    "message": f"项目 '{args.name}' 创建成功",
                    "project": {
                        "name": project.name,
                        "path": str(project.path),
                        "behavior_pack_path": str(project.behavior_pack_path),
                        "resource_pack_path": str(project.resource_pack_path),
                    }
                }
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"✅ 项目 '{args.name}' 创建成功!")
                print(f"\n目录结构:")
                print(f"  📁 {project.path}")
                print(f"    📁 behavior_pack/")
                print(f"      📄 manifest.json")
                print(f"      📁 scripts/")
                print(f"    📁 resource_pack/")
                print(f"      📄 manifest.json")
                print(f"      📁 textures/")

        except FileExistsError as e:
            if args.format == "json":
                print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            else:
                print(f"❌ 错误: {e}")
                print("提示: 使用 --force 覆盖已存在的项目")
            return 1

    elif args.type == "entity":
        # 添加实体
        created_files = creator.add_entity(
            name=args.name,
            project=args.path or ".",
        )

        if args.format == "json":
            data = {
                "success": True,
                "message": f"实体 '{args.name}' 添加成功",
                "files": [str(f) for f in created_files]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 实体 '{args.name}' 添加成功!")
            print(f"\n创建的文件:")
            for f in created_files:
                print(f"  📄 {f}")

    elif args.type == "item":
        # 添加物品
        try:
            creator.add_item(name=args.name, project=args.path or ".")
        except NotImplementedError as e:
            if args.format == "json":
                print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            else:
                print(f"❌ 功能未实现: {e}")
            return 1

    elif args.type == "block":
        # 添加方块
        try:
            creator.add_block(name=args.name, project=args.path or ".")
        except NotImplementedError as e:
            if args.format == "json":
                print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            else:
                print(f"❌ 功能未实现: {e}")
            return 1

    return 0


def cmd_kb(args: argparse.Namespace) -> int:
    """知识库管理"""
    from mc_agent_kit.knowledge_base import KnowledgeBase, KnowledgeRetriever

    if args.action == "status":
        # 查看状态
        if args.format == "json":
            data = {
                "status": "ready",
                "docs_path": "resources/docs/mcdocs",
                "index_path": "data/knowledge_base.json"
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("知识库状态:")
            print("  状态: ✅ 就绪")
            print("  文档路径: resources/docs/mcdocs")
            print("  索引路径: data/knowledge_base.json")

    elif args.action == "search":
        # 搜索
        retriever = KnowledgeRetriever()
        retriever.load("data/knowledge_base.json")

        results = retriever.search(
            query=args.query,
            limit=args.limit or 5,
        )

        if args.format == "json":
            data = {
                "success": True,
                "query": args.query,
                "results": [
                    {
                        "name": r.name,
                        "type": type(r).__name__,
                        "module": r.module,
                        "description": r.description[:100] + "..." if len(r.description) > 100 else r.description,
                    }
                    for r in results
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"搜索结果: '{args.query}'\n")
            if results:
                for i, r in enumerate(results, 1):
                    print(f"[{i}] {r.name} ({type(r).__name__})")
                    print(f"    模块: {r.module}")
                    desc = r.description[:100] + "..." if len(r.description) > 100 else r.description
                    print(f"    描述: {desc}")
                    print()
            else:
                print("未找到相关结果")

    elif args.action == "api":
        # 精确查 API
        retriever = KnowledgeRetriever()
        retriever.load("data/knowledge_base.json")

        api = retriever.get_api(args.name)

        if args.format == "json":
            if api:
                data = {
                    "success": True,
                    "api": {
                        "name": api.name,
                        "module": api.module,
                        "description": api.description,
                        "scope": api.scope.value if api.scope else "unknown",
                        "parameters": [
                            {"name": p.name, "type": p.data_type, "description": p.description}
                            for p in api.parameters
                        ],
                    }
                }
            else:
                data = {"success": False, "error": f"API '{args.name}' 未找到"}
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if api:
                print(f"API: {api.name}\n")
                print(f"模块: {api.module}")
                print(f"描述: {api.description}")
                if api.scope:
                    print(f"作用域: {api.scope.value}")
                if api.parameters:
                    print("\n参数:")
                    for p in api.parameters:
                        print(f"  - {p.name}: {p.data_type}")
                        if p.description:
                            print(f"    {p.description}")
            else:
                print(f"❌ API '{args.name}' 未找到")

    elif args.action == "event":
        # 精确查事件
        retriever = KnowledgeRetriever()
        retriever.load("data/knowledge_base.json")

        event = retriever.get_event(args.name)

        if args.format == "json":
            if event:
                data = {
                    "success": True,
                    "event": {
                        "name": event.name,
                        "module": event.module,
                        "description": event.description,
                        "scope": event.scope.value if event.scope else "unknown",
                    }
                }
            else:
                data = {"success": False, "error": f"事件 '{args.name}' 未找到"}
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if event:
                print(f"事件: {event.name}\n")
                print(f"模块: {event.module}")
                print(f"描述: {event.description}")
                if event.scope:
                    print(f"作用域: {event.scope.value}")
            else:
                print(f"❌ 事件 '{args.name}' 未找到")

    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """运行游戏并加载 Addon"""
    from mc_agent_kit.launcher import (
        AddonInfo,
        GameConfig,
        PlayerInfo,
        ServerInfo,
        WorldInfo,
        generate_config,
        launch_game,
        scan_addon,
    )
    from mc_agent_kit.log_capture import start_log_server
    import time

    # 扫描 Addon
    try:
        addon_info = scan_addon(args.addon_path)
    except FileNotFoundError as e:
        if args.format == "json":
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(f"❌ 错误: {e}")
        return 1

    # 检查游戏路径
    game_path = args.game_path
    if not game_path:
        # 尝试自动检测
        from mc_agent_kit.launcher.diagnoser import LauncherDiagnoser
        diagnoser = LauncherDiagnoser()
        game_path = diagnoser._detect_game_path()
        if not game_path:
            if args.format == "json":
                print(json.dumps({
                    "success": False,
                    "error": "未找到游戏路径，请使用 --game-path 指定"
                }, ensure_ascii=False))
            else:
                print("❌ 未找到游戏路径，请使用 --game-path 指定")
            return 1

    # 生成配置
    world_info = WorldInfo()
    player_info = PlayerInfo()
    server_info = ServerInfo()

    game_config = GameConfig(
        addon_id=addon_info.id,
        addon_name=addon_info.name,
        addon_path=args.addon_path,
        game_version=args.version or "1.0.0",
        game_exe_path=game_path,
        world_info=world_info,
        player_info=player_info,
        server_info=server_info,
    )

    config, config_path = generate_config(addon_info, game_config, args.output_dir or ".")

    # 启动日志服务器
    log_server = None
    log_entries = []
    if not args.no_logs:
        try:
            log_server = start_log_server(port=args.log_port or 0)
            game_config.logging_port = log_server.port
        except Exception as e:
            if args.verbose:
                print(f"警告: 无法启动日志服务器: {e}")

    # 启动游戏
    try:
        game_process = launch_game(
            game_exe_path=game_path,
            config_path=config_path,
            logging_port=game_config.logging_port,
            logging_ip=game_config.logging_ip,
        )

        result = {
            "success": True,
            "pid": game_process.pid,
            "config_path": config_path,
            "game_path": game_path,
            "addon_name": addon_info.name,
            "logging_port": game_config.logging_port,
        }

        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 游戏启动成功!")
            print(f"   PID: {game_process.pid}")
            print(f"   配置文件: {config_path}")
            print(f"   Addon: {addon_info.name}")
            if game_config.logging_port:
                print(f"   日志端口: {game_config.logging_port}")

        if args.wait:
            if args.verbose:
                print("\n等待游戏退出...")
            exit_code = game_process.wait()
            result["exit_code"] = exit_code
            result["duration"] = time.time()  # 简化

            if args.format == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"\n游戏已退出，返回码: {exit_code}")

        return 0

    except Exception as e:
        if args.format == "json":
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(f"❌ 启动失败: {e}")
        return 1


def cmd_logs(args: argparse.Namespace) -> int:
    """日志分析"""
    from mc_agent_kit.log_capture import LogAnalyzer, LogParser

    analyzer = LogAnalyzer()
    parser = LogParser()

    # 读取日志
    log_content = args.log
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                log_content = f.read()
        except FileNotFoundError:
            print(f"错误：文件不存在：{args.file}")
            return 1

    if not log_content:
        print("错误：请提供日志内容或日志文件 (--file)")
        return 1

    # 将日志内容按行分割后批量解析
    log_lines = [line.strip() for line in log_content.split("\n") if line.strip()]

    if args.action == "analyze":
        # 解析日志
        entries = parser.parse_batch(log_lines) if log_lines else []

        # 分析日志
        stats = analyzer.get_statistics()

        if args.format == "json":
            data = {
                "success": True,
                "total_entries": len(entries),
                "statistics": {
                    "total_logs": stats["total_logs"],
                    "error_count": stats["error_count"],
                    "warning_count": stats["warning_count"],
                    "by_level": stats["by_level"],
                },
                "entries": [
                    {
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "level": e.level.value if e.level else "unknown",
                        "source": e.source,
                        "message": e.message[:200] if len(e.message) > 200 else e.message,
                    }
                    for e in entries[:args.limit]
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"日志分析结果:\n")
            print(f"  总条目: {len(entries)}")
            print(f"  错误: {stats['error_count']}")
            print(f"  警告: {stats['warning_count']}")

            if entries:
                print(f"\n最近 {min(args.limit, len(entries))} 条日志:\n")
                for e in entries[:args.limit]:
                    level_icon = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(e.level.value, "📝")
                    print(f"  {level_icon} [{e.level.value}] {e.message[:100]}")

    elif args.action == "errors":
        # 提取错误
        entries = parser.parse_batch(log_lines) if log_lines else []
        errors = [e for e in entries if e.level and e.level.value in ("ERROR", "CRITICAL")]

        if args.format == "json":
            data = {
                "success": True,
                "error_count": len(errors),
                "errors": [
                    {
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "source": e.source,
                        "message": e.message,
                    }
                    for e in errors
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if errors:
                print(f"发现 {len(errors)} 个错误:\n")
                for i, e in enumerate(errors, 1):
                    print(f"[{i}] {e.message[:200]}")
                    if e.source:
                        print(f"    来源: {e.source}")
                    print()
            else:
                print("✅ 未发现错误")

    elif args.action == "patterns":
        # 列出错误模式
        patterns = analyzer.patterns

        if args.format == "json":
            data = {
                "success": True,
                "patterns": [
                    {
                        "name": p.name,
                        "category": p.category.value,
                        "severity": p.severity.value,
                        "description": p.description,
                    }
                    for p in patterns
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"已定义的错误模式 ({len(patterns)} 个):\n")
            for p in patterns:
                print(f"  📋 {p.name}")
                print(f"     类别: {p.category.value}")
                print(f"     严重程度: {p.severity.value}")
                if p.description:
                    print(f"     描述: {p.description}")
                print()

    return 0


def cmd_launcher(args: argparse.Namespace) -> int:
    """启动器诊断"""
    from mc_agent_kit.launcher import diagnose_launcher, fix_config
    from mc_agent_kit.launcher.auto_fixer import analyze_addon_memory, get_memory_optimization_tips

    if args.action == "analyze":
        # 内存分析
        if not args.addon_path:
            if args.format == "json":
                print(json.dumps({"success": False, "error": "请提供 --addon-path 参数"}, ensure_ascii=False))
            else:
                print("错误：请提供 --addon-path 参数")
            return 1

        report = analyze_addon_memory(args.addon_path)

        if args.format == "json":
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print("Addon 内存分析报告")
            print("=" * 60)
            print()
            print(f"Addon 路径: {report.addon_path}")
            print(f"发现问题: {report.total_issues}")
            print(f"  严重问题: {report.critical_issues}")
            print(f"  可自动修复: {report.auto_fixable_issues}")
            print()

            if report.suggestions:
                print("-" * 60)
                print("修复建议")
                print("-" * 60)

                # 按严重程度分组
                critical = [s for s in report.suggestions if s.severity.value in ("critical", "high")]
                medium = [s for s in report.suggestions if s.severity.value == "medium"]
                low = [s for s in report.suggestions if s.severity.value == "low"]

                if critical:
                    print("\n❌ 严重问题:")
                    for s in critical:
                        print(f"\n  [{s.fix_type.value}] {s.title}")
                        print(f"  {s.description}")
                        if s.current_value and s.suggested_value:
                            print(f"  当前: {s.current_value} → 建议: {s.suggested_value}")
                        if s.estimated_savings:
                            print(f"  预计节省: {s.estimated_savings}")
                        if s.fix_command:
                            print(f"  修复方法: {s.fix_command}")

                if medium:
                    print("\n⚠️  中等问题:")
                    for s in medium:
                        print(f"\n  [{s.fix_type.value}] {s.title}")
                        print(f"  {s.description}")

                if low:
                    print("\nℹ️  低优先级:")
                    for s in low:
                        print(f"\n  [{s.fix_type.value}] {s.title}")

            if report.errors:
                print("\n❌ 错误:")
                for e in report.errors:
                    print(f"  - {e}")

            print()
            print("=" * 60)
            if report.has_critical_issues:
                print("⚠️  发现严重内存问题，建议优先修复")
            elif report.total_issues > 0:
                print("✅ 分析完成，发现可优化的项目")
            else:
                print("✅ 分析完成，未发现内存问题")
            print("=" * 60)

        return 0 if not report.has_critical_issues else 1

    elif args.action == "fix":
        # 内存自动修复（基于配置文件）
        report = fix_config(
            args.config_path,
            args.output_path,
        )

        if args.format == "json":
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("配置文件修复结果:\n")

            if report.fixes:
                print(f"应用的修复 ({len(report.fixes)} 个):")
                for fix in report.fixes:
                    print(f"  - {fix.field}: {fix.description}")
                    if fix.auto_fixable:
                        print(f"    {fix.current_value} → {fix.suggested_value}")
                print()

            if report.errors:
                print("❌ 错误:")
                for e in report.errors:
                    print(f"  - {e}")
                print()

            if report.warnings:
                print("⚠️  警告:")
                for w in report.warnings:
                    print(f"  - {w}")
                print()

            if report.fixed:
                print("✅ 配置文件修复完成")
            else:
                print("❌ 配置文件修复失败")

        return 0 if report.fixed else 1

    elif args.action == "tips":
        # 获取优化技巧
        tips = get_memory_optimization_tips()

        if args.format == "json":
            print(json.dumps({"tips": tips}, ensure_ascii=False, indent=2))
        else:
            print("内存优化技巧:\n")

            # 按类别分组
            by_category: dict[str, list[dict]] = {}
            for tip in tips:
                cat = tip["category"]
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(tip)

            for category, category_tips in by_category.items():
                print(f"\n[{category}]")
                for tip in category_tips:
                    print(f"\n  💡 {tip['tip']}")
                    print(f"     原因: {tip['reason']}")

        return 0

    elif args.action == "diagnose":
        # 执行诊断
        report = diagnose_launcher(
            addon_path=args.addon_path,
            config_path=args.config_path,
            game_path=args.game_path,
        )

        if args.format == "json":
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print("游戏启动器诊断报告")
            print("=" * 60)
            print()

            # 基本信息
            if report.game_path:
                print(f"🎮 游戏路径: {report.game_path}")
            if report.game_version:
                print(f"📦 游戏版本: {report.game_version}")
            if report.addon_path:
                print(f"📁 Addon 路径: {report.addon_path}")
            if report.config_path:
                print(f"📄 配置文件: {report.config_path}")

            print()
            print("-" * 60)
            print("检查结果统计")
            print("-" * 60)
            print(f"  ✅ 通过: {report.checks_passed}")
            print(f"  ❌ 失败: {report.checks_failed}")
            print(f"  ⚠️  警告: {report.checks_warning}")
            print()

            if report.issues:
                print("-" * 60)
                print("发现的问题")
                print("-" * 60)

                # 按严重程度分组
                errors = [i for i in report.issues if i.severity.value == "error"]
                warnings = [i for i in report.issues if i.severity.value == "warning"]
                infos = [i for i in report.issues if i.severity.value == "info"]

                if errors:
                    print("\n❌ 错误:")
                    for i in errors:
                        print(f"\n  [{i.code}] {i.message}")
                        if i.details:
                            print(f"     详情: {i.details}")
                        if i.suggestion:
                            print(f"     建议: {i.suggestion}")
                        if i.location:
                            print(f"     位置: {i.location}")

                if warnings:
                    print("\n⚠️  警告:")
                    for i in warnings:
                        print(f"\n  [{i.code}] {i.message}")
                        if i.suggestion:
                            print(f"     建议: {i.suggestion}")

                if infos:
                    print("\nℹ️  信息:")
                    for i in infos:
                        print(f"\n  [{i.code}] {i.message}")
                        if i.details:
                            # 截断过长的详情
                            details = i.details[:500] + "..." if len(i.details) > 500 else i.details
                            print(f"     {details}")

            print()
            print("=" * 60)
            if report.success:
                print("✅ 诊断完成: 未发现严重问题")
            else:
                print("❌ 诊断完成: 发现需要修复的问题")
            print("=" * 60)

        return 0 if report.success else 1

    elif args.action == "compare":
        # 对比配置文件
        from mc_agent_kit.launcher import LauncherDiagnoser

        diagnoser = LauncherDiagnoser(args.game_path)
        result = diagnoser.compare_with_mc_studio_config(
            args.config_path,
            args.mc_studio_config,
        )

        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("配置文件对比结果:\n")

            if result["warnings"]:
                print("⚠️  警告:")
                for w in result["warnings"]:
                    print(f"  - {w}")
                print()

            if result["differences"]:
                print("📋 差异:")
                for d in result["differences"]:
                    print(f"  字段: {d['field']}")
                    print(f"    当前值: {d['current']}")
                    print(f"    MC Studio: {d['mc_studio']}")
                    print()

            if result["suggestions"]:
                print("💡 建议:")
                for s in result["suggestions"]:
                    print(f"  - {s}")

            if not result["differences"] and not result["warnings"]:
                print("✅ 配置文件与 MC Studio 格式一致")

        return 0

    elif args.action == "fix":
        # 自动修复配置文件
        report = fix_config(
            args.config_path,
            args.output_path,
        )

        if args.format == "json":
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("配置文件修复结果:\n")

            if report.fixes:
                print(f"应用的修复 ({len(report.fixes)} 个):")
                for fix in report.fixes:
                    print(f"  - {fix.field}: {fix.description}")
                    if fix.auto_fixable:
                        print(f"    {fix.current_value} → {fix.suggested_value}")
                print()

            if report.errors:
                print("❌ 错误:")
                for e in report.errors:
                    print(f"  - {e}")
                print()

            if report.warnings:
                print("⚠️  警告:")
                for w in report.warnings:
                    print(f"  - {w}")
                print()

            if report.fixed:
                print("✅ 配置文件修复完成")
            else:
                print("❌ 配置文件修复失败")

        return 0 if report.fixed else 1

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """API 使用统计"""
    from mc_agent_kit.stats import ApiUsageTracker

    # 初始化追踪器
    data_path = args.data_path or "data/api_stats.json"
    tracker = ApiUsageTracker(data_path)

    if args.action == "summary":
        # 获取统计摘要
        summary = tracker.get_summary()

        if args.format == "json":
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print("API 使用统计摘要\n")
            print("=" * 50)
            print(f"总 API 数: {summary['total_apis']}")
            print(f"总调用次数: {summary['total_calls']}")
            print(f"成功次数: {summary['total_success']}")
            print(f"错误次数: {summary['total_errors']}")
            print(f"成功率: {summary['success_rate']:.2%}")

            if summary['hot_apis']:
                print("\n热门 API (Top 5):")
                for i, api in enumerate(summary['hot_apis'], 1):
                    print(f"  {i}. {api['api_name']} ({api['total_calls']} 次调用)")

            if summary['problematic_apis']:
                print("\n问题 API (错误率高):")
                for api in summary['problematic_apis']:
                    print(f"  - {api['api_name']} (错误率: {api['error_rate']:.2%})")

    elif args.action == "hot":
        # 获取热门 API
        hot_apis = tracker.get_hot_apis(limit=args.limit)

        if args.format == "json":
            data = {"apis": [api.to_dict() for api in hot_apis]}
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"热门 API (Top {args.limit})\n")
            if hot_apis:
                for i, api in enumerate(hot_apis, 1):
                    print(f"{i}. {api.api_name}")
                    print(f"   调用次数: {api.total_calls}")
                    print(f"   成功率: {api.success_rate:.2%}")
                    if api.last_used:
                        print(f"   最近使用: {api.last_used}")
                    print()
            else:
                print("暂无数据")

    elif args.action == "problems":
        # 获取问题 API
        problematic = tracker.get_problematic_apis(
            min_calls=args.min_calls,
            error_rate_threshold=args.error_rate,
            limit=args.limit,
        )

        if args.format == "json":
            data = {
                "min_calls": args.min_calls,
                "error_rate_threshold": args.error_rate,
                "apis": [api.to_dict() for api in problematic],
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"问题 API (最小调用: {args.min_calls}, 错误率 >= {args.error_rate:.0%})\n")
            if problematic:
                for i, api in enumerate(problematic, 1):
                    print(f"{i}. {api.api_name}")
                    print(f"   调用次数: {api.total_calls}")
                    print(f"   错误率: {api.error_rate:.2%}")
                    if api.common_errors:
                        print(f"   常见错误: {', '.join(api.common_errors[:3])}")
                    print()
            else:
                print("暂无问题 API")

    elif args.action == "module":
        # 按模块分组统计
        by_module = tracker.get_stats_by_module()
        module_name = args.module

        if module_name:
            # 指定模块
            apis = by_module.get(module_name, [])

            if args.format == "json":
                data = {
                    "module": module_name,
                    "apis": [api.to_dict() for api in apis],
                }
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"模块 '{module_name}' 的 API 统计\n")
                if apis:
                    for api in apis:
                        print(f"  - {api.api_name}: {api.total_calls} 次调用")
                else:
                    print("  该模块暂无数据")
        else:
            # 所有模块概览
            if args.format == "json":
                data = {
                    "modules": {
                        mod: [api.to_dict() for api in apis]
                        for mod, apis in by_module.items()
                    }
                }
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print("模块统计概览\n")
                if by_module:
                    for module, apis in sorted(by_module.items()):
                        total_calls = sum(api.total_calls for api in apis)
                        print(f"  {module}: {len(apis)} 个 API, {total_calls} 次调用")
                else:
                    print("  暂无数据")

    elif args.action == "api":
        # 指定 API 的详细信息
        api_name = args.api_name
        if not api_name:
            if args.format == "json":
                print(json.dumps({"error": "请提供 --api-name 参数"}, ensure_ascii=False))
            else:
                print("错误：请提供 --api-name 参数")
            return 1

        stats = tracker.get_stats(api_name)

        if args.format == "json":
            if stats:
                print(json.dumps(stats.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(json.dumps({"error": f"API '{api_name}' 无统计数据"}, ensure_ascii=False))
        else:
            if stats:
                print(f"API: {api_name}\n")
                print(f"  调用次数: {stats.total_calls}")
                print(f"  成功次数: {stats.success_count}")
                print(f"  错误次数: {stats.error_count}")
                print(f"  成功率: {stats.success_rate:.2%}")
                if stats.last_used:
                    print(f"  最近使用: {stats.last_used}")
                if stats.avg_duration_ms:
                    print(f"  平均耗时: {stats.avg_duration_ms:.2f} ms")
                if stats.common_errors:
                    print("\n  常见错误:")
                    for e in stats.common_errors[:5]:
                        print(f"    - {e}")
            else:
                print(f"API '{api_name}' 无统计数据")

    return 0


def main() -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="mc-agent",
        description="MC-Agent-Kit CLI - ModSDK 开发辅助工具",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有 Skills")
    list_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # api 命令
    api_parser = subparsers.add_parser("api", help="搜索 ModSDK API")
    api_parser.add_argument("-q", "--query", help="搜索关键词")
    api_parser.add_argument("-n", "--name", help="精确匹配 API 名称")
    api_parser.add_argument("-m", "--module", help="按模块过滤")
    api_parser.add_argument("-s", "--scope", choices=["client", "server"], help="按作用域过滤")
    api_parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")
    api_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # event 命令
    event_parser = subparsers.add_parser("event", help="搜索 ModSDK 事件")
    event_parser.add_argument("-q", "--query", help="搜索关键词")
    event_parser.add_argument("-n", "--name", help="精确匹配事件名称")
    event_parser.add_argument("-m", "--module", help="按模块过滤")
    event_parser.add_argument("-s", "--scope", choices=["client", "server"], help="按作用域过滤")
    event_parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")
    event_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # gen 命令
    gen_parser = subparsers.add_parser("gen", help="生成 ModSDK 代码")
    gen_parser.add_argument("-t", "--template", help="模板名称")
    gen_parser.add_argument("-p", "--params", help="模板参数 (JSON 格式)")
    gen_parser.add_argument("-a", "--action", default="generate", help="操作类型")
    gen_parser.add_argument("-k", "--keyword", help="搜索关键词")
    gen_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # debug 命令
    debug_parser = subparsers.add_parser("debug", help="调试 ModSDK 错误")
    debug_parser.add_argument("-l", "--log", help="日志内容")
    debug_parser.add_argument("--file", dest="file", help="日志文件路径")
    debug_parser.add_argument("-a", "--action", default="diagnose", help="操作类型")
    debug_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # complete 命令
    complete_parser = subparsers.add_parser("complete", help="代码补全")
    complete_parser.add_argument("-c", "--code", help="代码内容")
    complete_parser.add_argument("--file", dest="file", help="代码文件路径")
    complete_parser.add_argument("-l", "--line", type=int, default=1, help="光标行号")
    complete_parser.add_argument("-C", "--column", type=int, default=0, help="光标列号")
    complete_parser.add_argument("-p", "--prefix", help="补全前缀")
    complete_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # refactor 命令
    refactor_parser = subparsers.add_parser("refactor", help="代码重构")
    refactor_parser.add_argument("-c", "--code", help="代码内容")
    refactor_parser.add_argument("--file", dest="file", help="代码文件路径")
    refactor_parser.add_argument("-a", "--action", choices=["detect", "suggest"], default="detect", help="操作类型")
    refactor_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # check 命令
    check_parser = subparsers.add_parser("check", help="最佳实践检查")
    check_parser.add_argument("-c", "--code", help="代码内容")
    check_parser.add_argument("--file", dest="file", help="代码文件路径")
    check_parser.add_argument("-a", "--action", choices=["check", "list"], default="check", help="操作类型")
    check_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # autofix 命令
    autofix_parser = subparsers.add_parser("autofix", help="自动修复错误")
    autofix_parser.add_argument("-c", "--code", help="代码内容")
    autofix_parser.add_argument("--file", dest="file", help="代码文件路径")
    autofix_parser.add_argument("-e", "--error", help="错误日志内容")
    autofix_parser.add_argument("-E", "--error-file", help="错误日志文件路径")
    autofix_parser.add_argument("-a", "--action", choices=["diagnose", "fix", "preview"], default="diagnose", help="操作类型")
    autofix_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # create 命令
    create_parser = subparsers.add_parser("create", help="创建 Addon 项目")
    create_parser.add_argument("type", choices=["project", "entity", "item", "block"], help="创建类型")
    create_parser.add_argument("name", help="名称")
    create_parser.add_argument("-p", "--path", help="目标路径")
    create_parser.add_argument("-t", "--template", choices=["empty", "entity", "item", "block"], help="项目模板")
    create_parser.add_argument("--force", action="store_true", help="覆盖已存在的项目")
    create_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # kb 命令
    kb_parser = subparsers.add_parser("kb", help="知识库管理")
    kb_parser.add_argument("action", choices=["status", "search", "api", "event"], help="操作类型")
    kb_parser.add_argument("-q", "--query", help="搜索查询")
    kb_parser.add_argument("-n", "--name", help="API/事件名称")
    kb_parser.add_argument("-l", "--limit", type=int, default=5, help="返回结果数量")
    kb_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行游戏并加载 Addon")
    run_parser.add_argument("addon_path", help="Addon 目录路径")
    run_parser.add_argument("--game-path", help="游戏可执行文件路径")
    run_parser.add_argument("--version", help="游戏版本")
    run_parser.add_argument("-o", "--output-dir", help="配置输出目录")
    run_parser.add_argument("--log-port", type=int, default=0, help="日志接收端口")
    run_parser.add_argument("--no-logs", action="store_true", help="禁用日志捕获")
    run_parser.add_argument("--wait", action="store_true", help="等待游戏退出")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    run_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # logs 命令
    logs_parser = subparsers.add_parser("logs", help="日志分析")
    logs_parser.add_argument("action", choices=["analyze", "errors", "patterns"], help="操作类型")
    logs_parser.add_argument("--log", help="日志内容")
    logs_parser.add_argument("--file", dest="file", help="日志文件路径")
    logs_parser.add_argument("-l", "--limit", type=int, default=20, help="返回结果数量")
    logs_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # launcher 命令
    launcher_parser = subparsers.add_parser("launcher", help="启动器诊断")
    launcher_parser.add_argument("action", choices=["diagnose", "compare", "fix", "analyze", "tips"], help="操作类型")
    launcher_parser.add_argument("--addon-path", help="Addon 目录路径")
    launcher_parser.add_argument("--config-path", help="配置文件路径")
    launcher_parser.add_argument("--game-path", help="游戏可执行文件路径")
    launcher_parser.add_argument("--mc-studio-config", help="MC Studio 配置文件路径 (用于对比)")
    launcher_parser.add_argument("--output-path", help="修复后的配置输出路径")
    launcher_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="API 使用统计")
    stats_parser.add_argument("action", choices=["summary", "hot", "problems", "module", "api"], help="操作类型")
    stats_parser.add_argument("--api-name", help="API 名称 (用于 api 操作)")
    stats_parser.add_argument("--module", help="模块名称 (用于 module 操作)")
    stats_parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量")
    stats_parser.add_argument("--min-calls", type=int, default=5, help="最小调用次数阈值")
    stats_parser.add_argument("--error-rate", type=float, default=0.3, help="错误率阈值")
    stats_parser.add_argument("--data-path", help="统计数据文件路径")
    stats_parser.add_argument(
        "--format",
        dest="format",
        choices=["text", "json"],
        default="text",
        help="输出格式",
    )

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
    elif args.command == "create":
        return cmd_create(args)
    elif args.command == "kb":
        return cmd_kb(args)
    elif args.command == "run":
        return cmd_run(args)
    elif args.command == "logs":
        return cmd_logs(args)
    elif args.command == "launcher":
        return cmd_launcher(args)
    elif args.command == "stats":
        return cmd_stats(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
