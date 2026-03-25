#!/usr/bin/env python3
"""
MC-Agent-Kit Workflow CLI

工作流命令行工具，用于管理和执行智能工作流。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


def cmd_run(args: argparse.Namespace) -> int:
    """运行工作流"""
    from mc_agent_kit.llm import LLMConfig
    from mc_agent_kit.llm.workflow import (
        IntelligentWorkflow,
        WorkflowContext,
        WorkflowStatus,
        WorkflowStepType,
        run_workflow,
    )

    # 配置 LLM
    llm_config = None
    if args.provider:
        llm_config = LLMConfig(
            provider=args.provider,
            model=args.model,
        )

    # 配置上下文
    context = WorkflowContext(
        project_name=args.project_name or "my_addon",
        module_name=args.module_name or "",
        target=args.target or "server",
        max_iterations=args.max_iterations,
        min_review_score=args.min_score,
    )

    # 进度回调
    def on_progress(step):
        if not args.quiet:
            step_name = {
                WorkflowStepType.ANALYZE: "Analyzing requirements",
                WorkflowStepType.DESIGN: "Designing solution",
                WorkflowStepType.GENERATE: "Generating code",
                WorkflowStepType.REVIEW: "Reviewing code",
                WorkflowStepType.FIX: "Fixing issues",
                WorkflowStepType.TEST: "Running tests",
                WorkflowStepType.ITERATE: "Iterating",
            }.get(step.step_type, step.step_type.value)

            status_icon = {
                WorkflowStatus.RUNNING: "🔄",
                WorkflowStatus.COMPLETED: "✅",
                WorkflowStatus.FAILED: "❌",
            }.get(step.status, "⏳")

            print(f"  {status_icon} {step_name}: {step.name}")
            if args.verbose and step.output_data:
                for key, value in step.output_data.items():
                    print(f"     - {key}: {value}")

    # 运行工作流
    if not args.quiet:
        print(f"\n🚀 Starting workflow...")
        print(f"   Project: {context.project_name}")
        print(f"   Target: {context.target}")
        print(f"   Max iterations: {context.max_iterations}")
        print()

    start_time = time.time()

    if args.requirement_file:
        with open(args.requirement_file, encoding="utf-8") as f:
            requirement = f.read()
    else:
        requirement = args.requirement or "Create a simple ModSDK addon"

    result = run_workflow(
        requirement=requirement,
        project_name=context.project_name,
        target=context.target,
        max_iterations=context.max_iterations,
        min_review_score=context.min_review_score,
        llm_config=llm_config,
    )

    duration = time.time() - start_time

    # 输出结果
    if args.format == "json":
        output = result.to_dict()
        output["duration_seconds"] = duration
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        print("Workflow Result")
        print("=" * 60)
        print()
        print(f"  Status: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"  Iterations: {result.iterations}")
        print(f"  Duration: {duration:.2f}s")

        if result.generated_code:
            print("\n📝 Generated Code:")
            print("-" * 40)
            code = result.generated_code.code
            if len(code) > 500:
                print(code[:500] + "\n... (truncated)")
            else:
                print(code)

        if result.review_result:
            print(f"\n📊 Review Score: {result.review_result.score}/100")
            if result.review_result.issues:
                print(f"   Issues: {len(result.review_result.issues)}")

        if result.error:
            print(f"\n❌ Error: {result.error}")

        print("\n" + "=" * 60)

    return 0 if result.success else 1


def cmd_template(args: argparse.Namespace) -> int:
    """管理工作流模板"""
    from mc_agent_kit.workflow.engine import WorkflowOrchestrator, WorkflowTemplate

    orchestrator = WorkflowOrchestrator()

    if args.action == "list":
        templates = orchestrator.list_templates(tag=args.tag)

        if args.format == "json":
            data = {
                "templates": [t.to_dict() for t in templates]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print("\n📋 Available Workflow Templates:\n")
            if templates:
                for t in templates:
                    print(f"  📦 {t.id}: {t.name}")
                    print(f"     Description: {t.description}")
                    if t.tags:
                        print(f"     Tags: {', '.join(t.tags)}")
                    print()
            else:
                print("  No templates found.")

    elif args.action == "show":
        template = orchestrator.get_template(args.template_id)

        if not template:
            print(f"❌ Template not found: {args.template_id}")
            return 1

        if args.format == "json":
            print(json.dumps(template.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"\n📦 Template: {template.name}\n")
            print(f"  ID: {template.id}")
            print(f"  Description: {template.description}")
            print(f"  Version: {template.version}")
            if template.tags:
                print(f"  Tags: {', '.join(template.tags)}")

            print("\n  Steps:")
            for i, step in enumerate(template.steps, 1):
                step_type = step.get("type", "task")
                step_name = step.get("name", step.get("id", "unknown"))
                print(f"    {i}. [{step_type}] {step_name}")

            if template.variables:
                print("\n  Variables:")
                for key, value in template.variables.items():
                    print(f"    - {key}: {value}")

    elif args.action == "create":
        # 创建新模板
        template_data = {
            "id": args.template_id,
            "name": args.name or args.template_id,
            "description": args.description or "",
            "steps": [],
            "tags": args.tags.split(",") if args.tags else [],
        }

        template = WorkflowTemplate.from_dict(template_data)

        # 添加步骤
        if args.steps:
            for i, step_str in enumerate(args.steps):
                step_parts = step_str.split(":")
                step_id = f"step_{i+1}"
                step_name = step_parts[0] if step_parts else f"Step {i+1}"
                step_type = step_parts[1] if len(step_parts) > 1 else "task"

                template.steps.append({
                    "id": step_id,
                    "name": step_name,
                    "type": step_type,
                })

        orchestrator.register_template(template)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"✅ Template saved to: {args.output}")
        else:
            print(json.dumps(template.to_dict(), ensure_ascii=False, indent=2))

    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    """执行工作流模板"""
    from mc_agent_kit.workflow.engine import WorkflowOrchestrator, WorkflowStepConfig, StepType

    orchestrator = WorkflowOrchestrator()

    # 加载模板
    if args.template_file:
        with open(args.template_file, encoding="utf-8") as f:
            template_data = json.load(f)
        
        from mc_agent_kit.workflow.engine import WorkflowTemplate
        template = WorkflowTemplate.from_dict(template_data)
        orchestrator.register_template(template)
        template_id = template.id
    else:
        template_id = args.template_id

    # 解析变量
    variables = {}
    if args.vars:
        for var_str in args.vars:
            if "=" in var_str:
                key, value = var_str.split("=", 1)
                variables[key.strip()] = value.strip()

    # 定义动作映射
    action_map = {}
    
    def create_action(action_name: str):
        def action(ctx):
            return {"action": action_name, "executed": True}
        return action

    # 为模板步骤创建动作
    template = orchestrator.get_template(template_id)
    if template:
        for step in template.steps:
            step_id = step.get("id", "")
            action_map[step_id] = create_action(step_id)

    if not args.quiet:
        print(f"\n🔄 Executing workflow template: {template_id}")
        if variables:
            print(f"   Variables: {variables}")
        print()

    # 执行
    result = orchestrator.execute_template(template_id, variables, action_map)

    if args.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        print("Execution Result")
        print("=" * 60)
        print()
        print(f"  Status: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"  Duration: {result.total_duration_seconds:.2f}s")

        if result.step_results:
            print("\n  Steps:")
            for step in result.step_results:
                status = "✅" if step.success else "❌" if not step.skipped else "⏭️"
                print(f"    {status} {step.step_name} ({step.duration_seconds:.2f}s)")
                if step.error:
                    print(f"       Error: {step.error}")

        if result.error:
            print(f"\n  ❌ Error: {result.error}")

        print("\n" + "=" * 60)

    return 0 if result.success else 1


def cmd_visualize(args: argparse.Namespace) -> int:
    """可视化工作流"""
    from mc_agent_kit.workflow.engine import WorkflowOrchestrator

    orchestrator = WorkflowOrchestrator()

    # 加载模板
    if args.template_file:
        with open(args.template_file, encoding="utf-8") as f:
            template_data = json.load(f)
        
        from mc_agent_kit.workflow.engine import WorkflowTemplate
        template = WorkflowTemplate.from_dict(template_data)
        orchestrator.register_template(template)
        template_id = template.id
    else:
        template_id = args.template_id

    visualization = orchestrator.visualize_template(template_id)

    if not visualization:
        print(f"❌ Template not found: {template_id}")
        return 1

    if args.format == "mermaid":
        print(visualization.to_mermaid())
    elif args.format == "json":
        print(json.dumps(visualization.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("\n📊 Workflow Visualization\n")
        print("Nodes:")
        for node in visualization.nodes:
            print(f"  - [{node.get('type', 'task')}] {node.get('label', node.get('id', ''))}")

        print("\nEdges:")
        for edge in visualization.edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            label = edge.get("label", "")
            print(f"  - {source} -> {target}" + (f" ({label})" if label else ""))

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """查看工作流状态"""
    from mc_agent_kit.workflow.cache import get_workflow_cache

    cache = get_workflow_cache()
    stats = cache.get_stats()

    if args.format == "json":
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print("\n📊 Workflow System Status\n")
        print(f"  Cache entries: {stats['entries']}/{stats['max_entries']}")
        print(f"  Cache hits: {stats['hits']}")
        print(f"  Cache misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']:.2%}")
        print(f"  Persisted: {'Yes' if stats['persisted'] else 'No'}")

    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    """工作流诊断"""
    from mc_agent_kit.autofix import AutoFixer, ErrorDiagnoser
    from mc_agent_kit.autofix.log_analyzer import EnhancedLogAnalyzer

    if not args.quiet:
        print("\n🔍 Workflow Diagnostics\n")

    results = {
        "success": True,
        "checks": [],
    }

    # 检查知识库
    try:
        from mc_agent_kit.knowledge_base import KnowledgeRetriever
        retriever = KnowledgeRetriever()
        results["checks"].append({
            "name": "Knowledge Base",
            "status": "ok",
            "message": "Knowledge base module available",
        })
    except ImportError as e:
        results["checks"].append({
            "name": "Knowledge Base",
            "status": "warning",
            "message": f"Knowledge base not fully available: {e}",
        })

    # 检查自动修复
    try:
        fixer = AutoFixer()
        results["checks"].append({
            "name": "Auto Fixer",
            "status": "ok",
            "message": "Auto fixer module available",
        })
    except ImportError as e:
        results["checks"].append({
            "name": "Auto Fixer",
            "status": "error",
            "message": f"Auto fixer not available: {e}",
        })
        results["success"] = False

    # 检查日志分析
    try:
        analyzer = EnhancedLogAnalyzer()
        results["checks"].append({
            "name": "Log Analyzer",
            "status": "ok",
            "message": "Log analyzer module available",
        })
    except ImportError as e:
        results["checks"].append({
            "name": "Log Analyzer",
            "status": "warning",
            "message": f"Log analyzer not fully available: {e}",
        })

    # 检查工作流引擎
    try:
        from mc_agent_kit.workflow.engine import WorkflowOrchestrator
        orchestrator = WorkflowOrchestrator()
        templates = orchestrator.list_templates()
        results["checks"].append({
            "name": "Workflow Engine",
            "status": "ok",
            "message": f"Workflow engine available with {len(templates)} templates",
        })
    except ImportError as e:
        results["checks"].append({
            "name": "Workflow Engine",
            "status": "error",
            "message": f"Workflow engine not available: {e}",
        })
        results["success"] = False

    # 检查 LLM 集成
    try:
        from mc_agent_kit.llm import get_llm_manager
        manager = get_llm_manager()
        providers = manager.list_providers()
        results["checks"].append({
            "name": "LLM Integration",
            "status": "ok" if providers else "warning",
            "message": f"Available providers: {', '.join(providers) if providers else 'none'}",
        })
    except ImportError as e:
        results["checks"].append({
            "name": "LLM Integration",
            "status": "warning",
            "message": f"LLM integration not fully available: {e}",
        })

    # 输出结果
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for check in results["checks"]:
            status_icon = {
                "ok": "✅",
                "warning": "⚠️",
                "error": "❌",
            }.get(check["status"], "❓")
            print(f"  {status_icon} {check['name']}: {check['message']}")

        print()
        if results["success"]:
            print("✅ All critical checks passed")
        else:
            print("❌ Some critical checks failed")

    return 0 if results["success"] else 1


def cmd_feedback(args: argparse.Namespace) -> int:
    """管理用户反馈"""
    feedback_dir = Path("data/feedback")
    feedback_dir.mkdir(parents=True, exist_ok=True)

    if args.action == "submit":
        feedback = {
            "type": args.type or "general",
            "message": args.message,
            "priority": args.priority or "normal",
            "timestamp": time.time(),
        }

        if args.context:
            feedback["context"] = args.context

        feedback_file = feedback_dir / f"feedback_{int(time.time())}.json"
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

        print(f"✅ Feedback submitted: {feedback_file}")
        return 0

    elif args.action == "list":
        feedback_files = list(feedback_dir.glob("feedback_*.json"))

        if args.format == "json":
            feedback_list = []
            for ff in feedback_files:
                with open(ff, encoding="utf-8") as f:
                    feedback_list.append(json.load(f))
            print(json.dumps(feedback_list, ensure_ascii=False, indent=2))
        else:
            print(f"\n📋 Feedback Items ({len(feedback_files)}):\n")
            for ff in feedback_files:
                with open(ff, encoding="utf-8") as f:
                    feedback = json.load(f)
                print(f"  [{feedback.get('type', 'general')}] {feedback.get('message', '')[:50]}...")
                print(f"    Priority: {feedback.get('priority', 'normal')}")
                print(f"    File: {ff.name}")
                print()

    elif args.action == "stats":
        feedback_files = list(feedback_dir.glob("feedback_*.json"))
        
        stats = {
            "total": len(feedback_files),
            "by_type": {},
            "by_priority": {},
        }

        for ff in feedback_files:
            with open(ff, encoding="utf-8") as f:
                feedback = json.load(f)
            
            fb_type = feedback.get("type", "general")
            stats["by_type"][fb_type] = stats["by_type"].get(fb_type, 0) + 1

            priority = feedback.get("priority", "normal")
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

        if args.format == "json":
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("\n📊 Feedback Statistics\n")
            print(f"  Total feedback: {stats['total']}")
            print(f"\n  By type:")
            for fb_type, count in stats["by_type"].items():
                print(f"    - {fb_type}: {count}")
            print(f"\n  By priority:")
            for priority, count in stats["by_priority"].items():
                print(f"    - {priority}: {count}")

    return 0


def main() -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="mc-workflow",
        description="MC-Agent-Kit Workflow CLI - Intelligent workflow management",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run 命令
    run_parser = subparsers.add_parser("run", help="Run intelligent workflow")
    run_parser.add_argument("-r", "--requirement", help="Requirement description")
    run_parser.add_argument("-f", "--requirement-file", help="File containing requirement")
    run_parser.add_argument("-p", "--project-name", help="Project name")
    run_parser.add_argument("-m", "--module-name", help="Module name")
    run_parser.add_argument("-t", "--target", choices=["server", "client"], default="server", help="Target environment")
    run_parser.add_argument("--max-iterations", type=int, default=3, help="Maximum iterations")
    run_parser.add_argument("--min-score", type=float, default=70.0, help="Minimum review score")
    run_parser.add_argument("--provider", help="LLM provider")
    run_parser.add_argument("--model", help="LLM model")
    run_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    run_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    # template 命令
    template_parser = subparsers.add_parser("template", help="Manage workflow templates")
    template_parser.add_argument(
        "action",
        choices=["list", "show", "create"],
        help="Action to perform",
    )
    template_parser.add_argument("--template-id", help="Template ID")
    template_parser.add_argument("--name", help="Template name")
    template_parser.add_argument("--description", help="Template description")
    template_parser.add_argument("--tags", help="Comma-separated tags")
    template_parser.add_argument("--steps", nargs="+", help="Steps (format: name:type)")
    template_parser.add_argument("--tag", help="Filter by tag (for list)")
    template_parser.add_argument("-o", "--output", help="Output file")
    template_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="Execute workflow template")
    execute_parser.add_argument("template_id", nargs="?", help="Template ID")
    execute_parser.add_argument("-f", "--template-file", help="Template JSON file")
    execute_parser.add_argument("-c", "--vars", nargs="+", help="Variables (format: key=value)")
    execute_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    execute_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    # visualize 命令
    visualize_parser = subparsers.add_parser("visualize", help="Visualize workflow")
    visualize_parser.add_argument("template_id", nargs="?", help="Template ID")
    visualize_parser.add_argument("-f", "--template-file", help="Template JSON file")
    visualize_parser.add_argument("--format", choices=["text", "json", "mermaid"], default="text", help="Output format")

    # status 命令
    status_parser = subparsers.add_parser("status", help="Show workflow status")
    status_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # diagnose 命令
    diagnose_parser = subparsers.add_parser("diagnose", help="Run workflow diagnostics")
    diagnose_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    diagnose_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    # feedback 命令
    feedback_parser = subparsers.add_parser("feedback", help="Manage user feedback")
    feedback_parser.add_argument(
        "action",
        choices=["submit", "list", "stats"],
        help="Action to perform",
    )
    feedback_parser.add_argument("-m", "--message", help="Feedback message")
    feedback_parser.add_argument("-t", "--type", help="Feedback type")
    feedback_parser.add_argument("-p", "--priority", choices=["low", "normal", "high", "critical"], help="Priority")
    feedback_parser.add_argument("-c", "--context", help="Additional context")
    feedback_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "template":
        return cmd_template(args)
    elif args.command == "execute":
        return cmd_execute(args)
    elif args.command == "visualize":
        return cmd_visualize(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "diagnose":
        return cmd_diagnose(args)
    elif args.command == "feedback":
        return cmd_feedback(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())