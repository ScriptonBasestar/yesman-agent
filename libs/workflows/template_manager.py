"""Workflow template management with YAML configuration support.

This module manages workflow templates for LangChain-based automation workflows.
Templates are loaded from user and project-specific directories.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from libs.core.error_handling import ErrorCategory, YesmanError
from libs.workflows.models import WorkflowConfig


class TemplateManagerError(YesmanError):
    """Template manager specific error."""

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message=message, category=ErrorCategory.CONFIGURATION, **kwargs)


class WorkflowTemplateManager:
    """Manager for workflow template configuration and loading."""

    def __init__(self, base_template_dir: Path | None = None) -> None:
        """Initialize template manager.

        Args:
            base_template_dir: Base directory for workflow templates
        """
        self.logger = logging.getLogger("yesman.workflows.template_manager")

        # Template directories (in order of precedence)
        self.template_dirs = []

        # User-specific templates (highest precedence)
        user_template_dir = Path.home() / ".scripton" / "yesman" / "workflows"
        if user_template_dir.exists():
            self.template_dirs.append(user_template_dir)

        # Project-specific templates
        project_template_dir = Path.cwd() / ".scripton" / "yesman" / "workflows"
        if project_template_dir.exists():
            self.template_dirs.append(project_template_dir)

        # Custom base directory
        if base_template_dir and base_template_dir.exists():
            self.template_dirs.append(base_template_dir)

        # Built-in templates (lowest precedence)
        builtin_template_dir = Path(__file__).parent / "templates"
        self.template_dirs.append(builtin_template_dir)

        # Template cache
        self._template_cache: dict[str, dict[str, Any]] = {}
        self._cache_timestamp: datetime | None = None
        self._cache_ttl = 300  # 5 minutes

        self.logger.info(f"Template manager initialized with directories: {[str(d) for d in self.template_dirs]}")

    def create_template_directories(self) -> None:
        """Create template directories if they don't exist."""
        user_template_dir = Path.home() / ".scripton" / "yesman" / "workflows"
        project_template_dir = Path.cwd() / ".scripton" / "yesman" / "workflows"

        for template_dir in [user_template_dir, project_template_dir]:
            template_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created template directory: {template_dir}")

            if template_dir not in self.template_dirs:
                self.template_dirs.insert(0, template_dir)

    def list_templates(self, refresh_cache: bool = False) -> dict[str, dict[str, Any]]:
        """List all available workflow templates.

        Args:
            refresh_cache: Force cache refresh

        Returns:
            Dictionary mapping template IDs to template metadata
        """
        if self._should_refresh_cache() or refresh_cache:
            self._refresh_template_cache()

        return self._template_cache.copy()

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        """Get specific template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template data if found, None otherwise
        """
        templates = self.list_templates()
        return templates.get(template_id)

    def get_template_config(self, template_id: str) -> WorkflowConfig | None:
        """Get workflow configuration for template.

        Args:
            template_id: Template identifier

        Returns:
            WorkflowConfig instance if template found and valid

        Raises:
            TemplateManagerError: If template is invalid
        """
        template_data = self.get_template(template_id)
        if not template_data:
            return None

        try:
            # Load the actual YAML file
            template_path = template_data["file_path"]
            with open(template_path, encoding="utf-8") as f:
                yaml_content = yaml.safe_load(f)

            # Extract workflow configuration
            workflow_config = yaml_content.get("workflow", {})

            # Create WorkflowConfig with validation
            config = WorkflowConfig(**workflow_config)

            return config

        except Exception as e:
            self.logger.exception(f"Failed to load template config for {template_id}")
            raise TemplateManagerError(f"Invalid template configuration '{template_id}': {e}")

    def save_template(self, template_id: str, template_data: dict[str, Any], user_template: bool = True) -> Path:
        """Save workflow template to YAML file.

        Args:
            template_id: Template identifier
            template_data: Template configuration data
            user_template: Whether to save as user template (vs project template)

        Returns:
            Path to saved template file

        Raises:
            TemplateManagerError: If save fails
        """
        try:
            # Determine save location
            if user_template:
                template_dir = Path.home() / ".scripton" / "yesman" / "workflows"
            else:
                template_dir = Path.cwd() / ".scripton" / "yesman" / "workflows"

            template_dir.mkdir(parents=True, exist_ok=True)
            template_path = template_dir / f"{template_id}.yaml"

            # Add metadata
            full_template = {"metadata": {"id": template_id, "created_at": datetime.now(UTC).isoformat(), "version": "1.0"}, **template_data}

            # Save to file
            with open(template_path, "w", encoding="utf-8") as f:
                yaml.dump(full_template, f, default_flow_style=False, indent=2)

            # Refresh cache
            self._refresh_template_cache()

            self.logger.info(f"Saved template '{template_id}' to {template_path}")
            return template_path

        except Exception as e:
            self.logger.exception(f"Failed to save template {template_id}")
            raise TemplateManagerError(f"Failed to save template '{template_id}': {e}")

    def delete_template(self, template_id: str, user_template: bool = True) -> bool:
        """Delete workflow template.

        Args:
            template_id: Template identifier
            user_template: Whether to delete from user templates (vs project)

        Returns:
            True if template was deleted

        Raises:
            TemplateManagerError: If deletion fails
        """
        try:
            # Find template file
            template_data = self.get_template(template_id)
            if not template_data:
                return False

            template_path = Path(template_data["file_path"])

            # Verify it's in the expected location
            if user_template:
                expected_dir = Path.home() / ".scripton" / "yesman" / "workflows"
            else:
                expected_dir = Path.cwd() / ".scripton" / "yesman" / "workflows"

            if not template_path.parent == expected_dir:
                raise TemplateManagerError(f"Template '{template_id}' is not in expected location")

            # Delete file
            template_path.unlink()

            # Refresh cache
            self._refresh_template_cache()

            self.logger.info(f"Deleted template '{template_id}' from {template_path}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to delete template {template_id}")
            raise TemplateManagerError(f"Failed to delete template '{template_id}': {e}")

    def validate_template(self, template_data: dict[str, Any]) -> list[str]:
        """Validate template configuration.

        Args:
            template_data: Template data to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Check required top-level fields
            required_fields = ["metadata", "workflow"]
            for field in required_fields:
                if field not in template_data:
                    errors.append(f"Missing required field: {field}")

            # Validate metadata
            metadata = template_data.get("metadata", {})
            if not metadata.get("name"):
                errors.append("Missing template name in metadata")

            # Validate workflow configuration
            workflow_config = template_data.get("workflow", {})
            if not workflow_config.get("steps"):
                errors.append("Workflow must have at least one step")

            # Try to create WorkflowConfig to validate structure
            try:
                WorkflowConfig(**workflow_config)
            except Exception as e:
                errors.append(f"Invalid workflow configuration: {e}")

        except Exception as e:
            errors.append(f"Template validation failed: {e}")

        return errors

    def create_template_from_config(self, template_id: str, name: str, description: str, steps: list[dict[str, Any]], **kwargs) -> dict[str, Any]:
        """Create template data structure from configuration.

        Args:
            template_id: Template identifier
            name: Template display name
            description: Template description
            steps: Workflow steps configuration
            **kwargs: Additional workflow configuration options

        Returns:
            Complete template data structure
        """
        template_data = {
            "metadata": {"id": template_id, "name": name, "description": description, "version": "1.0", "created_at": datetime.now(UTC).isoformat()},
            "workflow": {
                "steps": steps,
                "variables": kwargs.get("variables", []),
                "timeout": kwargs.get("timeout", 1800),
                "continue_on_error": kwargs.get("continue_on_error", False),
                "recovery_strategies": kwargs.get("recovery_strategies", ["retry", "skip"]),
                "checkpoint_interval": kwargs.get("checkpoint_interval", 5),
            },
        }

        return template_data

    def _should_refresh_cache(self) -> bool:
        """Check if template cache should be refreshed."""
        if not self._cache_timestamp:
            return True

        elapsed = (datetime.now(UTC) - self._cache_timestamp).total_seconds()
        return elapsed > self._cache_ttl

    def _refresh_template_cache(self) -> None:
        """Refresh the template cache by scanning directories."""
        self.logger.debug("Refreshing template cache")
        self._template_cache.clear()

        for template_dir in self.template_dirs:
            if not template_dir.exists():
                continue

            try:
                self._scan_template_directory(template_dir)
            except Exception as e:
                self.logger.warning(f"Failed to scan template directory {template_dir}: {e}")

        self._cache_timestamp = datetime.now(UTC)
        self.logger.debug(f"Template cache refreshed with {len(self._template_cache)} templates")

    def _scan_template_directory(self, template_dir: Path) -> None:
        """Scan directory for template YAML files."""
        for yaml_file in template_dir.glob("*.yaml"):
            try:
                template_data = self._load_template_file(yaml_file)
                if template_data:
                    template_id = template_data["metadata"].get("id", yaml_file.stem)

                    # Don't overwrite higher precedence templates
                    if template_id not in self._template_cache:
                        template_data["file_path"] = str(yaml_file)
                        template_data["source_dir"] = str(template_dir)
                        self._template_cache[template_id] = template_data

            except Exception as e:
                self.logger.warning(f"Failed to load template {yaml_file}: {e}")

    def _load_template_file(self, yaml_file: Path) -> dict[str, Any] | None:
        """Load and validate template YAML file."""
        try:
            with open(yaml_file, encoding="utf-8") as f:
                template_data = yaml.safe_load(f)

            if not isinstance(template_data, dict):
                self.logger.warning(f"Template {yaml_file} is not a valid YAML object")
                return None

            # Basic validation
            if "metadata" not in template_data:
                self.logger.warning(f"Template {yaml_file} missing metadata section")
                return None

            if "workflow" not in template_data:
                self.logger.warning(f"Template {yaml_file} missing workflow section")
                return None

            return template_data

        except Exception as e:
            self.logger.warning(f"Failed to parse template {yaml_file}: {e}")
            return None
