"""Headless Claude Code adapter implementation."""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from .interfaces import (
    AgentConfig,
    AgentEvent,
    AgentInfo,
    AgentStatus,
    EventType,
    TaskOptions,
)
from .workspace import DefaultWorkspaceManager


@dataclass
class AgentProcess:
    """Agent process information."""

    agent_id: str
    config: AgentConfig
    workspace_path: Path
    status: AgentStatus
    created_at: str
    current_process: Optional[asyncio.subprocess.Process] = None
    current_run_id: Optional[str] = None
    last_activity: Optional[str] = None
    error_message: Optional[str] = None
    event_queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now().isoformat()

    def to_agent_info(self) -> AgentInfo:
        """Convert to AgentInfo."""
        return AgentInfo(
            agent_id=self.agent_id,
            config=self.config,
            status=self.status,
            created_at=self.created_at,
            last_activity=self.last_activity,
            current_run_id=self.current_run_id,
            error_message=self.error_message,
        )


class HeadlessAdapter:
    """Headless Claude Code adapter implementation."""

    def __init__(
        self,
        workspace_manager: DefaultWorkspaceManager,
        claude_binary: str = "claude",
        max_concurrent: int = 5,
    ):
        """Initialize headless adapter.

        Args:
            workspace_manager: Workspace manager instance
            claude_binary: Path to claude binary
            max_concurrent: Maximum concurrent agents
        """
        self.workspace_manager = workspace_manager
        self.claude_binary = claude_binary
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(f"{__name__}.HeadlessAdapter")

        # Track active agents
        self.active_agents: Dict[str, AgentProcess] = {}
        self._shutdown_event = asyncio.Event()

        # Start background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new Claude agent.

        Args:
            config: Agent configuration

        Returns:
            Agent ID

        Raises:
            RuntimeError: If too many agents or creation fails
        """
        if len(self.active_agents) >= self.max_concurrent:
            raise RuntimeError(f"Maximum concurrent agents limit reached ({self.max_concurrent})")

        agent_id = str(uuid.uuid4())

        try:
            # Create sandbox workspace
            workspace_path = self.workspace_manager.create_sandbox(agent_id)

            # Create agent process info
            agent_process = AgentProcess(
                agent_id=agent_id,
                config=config,
                workspace_path=workspace_path,
                status=AgentStatus.CREATED,
                created_at=datetime.now().isoformat(),
            )

            # Store agent
            self.active_agents[agent_id] = agent_process

            # Emit creation event
            await self._emit_event(
                agent_process,
                EventType.STATUS_CHANGE,
                {"status": AgentStatus.CREATED.value, "message": "Agent created"},
            )

            self.logger.info(f"Created agent {agent_id} with workspace {workspace_path}")
            return agent_id

        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}")
            # Cleanup if partially created
            if agent_id in self.active_agents:
                await self.dispose_agent(agent_id)
            raise RuntimeError(f"Agent creation failed: {e}") from e

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
            ValueError: If agent not found
            RuntimeError: If task execution fails
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if agent.status == AgentStatus.RUNNING:
            raise RuntimeError(f"Agent {agent_id} is already running a task")

        run_id = str(uuid.uuid4())

        try:
            # Merge options with agent config
            if options is None:
                options = TaskOptions()
            merged_options = options.merge_with_config(agent.config)

            # Build command
            cmd = await self._build_command(agent, prompt, merged_options, run_id)

            # Prepare environment for subprocess
            env = os.environ.copy()

            # Ensure Claude CLI can access authentication
            # The subprocess will inherit the current environment

            # Start process
            agent.current_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=agent.workspace_path,
                env=env,
            )

            # Update agent state
            agent.status = AgentStatus.RUNNING
            agent.current_run_id = run_id
            agent.update_activity()

            # Start monitoring task
            asyncio.create_task(self._monitor_process(agent))

            # Emit start event
            await self._emit_event(
                agent,
                EventType.TASK_START,
                {"run_id": run_id, "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt},
                run_id,
            )

            self.logger.info(f"Started task {run_id} for agent {agent_id}")
            return run_id

        except Exception as e:
            self.logger.error(f"Failed to start task for agent {agent_id}: {e}")
            agent.status = AgentStatus.ERROR
            agent.error_message = str(e)
            raise RuntimeError(f"Task execution failed: {e}") from e

    async def stream_events(self, agent_id: str) -> AsyncIterator[AgentEvent]:
        """Stream events from the specified agent.

        Args:
            agent_id: Agent identifier

        Yields:
            Agent events as they occur

        Raises:
            ValueError: If agent not found
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        while agent_id in self.active_agents and not self._shutdown_event.is_set():
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(agent.event_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error streaming events for agent {agent_id}: {e}")
                break

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
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if agent.current_run_id != run_id:
            raise ValueError(f"Run {run_id} not found for agent {agent_id}")

        try:
            if agent.current_process and agent.current_process.returncode is None:
                # Send SIGTERM first
                agent.current_process.terminate()

                try:
                    # Wait for graceful termination
                    await asyncio.wait_for(agent.current_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if needed
                    agent.current_process.kill()
                    await agent.current_process.wait()

                # Update status
                agent.status = AgentStatus.IDLE
                agent.current_run_id = None
                agent.update_activity()

                # Emit cancellation event
                await self._emit_event(
                    agent,
                    EventType.STATUS_CHANGE,
                    {"status": AgentStatus.IDLE.value, "message": "Task cancelled"},
                    run_id,
                )

                self.logger.info(f"Cancelled task {run_id} for agent {agent_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to cancel task {run_id} for agent {agent_id}: {e}")
            return False

    async def get_status(self, agent_id: str) -> AgentInfo:
        """Get agent status and information.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent information

        Raises:
            ValueError: If agent not found
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        return agent.to_agent_info()

    async def list_agents(self) -> List[AgentInfo]:
        """List all active agents.

        Returns:
            List of agent information
        """
        return [agent.to_agent_info() for agent in self.active_agents.values()]

    async def dispose_agent(self, agent_id: str) -> bool:
        """Dispose of an agent and clean up resources.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was disposed successfully

        Raises:
            ValueError: If agent not found
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        try:
            # Cancel any running task
            if agent.current_run_id:
                await self.cancel_task(agent_id, agent.current_run_id)

            # Clean up workspace
            self.workspace_manager.cleanup_sandbox(agent_id)

            # Remove from active agents
            del self.active_agents[agent_id]

            # Emit disposal event
            await self._emit_event(
                agent,
                EventType.STATUS_CHANGE,
                {"status": AgentStatus.DISPOSED.value, "message": "Agent disposed"},
            )

            self.logger.info(f"Disposed agent {agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to dispose agent {agent_id}: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown adapter and clean up all resources."""
        self._shutdown_event.set()

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Dispose all agents
        agent_ids = list(self.active_agents.keys())
        for agent_id in agent_ids:
            try:
                await self.dispose_agent(agent_id)
            except Exception as e:
                self.logger.error(f"Error disposing agent {agent_id} during shutdown: {e}")

        self.logger.info("Headless adapter shutdown complete")

    async def _build_command(
        self,
        agent: AgentProcess,
        prompt: str,
        options: TaskOptions,
        run_id: str,
    ) -> List[str]:
        """Build command for Claude execution.

        Args:
            agent: Agent process info
            prompt: Task prompt
            options: Task options
            run_id: Run identifier

        Returns:
            Command arguments
        """
        cmd = [
            self.claude_binary,
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        # Add tools if specified
        # Temporarily disabled to ensure Claude CLI works properly
        # if options.tools:
        #     cmd.extend(["--allowedTools", ",".join(options.tools)])

        # Add timeout if specified
        # Disabled - Claude CLI doesn't support --timeout option
        # if options.timeout:
        #     cmd.extend(["--timeout", str(options.timeout)])

        # Add session resumption
        if options.resume_session:
            session_file = agent.workspace_path / f"{agent.agent_id}.session"
            cmd.extend(["--resume", str(session_file)])

        return cmd

    async def _monitor_process(self, agent: AgentProcess) -> None:
        """Monitor agent process and handle events.

        Args:
            agent: Agent process to monitor
        """
        if not agent.current_process:
            return

        try:
            # Read stdout line by line
            while agent.current_process.returncode is None:
                try:
                    line = await asyncio.wait_for(agent.current_process.stdout.readline(), timeout=1.0)

                    if not line:
                        break

                    await self._process_output_line(agent, line.decode().strip())

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error reading process output: {e}")
                    break

            # Process completed
            return_code = agent.current_process.returncode

            # Read any remaining output
            try:
                remaining_stdout, remaining_stderr = await agent.current_process.communicate()
                if remaining_stdout:
                    for line in remaining_stdout.decode().splitlines():
                        await self._process_output_line(agent, line.strip())
                if remaining_stderr:
                    self.logger.warning(f"Agent {agent.agent_id} stderr: {remaining_stderr.decode()}")
            except Exception as e:
                self.logger.error(f"Error reading remaining output: {e}")

            # Update agent status
            if return_code == 0:
                agent.status = AgentStatus.IDLE
                await self._emit_event(
                    agent,
                    EventType.TASK_COMPLETE,
                    {"run_id": agent.current_run_id, "return_code": return_code},
                    agent.current_run_id,
                )
            else:
                agent.status = AgentStatus.ERROR
                agent.error_message = f"Process exited with code {return_code}"
                await self._emit_event(
                    agent,
                    EventType.ERROR,
                    {
                        "run_id": agent.current_run_id,
                        "return_code": return_code,
                        "error": agent.error_message,
                    },
                    agent.current_run_id,
                )

            agent.current_run_id = None
            agent.update_activity()

        except Exception as e:
            self.logger.error(f"Error monitoring process for agent {agent.agent_id}: {e}")
            agent.status = AgentStatus.ERROR
            agent.error_message = str(e)

    async def _process_output_line(self, agent: AgentProcess, line: str) -> None:
        """Process a line of output from Claude.

        Args:
            agent: Agent process
            line: Output line
        """
        if not line.strip():
            return

        try:
            # Try to parse as JSON
            data = json.loads(line)
            event_type = EventType(data.get("type", "log"))

            await self._emit_event(
                agent,
                event_type,
                data,
                agent.current_run_id,
            )

        except (json.JSONDecodeError, ValueError):
            # Not JSON, treat as log
            await self._emit_event(
                agent,
                EventType.LOG,
                {"message": line},
                agent.current_run_id,
            )

    async def _emit_event(
        self,
        agent: AgentProcess,
        event_type: EventType,
        data: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> None:
        """Emit an event for an agent.

        Args:
            agent: Agent process
            event_type: Type of event
            data: Event data
            run_id: Optional run identifier
        """
        event = AgentEvent.create(
            event_type=event_type,
            data=data,
            agent_id=agent.agent_id,
            run_id=run_id,
        )

        try:
            await agent.event_queue.put(event)
        except Exception as e:
            self.logger.error(f"Failed to emit event for agent {agent.agent_id}: {e}")

    def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_background())

    async def _cleanup_background(self) -> None:
        """Background cleanup task."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up orphaned sandboxes
                cleaned = self.workspace_manager.cleanup_orphaned_sandboxes()
                if cleaned > 0:
                    self.logger.info(f"Cleaned up {cleaned} orphaned sandboxes")

                # Check for zombie agents
                for agent_id, agent in list(self.active_agents.items()):
                    if agent.current_process and agent.current_process.returncode is not None and agent.status == AgentStatus.RUNNING:
                        # Process finished but status not updated
                        self.logger.warning(f"Found zombie agent {agent_id}, cleaning up")
                        agent.status = AgentStatus.ERROR
                        agent.error_message = "Process terminated unexpectedly"
                        agent.current_run_id = None

                # Wait before next cleanup
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                self.logger.error(f"Error in background cleanup: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
