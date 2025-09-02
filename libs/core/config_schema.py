# Copyright notice.

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Configuration schemas using Pydantic for type safety and validation."""


class TmuxConfig(BaseModel):
    """Tmux-specific configuration settings."""

    default_shell: str = "/bin/bash"
    base_index: int = 0
    pane_base_index: int = 0
    mouse: bool = True
    status_position: str = Field(default="bottom", pattern="^(top|bottom)$")
    status_interval: int = Field(default=1, ge=1, le=60)


class LoggingConfig(BaseModel):
    """Logging configuration settings."""

    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None
    log_path: str = "~/.scripton/yesman/logs/"
    max_size: int = Field(default=10485760, ge=1048576)  # 10MB minimum
    backup_count: int = Field(default=5, ge=1, le=20)

    @field_validator("level")
    @classmethod
    def uppercase_level(cls, v: str) -> str:
        """Ensure log level is uppercase.

        Returns:
        str: Description of return value.
        """
        return v.upper()


class SessionConfig(BaseModel):
    """Session management configuration."""

    sessions_dir: str = "sessions"
    templates_dir: str = "templates"
    default_window_name: str = "main"
    default_layout: str = "even-horizontal"


class AIConfig(BaseModel):
    """AI/LLM configuration settings."""

    provider: str = Field(default="anthropic", pattern="^(anthropic|openai|local)$")
    model: str = "claude-3-opus-20240229"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=100, le=32000)
    api_key_env: str = "ANTHROPIC_API_KEY"
    base_url: str | None = None


class HeadlessConfig(BaseModel):
    """Claude Code Headless configuration settings."""

    enabled: bool = False
    claude_binary_path: str = "claude"
    workspace_root: str = "~/.scripton/yesman/workspaces"
    allowed_tools: list[str] = Field(default_factory=lambda: ["Read", "Edit", "Bash", "Write"])
    max_concurrent_agents: int = Field(default=5, ge=1, le=20)
    agent_timeout: int = Field(default=300, ge=30, le=3600)  # seconds
    forbidden_paths: list[str] = Field(default_factory=lambda: ["/etc", "~/.ssh", "/root", "/sys", "/proc"])
    cleanup_interval: int = Field(default=300, ge=60, le=3600)  # seconds

    @field_validator("workspace_root", "forbidden_paths", mode="after")
    @classmethod
    def expand_paths(cls, v) -> str | list[str]:
        """Expand user home directory in paths."""
        if isinstance(v, str):
            return str(Path(v).expanduser())
        elif isinstance(v, list):
            return [str(Path(path).expanduser()) for path in v]
        return v


class ClaudeConfig(BaseModel):
    """Claude Code integration configuration."""

    mode: str = Field(default="interactive", pattern="^(interactive|headless)$")
    headless: HeadlessConfig = Field(default_factory=HeadlessConfig)


class DatabaseConfig(BaseModel):
    """Database configuration (optional)."""

    enabled: bool = False
    url: str = "sqlite:///~/.scripton/yesman/yesman.db"
    pool_size: int = Field(default=5, ge=1, le=20)
    echo: bool = False


class ServerConfig(BaseModel):
    """Server configuration settings."""

    host: str = "localhost"
    port: int = Field(default=10501, ge=1, le=65535)


class YesmanConfigSchema(BaseModel):
    """Main configuration schema for Yesman."""

    model_config = ConfigDict(extra="allow")  # Allow extra fields for testing

    # Core settings
    mode: str = Field(default="merge", pattern="^(merge|isolated|local)$")
    root_dir: str = "~/.scripton/yesman"

    # Sub-configurations
    tmux: TmuxConfig = Field(default_factory=TmuxConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    # Additional settings
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    auto_cleanup_days: int = Field(default=30, ge=1)
    enable_telemetry: bool = False

    # Custom settings (allows flexibility)
    custom: dict[str, Any] = Field(default_factory=dict)

    @field_validator("root_dir")
    @classmethod
    def expand_path(cls, v: str) -> str:
        """Expand user home directory in paths.

        Returns:
        str: Description of return value.
        """
        return str(Path(v).expanduser())

    def model_post_init(self, __context: object) -> None:
        """Post-initialization validation and setup."""
        # Expand paths in nested configs
        if self.logging.log_path:
            self.logging.log_path = str(Path(self.logging.log_path).expanduser())
        if self.logging.file:
            self.logging.file = str(Path(self.logging.file).expanduser())
        if self.database.url.startswith("sqlite:///"):
            db_path = self.database.url.replace("sqlite:///", "")
            self.database.url = f"sqlite:///{Path(db_path).expanduser()}"

    # Config is now handled by model_config above
