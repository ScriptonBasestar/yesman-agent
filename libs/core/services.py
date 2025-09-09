# Copyright notice.

from pathlib import Path

from libs.claude.headless_adapter import HeadlessAdapter
from libs.claude.interactive_adapter import InteractiveAdapter
from libs.claude.interfaces import ClaudeAgentService
from libs.claude.workspace import DefaultSecurityPolicy, DefaultWorkspaceManager
from libs.core.container import container
from libs.core.session_manager import SessionManager
from libs.tmux_manager import TmuxManager
from libs.workflows.execution_engine import WorkflowExecutionEngine
from libs.workflows.workflow_service import WorkflowService
from libs.yesman_config import YesmanConfig

# Auto-initialize services when module is imported

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Service registration and DI container setup."""


def register_core_services() -> None:
    """Register all core services with the DI container."""
    # Register YesmanConfig as a singleton factory
    container.register_factory(YesmanConfig, YesmanConfig)

    # Register TmuxManager as a singleton factory that depends on YesmanConfig
    container.register_factory(TmuxManager, lambda: TmuxManager(container.resolve(YesmanConfig)))

    # Register SessionManager as a singleton factory
    container.register_factory(SessionManager, SessionManager)

    # Register Claude services
    register_claude_services()

    # Register Workflow services
    register_workflow_services()


def register_claude_services() -> None:
    """Register Claude-related services with the DI container."""

    def create_claude_service() -> ClaudeAgentService:
        """Factory function to create appropriate Claude service based on config."""
        config = container.resolve(YesmanConfig)

        # Check if claude config exists
        claude_config = getattr(config._config_schema, "claude", None)

        if claude_config and hasattr(claude_config, "mode") and claude_config.mode == "headless" and hasattr(claude_config, "headless") and claude_config.headless.enabled:
            # Create headless adapter
            security_policy = DefaultSecurityPolicy(
                allowed_tools=claude_config.headless.allowed_tools,
                forbidden_paths=[Path(p) for p in claude_config.headless.forbidden_paths],
                max_concurrent_agents=claude_config.headless.max_concurrent_agents,
            )

            workspace_manager = DefaultWorkspaceManager(
                base_path=Path(claude_config.headless.workspace_root),
                allowed_paths=[Path("~/.scripton/yesman").expanduser(), Path.cwd()],
                security_policy=security_policy,
            )

            adapter = HeadlessAdapter(
                workspace_manager=workspace_manager,
                claude_binary=claude_config.headless.claude_binary_path,
                max_concurrent=claude_config.headless.max_concurrent_agents,
            )

            # Start cleanup task
            adapter.start_cleanup_task()
            return adapter
        else:
            # Create interactive adapter (fallback)
            return InteractiveAdapter()

    # Register Claude service factory
    container.register_factory(ClaudeAgentService, create_claude_service)


def register_workflow_services() -> None:
    """Register workflow-related services with the DI container."""

    def create_workflow_execution_engine() -> WorkflowExecutionEngine:
        """Factory function to create workflow execution engine."""
        config = container.resolve(YesmanConfig)
        tmux_manager = container.resolve(TmuxManager)
        return WorkflowExecutionEngine(config=config, tmux_manager=tmux_manager)

    def create_workflow_service() -> WorkflowService:
        """Factory function to create workflow service."""
        config = container.resolve(YesmanConfig)
        tmux_manager = container.resolve(TmuxManager)
        execution_engine = container.resolve(WorkflowExecutionEngine)
        return WorkflowService(config=config, tmux_manager=tmux_manager, execution_engine=execution_engine)

    # Register WorkflowExecutionEngine as singleton factory
    container.register_factory(WorkflowExecutionEngine, create_workflow_execution_engine)

    # Register WorkflowService as singleton factory
    container.register_factory(WorkflowService, create_workflow_service)


def register_test_services(config: YesmanConfig | None = None, tmux_manager: TmuxManager | None = None) -> None:
    """Register mock services for testing.

    Args:
        config: Optional mock config instance
        tmux_manager: Optional mock tmux manager instance.
    """
    # Clear existing registrations
    container.clear()

    # Register provided mocks or create default ones
    if config is not None:
        container.register_singleton(YesmanConfig, config)
    else:
        container.register_factory(YesmanConfig, YesmanConfig)

    if tmux_manager is not None:
        container.register_singleton(TmuxManager, tmux_manager)
    else:
        container.register_factory(TmuxManager, lambda: TmuxManager(container.resolve(YesmanConfig)))

    # Always register SessionManager for tests
    container.register_factory(SessionManager, SessionManager)


def get_config() -> YesmanConfig:
    """Convenience function to get YesmanConfig from container.

    Returns:
        YesmanConfig: Description of return value.
    """
    return container.resolve(YesmanConfig)


def get_tmux_manager() -> TmuxManager:
    """Convenience function to get TmuxManager from container.

    Returns:
        TmuxManager: Description of return value.
    """
    return container.resolve(TmuxManager)


def get_session_manager() -> SessionManager:
    """Convenience function to get SessionManager from container.

    Returns:
        SessionManager: Description of return value.
    """
    return container.resolve(SessionManager)


def get_claude_service() -> ClaudeAgentService:
    """Convenience function to get ClaudeAgentService from container.

    Returns:
        ClaudeAgentService: The configured Claude agent service
    """
    return container.resolve(ClaudeAgentService)


def get_workflow_service() -> WorkflowService:
    """Convenience function to get WorkflowService from container.

    Returns:
        WorkflowService: The configured workflow service
    """
    return container.resolve(WorkflowService)


def get_workflow_execution_engine() -> WorkflowExecutionEngine:
    """Convenience function to get WorkflowExecutionEngine from container.

    Returns:
        WorkflowExecutionEngine: The configured workflow execution engine
    """
    return container.resolve(WorkflowExecutionEngine)


def is_container_initialized() -> bool:
    """Check if the container has been initialized with core services.

    Returns:
        bool: Description of return value.
    """
    return container.is_registered(YesmanConfig) and container.is_registered(TmuxManager) and container.is_registered(SessionManager) and container.is_registered(WorkflowService)


def initialize_services() -> None:
    """Initialize services if not already done."""
    if not is_container_initialized():
        register_core_services()


initialize_services()
