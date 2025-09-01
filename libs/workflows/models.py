"""Data models for LangChain workflow integration."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepType(Enum):
    """Workflow step types."""
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    GENERAL = "general"


@dataclass
class WorkflowStep:
    """Individual workflow step configuration."""
    id: str
    type: StepType
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    retry_count: int = 3
    dependencies: List[str] = field(default_factory=list)
    

@dataclass
class ExecutionCheckpoint:
    """Checkpoint data for workflow execution."""
    step_index: int
    results: Dict[str, Any]
    timestamp: datetime
    session_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result from workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    steps_completed: int
    total_steps: int
    results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None


class WorkflowConfig(BaseModel):
    """Configuration for a workflow template."""
    
    name: str = Field(..., description="Workflow template name")
    description: str = Field(..., description="Workflow description")
    version: str = Field(default="1.0.0", description="Template version")
    author: Optional[str] = Field(None, description="Template author")
    
    # Execution settings
    timeout: int = Field(default=3600, description="Max execution time in seconds")
    checkpoint_interval: int = Field(default=2, description="Steps between checkpoints")
    allow_parallel: bool = Field(default=False, description="Allow parallel step execution")
    
    # Context and environment
    working_directory: Optional[str] = Field(None, description="Working directory for execution")
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    
    # Steps definition
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps")
    
    # Error handling
    continue_on_error: bool = Field(default=False, description="Continue execution on step failure")
    recovery_strategies: List[str] = Field(
        default_factory=lambda: ["retry", "skip", "prompt"],
        description="Error recovery strategies"
    )
    
    def to_workflow_steps(self) -> List[WorkflowStep]:
        """Convert steps configuration to WorkflowStep objects."""
        workflow_steps = []
        
        for step_data in self.steps:
            step = WorkflowStep(
                id=step_data["id"],
                type=StepType(step_data.get("type", "general")),
                prompt=step_data["prompt"],
                context=step_data.get("context", {}),
                timeout=step_data.get("timeout"),
                retry_count=step_data.get("retry_count", 3),
                dependencies=step_data.get("dependencies", [])
            )
            workflow_steps.append(step)
            
        return workflow_steps


@dataclass
class WorkflowExecution:
    """Active workflow execution state."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: WorkflowConfig = field(default=None)
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[int] = None
    
    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results and state
    step_results: Dict[str, Any] = field(default_factory=dict)
    checkpoints: Dict[int, ExecutionCheckpoint] = field(default_factory=dict)
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session management
    claude_session_id: Optional[str] = None
    project_path: Optional[Path] = None
    
    def get_progress(self) -> float:
        """Get execution progress as percentage."""
        if not self.config or not self.config.steps:
            return 0.0
            
        completed_steps = len(self.step_results)
        total_steps = len(self.config.steps)
        
        return (completed_steps / total_steps) * 100.0
    
    def get_execution_time(self) -> Optional[float]:
        """Get total execution time in seconds."""
        if not self.started_at:
            return None
            
        end_time = self.completed_at or datetime.now(UTC)
        return (end_time - self.started_at).total_seconds()
    
    def add_error(self, step_id: str, error: str, recovery_action: Optional[str] = None) -> None:
        """Add error to execution log."""
        error_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "step_id": step_id,
            "error": error,
            "recovery_action": recovery_action
        }
        self.error_log.append(error_entry)
    
    def create_checkpoint(self, step_index: int, session_state: Optional[Dict[str, Any]] = None) -> None:
        """Create execution checkpoint."""
        checkpoint = ExecutionCheckpoint(
            step_index=step_index,
            results=self.step_results.copy(),
            timestamp=datetime.now(UTC),
            session_state=session_state or {}
        )
        self.checkpoints[step_index] = checkpoint


class WorkflowTemplate(BaseModel):
    """Predefined workflow template."""
    
    template_id: str = Field(..., description="Unique template identifier") 
    config: WorkflowConfig = Field(..., description="Workflow configuration")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    is_builtin: bool = Field(default=False, description="Whether this is a built-in template")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))