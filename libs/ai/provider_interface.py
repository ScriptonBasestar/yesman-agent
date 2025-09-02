"""Multi-AI Provider Interface System.

이 모듈은 다양한 AI 제공업체(Claude Code, Ollama, ChatGPT, Gemini 등)를
통합 인터페이스로 관리하는 시스템을 제공합니다.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from typing import Any


class AIProviderType(Enum):
    """지원하는 AI 제공업체 타입."""

    CLAUDE_CODE = "claude_code"
    CLAUDE_API = "claude_api"
    OLLAMA = "ollama"
    OPENAI_GPT = "openai_gpt"
    GEMINI = "gemini"
    GEMINI_CODE = "gemini_code"


class TaskStatus(Enum):
    """AI 작업 상태."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AIMessage:
    """AI 메시지 표준 형식."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class AIResponse:
    """AI 응답 표준 형식."""

    content: str
    status: TaskStatus
    provider: AIProviderType
    model: str
    usage: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class AITask:
    """AI 작업 정의."""

    task_id: str
    prompt: str
    model: str
    provider: AIProviderType
    workspace_path: str | None = None
    tools: list[str] | None = None
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout: int = 300
    stream: bool = False
    context: list[AIMessage] | None = None
    metadata: dict[str, Any] | None = None


class AIProvider(ABC):
    """AI 제공업체 추상 인터페이스."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.provider_type = self._get_provider_type()
        self._initialized = False

    @abstractmethod
    def _get_provider_type(self) -> AIProviderType:
        """제공업체 타입 반환."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """제공업체 초기화."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """제공업체 상태 확인."""
        pass

    @abstractmethod
    async def get_available_models(self) -> list[str]:
        """사용 가능한 모델 목록 반환."""
        pass

    @abstractmethod
    async def execute_task(self, task: AITask) -> AIResponse:
        """단일 작업 실행."""
        pass

    @abstractmethod
    async def stream_task(self, task: AITask) -> AsyncGenerator[str, None]:
        """스트리밍 작업 실행."""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """리소스 정리."""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def validate_config(self) -> list[str]:
        """설정 검증 - 오류 목록 반환."""
        errors = []
        required_keys = self.get_required_config_keys()

        for key in required_keys:
            if key not in self.config:
                errors.append(f"Missing required config key: {key}")

        return errors

    @abstractmethod
    def get_required_config_keys(self) -> list[str]:
        """필수 설정 키 목록 반환."""
        pass

    def get_config_schema(self) -> dict[str, Any]:
        """설정 스키마 반환 (UI 생성용)."""
        return {"type": "object", "properties": {}, "required": self.get_required_config_keys()}


class AIProviderManager:
    """AI 제공업체 매니저."""

    def __init__(self) -> None:
        self._providers: dict[AIProviderType, AIProvider] = {}
        self._active_tasks: dict[str, AITask] = {}
        self._task_handlers: dict[str, asyncio.Task] = {}

    def register_provider(self, provider: AIProvider) -> None:
        """제공업체 등록."""
        self._providers[provider.provider_type] = provider

    def get_provider(self, provider_type: AIProviderType) -> AIProvider | None:
        """제공업체 가져오기."""
        return self._providers.get(provider_type)

    async def initialize_all(self) -> dict[AIProviderType, bool]:
        """모든 제공업체 초기화."""
        results = {}
        for provider_type, provider in self._providers.items():
            try:
                results[provider_type] = await provider.initialize()
            except Exception as e:
                print(f"Failed to initialize {provider_type}: {e}")
                results[provider_type] = False
        return results

    async def health_check_all(self) -> dict[AIProviderType, dict[str, Any]]:
        """모든 제공업체 상태 확인."""
        results = {}
        for provider_type, provider in self._providers.items():
            try:
                if provider.is_initialized:
                    results[provider_type] = await provider.health_check()
                else:
                    results[provider_type] = {"status": "not_initialized"}
            except Exception as e:
                results[provider_type] = {"status": "error", "error": str(e)}
        return results

    async def execute_task(self, task: AITask) -> AIResponse:
        """작업 실행."""
        provider = self.get_provider(task.provider)
        if not provider:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=task.provider, model=task.model, error=f"Provider {task.provider} not found")

        if not provider.is_initialized:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=task.provider, model=task.model, error=f"Provider {task.provider} not initialized")

        self._active_tasks[task.task_id] = task

        try:
            response = await provider.execute_task(task)
            return response
        except Exception as e:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=task.provider, model=task.model, error=str(e))
        finally:
            self._active_tasks.pop(task.task_id, None)

    async def stream_task(self, task: AITask) -> AsyncGenerator[str, None]:
        """스트리밍 작업 실행."""
        provider = self.get_provider(task.provider)
        if not provider:
            yield json.dumps({"error": f"Provider {task.provider} not found", "status": "failed"})
            return

        if not provider.is_initialized:
            yield json.dumps({"error": f"Provider {task.provider} not initialized", "status": "failed"})
            return

        self._active_tasks[task.task_id] = task

        try:
            async for chunk in provider.stream_task(task):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e), "status": "failed"})
        finally:
            self._active_tasks.pop(task.task_id, None)

    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소."""
        task = self._active_tasks.get(task_id)
        if not task:
            return False

        provider = self.get_provider(task.provider)
        if not provider:
            return False

        return await provider.cancel_task(task_id)

    def get_active_tasks(self) -> list[AITask]:
        """활성 작업 목록 반환."""
        return list(self._active_tasks.values())

    async def cleanup_all(self) -> None:
        """모든 제공업체 정리."""
        for provider in self._providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                print(f"Error cleaning up provider: {e}")

    def get_providers_info(self) -> dict[str, dict[str, Any]]:
        """제공업체 정보 반환."""
        info = {}
        for provider_type, provider in self._providers.items():
            info[provider_type.value] = {"initialized": provider.is_initialized, "config_schema": provider.get_config_schema(), "required_keys": provider.get_required_config_keys()}
        return info


# 전역 매니저 인스턴스
ai_provider_manager = AIProviderManager()
