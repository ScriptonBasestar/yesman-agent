# Copyright notice.

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Configuration schemas using Pydantic for type safety and validation."""


class WorkspaceDefinition(BaseModel):
    """Individual workspace configuration."""
    
    rel_dir: str  # Relative or absolute directory path
    allowed_paths: list[str] = Field(default_factory=lambda: ["."])
    description: str | None = None

    @field_validator("rel_dir", "allowed_paths", mode="after")
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
    base_dir: str = "~/projects"
    
    @field_validator("base_dir", mode="after")
    @classmethod
    def expand_base_dir(cls, v: str) -> str:
        """Expand user home directory in base directory path."""
        return str(Path(v).expanduser())




class YesmanConfigSchema(BaseModel):
    """Main configuration schema for Yesman."""

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility

    # Top-level metadata
    session_name: str | None = None
    description: str | None = None

    # No core settings needed - simplified configuration

    # Workspace configuration
    workspace_config: WorkspaceConfig | None = None
    workspace_definitions: dict[str, WorkspaceDefinition] | None = None  # Separated from config
    workspaces: dict[str, WorkspaceDefinition] | None = None  # Alternative flat structure

    # Simple session settings (for tmux if needed)
    environment: dict[str, str] = Field(default_factory=dict)
    before_script: str | None = None
    after_script: str | None = None

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


    def get_absolute_workspace_path(self, workspace_name: str) -> Path | None:
        """Get absolute path for a workspace, resolving relative paths from base_dir."""
        if not self.workspace_definitions or workspace_name not in self.workspace_definitions:
            return None
        
        workspace_def = self.workspace_definitions[workspace_name]
        workspace_path = Path(workspace_def.rel_dir)
        
        # If path is already absolute, return as-is
        if workspace_path.is_absolute():
            return workspace_path
        
        # Otherwise, resolve relative to base_dir
        if self.workspace_config:
            base_path = Path(self.workspace_config.base_dir)
            return base_path / workspace_path
        
        return workspace_path
    
    def model_post_init(self, __context: object) -> None:
        """Post-initialization validation and setup."""
        # Expand paths in logging config
        if isinstance(self.logging, dict) and "file" in self.logging:
            self.logging["file"] = str(Path(self.logging["file"]).expanduser())
