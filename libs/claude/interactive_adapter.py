"""Interactive Claude Code adapter implementation for backward compatibility."""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from libs.core.claude_manager import DashboardController

from .interfaces import (
    AgentConfig,
    AgentEvent,
    AgentInfo,
    AgentStatus,
    EventType,
    TaskOptions,
)


class InteractiveAdapter:
    """Interactive Claude Code adapter wrapping existing tmux-based system."""

    def __init__(self, claude_manager=None) -> None:
        """Initialize interactive adapter.

        Args:
            claude_manager: Existing Claude manager instance (optional)
        """
        self.claude_manager = claude_manager
        self.logger = logging.getLogger(f"{__name__}.InteractiveAdapter")

        # Track session-based agents
        self.session_agents = {}  # session_name -> agent_info
        self.controllers = {}  # agent_id -> DashboardController

    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new Claude agent using existing session system.

        Args:
            config: Agent configuration

        Returns:
            Agent ID (session name)

        Raises:
            RuntimeError: If agent creation fails
        """
        try:
            # Generate unique session name
            session_name = f"claude-agent-{uuid.uuid4().hex[:8]}"

            # Create controller using existing system
            controller = DashboardController(session_name)

            # Start the controller
            if not controller.start():
                raise RuntimeError(f"Failed to start controller for session {session_name}")

            # Create agent info
            agent_info = AgentInfo(
                agent_id=session_name,
                config=config,
                status=AgentStatus.CREATED,
                created_at=datetime.now().isoformat(),
            )

            # Store mappings
            self.session_agents[session_name] = agent_info
            self.controllers[session_name] = controller

            self.logger.info(f"Created interactive agent {session_name}")
            return session_name

        except Exception as e:
            self.logger.exception("Failed to create interactive agent")
            raise RuntimeError(f"Agent creation failed: {e}") from e

    async def run_task(
        self,
        agent_id: str,
        prompt: str,
        options: TaskOptions | None = None,
    ) -> str:
        """Run a task on the specified agent.

        Args:
            agent_id: Agent identifier (session name)
            prompt: Task prompt
            options: Task execution options

        Returns:
            Run ID for tracking the task

        Raises:
            ValueError: If agent not found
            RuntimeError: If task execution fails
        """
        if agent_id not in self.session_agents:
            raise ValueError(f"Agent {agent_id} not found")

        controller = self.controllers.get(agent_id)
        if not controller:
            raise RuntimeError(f"Controller not found for agent {agent_id}")

        run_id = str(uuid.uuid4())

        try:
            # Use existing controller to send prompt
            # This is a simplified implementation - in real usage,
            # you would integrate with the existing prompt detection and sending system

            # Update agent status
            agent_info = self.session_agents[agent_id]
            agent_info.status = AgentStatus.RUNNING
            agent_info.current_run_id = run_id
            agent_info.last_activity = datetime.now().isoformat()

            # Send prompt through existing system
            # Note: This is a placeholder - actual implementation would depend
            # on how the existing system handles prompt sending
            if hasattr(controller, "session_manager"):
                controller.session_manager.send_keys(prompt)
                controller.session_manager.send_keys("Enter")

            self.logger.info(f"Started task {run_id} for interactive agent {agent_id}")
            return run_id

        except Exception as e:
            self.logger.exception(f"Failed to start task for agent {agent_id}")
            agent_info.status = AgentStatus.ERROR
            agent_info.error_message = str(e)
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
        if agent_id not in self.session_agents:
            raise ValueError(f"Agent {agent_id} not found")

        controller = self.controllers.get(agent_id)
        if not controller:
            return

        # This is a simplified event streaming implementation
        # In a real implementation, you would integrate with the existing
        # monitoring and event system

        while agent_id in self.session_agents:
            try:
                # Simulate event streaming by checking controller status
                await asyncio.sleep(1)

                # Check if controller is still running
                if controller.is_running:
                    yield AgentEvent.create(
                        event_type=EventType.LOG,
                        data={"message": "Controller is running"},
                        agent_id=agent_id,
                    )

                # You would integrate with the existing status and activity callbacks here

            except Exception as e:
                self.logger.exception(f"Error streaming events for agent {agent_id}")
                yield AgentEvent.create(
                    event_type=EventType.ERROR,
                    data={"error": str(e)},
                    agent_id=agent_id,
                )
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
        if agent_id not in self.session_agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent_info = self.session_agents[agent_id]
        if agent_info.current_run_id != run_id:
            raise ValueError(f"Run {run_id} not found for agent {agent_id}")

        controller = self.controllers.get(agent_id)
        if not controller:
            return False

        try:
            # Send interrupt signal through existing system
            if hasattr(controller, "session_manager"):
                controller.session_manager.send_keys("C-c")  # Ctrl+C

            # Update agent status
            agent_info.status = AgentStatus.IDLE
            agent_info.current_run_id = None
            agent_info.last_activity = datetime.now().isoformat()

            self.logger.info(f"Cancelled task {run_id} for agent {agent_id}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to cancel task {run_id} for agent {agent_id}")
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
        if agent_id not in self.session_agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent_info = self.session_agents[agent_id]

        # Update status based on controller state
        controller = self.controllers.get(agent_id)
        if controller:
            if controller.is_running and agent_info.status == AgentStatus.CREATED:
                agent_info.status = AgentStatus.IDLE
            elif not controller.is_running and agent_info.status != AgentStatus.DISPOSED:
                agent_info.status = AgentStatus.ERROR
                agent_info.error_message = "Controller not running"

        return agent_info

    async def list_agents(self) -> list[AgentInfo]:
        """List all active agents.

        Returns:
            List of agent information
        """
        # Update statuses before returning
        for agent_id in list(self.session_agents.keys()):
            try:
                await self.get_status(agent_id)
            except Exception as e:
                self.logger.warning(f"Failed to get status for agent {agent_id}: {e}")

        return list(self.session_agents.values())

    async def dispose_agent(self, agent_id: str) -> bool:
        """Dispose of an agent and clean up resources.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was disposed successfully

        Raises:
            ValueError: If agent not found
        """
        if agent_id not in self.session_agents:
            raise ValueError(f"Agent {agent_id} not found")

        try:
            # Stop controller if running
            controller = self.controllers.get(agent_id)
            if controller:
                try:
                    controller.stop()
                except Exception as e:
                    self.logger.warning(f"Error stopping controller for agent {agent_id}: {e}")

            # Clean up session using existing system
            if self.claude_manager and hasattr(self.claude_manager, "remove_controller"):
                try:
                    self.claude_manager.remove_controller(agent_id)
                except Exception as e:
                    self.logger.warning(f"Error removing controller from manager: {e}")

            # Remove from tracking
            del self.session_agents[agent_id]
            if agent_id in self.controllers:
                del self.controllers[agent_id]

            self.logger.info(f"Disposed interactive agent {agent_id}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to dispose agent {agent_id}")
            return False

    async def shutdown(self) -> None:
        """Shutdown adapter and clean up all resources."""
        agent_ids = list(self.session_agents.keys())
        for agent_id in agent_ids:
            try:
                await self.dispose_agent(agent_id)
            except Exception as e:
                self.logger.exception(f"Error disposing agent {agent_id} during shutdown")

        self.logger.info("Interactive adapter shutdown complete")
