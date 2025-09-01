"""Claude Code integration interfaces and protocols."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol


class AgentStatus(Enum):
    """Agent lifecycle status."""

    CREATED = "created"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    DISPOSED = "disposed"


class EventType(Enum):
    """Agent event types."""

    TOOL_CALL = "tool_call"
    EDIT = "edit"
    LOG = "log"
    STATUS_CHANGE = "status_change"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    ERROR = "error"


@dataclass
class AgentEvent:
    """Agent event data structure."""

    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    agent_id: str
    run_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        event_type: EventType,
        data: Dict[str, Any],
        agent_id: str,
        run_id: Optional[str] = None,
    ) -> AgentEvent:
        """Create a new event with current timestamp."""
        return cls(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data=data,
            agent_id=agent_id,
            run_id=run_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "agent_id": self.agent_id,
            "run_id": self.run_id,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class AgentConfig:
    """Agent configuration."""

    workspace_path: Path
    model: str = "claude-3-5-sonnet-20241022"
    allowed_tools: List[str] = field(default_factory=lambda: ["Read", "Edit", "Bash"])
    timeout: int = 300  # seconds
    max_tokens: int = 4000
    temperature: float = 0.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.workspace_path = Path(self.workspace_path).resolve()
        if not self.workspace_path.exists():
            raise ValueError(f"Workspace path does not exist: {self.workspace_path}")

        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")

        if not 0 <= self.temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")


@dataclass
class TaskOptions:
    """Options for task execution."""

    tools: Optional[List[str]] = None
    timeout: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    resume_session: bool = True

    def merge_with_config(self, config: AgentConfig) -> TaskOptions:
        """Merge with agent config, with options taking precedence."""
        return TaskOptions(
            tools=self.tools or config.allowed_tools,
            timeout=self.timeout or config.timeout,
            max_tokens=self.max_tokens or config.max_tokens,
            temperature=self.temperature if self.temperature is not None else config.temperature,
            resume_session=self.resume_session,
        )


@dataclass
class AgentInfo:
    """Agent information."""

    agent_id: str
    config: AgentConfig
    status: AgentStatus
    created_at: str
    last_activity: Optional[str] = None
    current_run_id: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_id": self.agent_id,
            "config": {
                "workspace_path": str(self.config.workspace_path),
                "model": self.config.model,
                "allowed_tools": self.config.allowed_tools,
                "timeout": self.config.timeout,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
            "status": self.status.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "current_run_id": self.current_run_id,
            "error_message": self.error_message,
        }


class ClaudeAgentService(Protocol):
    """Protocol for Claude agent service implementations."""

    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new Claude agent.

        Args:
            config: Agent configuration

        Returns:
            Agent ID

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If agent creation fails
        """
        ...

    async def run_task(
        self,
        agent_id: str,
        prompt: str,
        options: Optional[TaskOptions] = None,
    ) -> str:
        """Run a task on the specified agent.

        Args:
            agent_id: Agent identifier
            prompt: Task prompt
            options: Task execution options

        Returns:
            Run ID for tracking the task

        Raises:
            ValueError: If agent not found or invalid parameters
            RuntimeError: If task execution fails
        """
        ...

    async def stream_events(self, agent_id: str) -> AsyncIterator[AgentEvent]:
        """Stream events from the specified agent.

        Args:
            agent_id: Agent identifier

        Yields:
            Agent events as they occur

        Raises:
            ValueError: If agent not found
        """
        ...

    async def cancel_task(self, agent_id: str, run_id: str) -> bool:
        """Cancel a running task.

        Args:
            agent_id: Agent identifier
            run_id: Run identifier

        Returns:
            True if task was cancelled successfully

        Raises:
            ValueError: If agent or run not found
        """
        ...

    async def get_status(self, agent_id: str) -> AgentInfo:
        """Get agent status and information.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent information

        Raises:
            ValueError: If agent not found
        """
        ...

    async def list_agents(self) -> List[AgentInfo]:
        """List all active agents.

        Returns:
            List of agent information
        """
        ...

    async def dispose_agent(self, agent_id: str) -> bool:
        """Dispose of an agent and clean up resources.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was disposed successfully

        Raises:
            ValueError: If agent not found
        """
        ...


class WorkspaceManager(ABC):
    """Abstract workspace manager for agent sandboxing."""

    @abstractmethod
    def validate_path(self, path: Path) -> bool:
        """Validate if a path is accessible within security policy."""
        ...

    @abstractmethod
    def create_sandbox(self, agent_id: str) -> Path:
        """Create a sandboxed workspace for an agent."""
        ...

    @abstractmethod
    def cleanup_sandbox(self, agent_id: str) -> bool:
        """Clean up agent sandbox."""
        ...

    @abstractmethod
    def get_allowed_tools(self) -> List[str]:
        """Get list of allowed tools for agents."""
        ...


class SecurityPolicy(ABC):
    """Abstract security policy for agent operations."""

    @abstractmethod
    def validate_tool_access(self, tool: str, agent_id: str) -> bool:
        """Validate if an agent can use a specific tool."""
        ...

    @abstractmethod
    def validate_file_access(self, file_path: Path, agent_id: str) -> bool:
        """Validate if an agent can access a specific file."""
        ...

    @abstractmethod
    def validate_command_execution(self, command: str, agent_id: str) -> bool:
        """Validate if an agent can execute a specific command."""
        ...

    @abstractmethod
    def get_max_concurrent_agents(self) -> int:
        """Get maximum number of concurrent agents allowed."""
        ...
