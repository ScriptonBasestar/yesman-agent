"""Workflow management CLI commands."""

import asyncio
import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from libs.core.base_command import BaseCommand, CommandError
from libs.core.services import get_workflow_service
from libs.workflows.models import WorkflowExecution, WorkflowStatus


class WorkflowCommand(BaseCommand):
    """Base class for workflow commands."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()

    def _resolve_workflow_service(self):
        """Resolve workflow service from DI container."""
        try:
            return get_workflow_service()
        except Exception as e:
            raise CommandError(f"Failed to resolve workflow service: {e}")


class WorkflowListCommand(WorkflowCommand):
    """List available workflow templates."""

    def execute(
        self,
        builtin: bool = True,
        user: bool = True,
        tags: list[str] | None = None,
        format: str = "table",
        **kwargs: Any
    ) -> dict[str, Any]:
        """Execute list command.

        Args:
            builtin: Include built-in templates
            user: Include user templates
            tags: Filter by tags
            format: Output format (table, json, yaml)

        Returns:
            Dictionary containing template information
        """
        workflow_service = self._resolve_workflow_service()

        # Get templates
        templates = workflow_service.list_templates(
            include_builtin=builtin,
            tags=tags
        )

        # Filter user templates if needed
        if not user:
            templates = [t for t in templates if t.is_builtin]
        if not builtin:
            templates = [t for t in templates if not t.is_builtin]

        if format == "table":
            self._display_templates_table(templates)
        elif format == "json":
            self._display_templates_json(templates)
        elif format == "yaml":
            self._display_templates_yaml(templates)
        else:
            raise CommandError(f"Unknown format: {format}")

        return {
            "templates": [
                {
                    "id": t.template_id,
                    "name": t.config.name,
                    "description": t.config.description,
                    "tags": t.tags,
                    "builtin": t.is_builtin,
                    "steps": len(t.config.steps)
                }
                for t in templates
            ]
        }

    def _display_templates_table(self, templates) -> None:
        """Display templates in table format."""
        if not templates:
            self.print_info("No workflow templates found")
            return

        table = Table(title="Available Workflow Templates")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description", style="yellow")
        table.add_column("Steps", justify="right", style="magenta")
        table.add_column("Tags", style="blue")
        table.add_column("Type", style="red")

        for template in templates:
            table.add_row(
                template.template_id,
                template.config.name,
                template.config.description[:50] + "..." if len(template.config.description) > 50 else template.config.description,
                str(len(template.config.steps)),
                ", ".join(template.tags) if template.tags else "-",
                "Built-in" if template.is_builtin else "User"
            )

        self.console.print(table)

    def _display_templates_json(self, templates) -> None:
        """Display templates in JSON format."""
        template_data = []
        for template in templates:
            template_data.append({
                "id": template.template_id,
                "name": template.config.name,
                "description": template.config.description,
                "version": template.config.version,
                "author": template.config.author,
                "tags": template.tags,
                "is_builtin": template.is_builtin,
                "steps": len(template.config.steps),
                "timeout": template.config.timeout,
                "checkpoint_interval": template.config.checkpoint_interval
            })

        self.console.print_json(json.dumps(template_data, indent=2))

    def _display_templates_yaml(self, templates) -> None:
        """Display templates in YAML format."""
        import yaml
        template_data = []
        for template in templates:
            template_data.append({
                "id": template.template_id,
                "config": template.config.dict(),
                "tags": template.tags,
                "is_builtin": template.is_builtin
            })

        yaml_output = yaml.dump(template_data, default_flow_style=False)
        self.console.print(yaml_output)


class WorkflowRunCommand(WorkflowCommand):
    """Run a workflow template."""

    def execute(
        self,
        template_id: str,
        project_path: str | None = None,
        variables: dict[str, str] | None = None,
        detached: bool = False,
        monitor: bool = False,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Execute workflow run command.

        Args:
            template_id: Template to execute
            project_path: Project directory path
            variables: Template variables
            detached: Run in background
            monitor: Show real-time monitoring

        Returns:
            Dictionary containing execution results
        """
        workflow_service = self._resolve_workflow_service()

        # Validate template exists
        template = workflow_service.get_template(template_id)
        if not template:
            available = [t.template_id for t in workflow_service.list_templates()]
            raise CommandError(
                f"Template '{template_id}' not found",
                recovery_hint=f"Available templates: {', '.join(available)}"
            )

        # Resolve project path
        if project_path:
            project_dir = Path(project_path).resolve()
            if not project_dir.exists():
                raise CommandError(f"Project path does not exist: {project_path}")
        else:
            project_dir = Path.cwd()

        self.print_info(f"🚀 Starting workflow: {template.config.name}")
        self.print_info(f"📁 Project: {project_dir}")
        self.print_info(f"🔧 Template: {template_id}")

        if variables:
            self.print_info(f"📋 Variables: {', '.join(f'{k}={v}' for k, v in variables.items())}")

        try:
            if detached:
                # Run in background
                execution_id = asyncio.run(workflow_service.start_workflow(
                    template_id=template_id,
                    project_path=project_dir,
                    variables=variables or {},
                    detached=True
                ))

                self.print_success(f"Workflow started in background: {execution_id}")
                self.print_info(f"Use 'yesman workflow status {execution_id}' to check progress")

                return {"execution_id": execution_id, "detached": True}

            # Run with monitoring
            elif monitor:
                return self._run_with_monitoring(
                    workflow_service, template_id, project_dir, variables or {}
                )
            else:
                # Simple synchronous run
                execution_id = asyncio.run(workflow_service.start_workflow(
                    template_id=template_id,
                    project_path=project_dir,
                    variables=variables or {},
                    detached=False
                ))

                # Get final status
                execution = workflow_service.get_execution(execution_id)
                if execution:
                    self._display_execution_result(execution)

                return {"execution_id": execution_id, "status": execution.status.value if execution else "unknown"}

        except Exception as e:
            raise CommandError(f"Workflow execution failed: {e}")

    def _run_with_monitoring(
        self,
        workflow_service,
        template_id: str,
        project_dir: Path,
        variables: dict[str, str]
    ) -> dict[str, Any]:
        """Run workflow with real-time monitoring."""

        async def run_and_monitor():
            # Start workflow
            execution_id = await workflow_service.start_workflow(
                template_id=template_id,
                project_path=project_dir,
                variables=variables,
                detached=True  # Start in background for monitoring
            )

            # Monitor progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
                transient=True
            ) as progress:

                task = progress.add_task("Running workflow...", total=100)

                while True:
                    execution = workflow_service.get_execution(execution_id)
                    if not execution:
                        break

                    # Update progress
                    progress_pct = execution.get_progress()
                    progress.update(task, completed=progress_pct)

                    # Update description
                    if execution.current_step is not None:
                        step_name = execution.config.steps[execution.current_step].get("id", "Unknown")
                        progress.update(task, description=f"Step: {step_name}")

                    # Check if finished
                    if execution.status in {WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED}:
                        break

                    await asyncio.sleep(2)

            return execution_id

        # Run the async function
        execution_id = asyncio.run(run_and_monitor())

        # Display final result
        execution = workflow_service.get_execution(execution_id)
        if execution:
            self._display_execution_result(execution)

        return {"execution_id": execution_id, "status": execution.status.value if execution else "unknown"}

    def _display_execution_result(self, execution: WorkflowExecution) -> None:
        """Display execution results."""
        status_color = {
            WorkflowStatus.COMPLETED: "green",
            WorkflowStatus.FAILED: "red",
            WorkflowStatus.CANCELLED: "yellow",
            WorkflowStatus.RUNNING: "blue"
        }.get(execution.status, "white")

        panel_title = f"Workflow Execution: {execution.id[:8]}..."

        # Build content
        content = []
        content.append(f"Status: [{status_color}]{execution.status.value.upper()}[/{status_color}]")
        content.append(f"Progress: {execution.get_progress():.1f}%")
        content.append(f"Steps: {len(execution.step_results)}/{len(execution.config.steps)}")

        if execution.get_execution_time():
            content.append(f"Duration: {execution.get_execution_time():.1f}s")

        if execution.error_log:
            content.append(f"Errors: {len(execution.error_log)}")

        panel = Panel(
            "\n".join(content),
            title=panel_title,
            border_style=status_color
        )

        self.console.print(panel)

        # Show step results if completed
        if execution.status == WorkflowStatus.COMPLETED and execution.step_results:
            self.print_info("\n📋 Step Results:")
            for step_id, result in execution.step_results.items():
                result_preview = result[:100] + "..." if len(result) > 100 else result
                self.console.print(f"  • {step_id}: {result_preview}")


class WorkflowStatusCommand(WorkflowCommand):
    """Check workflow execution status."""

    def execute(
        self,
        execution_id: str | None = None,
        list_all: bool = False,
        running_only: bool = False,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Execute status command.

        Args:
            execution_id: Specific execution to check
            list_all: List all executions
            running_only: Show only running executions

        Returns:
            Dictionary containing status information
        """
        workflow_service = self._resolve_workflow_service()

        if execution_id:
            # Show specific execution
            execution = workflow_service.get_execution(execution_id)
            if not execution:
                raise CommandError(f"Execution not found: {execution_id}")

            self._display_execution_detail(execution)

            return {
                "execution_id": execution_id,
                "status": execution.status.value,
                "progress": execution.get_progress()
            }

        else:
            # List executions
            status_filter = WorkflowStatus.RUNNING if running_only else None
            executions = workflow_service.list_executions(status_filter)

            if not executions:
                self.print_info("No workflow executions found")
                return {"executions": []}

            self._display_executions_table(executions)

            return {
                "executions": [
                    {
                        "id": e.id,
                        "status": e.status.value,
                        "progress": e.get_progress(),
                        "workflow": e.config.name if e.config else "Unknown"
                    }
                    for e in executions
                ]
            }

    def _display_execution_detail(self, execution: WorkflowExecution) -> None:
        """Display detailed execution information."""
        # Similar to _display_execution_result but more detailed
        status_color = {
            WorkflowStatus.COMPLETED: "green",
            WorkflowStatus.FAILED: "red",
            WorkflowStatus.CANCELLED: "yellow",
            WorkflowStatus.RUNNING: "blue"
        }.get(execution.status, "white")

        # Main info panel
        content = []
        content.append(f"ID: {execution.id}")
        content.append(f"Workflow: {execution.config.name if execution.config else 'Unknown'}")
        content.append(f"Status: [{status_color}]{execution.status.value.upper()}[/{status_color}]")
        content.append(f"Progress: {execution.get_progress():.1f}%")
        content.append(f"Steps: {len(execution.step_results)}/{len(execution.config.steps) if execution.config else 0}")

        if execution.started_at:
            content.append(f"Started: {execution.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if execution.completed_at:
            content.append(f"Completed: {execution.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if execution.get_execution_time():
            content.append(f"Duration: {execution.get_execution_time():.1f}s")

        panel = Panel(
            "\n".join(content),
            title="Workflow Execution Details",
            border_style=status_color
        )

        self.console.print(panel)

        # Step results
        if execution.step_results:
            self.console.print("\n📋 Step Results:")
            for step_id, result in execution.step_results.items():
                self.console.print(f"  ✅ {step_id}")

        # Errors
        if execution.error_log:
            self.console.print(f"\n❌ Errors ({len(execution.error_log)}):")
            for error in execution.error_log[-5:]:  # Show last 5 errors
                self.console.print(f"  • [{error['timestamp']}] {error['step_id']}: {error['error']}")

    def _display_executions_table(self, executions: list[WorkflowExecution]) -> None:
        """Display executions in table format."""
        table = Table(title="Workflow Executions")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Workflow", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Progress", justify="right", style="magenta")
        table.add_column("Duration", justify="right", style="blue")
        table.add_column("Started", style="dim")

        for execution in executions:
            status_emoji = {
                WorkflowStatus.COMPLETED: "✅",
                WorkflowStatus.FAILED: "❌",
                WorkflowStatus.CANCELLED: "⚠️",
                WorkflowStatus.RUNNING: "🔄",
                WorkflowStatus.PENDING: "⏳"
            }.get(execution.status, "❓")

            table.add_row(
                execution.id[:8] + "...",
                execution.config.name if execution.config else "Unknown",
                f"{status_emoji} {execution.status.value}",
                f"{execution.get_progress():.1f}%",
                f"{execution.get_execution_time():.1f}s" if execution.get_execution_time() else "-",
                execution.started_at.strftime("%m-%d %H:%M") if execution.started_at else "-"
            )

        self.console.print(table)


class WorkflowCancelCommand(WorkflowCommand):
    """Cancel running workflow execution."""

    def execute(self, execution_id: str, **kwargs: Any) -> dict[str, Any]:
        """Execute cancel command.

        Args:
            execution_id: Execution to cancel

        Returns:
            Dictionary containing cancellation results
        """
        workflow_service = self._resolve_workflow_service()

        execution = workflow_service.get_execution(execution_id)
        if not execution:
            raise CommandError(f"Execution not found: {execution_id}")

        if execution.status not in {WorkflowStatus.RUNNING, WorkflowStatus.PENDING}:
            raise CommandError(f"Cannot cancel execution in status: {execution.status.value}")

        self.print_info(f"🛑 Cancelling workflow execution: {execution_id}")

        try:
            success = asyncio.run(workflow_service.cancel_execution(execution_id))

            if success:
                self.print_success("Workflow execution cancelled successfully")
                return {"execution_id": execution_id, "cancelled": True}
            else:
                raise CommandError("Failed to cancel workflow execution")

        except Exception as e:
            raise CommandError(f"Cancellation failed: {e}")


# CLI Commands

@click.group(name="workflow")
def workflow_group() -> None:
    """Workflow management commands."""


@workflow_group.command()
@click.option("--builtin/--no-builtin", default=True, help="Include built-in templates")
@click.option("--user/--no-user", default=True, help="Include user templates")
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table", help="Output format")
def list_templates(builtin: bool, user: bool, tags: tuple, format: str) -> None:
    """List available workflow templates."""
    command = WorkflowListCommand()
    command.run(builtin=builtin, user=user, tags=list(tags), format=format)


@workflow_group.command()
@click.argument("template_id")
@click.option("--project-path", "-p", help="Project directory path")
@click.option("--var", "-v", multiple=True, help="Template variables (key=value)")
@click.option("--detached", "-d", is_flag=True, help="Run in background")
@click.option("--monitor", "-m", is_flag=True, help="Show real-time monitoring")
def run(template_id: str, project_path: str | None, var: tuple, detached: bool, monitor: bool) -> None:
    """Run a workflow template."""
    # Parse variables
    variables = {}
    for v in var:
        if "=" not in v:
            click.echo(f"Invalid variable format: {v} (expected key=value)", err=True)
            return
        key, value = v.split("=", 1)
        variables[key] = value

    command = WorkflowRunCommand()
    command.run(
        template_id=template_id,
        project_path=project_path,
        variables=variables or None,
        detached=detached,
        monitor=monitor
    )


@workflow_group.command()
@click.argument("execution_id", required=False)
@click.option("--list", "-l", "list_all", is_flag=True, help="List all executions")
@click.option("--running", "-r", is_flag=True, help="Show only running executions")
def status(execution_id: str | None, list_all: bool, running: bool) -> None:
    """Check workflow execution status."""
    if not execution_id and not list_all and not running:
        list_all = True  # Default behavior

    command = WorkflowStatusCommand()
    command.run(execution_id=execution_id, list_all=list_all, running_only=running)


@workflow_group.command()
@click.argument("execution_id")
def cancel(execution_id: str) -> None:
    """Cancel running workflow execution."""
    command = WorkflowCancelCommand()
    command.run(execution_id=execution_id)


# Export the group
__all__ = ["workflow_group"]
