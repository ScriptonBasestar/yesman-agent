"""Workspace management and security for Claude agents."""

import logging
import shutil
import uuid
from pathlib import Path

from .interfaces import SecurityPolicy, WorkspaceManager


class DefaultWorkspaceManager(WorkspaceManager):
    """Default implementation of workspace manager with sandboxing."""

    def __init__(
        self,
        base_path: Path,
        allowed_paths: list[Path],
        security_policy: SecurityPolicy,
    ) -> None:
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
        self.active_sandboxes: set[str] = set()

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
            return bool(resolved_path.is_relative_to(self.base_path))

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

            # Create sandbox directory with restrictive permissions
            sandbox_path.mkdir(parents=True, exist_ok=True)

            # Set restrictive permissions (owner only: rwx------)
            sandbox_path.chmod(0o700)

            # Set up basic structure with proper permissions
            workspace_dir = sandbox_path / "workspace"
            logs_dir = sandbox_path / "logs"
            temp_dir = sandbox_path / "temp"

            workspace_dir.mkdir(exist_ok=True)
            logs_dir.mkdir(exist_ok=True)
            temp_dir.mkdir(exist_ok=True)

            # Set directory permissions
            workspace_dir.chmod(0o755)  # rwxr-xr-x for workspace
            logs_dir.chmod(0o750)  # rwxr-x--- for logs
            temp_dir.chmod(0o700)  # rwx------ for temp

            # Create .gitignore to avoid tracking temporary files
            gitignore = sandbox_path / ".gitignore"
            gitignore.write_text("logs/\ntemp/\n*.log\n*.tmp\n")
            gitignore.chmod(0o644)  # rw-r--r--

            # Create README with sandbox info
            readme = sandbox_path / "README.md"
            readme.write_text(
                f"# Agent Sandbox: {agent_id}\n\n"
                f"Created: {sandbox_path.stat().st_ctime}\n"
                f"Purpose: Isolated workspace for Claude agent\n\n"
                f"## Structure\n"
                f"- `workspace/`: Main working directory\n"
                f"- `logs/`: Agent execution logs\n"
                f"- `temp/`: Temporary files\n"
            )
            readme.chmod(0o644)

            # Track active sandbox
            self.active_sandboxes.add(agent_id)

            self.logger.info(f"Created sandbox for agent {agent_id} at {sandbox_path}")
            return sandbox_path

        except Exception as e:
            self.logger.exception(f"Failed to create sandbox for agent {agent_id}")
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
            self.logger.exception(f"Failed to cleanup sandbox for agent {agent_id}")
            return False

    def get_allowed_tools(self) -> list[str]:
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

    def list_active_sandboxes(self) -> list[str]:
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
                        import time

                        current_time = time.time()
                        sandbox_mtime = sandbox_path.stat().st_mtime

                        if current_time - sandbox_mtime > 86400:  # 24 hours
                            # Secure cleanup: remove read-only flags first
                            self._secure_rmtree(sandbox_path)
                            self.logger.info(f"Cleaned up orphaned sandbox {sandbox_path} (age: {(current_time - sandbox_mtime) / 3600:.1f} hours)")
                            cleaned_count += 1

            return cleaned_count

        except Exception as e:
            self.logger.exception("Failed to cleanup orphaned sandboxes")
            return 0

    def _secure_rmtree(self, path: Path) -> None:
        """Securely remove directory tree with proper permission handling.

        Args:
            path: Path to remove
        """
        try:
            # First, make all files and directories writable
            import os

            if path.is_dir():
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        dir_path = Path(root) / d
                        try:
                            dir_path.chmod(0o700)
                        except OSError:
                            pass
                    for f in files:
                        file_path = Path(root) / f
                        try:
                            file_path.chmod(0o600)
                        except OSError:
                            pass

            # Now remove the tree
            shutil.rmtree(path)

        except Exception as e:
            self.logger.exception(f"Failed to securely remove {path}")
            # Fallback to regular rmtree
            try:
                shutil.rmtree(path)
            except Exception as fallback_e:
                self.logger.exception("Fallback removal also failed")
                raise

    def get_sandbox_stats(self, agent_id: str) -> dict:
        """Get statistics for an agent's sandbox.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary with sandbox statistics
        """
        sandbox_path = self.get_sandbox_path(agent_id)
        if not sandbox_path or not sandbox_path.exists():
            return {}

        try:
            import os

            stats = sandbox_path.stat()

            # Calculate directory size
            total_size = 0
            file_count = 0

            for dirpath, dirnames, filenames in os.walk(sandbox_path):
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    try:
                        file_stat = file_path.stat()
                        total_size += file_stat.st_size
                        file_count += 1
                    except (OSError, FileNotFoundError):
                        continue

            return {
                "path": str(sandbox_path),
                "created_time": stats.st_ctime,
                "modified_time": stats.st_mtime,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "permissions": oct(stats.st_mode)[-3:],
            }

        except Exception as e:
            self.logger.exception(f"Failed to get sandbox stats for {agent_id}")
            return {"error": str(e)}

    def enforce_quota(self, agent_id: str, max_size_mb: int = 100) -> bool:
        """Enforce storage quota for an agent's sandbox.

        Args:
            agent_id: Agent identifier
            max_size_mb: Maximum allowed size in MB

        Returns:
            True if within quota, False if exceeded
        """
        stats = self.get_sandbox_stats(agent_id)
        if not stats or "total_size_mb" not in stats:
            return True

        if stats["total_size_mb"] > max_size_mb:
            self.logger.warning(f"Agent {agent_id} sandbox exceeds quota: {stats['total_size_mb']}MB > {max_size_mb}MB")

            # Try to clean up temp files first
            sandbox_path = self.get_sandbox_path(agent_id)
            if sandbox_path:
                temp_dir = sandbox_path / "temp"
                if temp_dir.exists():
                    try:
                        self._secure_rmtree(temp_dir)
                        temp_dir.mkdir()
                        temp_dir.chmod(0o700)
                        self.logger.info(f"Cleaned temp directory for agent {agent_id}")

                        # Recheck quota after cleanup
                        new_stats = self.get_sandbox_stats(agent_id)
                        if new_stats.get("total_size_mb", 0) <= max_size_mb:
                            return True

                    except Exception as e:
                        self.logger.exception(f"Failed to clean temp directory for {agent_id}")

            return False

        return True


class DefaultSecurityPolicy(SecurityPolicy):
    """Default security policy implementation."""

    def __init__(
        self,
        allowed_tools: list[str] | None = None,
        forbidden_paths: list[Path] | None = None,
        max_concurrent_agents: int = 5,
    ) -> None:
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
        # Enhanced command validation with pattern matching
        dangerous_patterns = {
            # System destruction
            r"rm\s+(-rf?|--recursive)\s+/",
            r"dd\s+if=/dev/(zero|urandom)",
            r"mkfs\.[a-z]+",
            r"fdisk\s+/dev/",
            # Privilege escalation
            r"\bsudo\b",
            r"\bsu\b",
            r"\bsudo\s+-i\b",
            # Permission manipulation
            r"chmod\s+(777|666)",
            r"chown\s+root",
            r"chgrp\s+root",
            # Network/firewall
            r"\biptables\b",
            r"\bufw\b",
            r"\bfirewalld\b",
            # System services
            r"\bsystemctl\b",
            r"\bservice\s+\w+\s+(start|stop|restart)",
            r"/etc/init\.d/",
            # Package management
            r"\bapt(-get)?\s+(install|remove|purge)",
            r"\byum\s+(install|remove|erase)",
            r"\bpip\s+install\s+.*--break-system-packages",
            # File system manipulation
            r"\bmount\s+",
            r"\bumount\s+",
            r"\blosetup\s+",
            # Process manipulation
            r"\bkill\s+-9\s+1\b",  # Don't kill init
            r"\bkillall\s+(init|systemd)",
            # Sensitive file access
            r"/etc/(passwd|shadow|sudoers)",
            r"/root/\.[^\s]*",
            r"~root/\.[^\s]*",
            r"/home/[^/]+/\.ssh/",
            # System configuration
            r"/sys/(kernel|fs|dev)/",
            r"/proc/(sys|1)/",
        }

        import re

        # Check against dangerous patterns
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower, re.IGNORECASE):
                self.logger.warning(f"Command execution denied for agent {agent_id}: {command} (matched pattern: {pattern})")
                return False

        command_lower = command.lower().strip()

        # Additional simple string checks for common dangerous commands
        simple_dangerous = {
            "rm -rf /",
            "dd if=/dev/zero",
            ":(){ :|:& };:",  # Fork bomb
            "curl | sh",
            "wget | sh",
            "| bash",
            "| sh",
        }

        for dangerous in simple_dangerous:
            if dangerous in command_lower:
                self.logger.warning(f"Command execution denied for agent {agent_id}: {command} (matched: {dangerous})")
                return False

        # Check for potential code injection
        injection_patterns = [
            ";",  # Command chaining
            "&&",  # AND operator
            "||",  # OR operator
            "`",  # Command substitution
            "$(",  # Command substitution
            ">",  # Redirection (when not in allowed context)
            ">>",  # Append redirection
            "<",  # Input redirection
        ]

        # Allow some safe redirections in limited contexts
        safe_contexts = [
            "echo",
            "cat >",
            "tee",
        ]

        has_injection = any(pattern in command_lower for pattern in injection_patterns)
        has_safe_context = any(context in command_lower for context in safe_contexts)

        if has_injection and not has_safe_context:
            self.logger.warning(f"Potentially unsafe command for agent {agent_id}: {command}")
            # Don't block entirely, but log for monitoring

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

    def validate_resource_usage(self, agent_id: str, cpu_percent: float = 80.0, memory_mb: int = 512) -> bool:
        """Validate resource usage for an agent.

        Args:
            agent_id: Agent identifier
            cpu_percent: Maximum CPU usage percentage
            memory_mb: Maximum memory usage in MB

        Returns:
            True if resource usage is within limits
        """
        try:
            import os

            import psutil

            # Find processes associated with this agent
            agent_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["cmdline"] and agent_id in " ".join(proc.info["cmdline"]):
                        agent_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not agent_processes:
                return True  # No processes found, assume OK

            total_cpu = 0
            total_memory = 0

            for proc in agent_processes:
                try:
                    cpu_usage = proc.cpu_percent(interval=0.1)
                    memory_usage = proc.memory_info().rss / (1024 * 1024)  # Convert to MB

                    total_cpu += cpu_usage
                    total_memory += memory_usage

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if total_cpu > cpu_percent:
                self.logger.warning(f"Agent {agent_id} CPU usage exceeded: {total_cpu:.1f}% > {cpu_percent}%")
                return False

            if total_memory > memory_mb:
                self.logger.warning(f"Agent {agent_id} memory usage exceeded: {total_memory:.1f}MB > {memory_mb}MB")
                return False

            return True

        except ImportError:
            self.logger.warning("psutil not available for resource monitoring")
            return True  # Assume OK if can't monitor
        except Exception as e:
            self.logger.exception(f"Failed to validate resource usage for {agent_id}")
            return True  # Assume OK on error to avoid blocking agents

    def get_security_report(self) -> dict:
        """Generate security report for current state.

        Returns:
            Dictionary with security information
        """
        import time

        return {
            "timestamp": time.time(),
            "allowed_tools": list(self.allowed_tools),
            "forbidden_paths": [str(p) for p in self.forbidden_paths],
            "max_concurrent_agents": self.max_concurrent_agents,
            "security_policy_version": "1.0",
            "last_updated": time.time(),
        }
