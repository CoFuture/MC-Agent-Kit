"""Batch processing CLI commands for MC-Agent-Kit."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from mc_agent_kit.workflow.batch_workflow import (
    BatchWorkflow,
    WorkflowStatus,
    WorkflowStep,
)

console = Console()


@click.group()
def batch() -> None:
    """Batch processing commands."""
    pass


@batch.command("run")
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option(
    "--context",
    "-c",
    multiple=True,
    help="Context variable in KEY=VALUE format",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def run_workflow(workflow_file: str, context: tuple[str, ...], verbose: bool) -> None:
    """Run a batch workflow.

    WORKFLOW_FILE: Path to workflow JSON file
    """
    try:
        # Load workflow
        workflow = BatchWorkflow.load(workflow_file)
        console.print(f"[bold blue]Running workflow:[/bold blue] {workflow.name}")

        # Parse context variables
        ctx_dict: dict[str, Any] = {}
        for item in context:
            if "=" in item:
                key, value = item.split("=", 1)
                ctx_dict[key.strip()] = value.strip()

        # Set context
        for key, value in ctx_dict.items():
            workflow.set_context(key, value)

        # Execute workflow
        console.print("\n[bold]Executing steps...[/bold]\n")
        result = workflow.execute()

        # Display results
        if verbose:
            for step_result in result.results:
                status = "[green]✓[/green]" if step_result.get("success") else "[red]✗[/red]"
                step_name = step_result.get("step", "Unknown")
                console.print(f"  {status} {step_name}")

        # Summary
        console.print("\n[bold]Workflow Summary:[/bold]")
        table = Table(show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Status", result.status.value)
        table.add_row("Duration", f"{result.duration:.2f}s")
        table.add_row("Steps Completed", str(len(result.results)))
        table.add_row("Errors", str(len(result.errors)))

        console.print(table)

        if result.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in result.errors:
                console.print(f"  • {error}")

        # Exit with appropriate code
        if result.status == WorkflowStatus.FAILED:
            raise click.ClickException("Workflow failed")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise


@batch.command("create")
@click.argument("name")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="workflow.json",
    help="Output file path",
)
def create_workflow(name: str, output: str) -> None:
    """Create a new workflow template.

    NAME: Workflow name
    """
    workflow = BatchWorkflow(name=name)

    # Add example steps
    workflow.add_step(WorkflowStep(
        name="example_step",
        action="echo",
        params={"message": "Hello, World!"},
    ))

    # Save workflow
    workflow.save(output)
    console.print(f"[green]✓[/green] Created workflow template: [bold]{output}[/bold]")
    console.print("\nEdit the file to add your steps, then run with:")
    console.print(f"  [cyan]mc-batch run {output}[/cyan]")


@batch.command("list")
@click.argument("directory", type=click.Path(exists=True), default=".")
def list_workflows(directory: str) -> None:
    """List workflows in a directory.

    DIRECTORY: Directory to search (default: current)
    """
    dir_path = Path(directory)
    workflow_files = list(dir_path.glob("*.json"))

    if not workflow_files:
        console.print("[yellow]No workflow files found.[/yellow]")
        return

    table = Table(title="Workflows")
    table.add_column("File", style="cyan")
    table.add_column("Name")
    table.add_column("Steps")

    for wf_file in workflow_files:
        try:
            with open(wf_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", "Unknown")
            steps = len(data.get("steps", []))
            table.add_row(wf_file.name, name, str(steps))
        except Exception:
            table.add_row(wf_file.name, "[red]Invalid[/red]", "-")

    console.print(table)


@batch.command("validate")
@click.argument("workflow_file", type=click.Path(exists=True))
def validate_workflow(workflow_file: str) -> None:
    """Validate a workflow file.

    WORKFLOW_FILE: Path to workflow JSON file
    """
    try:
        with open(workflow_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Basic validation
        errors = []

        if "name" not in data:
            errors.append("Missing 'name' field")

        if "steps" not in data:
            errors.append("Missing 'steps' field")
        elif not isinstance(data["steps"], list):
            errors.append("'steps' must be a list")
        else:
            for i, step in enumerate(data["steps"]):
                if "name" not in step:
                    errors.append(f"Step {i}: missing 'name'")
                if "action" not in step:
                    errors.append(f"Step {i}: missing 'action'")

        if errors:
            console.print("[bold red]Validation failed:[/bold red]")
            for error in errors:
                console.print(f"  • {error}")
            raise click.ClickException("Workflow validation failed")
        else:
            console.print(f"[green]✓[/green] Workflow [bold]{data['name']}[/bold] is valid")
            console.print(f"  Steps: {len(data['steps'])}")

    except json.JSONDecodeError as e:
        console.print(f"[bold red]Invalid JSON:[/bold red] {e}")
        raise


@batch.command("stats")
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option(
    "--iterations",
    "-n",
    type=int,
    default=1,
    help="Number of iterations for benchmarking",
)
def workflow_stats(workflow_file: str, iterations: int) -> None:
    """Show workflow statistics and benchmarks.

    WORKFLOW_FILE: Path to workflow JSON file
    """
    workflow = BatchWorkflow.load(workflow_file)

    console.print(f"[bold blue]Workflow:[/bold blue] {workflow.name}")
    console.print(f"[bold blue]Steps:[/bold blue] {len(workflow.steps)}\n")

    if iterations > 1:
        console.print(f"[bold]Running benchmark ({iterations} iterations)...[/bold]\n")

        times = []
        for i in range(iterations):
            start = time.time()
            workflow.execute()
            elapsed = time.time() - start
            times.append(elapsed)
            console.print(f"  Iteration {i+1}: {elapsed:.3f}s")

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        console.print(f"\n[bold]Benchmark Results:[/bold]")
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value")

        table.add_row("Average", f"{avg_time:.3f}s")
        table.add_row("Min", f"{min_time:.3f}s")
        table.add_row("Max", f"{max_time:.3f}s")
        table.add_row("Iterations", str(iterations))

        console.print(table)
    else:
        console.print("[yellow]Use --iterations for benchmarking[/yellow]")


def main() -> None:
    """Main entry point."""
    batch()


if __name__ == "__main__":
    main()
