# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""AI-powered automation and learning components."""

from .adaptive_response import AdaptiveResponse

# Multi-Provider AI Integration
from .provider_interface import AIMessage, AIProvider, AIProviderManager, AIProviderType, AIResponse, AITask, TaskStatus, ai_provider_manager
from .providers.claude_code_provider import ClaudeCodeProvider
from .providers.gemini_provider import GeminiCodeProvider, GeminiProvider
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .response_analyzer import ResponseAnalyzer

__all__ = [
    "AdaptiveResponse",
    "ResponseAnalyzer",
    # Multi-Provider AI
    "AIProvider",
    "AIProviderType",
    "AITask",
    "AIResponse",
    "TaskStatus",
    "AIMessage",
    "AIProviderManager",
    "ai_provider_manager",
    "ClaudeCodeProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "GeminiCodeProvider",
]
