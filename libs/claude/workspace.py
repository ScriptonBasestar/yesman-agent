"""Workspace management and security for Claude agents."""

import logging
import shutil
import uuid
from pathlib import Path
from typing import List, Set

from .interfaces import SecurityPolicy, WorkspaceManager


class DefaultWorkspaceManager(WorkspaceManager):
    """Default implementation of workspace manager with sandboxing."""

    def __init__(
        self,
        base_path: Path,
        allowed_paths: List[Path],
        security_policy: SecurityPolicy,
    ):
        """Initialize workspace manager.

        Args:
            base_path: Base path for agent sandboxes
            allowed_paths: List of paths agents can access
            security_policy: Security policy for validation
        """
        self.base_path = Path(base_path).resolve()
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]
        self.security_policy = security_policy
        self.logger = logging.getLogger(f"{__name__}.DefaultWorkspaceManager")

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Track active sandboxes
        self.active_sandboxes: Set[str] = set()

    def validate_path(self, path: Path) -> bool:
        """Validate if a path is accessible within security policy.

        Args:
            path: Path to validate

        Returns:
            True if path is accessible
        """
        try:
            resolved_path = Path(path).resolve()

            # Check against allowed paths
            for allowed in self.allowed_paths:
                if resolved_path.is_relative_to(allowed):
                    return True

            # Check if it's within an agent sandbox
            if resolved_path.is_relative_to(self.base_path):
                return True

            return False

        except (OSError, ValueError) as e:
            self.logger.warning(f"Path validation failed for {path}: {e}")
            return False

    def create_sandbox(self, agent_id: str) -> Path:
        """Create a sandboxed workspace for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Path to agent sandbox

        Raises:
            RuntimeError: If sandbox creation fails
        """
        try:
            # Create unique sandbox directory
            sandbox_name = f"agent-{agent_id}-{uuid.uuid4().hex[:8]}"
            sandbox_path = self.base_path / sandbox_name

            # Create sandbox directory
            sandbox_path.mkdir(parents=True, exist_ok=True)

            # Set up basic structure
            (sandbox_path / "workspace").mkdir(exist_ok=True)
            (sandbox_path / "logs").mkdir(exist_ok=True)
            (sandbox_path / "temp").mkdir(exist_ok=True)

            # Create .gitignore to avoid tracking temporary files
            gitignore = sandbox_path / ".gitignore"
            gitignore.write_text("logs/\ntemp/\n*.log\n*.tmp\n")

            # Track active sandbox
            self.active_sandboxes.add(agent_id)

            self.logger.info(f"Created sandbox for agent {agent_id} at {sandbox_path}")
            return sandbox_path

        except Exception as e:
            self.logger.error(f"Failed to create sandbox for agent {agent_id}: {e}")
            raise RuntimeError(f"Sandbox creation failed: {e}") from e

    def cleanup_sandbox(self, agent_id: str) -> bool:
        """Clean up agent sandbox.

        Args:
            agent_id: Agent identifier

        Returns:
            True if cleanup was successful
        """
        try:
            # Find sandbox by agent ID pattern
            pattern = f"agent-{agent_id}-*"
            sandbox_paths = list(self.base_path.glob(pattern))

            if not sandbox_paths:
                self.logger.warning(f"No sandbox found for agent {agent_id}")
                return False

            # Remove all matching sandboxes
            for sandbox_path in sandbox_paths:
                if sandbox_path.exists():
                    shutil.rmtree(sandbox_path)
                    self.logger.info(f"Removed sandbox {sandbox_path}")

            # Remove from active tracking
            self.active_sandboxes.discard(agent_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to cleanup sandbox for agent {agent_id}: {e}")
            return False

    def get_allowed_tools(self) -> List[str]:
        """Get list of allowed tools for agents.

        Returns:
            List of allowed tool names
        """
        # Return tools based on security policy
        default_tools = ["Read", "Edit", "Bash", "Write"]
        return [tool for tool in default_tools if self.security_policy.validate_tool_access(tool, "default")]

    def get_sandbox_path(self, agent_id: str) -> Path | None:
        """Get sandbox path for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Sandbox path if found, None otherwise
        """
        pattern = f"agent-{agent_id}-*"
        sandbox_paths = list(self.base_path.glob(pattern))
        return sandbox_paths[0] if sandbox_paths else None

    def list_active_sandboxes(self) -> List[str]:
        """List all active agent sandboxes.

        Returns:
            List of agent IDs with active sandboxes
        """
        return list(self.active_sandboxes)

    def cleanup_orphaned_sandboxes(self) -> int:
        """Clean up sandboxes without active agents.

        Returns:
            Number of cleaned up sandboxes
        """
        try:
            pattern = "agent-*"
            all_sandboxes = list(self.base_path.glob(pattern))

            cleaned_count = 0
            for sandbox_path in all_sandboxes:
                # Extract agent ID from directory name
                parts = sandbox_path.name.split("-")
                if len(parts) >= 2:
                    agent_id = parts[1]
                    if agent_id not in self.active_sandboxes:
                        # Check if sandbox is old (more than 1 day)
                        if sandbox_path.stat().st_mtime < (Path().stat().st_mtime - 86400):
                            shutil.rmtree(sandbox_path)
                            self.logger.info(f"Cleaned up orphaned sandbox {sandbox_path}")
                            cleaned_count += 1

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup orphaned sandboxes: {e}")
            return 0


class DefaultSecurityPolicy(SecurityPolicy):
    """Default security policy implementation."""

    def __init__(
        self,
        allowed_tools: List[str] | None = None,
        forbidden_paths: List[Path] | None = None,
        max_concurrent_agents: int = 5,
    ):
        """Initialize security policy.

        Args:
            allowed_tools: List of allowed tools (None for default)
            forbidden_paths: List of forbidden paths
            max_concurrent_agents: Maximum concurrent agents
        """
        self.allowed_tools = set(allowed_tools or ["Read", "Edit", "Bash", "Write"])
        self.forbidden_paths = [Path(p).expanduser().resolve() for p in (forbidden_paths or ["/etc", "~/.ssh", "/root", "/sys", "/proc"])]
        self.max_concurrent_agents = max_concurrent_agents
        self.logger = logging.getLogger(f"{__name__}.DefaultSecurityPolicy")

    def validate_tool_access(self, tool: str, agent_id: str) -> bool:
        """Validate if an agent can use a specific tool.

        Args:
            tool: Tool name
            agent_id: Agent identifier

        Returns:
            True if tool access is allowed
        """
        allowed = tool in self.allowed_tools
        if not allowed:
            self.logger.warning(f"Tool access denied for agent {agent_id}: {tool}")
        return allowed

    def validate_file_access(self, file_path: Path, agent_id: str) -> bool:
        """Validate if an agent can access a specific file.

        Args:
            file_path: File path to validate
            agent_id: Agent identifier

        Returns:
            True if file access is allowed
        """
        try:
            resolved_path = Path(file_path).resolve()

            # Check against forbidden paths
            for forbidden in self.forbidden_paths:
                if resolved_path.is_relative_to(forbidden):
                    self.logger.warning(f"File access denied for agent {agent_id}: {file_path} (forbidden path: {forbidden})")
                    return False

            return True

        except (OSError, ValueError) as e:
            self.logger.warning(f"File access validation failed: {e}")
            return False

    def validate_command_execution(self, command: str, agent_id: str) -> bool:
        """Validate if an agent can execute a specific command.

        Args:
            command: Command to validate
            agent_id: Agent identifier

        Returns:
            True if command execution is allowed
        """
        # Basic command validation - can be extended
        dangerous_commands = {
            "rm -rf /",
            "dd if=",
            "mkfs",
            "fdisk",
            "sudo",
            "su",
            "chmod 777",
            "chown root",
            "iptables",
            "ufw",
            "systemctl",
            "service",
        }

        command_lower = command.lower().strip()

        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                self.logger.warning(f"Command execution denied for agent {agent_id}: {command}")
                return False

        return True

    def get_max_concurrent_agents(self) -> int:
        """Get maximum number of concurrent agents allowed.

        Returns:
            Maximum concurrent agents
        """
        return self.max_concurrent_agents

    def add_allowed_tool(self, tool: str) -> None:
        """Add a tool to the allowed list.

        Args:
            tool: Tool name to allow
        """
        self.allowed_tools.add(tool)
        self.logger.info(f"Added allowed tool: {tool}")

    def remove_allowed_tool(self, tool: str) -> None:
        """Remove a tool from the allowed list.

        Args:
            tool: Tool name to remove
        """
        self.allowed_tools.discard(tool)
        self.logger.info(f"Removed allowed tool: {tool}")

    def add_forbidden_path(self, path: Path) -> None:
        """Add a path to the forbidden list.

        Args:
            path: Path to forbid
        """
        resolved_path = Path(path).expanduser().resolve()
        self.forbidden_paths.append(resolved_path)
        self.logger.info(f"Added forbidden path: {resolved_path}")

    def remove_forbidden_path(self, path: Path) -> None:
        """Remove a path from the forbidden list.

        Args:
            path: Path to remove from forbidden list
        """
        resolved_path = Path(path).expanduser().resolve()
        if resolved_path in self.forbidden_paths:
            self.forbidden_paths.remove(resolved_path)
            self.logger.info(f"Removed forbidden path: {resolved_path}")
