"""LangChain integration for Claude Code automation workflows.

This package provides integration between LangChain workflows and Claude Code CLI,
enabling advanced features like session continuity, MCP server integration,
and complex multi-step automation workflows.
"""

from libs.langchain_integration.langchain_claude_integration import ClaudeAgent

__all__ = ["ClaudeAgent"]
