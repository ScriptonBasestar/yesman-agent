# Copyright notice.

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Configuration schemas using Pydantic for type safety and validation."""


class WorkspaceDefinition(BaseModel):
    """Individual workspace configuration."""
    
    path: str  # Relative or absolute path
    allowed_paths: list[str] = Field(default_factory=lambda: ["."])
    security_policy: str = "default"
    max_size_mb: int = Field(default=100, ge=10, le=1000)
    description: str | None = None

    @field_validator("path", "allowed_paths", mode="after")
    @classmethod
    def expand_paths(cls, v) -> str | list[str]:
        """Expand user home directory in paths."""
        if isinstance(v, str):
            return str(Path(v).expanduser())
        elif isinstance(v, list):
            return [str(Path(path).expanduser()) for path in v]
        return v


class WorkspaceConfig(BaseModel):
    """Workspace configuration with base directory support."""
    
    # Base directory for relative paths
    base_directory: str = "~/projects"
    
    # Individual workspace definitions
    definitions: dict[str, WorkspaceDefinition] = Field(default_factory=dict)
    
    # Global workspace settings
    security_policy: str = "default"
    cleanup_policy: str = Field(default="on_session_end", pattern="^(on_session_end|manual|daily)$")
    auto_cleanup_days: int = Field(default=7, ge=1, le=30)
    
    @field_validator("base_directory", mode="after")
    @classmethod
    def expand_base_directory(cls, v: str) -> str:
        """Expand user home directory in base directory path."""
        return str(Path(v).expanduser())
    
    def get_absolute_path(self, workspace_name: str) -> Path | None:
        """Get absolute path for a workspace, resolving relative paths from base_directory."""
        if workspace_name not in self.definitions:
            return None
        
        workspace_def = self.definitions[workspace_name]
        workspace_path = Path(workspace_def.path)
        
        # If path is already absolute, return as-is
        if workspace_path.is_absolute():
            return workspace_path
        
        # Otherwise, resolve relative to base_directory
        base_path = Path(self.base_directory)
        return base_path / workspace_path


class WindowConfig(BaseModel):
    """Individual window configuration."""
    
    window_name: str
    layout: str = "even-horizontal"
    start_directory: str | None = None
    panes: list[str | dict] = Field(default_factory=list)


class SessionConfig(BaseModel):
    """Individual session configuration."""
    
    session_name: str
    start_directory: str
    description: str | None = None
    
    # Window configurations
    windows: list[WindowConfig] = Field(default_factory=list)
    
    # Environment variables
    environment: dict[str, str] = Field(default_factory=dict)
    
    # Scripts
    before_script: str | None = None
    after_script: str | None = None


class YesmanConfigSchema(BaseModel):
    """Main configuration schema for Yesman."""

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility

    # Top-level metadata
    session_name: str | None = None
    description: str | None = None

    # Core settings
    mode: str = Field(default="local", pattern="^(merge|isolated|local)$")
    root_dir: str = "~/.scripton/yesman"

    # Workspace configuration
    workspace_config: WorkspaceConfig | None = None
    workspaces: dict[str, WorkspaceDefinition] | None = None  # Alternative flat structure

    # Session configuration
    session_config: dict[str, SessionConfig] | None = None
    sessions: dict[str, SessionConfig] | None = None  # Alternative flat structure

    # Logging settings
    logging: dict[str, Any] = Field(default_factory=lambda: {
        "level": "INFO",
        "file": "~/.scripton/yesman/logs/yesman.log"
    })

    # Server settings
    server: dict[str, Any] = Field(default_factory=lambda: {
        "host": "localhost", 
        "port": 10501
    })

    # Custom settings (allows complete flexibility)
    custom: dict[str, Any] = Field(default_factory=dict)

    @field_validator("root_dir")
    @classmethod
    def expand_path(cls, v: str) -> str:
        """Expand user home directory in paths."""
        return str(Path(v).expanduser())

    def model_post_init(self, __context: object) -> None:
        """Post-initialization validation and setup."""
        # Expand paths in logging config
        if isinstance(self.logging, dict) and "file" in self.logging:
            self.logging["file"] = str(Path(self.logging["file"]).expanduser())
