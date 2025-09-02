"""Multi-AI Provider API Router.

다양한 AI 제공업체를 통합 관리하는 API 엔드포인트들
"""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from libs.ai import AIMessage, AIProviderType, AITask, ClaudeCodeProvider, GeminiCodeProvider, GeminiProvider, OllamaProvider, OpenAIProvider, ai_provider_manager

router = APIRouter(prefix="/ai-providers", tags=["AI Providers"])


# Pydantic 모델들
class ProviderConfigModel(BaseModel):
    """AI 제공업체 설정 모델."""

    provider_type: AIProviderType
    config: dict[str, Any]
    name: str | None = None
    description: str | None = None


class AITaskModel(BaseModel):
    """AI 작업 요청 모델."""

    prompt: str
    provider: AIProviderType
    model: str
    workspace_path: str | None = None
    tools: list[str] | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    timeout: int = Field(default=300, gt=0, le=1800)
    stream: bool = False
    context: list[dict[str, str]] | None = None


class AITaskResponse(BaseModel):
    """AI 작업 응답 모델."""

    task_id: str
    status: str
    content: str | None = None
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None


class ProviderStatusModel(BaseModel):
    """제공업체 상태 모델."""

    provider_type: str
    initialized: bool
    status: str
    available_models: list[str] = []
    health_info: dict[str, Any] = {}
    config_schema: dict[str, Any] = {}


# 제공업체 인스턴스 매핑
PROVIDER_CLASSES = {
    AIProviderType.CLAUDE_CODE: ClaudeCodeProvider,
    AIProviderType.OLLAMA: OllamaProvider,
    AIProviderType.OPENAI_GPT: OpenAIProvider,
    AIProviderType.GEMINI: GeminiProvider,
    AIProviderType.GEMINI_CODE: GeminiCodeProvider,
}


@router.get("/", response_model=list[ProviderStatusModel])
async def list_providers() -> list[ProviderStatusModel]:
    """등록된 모든 AI 제공업체 목록과 상태 반환."""
    providers_info = []

    # 등록된 제공업체들
    for provider_type, provider in ai_provider_manager._providers.items():
        health_info = await provider.health_check()
        available_models = await provider.get_available_models() if provider.is_initialized else []

        providers_info.append(
            ProviderStatusModel(
                provider_type=provider_type.value,
                initialized=provider.is_initialized,
                status=health_info.get("status", "unknown"),
                available_models=available_models,
                health_info=health_info,
                config_schema=provider.get_config_schema(),
            )
        )

    # 미등록 제공업체들 (스키마 정보만)
    registered_types = {p.provider_type for p in ai_provider_manager._providers.values()}
    for provider_type, provider_class in PROVIDER_CLASSES.items():
        if provider_type not in registered_types:
            dummy_provider = provider_class({})

            providers_info.append(
                ProviderStatusModel(
                    provider_type=provider_type.value,
                    initialized=False,
                    status="not_configured",
                    available_models=[],
                    health_info={"status": "not_configured"},
                    config_schema=dummy_provider.get_config_schema(),
                )
            )

    return providers_info


@router.post("/register")
async def register_provider(config: ProviderConfigModel) -> dict[str, str]:
    """AI 제공업체 등록."""
    try:
        provider_class = PROVIDER_CLASSES.get(config.provider_type)
        if not provider_class:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported provider type: {config.provider_type}")

        # 제공업체 인스턴스 생성
        provider = provider_class(config.config)

        # 설정 검증
        validation_errors = provider.validate_config()
        if validation_errors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"validation_errors": validation_errors})

        # 제공업체 등록 및 초기화
        ai_provider_manager.register_provider(provider)
        initialized = await provider.initialize()

        if not initialized:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initialize provider {config.provider_type}")

        return {"success": True, "message": f"Provider {config.provider_type} registered and initialized successfully", "provider_type": config.provider_type.value}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to register provider: {str(e)}")


@router.delete("/{provider_type}")
async def unregister_provider(provider_type: AIProviderType) -> dict[str, str | bool]:
    """AI 제공업체 등록 해제."""
    provider = ai_provider_manager.get_provider(provider_type)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider {provider_type} not found")

    try:
        await provider.cleanup()
        ai_provider_manager._providers.pop(provider_type, None)

        return {"success": True, "message": f"Provider {provider_type} unregistered successfully"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to unregister provider: {str(e)}")


@router.get("/{provider_type}/status", response_model=ProviderStatusModel)
async def get_provider_status(provider_type: AIProviderType) -> ProviderStatusModel:
    """특정 AI 제공업체 상태 조회."""
    provider = ai_provider_manager.get_provider(provider_type)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider {provider_type} not found")

    health_info = await provider.health_check()
    available_models = await provider.get_available_models() if provider.is_initialized else []

    return ProviderStatusModel(
        provider_type=provider_type.value,
        initialized=provider.is_initialized,
        status=health_info.get("status", "unknown"),
        available_models=available_models,
        health_info=health_info,
        config_schema=provider.get_config_schema(),
    )


@router.get("/{provider_type}/models")
async def get_provider_models(provider_type: AIProviderType) -> dict[str, str | list[str]]:
    """특정 제공업체의 사용 가능한 모델 목록 반환."""
    provider = ai_provider_manager.get_provider(provider_type)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider {provider_type} not found")

    if not provider.is_initialized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider {provider_type} not initialized")

    try:
        models = await provider.get_available_models()
        return {"provider": provider_type.value, "models": models}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get models: {str(e)}")


@router.post("/tasks", response_model=AITaskResponse)
async def create_task(task_request: AITaskModel) -> AITaskResponse:
    """AI 작업 실행."""
    try:
        # 컨텍스트 변환
        context = None
        if task_request.context:
            context = [AIMessage(role=msg["role"], content=msg["content"], metadata=msg.get("metadata")) for msg in task_request.context]

        # AI 작업 생성
        task = AITask(
            task_id=str(uuid.uuid4()),
            prompt=task_request.prompt,
            provider=task_request.provider,
            model=task_request.model,
            workspace_path=task_request.workspace_path,
            tools=task_request.tools,
            temperature=task_request.temperature,
            max_tokens=task_request.max_tokens,
            timeout=task_request.timeout,
            stream=task_request.stream,
            context=context,
        )

        # 스트리밍 요청인 경우
        if task_request.stream:

            async def stream_generator():
                async for chunk in ai_provider_manager.stream_task(task):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/plain", headers={"Cache-Control": "no-cache"})

        # 일반 작업 실행
        response = await ai_provider_manager.execute_task(task)

        return AITaskResponse(
            task_id=task.task_id,
            status=response.status.value,
            content=response.content,
            provider=response.provider.value,
            model=response.model,
            usage=response.usage,
            metadata=response.metadata,
            error=response.error,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to execute task: {str(e)}")


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str) -> dict[str, str | bool]:
    """AI 작업 취소."""
    try:
        cancelled = await ai_provider_manager.cancel_task(task_id)

        if cancelled:
            return {"success": True, "message": f"Task {task_id} cancelled"}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found or already completed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to cancel task: {str(e)}")


@router.get("/tasks")
async def list_active_tasks() -> dict[str, list[dict[str, Any]]]:
    """활성 작업 목록 반환."""
    try:
        active_tasks = ai_provider_manager.get_active_tasks()

        return {
            "active_tasks": len(active_tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "provider": task.provider.value,
                    "model": task.model,
                    "prompt": task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt,
                    "timeout": task.timeout,
                    "workspace_path": task.workspace_path,
                }
                for task in active_tasks
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list tasks: {str(e)}")


@router.post("/health-check")
async def health_check_all() -> dict[str, str | dict[str, Any]]:
    """모든 제공업체 상태 점검."""
    try:
        health_results = await ai_provider_manager.health_check_all()

        return {
            "overall_status": "healthy" if all(result.get("status") == "healthy" for result in health_results.values()) else "degraded",
            "providers": {provider_type.value: result for provider_type, result in health_results.items()},
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to perform health check: {str(e)}")


@router.post("/initialize-all")
async def initialize_all_providers() -> dict[str, str | dict[str, dict[str, Any]]]:
    """모든 등록된 제공업체 초기화."""
    try:
        results = await ai_provider_manager.initialize_all()

        return {"success": all(results.values()), "results": {provider_type.value: success for provider_type, success in results.items()}}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initialize providers: {str(e)}")


# 백그라운드 정리 작업
async def cleanup_providers_background() -> None:
    """백그라운드에서 제공업체들 정리."""
    await ai_provider_manager.cleanup_all()


@router.post("/cleanup")
async def cleanup_providers(background_tasks: BackgroundTasks) -> dict[str, str | bool]:
    """모든 제공업체 리소스 정리."""
    background_tasks.add_task(cleanup_providers_background)

    return {"success": True, "message": "Cleanup task scheduled in background"}
