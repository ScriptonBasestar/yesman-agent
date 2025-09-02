import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from libs.core.error_handling import ErrorCategory, YesmanError
from libs.core.services import get_workflow_execution_engine, get_workflow_service
from libs.workflows.execution_engine import WorkflowExecutionEngine
from libs.workflows.models import WorkflowExecution
from libs.workflows.workflow_service import WorkflowService

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Workflow management API endpoints with dependency injection and proper error handling."""

# Set up logger
logger = logging.getLogger("yesman.api.workflows")


# Request/Response models
class WorkflowStartRequest(BaseModel):
    """Request model for starting a workflow."""

    template_id: str
    project_path: str | None = None
    variables: dict[str, str] | None = None
    detached: bool = True


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""

    execution_id: str
    status: str
    template_id: str
    project_path: str | None = None
    current_step: int | None = None
    progress: float
    created_at: str
    updated_at: str
    error: str | None = None


class WorkflowTemplateResponse(BaseModel):
    """Response model for workflow templates."""

    template_id: str
    name: str
    description: str
    steps_count: int
    variables: list[str]


class WorkflowAPIService:
    """Service class for workflow API operations."""

    def __init__(self, workflow_service: WorkflowService, execution_engine: WorkflowExecutionEngine) -> None:
        self.workflow_service = workflow_service
        self.execution_engine = execution_engine
        self.logger = logging.getLogger("yesman.api.workflows.service")

    def get_all_templates(self) -> list[WorkflowTemplateResponse]:
        """Get all available workflow templates.

        Returns:
            List[WorkflowTemplateResponse]: List of workflow templates.

        Raises:
            YesmanError: If templates cannot be retrieved.
        """
        try:
            templates = self.workflow_service.list_templates()
            result = []

            for template_id, template_data in templates.items():
                # Get template configuration
                config = self.workflow_service.get_template_config(template_id)
                if config:
                    # Extract variables from config
                    variables = []
                    for step in config.steps:
                        if isinstance(step, dict) and "variables" in step:
                            variables.extend(step["variables"])

                    result.append(
                        WorkflowTemplateResponse(
                            template_id=template_id,
                            name=template_data.get("name", template_id),
                            description=template_data.get("description", ""),
                            steps_count=len(config.steps),
                            variables=list(set(variables)),  # Remove duplicates
                        )
                    )

            return result
        except Exception as e:
            self.logger.exception("Failed to get workflow templates")
            msg = "Failed to retrieve workflow templates"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def get_template_by_id(self, template_id: str) -> WorkflowTemplateResponse | None:
        """Get specific workflow template by ID.

        Returns:
            WorkflowTemplateResponse | None: Template data if found, None otherwise.

        Raises:
            YesmanError: If template retrieval fails.
        """
        try:
            templates = self.workflow_service.list_templates()
            if template_id not in templates:
                return None

            template_data = templates[template_id]
            config = self.workflow_service.get_template_config(template_id)

            if not config:
                return None

            # Extract variables from config
            variables = []
            for step in config.steps:
                if isinstance(step, dict) and "variables" in step:
                    variables.extend(step["variables"])

            return WorkflowTemplateResponse(
                template_id=template_id,
                name=template_data.get("name", template_id),
                description=template_data.get("description", ""),
                steps_count=len(config.steps),
                variables=list(set(variables)),  # Remove duplicates
            )
        except Exception as e:
            self.logger.exception(f"Failed to get workflow template {template_id}")
            msg = f"Failed to retrieve workflow template '{template_id}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def start_workflow(self, request: WorkflowStartRequest) -> WorkflowExecutionResponse:
        """Start a workflow execution.

        Returns:
            WorkflowExecutionResponse: Started workflow execution details.

        Raises:
            YesmanError: If workflow start fails.
        """
        try:
            # Prepare project path
            project_path = Path(request.project_path) if request.project_path else Path.cwd()

            # Start workflow
            execution_id = self.workflow_service.start_workflow(template_id=request.template_id, project_path=project_path, variables=request.variables or {}, detached=request.detached)

            # Get execution details
            execution = self.workflow_service.get_execution(execution_id)
            if not execution:
                raise YesmanError(f"Failed to retrieve started workflow execution {execution_id}", category=ErrorCategory.SYSTEM)

            return self._convert_execution_to_response(execution)

        except YesmanError:
            raise
        except Exception as e:
            self.logger.exception(f"Failed to start workflow {request.template_id}")
            msg = f"Failed to start workflow '{request.template_id}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def get_all_executions(self) -> list[WorkflowExecutionResponse]:
        """Get all workflow executions.

        Returns:
            List[WorkflowExecutionResponse]: List of all workflow executions.

        Raises:
            YesmanError: If executions cannot be retrieved.
        """
        try:
            executions = self.workflow_service.list_executions()
            return [self._convert_execution_to_response(execution) for execution in executions]
        except Exception as e:
            self.logger.exception("Failed to get workflow executions")
            msg = "Failed to retrieve workflow executions"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def get_execution_by_id(self, execution_id: str) -> WorkflowExecutionResponse | None:
        """Get specific workflow execution by ID.

        Returns:
            WorkflowExecutionResponse | None: Execution data if found, None otherwise.

        Raises:
            YesmanError: If execution retrieval fails.
        """
        try:
            execution = self.workflow_service.get_execution(execution_id)
            if not execution:
                return None

            return self._convert_execution_to_response(execution)
        except Exception as e:
            self.logger.exception(f"Failed to get workflow execution {execution_id}")
            msg = f"Failed to retrieve workflow execution '{execution_id}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def cancel_execution(self, execution_id: str) -> dict[str, Any]:
        """Cancel a workflow execution.

        Returns:
            Dict[str, Any]: Cancellation result.

        Raises:
            YesmanError: If cancellation fails.
        """
        try:
            success = self.workflow_service.cancel_workflow(execution_id)

            return {"execution_id": execution_id, "cancelled": success, "message": "Workflow cancellation requested" if success else "Failed to cancel workflow"}
        except Exception as e:
            self.logger.exception(f"Failed to cancel workflow execution {execution_id}")
            msg = f"Failed to cancel workflow execution '{execution_id}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def get_execution_logs(self, execution_id: str) -> dict[str, Any]:
        """Get execution logs for a workflow.

        Returns:
            Dict[str, Any]: Execution logs and progress details.

        Raises:
            YesmanError: If logs retrieval fails.
        """
        try:
            execution = self.workflow_service.get_execution(execution_id)
            if not execution:
                raise YesmanError(f"Workflow execution '{execution_id}' not found", category=ErrorCategory.VALIDATION)

            return {
                "execution_id": execution_id,
                "status": execution.status.value,
                "progress": execution.get_progress(),
                "current_step": execution.current_step,
                "total_steps": len(execution.config.steps),
                "steps": [
                    {
                        "index": i,
                        "id": step.get("id", f"step_{i}"),
                        "name": step.get("name", f"Step {i + 1}"),
                        "status": "completed" if i < (execution.current_step or 0) else "running" if i == (execution.current_step or 0) else "pending",
                    }
                    for i, step in enumerate(execution.config.steps)
                ],
                "error": execution.error,
                "created_at": execution.created_at.isoformat(),
                "updated_at": execution.updated_at.isoformat(),
            }
        except YesmanError:
            raise
        except Exception as e:
            self.logger.exception(f"Failed to get execution logs {execution_id}")
            msg = f"Failed to retrieve execution logs '{execution_id}'"
            raise YesmanError(
                msg,
                category=ErrorCategory.SYSTEM,
                cause=e,
            )

    def _convert_execution_to_response(self, execution: WorkflowExecution) -> WorkflowExecutionResponse:
        """Convert WorkflowExecution to API response format.

        Returns:
            WorkflowExecutionResponse: Converted execution data.
        """
        return WorkflowExecutionResponse(
            execution_id=execution.execution_id,
            status=execution.status.value,
            template_id=execution.template_id,
            project_path=str(execution.project_path) if execution.project_path else None,
            current_step=execution.current_step,
            progress=execution.get_progress(),
            created_at=execution.created_at.isoformat(),
            updated_at=execution.updated_at.isoformat(),
            error=execution.error,
        )


# Router with dependency injection
router = APIRouter(tags=["workflows"])


@router.get("/workflows/templates", response_model=list[WorkflowTemplateResponse], summary="Get all workflow templates", description="Retrieve information about all available workflow templates")
def get_all_templates() -> list[WorkflowTemplateResponse]:
    """Get all workflow templates.

    Returns:
        List[WorkflowTemplateResponse]: List of all workflow templates.

    Raises:
        HTTPException: If template retrieval fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        return service.get_all_templates()

    except YesmanError as e:
        logger.exception(f"YesmanError in get_all_templates: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_all_templates")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/workflows/templates/{template_id}", response_model=WorkflowTemplateResponse, summary="Get specific workflow template", description="Retrieve information about a specific workflow template"
)
def get_template(template_id: str) -> WorkflowTemplateResponse:
    """Get specific workflow template by ID.

    Returns:
        WorkflowTemplateResponse: Template information.

    Raises:
        HTTPException: If template not found or retrieval fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        template = service.get_template_by_id(template_id)

        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow template '{template_id}' not found")

        return template

    except HTTPException:
        raise
    except YesmanError as e:
        logger.exception(f"YesmanError in get_template: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_template")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/workflows/executions", response_model=WorkflowExecutionResponse, summary="Start workflow execution", description="Start a new workflow execution")
def start_workflow(request: WorkflowStartRequest) -> WorkflowExecutionResponse:
    """Start a new workflow execution.

    Returns:
        WorkflowExecutionResponse: Started workflow execution details.

    Raises:
        HTTPException: If workflow start fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        return service.start_workflow(request)

    except YesmanError as e:
        logger.exception(f"YesmanError in start_workflow: {e.message}")
        status_code = status.HTTP_400_BAD_REQUEST if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in start_workflow")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/workflows/executions", response_model=list[WorkflowExecutionResponse], summary="Get all workflow executions", description="Retrieve information about all workflow executions")
def get_all_executions() -> list[WorkflowExecutionResponse]:
    """Get all workflow executions.

    Returns:
        List[WorkflowExecutionResponse]: List of all workflow executions.

    Raises:
        HTTPException: If executions retrieval fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        return service.get_all_executions()

    except YesmanError as e:
        logger.exception(f"YesmanError in get_all_executions: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_all_executions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/workflows/executions/{execution_id}", response_model=WorkflowExecutionResponse, summary="Get specific workflow execution", description="Retrieve information about a specific workflow execution"
)
def get_execution(execution_id: str) -> WorkflowExecutionResponse:
    """Get specific workflow execution by ID.

    Returns:
        WorkflowExecutionResponse: Execution information.

    Raises:
        HTTPException: If execution not found or retrieval fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        execution = service.get_execution_by_id(execution_id)

        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow execution '{execution_id}' not found")

        return execution

    except HTTPException:
        raise
    except YesmanError as e:
        logger.exception(f"YesmanError in get_execution: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
        )
    except Exception:
        logger.exception("Unexpected error in get_execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/workflows/executions/{execution_id}/cancel", summary="Cancel workflow execution", description="Cancel a running workflow execution")
def cancel_execution(execution_id: str) -> dict[str, Any]:
    """Cancel a workflow execution.

    Returns:
        dict: Cancellation result.

    Raises:
        HTTPException: If cancellation fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        return service.cancel_execution(execution_id)

    except YesmanError as e:
        logger.exception(f"YesmanError in cancel_execution: {e.message}")
        status_code = status.HTTP_404_NOT_FOUND if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in cancel_execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/workflows/executions/{execution_id}/logs", summary="Get execution logs", description="Get detailed logs and progress for a workflow execution")
def get_execution_logs(execution_id: str) -> dict[str, Any]:
    """Get execution logs for a workflow.

    Returns:
        dict: Execution logs and progress details.

    Raises:
        HTTPException: If logs retrieval fails.
    """
    try:
        workflow_service = get_workflow_service()
        execution_engine = get_workflow_execution_engine()
        service = WorkflowAPIService(workflow_service, execution_engine)
        return service.get_execution_logs(execution_id)

    except YesmanError as e:
        logger.exception(f"YesmanError in get_execution_logs: {e.message}")
        status_code = status.HTTP_404_NOT_FOUND if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception:
        logger.exception("Unexpected error in get_execution_logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
