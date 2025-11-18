"""Async workflow execution engine with background task support."""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from libs.langchain_integration import ClaudeAgent
from libs.core.error_handling import ErrorSeverity, YesmanError
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig

from .models import ExecutionResult, StepType, WorkflowExecution, WorkflowStatus, WorkflowStep


class ExecutionEngineError(YesmanError):
    """Execution engine specific error."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message=message, severity=ErrorSeverity.HIGH, **kwargs)


class WorkflowExecutionEngine:
    """Engine for executing LangChain workflows with advanced features."""

    def __init__(self, config: YesmanConfig, tmux_manager: TmuxManager, max_concurrent: int = 5) -> None:
        """Initialize execution engine.

        Args:
            config: Yesman configuration
            tmux_manager: Tmux manager for session handling
            max_concurrent: Maximum concurrent workflow executions
        """
        self.config = config
        self.tmux_manager = tmux_manager
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Execution tracking
        self.running_executions: dict[str, WorkflowExecution] = {}
        self.execution_tasks: dict[str, asyncio.Task] = {}

        # Claude agent pool
        self.claude_agents: dict[str, ClaudeAgent] = {}

        # Semaphore for controlling concurrency
        self.execution_semaphore = asyncio.Semaphore(max_concurrent)

        # Background cleanup task
        self.cleanup_task: asyncio.Task | None = None
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""

        async def cleanup_routine():
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self._cleanup_finished_tasks()
                except asyncio.CancelledError:
                    break
                except Exception:
                    self.logger.exception("Cleanup task error")

        self.cleanup_task = asyncio.create_task(cleanup_routine())

    async def _cleanup_finished_tasks(self) -> None:
        """Clean up finished execution tasks."""
        finished_tasks = []

        for execution_id, task in self.execution_tasks.items():
            if task.done():
                finished_tasks.append(execution_id)

                # Handle task exceptions
                try:
                    await task
                except Exception as e:
                    self.logger.exception("Execution task %s failed", execution_id)

                    # Update execution status
                    execution = self.running_executions.get(execution_id)
                    if execution:
                        execution.status = WorkflowStatus.FAILED
                        execution.add_error("execution_engine", str(e))

        # Remove finished tasks
        for execution_id in finished_tasks:
            self.execution_tasks.pop(execution_id, None)
            self.logger.debug("Cleaned up finished task: %s", execution_id)

    async def execute_workflow(self, execution: WorkflowExecution, variables: dict[str, str] | None = None) -> ExecutionResult:
        """Execute workflow with full error handling and checkpointing.

        Args:
            execution: Workflow execution instance
            variables: Template variables for substitution

        Returns:
            Execution result

        Raises:
            ExecutionEngineError: If execution fails critically
        """
        execution_id = execution.id
        self.running_executions[execution_id] = execution

        try:
            # Acquire execution semaphore
            async with self.execution_semaphore:
                self.logger.info("Starting workflow execution: %s", execution_id)

                # Initialize execution
                execution.status = WorkflowStatus.RUNNING
                execution.started_at = datetime.now(UTC)

                # Create Claude agent for this execution
                claude_agent = await self._create_claude_agent(execution)
                self.claude_agents[execution_id] = claude_agent

                # Execute workflow steps
                result = await self._execute_steps(execution, claude_agent, variables or {})

                # Finalize execution
                execution.completed_at = datetime.now(UTC)
                if execution.status == WorkflowStatus.RUNNING:
                    execution.status = WorkflowStatus.COMPLETED

                self.logger.info("Completed workflow execution: %s", execution_id)
                return result

        except asyncio.CancelledError:
            execution.status = WorkflowStatus.CANCELLED
            self.logger.info("Workflow execution cancelled: %s", execution_id)
            raise
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.add_error("workflow", str(e))
            self.logger.exception("Workflow execution failed: %s", execution_id)

            # Create error result
            return ExecutionResult(
                workflow_id=execution_id,
                status=WorkflowStatus.FAILED,
                steps_completed=len(execution.step_results),
                total_steps=len(execution.config.steps),
                results=execution.step_results,
                error_message=str(e),
                started_at=execution.started_at,
                completed_at=datetime.now(UTC),
                execution_time=execution.get_execution_time(),
            )
        finally:
            # Cleanup
            self.running_executions.pop(execution_id, None)
            self.claude_agents.pop(execution_id, None)

    async def _create_claude_agent(self, execution: WorkflowExecution) -> ClaudeAgent:
        """Create Claude agent for workflow execution."""
        try:
            project_path = execution.project_path or Path.cwd()
            claude_agent = ClaudeAgent(str(project_path))

            # Store session ID for continuity
            execution.claude_session_id = claude_agent.session.session_id

            return claude_agent

        except Exception as e:
            raise ExecutionEngineError(f"Failed to create Claude agent: {e}") from e

    async def _execute_steps(self, execution: WorkflowExecution, claude_agent: ClaudeAgent, variables: dict[str, str]) -> ExecutionResult:
        """Execute workflow steps with dependency resolution."""
        workflow_steps = execution.config.to_workflow_steps()

        completed_steps = set()

        step_index = 0
        for step in workflow_steps:
            try:
                # Check dependencies
                if not self._dependencies_satisfied(step, completed_steps):
                    self.logger.warning("Step %s dependencies not satisfied, skipping", step.id)
                    continue

                execution.current_step = step_index

                # Execute step
                self.logger.info("Executing step: %s (%s)", step.id, step.type.value)
                result = await self._execute_step(step, claude_agent, variables, execution)

                # Store result
                execution.step_results[step.id] = result
                completed_steps.add(step.id)

                # Create checkpoint if needed
                if step_index % execution.config.checkpoint_interval == 0:
                    execution.create_checkpoint(step_index)
                    self.logger.debug("Created checkpoint at step %d", step_index)

                step_index += 1

            except Exception as e:
                self.logger.exception("Step %s failed", step.id)
                execution.add_error(step.id, str(e))

                # Handle error based on configuration
                if not execution.config.continue_on_error:
                    raise ExecutionEngineError(f"Step {step.id} failed: {e}")

                # Try recovery strategies
                recovery_result = await self._attempt_step_recovery(step, e, claude_agent, execution)
                if recovery_result:
                    execution.step_results[step.id] = recovery_result
                    completed_steps.add(step.id)
                    execution.add_error(step.id, str(e), "recovered")
                else:
                    self.logger.warning("Step %s recovery failed, continuing", step.id)

        # Create final result
        return ExecutionResult(
            workflow_id=execution.id,
            status=execution.status,
            steps_completed=len(execution.step_results),
            total_steps=len(workflow_steps),
            results=execution.step_results,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            execution_time=execution.get_execution_time(),
        )

    def _build_dependency_graph(self, steps: list[WorkflowStep]) -> dict[str, list[str]]:
        """Build step dependency graph."""
        dependencies = {}
        for step in steps:
            dependencies[step.id] = step.dependencies.copy()
        return dependencies

    def _dependencies_satisfied(self, step: WorkflowStep, completed_steps: set) -> bool:
        """Check if step dependencies are satisfied."""
        return all(dep in completed_steps for dep in step.dependencies)

    async def _execute_step(self, step: WorkflowStep, claude_agent: ClaudeAgent, variables: dict[str, str], execution: WorkflowExecution) -> str:
        """Execute individual workflow step."""
        # Apply variable substitution to prompt
        prompt = self._apply_variables(step.prompt, variables)

        # Determine custom prompt based on step type
        custom_prompts = {
            StepType.ANALYSIS: "Perform detailed analysis with comprehensive insights. Focus on providing actionable recommendations.",
            StepType.IMPLEMENTATION: "Implement following best practices and conventions. Ensure code quality and maintainability.",
            StepType.TESTING: "Create thorough tests with good coverage. Include edge cases and error scenarios.",
            StepType.DEPLOYMENT: "Prepare for production deployment with safety checks and rollback plans.",
            StepType.GENERAL: "Execute the requested task with attention to detail and best practices.",
        }

        custom_prompt = custom_prompts.get(step.type, custom_prompts[StepType.GENERAL])

        # Add context information to prompt if available
        if step.context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in step.context.items())
            prompt = f"{prompt}\n\nContext:\n{context_str}"

        try:
            # Execute through Claude CLI with timeout
            timeout = step.timeout or 300  # Default 5 minutes

            result = await asyncio.wait_for(self._run_claude_step(claude_agent, prompt, custom_prompt), timeout=timeout)

            return result

        except TimeoutError:
            raise ExecutionEngineError(f"Step {step.id} timed out after {timeout} seconds")
        except Exception as e:
            raise ExecutionEngineError(f"Step {step.id} execution failed: {e}")

    async def _run_claude_step(self, claude_agent: ClaudeAgent, prompt: str, custom_prompt: str) -> str:
        """Run Claude step in executor to avoid blocking."""
        loop = asyncio.get_event_loop()

        # Run in thread executor to avoid blocking the event loop
        result = await loop.run_in_executor(
            None,
            claude_agent.claude_tool._run,
            prompt,
            True,  # continue_session
            custom_prompt,
        )

        return result

    def _apply_variables(self, text: str, variables: dict[str, str]) -> str:
        """Apply variable substitution to text."""
        for key, value in variables.items():
            text = text.replace(f"{{{key}}}", value)
            text = text.replace(f"${{{key}}}", value)
        return text

    async def _attempt_step_recovery(self, step: WorkflowStep, error: Exception, claude_agent: ClaudeAgent, execution: WorkflowExecution) -> str | None:
        """Attempt to recover from step failure."""
        recovery_strategies = execution.config.recovery_strategies

        for strategy in recovery_strategies:
            try:
                if strategy == "retry":
                    # Retry with simplified prompt
                    simplified_prompt = f"Simple version: {step.prompt}"
                    result = await self._run_claude_step(claude_agent, simplified_prompt, "Keep it simple and focused")
                    return result

                elif strategy == "skip":
                    # Skip step with warning
                    self.logger.warning("Skipping failed step: %s", step.id)
                    return f"SKIPPED: {step.id} - {str(error)}"

                elif strategy == "prompt":
                    # Try with context reset
                    result = await self._run_claude_step(claude_agent, step.prompt, "Fresh attempt - ignore previous context if problematic")
                    return result

            except Exception as recovery_error:
                self.logger.debug("Recovery strategy %s failed: %s", strategy, recovery_error)
                continue

        return None

    async def start_execution_async(self, execution: WorkflowExecution, variables: dict[str, str] | None = None) -> str:
        """Start workflow execution in background.

        Args:
            execution: Workflow execution instance
            variables: Template variables

        Returns:
            Execution ID
        """
        execution_id = execution.id

        # Create background task
        task = asyncio.create_task(self.execute_workflow(execution, variables))

        self.execution_tasks[execution_id] = task
        self.logger.info("Started background execution: %s", execution_id)

        return execution_id

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution.

        Args:
            execution_id: Execution to cancel

        Returns:
            True if cancelled successfully
        """
        task = self.execution_tasks.get(execution_id)
        execution = self.running_executions.get(execution_id)

        if not task or not execution:
            return False

        if task.done():
            return False

        try:
            task.cancel()
            execution.status = WorkflowStatus.CANCELLED
            self.logger.info("Cancelled execution: %s", execution_id)
            return True

        except Exception:
            self.logger.exception("Failed to cancel execution %s", execution_id)
            return False

    def get_execution_status(self, execution_id: str) -> WorkflowExecution | None:
        """Get current execution status."""
        return self.running_executions.get(execution_id)

    def list_running_executions(self) -> list[WorkflowExecution]:
        """List all running executions."""
        return list(self.running_executions.values())

    async def shutdown(self) -> None:
        """Shutdown execution engine and cleanup resources."""
        self.logger.info("Shutting down workflow execution engine")

        # Cancel cleanup task
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # Cancel all running executions
        for execution_id in list(self.execution_tasks.keys()):
            await self.cancel_execution(execution_id)

        # Wait for tasks to complete
        if self.execution_tasks:
            await asyncio.gather(*self.execution_tasks.values(), return_exceptions=True)

        # Clear state
        self.running_executions.clear()
        self.execution_tasks.clear()
        self.claude_agents.clear()

        self.logger.info("Workflow execution engine shutdown complete")
