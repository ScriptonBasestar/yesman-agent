"""Agent management API endpoints for Claude Code Headless integration."""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from libs.claude.interfaces import AgentConfig, TaskOptions
from libs.core.services import get_claude_service

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


# Request/Response Models


class AgentConfigRequest(BaseModel):
    """Request model for agent creation."""

    workspace_path: str
    model: str = "claude-3-5-sonnet-20241022"
    allowed_tools: list[str] = Field(default_factory=lambda: ["Read", "Edit", "Bash", "Write"])
    timeout: int = Field(default=300, ge=30, le=3600)
    max_tokens: int = Field(default=4000, ge=100, le=32000)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)

    def to_agent_config(self) -> AgentConfig:
        """Convert to AgentConfig."""
        from pathlib import Path

        return AgentConfig(
            workspace_path=Path(self.workspace_path),
            model=self.model,
            allowed_tools=self.allowed_tools,
            timeout=self.timeout,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )


class TaskRequest(BaseModel):
    """Request model for task execution."""

    prompt: str
    tools: list[str] | None = None
    timeout: int | None = Field(default=None, ge=30, le=3600)
    max_tokens: int | None = Field(default=None, ge=100, le=32000)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    resume_session: bool = True

    def to_task_options(self) -> TaskOptions:
        """Convert to TaskOptions."""
        return TaskOptions(
            tools=self.tools,
            timeout=self.timeout,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            resume_session=self.resume_session,
        )


class AgentResponse(BaseModel):
    """Response model for agent information."""

    agent_id: str
    status: str
    created_at: str
    workspace_path: str
    model: str
    allowed_tools: list[str]
    last_activity: str | None = None
    current_run_id: str | None = None
    error_message: str | None = None


class TaskResponse(BaseModel):
    """Response model for task execution."""

    run_id: str
    agent_id: str
    status: str


# API Endpoints


@router.post("/", response_model=str)
async def create_agent(config_request: AgentConfigRequest) -> str:
    """Create a new Claude agent.

    Args:
        config_request: Agent configuration

    Returns:
        Agent ID

    Raises:
        HTTPException: If agent creation fails
    """
    try:
        claude_service = get_claude_service()
        config = config_request.to_agent_config()
        agent_id = await claude_service.create_agent(config)

        logger.info(f"Created agent {agent_id}")
        return agent_id

    except ValueError as e:
        logger.warning(f"Invalid agent configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.exception("Agent creation failed")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error creating agent")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[AgentResponse])
async def list_agents() -> list[AgentResponse]:
    """List all active agents.

    Returns:
        List of agent information

    Raises:
        HTTPException: If listing fails
    """
    try:
        claude_service = get_claude_service()
        agents = await claude_service.list_agents()

        return [
            AgentResponse(
                agent_id=agent.agent_id,
                status=agent.status.value,
                created_at=agent.created_at,
                workspace_path=str(agent.config.workspace_path),
                model=agent.config.model,
                allowed_tools=agent.config.allowed_tools,
                last_activity=agent.last_activity,
                current_run_id=agent.current_run_id,
                error_message=agent.error_message,
            )
            for agent in agents
        ]

    except Exception as e:
        logger.exception("Failed to list agents")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for agents subsystem - must be before /{agent_id} route
@router.get("/health", include_in_schema=False)
async def agents_health() -> dict[str, str | int | float]:
    """Health check for agents subsystem.

    Returns:
        Health status
    """
    try:
        claude_service = get_claude_service()
        agents = await claude_service.list_agents()

        return {
            "status": "healthy",
            "agents_count": len(agents),
            "timestamp": asyncio.get_event_loop().time(),
        }

    except Exception as e:
        logger.exception("Agents health check failed")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time(),
        }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_status(agent_id: str) -> AgentResponse:
    """Get agent status and information.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent information

    Raises:
        HTTPException: If agent not found or retrieval fails
    """
    try:
        claude_service = get_claude_service()
        agent_info = await claude_service.get_status(agent_id)

        return AgentResponse(
            agent_id=agent_info.agent_id,
            status=agent_info.status.value,
            created_at=agent_info.created_at,
            workspace_path=str(agent_info.config.workspace_path),
            model=agent_info.config.model,
            allowed_tools=agent_info.config.allowed_tools,
            last_activity=agent_info.last_activity,
            current_run_id=agent_info.current_run_id,
            error_message=agent_info.error_message,
        )

    except ValueError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get agent status {agent_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/tasks", response_model=TaskResponse)
async def run_task(agent_id: str, task_request: TaskRequest) -> TaskResponse:
    """Run a task on the specified agent.

    Args:
        agent_id: Agent identifier
        task_request: Task configuration

    Returns:
        Task execution information

    Raises:
        HTTPException: If agent not found or task execution fails
    """
    try:
        claude_service = get_claude_service()
        options = task_request.to_task_options()
        run_id = await claude_service.run_task(agent_id, task_request.prompt, options)

        logger.info(f"Started task {run_id} for agent {agent_id}")
        return TaskResponse(run_id=run_id, agent_id=agent_id, status="running")

    except ValueError as e:
        logger.warning(f"Agent not found or invalid request: {agent_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.exception(f"Task execution failed for agent {agent_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error running task for agent {agent_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{agent_id}/events")
async def stream_events(agent_id: str) -> EventSourceResponse:
    """Stream real-time events from the specified agent.

    Args:
        agent_id: Agent identifier

    Returns:
        SSE stream of agent events

    Raises:
        HTTPException: If agent not found
    """
    try:
        claude_service = get_claude_service()

        # Check if agent exists
        await claude_service.get_status(agent_id)

        async def event_generator():
            """Generate SSE events from agent stream."""
            try:
                async for event in claude_service.stream_events(agent_id):
                    yield {
                        "event": event.event_type.value,
                        "data": json.dumps(event.to_dict()),
                        "id": f"{event.agent_id}-{event.timestamp}",
                    }
            except Exception as e:
                logger.exception(f"Error streaming events for agent {agent_id}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }

        return EventSourceResponse(event_generator())

    except ValueError as e:
        logger.warning(f"Agent not found for streaming: {agent_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to setup event stream for agent {agent_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/cancel/{run_id}")
async def cancel_task(agent_id: str, run_id: str) -> dict[str, str]:
    """Cancel a running task.

    Args:
        agent_id: Agent identifier
        run_id: Run identifier

    Returns:
        Cancellation result

    Raises:
        HTTPException: If agent/run not found or cancellation fails
    """
    try:
        claude_service = get_claude_service()
        success = await claude_service.cancel_task(agent_id, run_id)

        if success:
            logger.info(f"Cancelled task {run_id} for agent {agent_id}")
            return {"message": "Task cancelled successfully"}
        else:
            logger.warning(f"Failed to cancel task {run_id} for agent {agent_id}")
            return {"message": "Task cancellation failed"}

    except ValueError as e:
        logger.warning(f"Agent or run not found: {agent_id}/{run_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error cancelling task {run_id} for agent {agent_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{agent_id}")
async def dispose_agent(agent_id: str) -> dict[str, str]:
    """Dispose of an agent and clean up resources.

    Args:
        agent_id: Agent identifier

    Returns:
        Disposal result

    Raises:
        HTTPException: If agent not found or disposal fails
    """
    try:
        claude_service = get_claude_service()
        success = await claude_service.dispose_agent(agent_id)

        if success:
            logger.info(f"Disposed agent {agent_id}")
            return {"message": "Agent disposed successfully"}
        else:
            logger.warning(f"Failed to dispose agent {agent_id}")
            raise HTTPException(status_code=500, detail="Agent disposal failed")

    except ValueError as e:
        logger.warning(f"Agent not found for disposal: {agent_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error disposing agent {agent_id}")
        raise HTTPException(status_code=500, detail="Internal server error")
