# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""AI-powered automation and learning components."""

from .adaptive_response import AdaptiveResponse
from .response_analyzer import ResponseAnalyzer

# Multi-Provider AI Integration
from .provider_interface import (
    AIProvider,
    AIProviderType,
    AITask,
    AIResponse,
    TaskStatus,
    AIMessage,
    AIProviderManager,
    ai_provider_manager
)

from .providers.claude_code_provider import ClaudeCodeProvider
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider, GeminiCodeProvider


__all__ = [
    "AdaptiveResponse",
    "ResponseAnalyzer",
    # Multi-Provider AI
    'AIProvider',
    'AIProviderType', 
    'AITask',
    'AIResponse',
    'TaskStatus',
    'AIMessage',
    'AIProviderManager',
    'ai_provider_manager',
    'ClaudeCodeProvider',
    'OllamaProvider', 
    'OpenAIProvider',
    'GeminiProvider',
    'GeminiCodeProvider'
]
