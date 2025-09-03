"""Workspace configuration manager with base directory support."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config_schema import WorkspaceConfig, WorkspaceDefinition, YesmanConfigSchema


class WorkspaceConfigManager:
    """Manages workspace configurations with base directory support."""

    def __init__(self, config_schema: YesmanConfigSchema) -> None:
        """Initialize workspace configuration manager.
        
        Args:
            config_schema: Full Yesman configuration schema
        """
        self.config_schema = config_schema
        self.workspace_config = config_schema.workspace_config
        self.workspace_definitions = config_schema.workspace_definitions or {}
        self.logger = logging.getLogger(f"{__name__}.WorkspaceConfigManager")

    def get_workspace_path(self, workspace_name: str) -> Path | None:
        """Get absolute path for a workspace.
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            Absolute path to the workspace or None if not found
        """
        return self.config_schema.get_absolute_workspace_path(workspace_name)

    def get_workspace_definition(self, workspace_name: str) -> WorkspaceDefinition | None:
        """Get workspace definition by name.
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            WorkspaceDefinition or None if not found
        """
        return self.workspace_definitions.get(workspace_name)

    def resolve_workspace_from_path(self, current_path: Path) -> str | None:
        """Resolve workspace name from current working path.
        
        Args:
            current_path: Current working directory path
            
        Returns:
            Workspace name that matches the path or None
        """
        try:
            current_path = Path(current_path).resolve()
            
            # Check each workspace to see if current_path is within it
            for workspace_name, workspace_def in self.workspace_definitions.items():
                workspace_path = self.get_workspace_path(workspace_name)
                if workspace_path and current_path.is_relative_to(workspace_path):
                    self.logger.debug(f"Resolved path {current_path} to workspace '{workspace_name}'")
                    return workspace_name
            
            self.logger.debug(f"No workspace found for path {current_path}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to resolve workspace for path {current_path}: {e}")
            return None

    def get_allowed_paths_for_workspace(self, workspace_name: str) -> List[Path]:
        """Get allowed paths for a workspace, resolved to absolute paths.
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            List of absolute paths allowed for the workspace
        """
        workspace_def = self.get_workspace_definition(workspace_name)
        if not workspace_def:
            return []
        
        workspace_path = self.get_workspace_path(workspace_name)
        if not workspace_path:
            return []
            
        allowed_paths = []
        for allowed_path_str in workspace_def.allowed_paths:
            allowed_path = Path(allowed_path_str)
            
            # If path is relative, resolve relative to workspace path
            if not allowed_path.is_absolute():
                allowed_path = workspace_path / allowed_path
                
            try:
                allowed_paths.append(allowed_path.resolve())
            except Exception as e:
                self.logger.warning(f"Failed to resolve allowed path {allowed_path}: {e}")
                
        return allowed_paths

    def is_path_allowed_in_workspace(self, workspace_name: str, target_path: Path) -> bool:
        """Check if a path is allowed within a workspace.
        
        Args:
            workspace_name: Name of the workspace
            target_path: Path to check
            
        Returns:
            True if path is allowed in the workspace
        """
        allowed_paths = self.get_allowed_paths_for_workspace(workspace_name)
        if not allowed_paths:
            return False
            
        try:
            target_path = Path(target_path).resolve()
            
            for allowed_path in allowed_paths:
                if target_path.is_relative_to(allowed_path):
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to check path {target_path} in workspace {workspace_name}: {e}")
            return False

    def list_workspace_names(self) -> List[str]:
        """Get list of all configured workspace names.
        
        Returns:
            List of workspace names
        """
        return list(self.workspace_definitions.keys())

    def get_workspace_info(self, workspace_name: str) -> Dict[str, Any] | None:
        """Get comprehensive information about a workspace.
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            Dictionary with workspace information or None if not found
        """
        workspace_def = self.get_workspace_definition(workspace_name)
        workspace_path = self.get_workspace_path(workspace_name)
        
        if not workspace_def or not workspace_path:
            return None
            
        return {
            "name": workspace_name,
            "path": str(workspace_path),
            "relative_path": workspace_def.rel_dir,
            "description": workspace_def.description,
            "allowed_paths": [str(p) for p in self.get_allowed_paths_for_workspace(workspace_name)],
            "exists": workspace_path.exists(),
            "is_directory": workspace_path.is_dir() if workspace_path.exists() else None,
        }

    def create_workspace_directory(self, workspace_name: str) -> bool:
        """Create workspace directory if it doesn't exist.
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            True if directory was created or already exists
        """
        workspace_path = self.get_workspace_path(workspace_name)
        if not workspace_path:
            self.logger.error(f"Workspace {workspace_name} not found in configuration")
            return False
            
        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created workspace directory: {workspace_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create workspace directory {workspace_path}: {e}")
            return False

    def validate_workspace_configuration(self) -> List[str]:
        """Validate the workspace configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if base directory exists
        base_path = Path(self.workspace_config.base_dir) if self.workspace_config else Path("~/projects")
        if not base_path.exists():
            errors.append(f"Base directory does not exist: {base_path}")
        elif not base_path.is_dir():
            errors.append(f"Base directory is not a directory: {base_path}")
            
        # Validate each workspace
        for workspace_name, workspace_def in self.workspace_definitions.items():
            workspace_path = self.get_workspace_path(workspace_name)
            
            if not workspace_path:
                errors.append(f"Failed to resolve path for workspace '{workspace_name}'")
                continue
                
            # Check for path conflicts
            for other_name, other_def in self.workspace_definitions.items():
                if other_name == workspace_name:
                    continue
                    
                other_path = self.get_workspace_path(other_name)
                if other_path and workspace_path == other_path:
                    errors.append(f"Workspace paths conflict: '{workspace_name}' and '{other_name}' both use {workspace_path}")
                elif other_path and (workspace_path.is_relative_to(other_path) or other_path.is_relative_to(workspace_path)):
                    errors.append(f"Workspace paths overlap: '{workspace_name}' ({workspace_path}) and '{other_name}' ({other_path})")
                    
        return errors

    def get_base_directory(self) -> Path:
        """Get the base directory as a Path object.
        
        Returns:
            Base directory path
        """
        return Path(self.workspace_config.base_dir) if self.workspace_config else Path("~/projects")

    def update_workspace_definition(self, workspace_name: str, workspace_def: WorkspaceDefinition) -> bool:
        """Update a workspace definition.
        
        Args:
            workspace_name: Name of the workspace
            workspace_def: New workspace definition
            
        Returns:
            True if update was successful
        """
        try:
            self.workspace_definitions[workspace_name] = workspace_def
            self.logger.info(f"Updated workspace definition for '{workspace_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update workspace definition for '{workspace_name}': {e}")
            return False

    def remove_workspace_definition(self, workspace_name: str) -> bool:
        """Remove a workspace definition.
        
        Args:
            workspace_name: Name of the workspace to remove
            
        Returns:
            True if removal was successful
        """
        try:
            if workspace_name in self.workspace_definitions:
                del self.workspace_definitions[workspace_name]
                self.logger.info(f"Removed workspace definition for '{workspace_name}'")
                return True
            else:
                self.logger.warning(f"Workspace '{workspace_name}' not found for removal")
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove workspace definition for '{workspace_name}': {e}")
            return False