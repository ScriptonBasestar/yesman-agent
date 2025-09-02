"""Workflow service for managing LangChain workflow executions."""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from libs.core.error_handling import ErrorCategory, YesmanError
from libs.workflows.execution_engine import AsyncWorkflowExecutionEngine
from libs.workflows.models import WorkflowConfig, WorkflowExecution, WorkflowStatus
from libs.workflows.template_manager import WorkflowTemplateManager


class WorkflowServiceError(YesmanError):
    """Workflow service specific errors."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(
            message=message,
            category=ErrorCategory.SERVICE,
            **kwargs
        )


class WorkflowService:
    """Service for managing workflow templates and executions."""

    def __init__(self, execution_engine: AsyncWorkflowExecutionEngine, template_manager: WorkflowTemplateManager | None = None) -> None:
        self.execution_engine = execution_engine
        self.executions: dict[str, WorkflowExecution] = {}
        self.template_manager = template_manager or WorkflowTemplateManager()
        self.logger = logging.getLogger("yesman.workflows.service")

        # Initialize template directories
        self.template_manager.create_template_directories()

    def list_templates(self) -> dict[str, dict[str, Any]]:
        """List all available workflow templates."""
        return self.template_manager.list_templates()

    def get_template_config(self, template_id: str) -> WorkflowConfig | None:
        """Get workflow configuration for a template."""
        return self.template_manager.get_template_config(template_id)

    def save_template(self, template_id: str, name: str, description: str,
                     steps: list[dict[str, Any]], **kwargs) -> Path:
        """Save a new workflow template."""
        template_data = self.template_manager.create_template_from_config(
            template_id, name, description, steps, **kwargs
        )
        return self.template_manager.save_template(template_id, template_data)

    def delete_template(self, template_id: str, user_template: bool = True) -> bool:
        """Delete a workflow template."""
        return self.template_manager.delete_template(template_id, user_template)

    def validate_template(self, template_data: dict[str, Any]) -> list[str]:
        """Validate template configuration."""
        return self.template_manager.validate_template(template_data)

    async def start_workflow(self, template_id: str, context: dict[str, Any] | None = None) -> str:
        """Start a new workflow execution."""
        config = self.get_template_config(template_id)
        if not config:
            raise WorkflowServiceError(f"Template not found: {template_id}")

        # Create execution instance
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            template_id=template_id,
            config=config,
            context=context or {},
            status=WorkflowStatus.PENDING,
            created_at=datetime.now(UTC)
        )

        # Store execution
        self.executions[execution.id] = execution

        try:
            # Start execution
            await self.execution_engine.start_workflow(execution)
            self.logger.info(f"Started workflow execution: {execution.id} (template: {template_id})")
            return execution.id

        except Exception as e:
            # Remove failed execution
            self.executions.pop(execution.id, None)
            raise WorkflowServiceError(f"Failed to start workflow: {e}")

    def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        """Get workflow execution by ID."""
        return self.executions.get(execution_id)

    def list_executions(self, status_filter: WorkflowStatus | None = None) -> list[WorkflowExecution]:
        """List all workflow executions."""
        executions = list(self.executions.values())

        if status_filter:
            executions = [e for e in executions if e.status == status_filter]

        # Sort by creation time, most recent first
        return sorted(executions, key=lambda e: e.created_at, reverse=True)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return False

        if execution.status not in {WorkflowStatus.PENDING, WorkflowStatus.RUNNING}:
            return False

        try:
            success = await self.execution_engine.cancel_workflow(execution_id)
            if success:
                execution.status = WorkflowStatus.CANCELLED
                execution.completed_at = datetime.now(UTC)
                self.logger.info(f"Cancelled workflow execution: {execution_id}")

            return success

        except Exception as e:
            self.logger.exception(f"Failed to cancel execution {execution_id}")
            return False

    def get_execution_status(self, execution_id: str) -> dict[str, Any] | None:
        """Get detailed status of workflow execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return None

        return {
            "id": execution.id,
            "template_id": execution.template_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "progress": execution.progress,
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "results": execution.results,
            "errors": execution.errors,
            "checkpoints": execution.checkpoints
        }

    def cleanup_completed_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old completed executions."""
        from datetime import timedelta

        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
        cleaned_count = 0

        # Find executions to clean up
        to_remove = []
        for execution_id, execution in self.executions.items():
            if execution.status in {WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED}:
                if execution.completed_at and execution.completed_at < cutoff_time:
                    to_remove.append(execution_id)

        # Remove them
        for execution_id in to_remove:
            self.executions.pop(execution_id, None)
            cleaned_count += 1

        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old workflow executions")

        return cleaned_count
