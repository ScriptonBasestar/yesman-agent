"""Google Gemini Provider Implementation.

Google Gemini API를 통한 제공업체 구현
Gemini Pro, Gemini Code 등 다양한 모델 지원
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from ..provider_interface import AIProvider, AIProviderType, AIResponse, AITask, TaskStatus


class GeminiProvider(AIProvider):
    """Google Gemini 제공업체."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://generativelanguage.googleapis.com/v1beta")
        self.session: aiohttp.ClientSession | None = None
        self._available_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro", "gemini-pro-vision"]

    def _get_provider_type(self) -> AIProviderType:
        return AIProviderType.GEMINI

    async def initialize(self) -> bool:
        """Gemini 제공업체 초기화."""
        if not self.api_key:
            print("Gemini API key not provided")
            return False

        try:
            # HTTP 클라이언트 세션 생성
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # API 연결 확인
            health_status = await self.health_check()
            if health_status.get("status") != "healthy":
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Failed to initialize Gemini provider: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False

    async def health_check(self) -> dict[str, Any]:
        """Gemini API 상태 확인."""
        if not self.session:
            return {"status": "not_initialized", "initialized": False}

        try:
            # 모델 목록 요청으로 API 상태 확인
            url = f"{self.base_url}/models?key={self.api_key}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])

                    return {"status": "healthy", "available_models": len(models), "base_url": self.base_url}
                elif response.status == 403:
                    return {"status": "unauthorized", "error": "Invalid API key or quota exceeded"}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_available_models(self) -> list[str]:
        """사용 가능한 모델 목록 반환."""
        if not self.session:
            return self._available_models

        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"].split("/")[-1] for model in data.get("models", [])]
                    return models if models else self._available_models
                else:
                    return self._available_models

        except Exception:
            return self._available_models

    def _prepare_contents(self, task: AITask) -> list[dict[str, Any]]:
        """작업을 Gemini 컨텐츠 형식으로 변환."""
        contents = []

        # 컨텍스트 메시지 추가
        if task.context:
            for msg in task.context:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

        # 현재 프롬프트 추가
        contents.append({"role": "user", "parts": [{"text": task.prompt}]})

        return contents

    async def execute_task(self, task: AITask) -> AIResponse:
        """단일 작업 실행."""
        if not self.session:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.GEMINI, model=task.model, error="Gemini provider not initialized")

        try:
            contents = self._prepare_contents(task)

            # 요청 데이터 구성
            request_data = {"contents": contents, "generationConfig": {"temperature": task.temperature, "candidateCount": 1}}

            if task.max_tokens:
                request_data["generationConfig"]["maxOutputTokens"] = task.max_tokens

            # Gemini API 호출
            model_name = f"models/{task.model}"
            url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"

            async with self.session.post(url, json=request_data, timeout=aiohttp.ClientTimeout(total=task.timeout)) as response:
                if response.status == 200:
                    data = await response.json()

                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        content = candidate["content"]["parts"][0]["text"]

                        return AIResponse(
                            content=content,
                            status=TaskStatus.COMPLETED,
                            provider=AIProviderType.GEMINI,
                            model=task.model,
                            usage=data.get("usageMetadata", {}),
                            metadata={"finishReason": candidate.get("finishReason"), "safetyRatings": candidate.get("safetyRatings", [])},
                        )
                    else:
                        error_msg = "No candidates in response"
                        if "promptFeedback" in data:
                            error_msg = f"Prompt blocked: {data['promptFeedback'].get('blockReason', 'Unknown')}"

                        return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.GEMINI, model=task.model, error=error_msg)
                else:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status}")

                    return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.GEMINI, model=task.model, error=error_msg)

        except TimeoutError:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.GEMINI, model=task.model, error=f"Task timed out after {task.timeout} seconds")
        except Exception as e:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.GEMINI, model=task.model, error=str(e))

    async def stream_task(self, task: AITask) -> AsyncGenerator[str, None]:
        """스트리밍 작업 실행."""
        if not self.session:
            yield json.dumps({"error": "Gemini provider not initialized", "status": "failed"})
            return

        try:
            contents = self._prepare_contents(task)

            # 요청 데이터 구성 (스트림 모드)
            request_data = {"contents": contents, "generationConfig": {"temperature": task.temperature, "candidateCount": 1}}

            if task.max_tokens:
                request_data["generationConfig"]["maxOutputTokens"] = task.max_tokens

            # Gemini API 스트리밍 호출
            model_name = f"models/{task.model}"
            url = f"{self.base_url}/{model_name}:streamGenerateContent?alt=sse&key={self.api_key}"

            async with self.session.post(url, json=request_data, timeout=aiohttp.ClientTimeout(total=task.timeout)) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status}")
                    yield json.dumps({"error": error_msg, "status": "failed"})
                    return

                # 스트림 응답 처리 (Server-Sent Events)
                async for line in response.content:
                    line_str = line.decode().strip()

                    if line_str.startswith("data: "):
                        data_str = line_str[6:]  # 'data: ' 제거

                        try:
                            data = json.loads(data_str)

                            if "candidates" in data and data["candidates"]:
                                candidate = data["candidates"][0]

                                if "content" in candidate:
                                    parts = candidate["content"].get("parts", [])
                                    if parts:
                                        content = parts[0].get("text", "")

                                        chunk_data = {"content": content, "done": False, "status": "running"}

                                        # 완료 확인
                                        finish_reason = candidate.get("finishReason")
                                        if finish_reason and finish_reason != "STOP":
                                            chunk_data["done"] = True
                                            chunk_data["status"] = "completed"
                                            chunk_data["finish_reason"] = finish_reason
                                        elif finish_reason == "STOP":
                                            chunk_data["done"] = True
                                            chunk_data["status"] = "completed"

                                        yield json.dumps(chunk_data)

                                        if chunk_data.get("done"):
                                            break

                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            yield json.dumps({"error": str(e), "status": "failed"})
                            return

        except TimeoutError:
            yield json.dumps({"error": f"Task timed out after {task.timeout} seconds", "status": "failed"})
        except Exception as e:
            yield json.dumps({"error": str(e), "status": "failed"})

    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소 (Gemini API는 명시적 취소 기능 없음)."""
        # 클라이언트 측에서 연결을 끊는 것으로 처리
        return True

    async def cleanup(self) -> None:
        """리소스 정리."""
        if self.session:
            await self.session.close()
            self.session = None

    def get_required_config_keys(self) -> list[str]:
        """필수 설정 키 목록."""
        return ["api_key"]

    def get_config_schema(self) -> dict[str, Any]:
        """설정 스키마 반환."""
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "Gemini API Key", "description": "Your Google AI Studio API key", "format": "password"},
                "base_url": {"type": "string", "title": "API Base URL", "description": "Gemini API base URL", "default": "https://generativelanguage.googleapis.com/v1beta"},
                "default_model": {
                    "type": "string",
                    "title": "Default Model",
                    "description": "Default model to use",
                    "default": "gemini-1.5-pro",
                    "enum": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro", "gemini-pro-vision"],
                },
                "safety_settings": {
                    "type": "object",
                    "title": "Safety Settings",
                    "description": "Content safety settings",
                    "properties": {
                        "harassment": {"type": "string", "enum": ["BLOCK_NONE", "BLOCK_ONLY_HIGH", "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_LOW_AND_ABOVE"], "default": "BLOCK_MEDIUM_AND_ABOVE"},
                        "hate_speech": {"type": "string", "enum": ["BLOCK_NONE", "BLOCK_ONLY_HIGH", "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_LOW_AND_ABOVE"], "default": "BLOCK_MEDIUM_AND_ABOVE"},
                        "sexually_explicit": {"type": "string", "enum": ["BLOCK_NONE", "BLOCK_ONLY_HIGH", "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_LOW_AND_ABOVE"], "default": "BLOCK_MEDIUM_AND_ABOVE"},
                        "dangerous_content": {"type": "string", "enum": ["BLOCK_NONE", "BLOCK_ONLY_HIGH", "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_LOW_AND_ABOVE"], "default": "BLOCK_MEDIUM_AND_ABOVE"},
                    },
                },
            },
            "required": ["api_key"],
        }


class GeminiCodeProvider(GeminiProvider):
    """Google Gemini Code 전용 제공업체."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        # 코딩 전용 모델들
        self._available_models = ["gemini-1.5-pro", "gemini-1.5-flash", "code-bison", "codechat-bison"]

    def _get_provider_type(self) -> AIProviderType:
        return AIProviderType.GEMINI_CODE

    def _prepare_contents(self, task: AITask) -> list[dict[str, Any]]:
        """코딩 작업에 최적화된 컨텐츠 준비."""
        contents = super()._prepare_contents(task)

        # 코딩 컨텍스트 추가
        if task.workspace_path:
            system_prompt = f"""
You are an expert code assistant.
Working directory: {task.workspace_path}
Available tools: {", ".join(task.tools or [])}

Please provide clear, well-documented code solutions.
"""
            contents.insert(0, {"role": "user", "parts": [{"text": system_prompt}]})

        return contents

    def get_config_schema(self) -> dict[str, Any]:
        """코딩 전용 설정 스키마."""
        schema = super().get_config_schema()

        # 코딩 관련 설정 추가
        schema["properties"]["default_model"]["enum"] = ["gemini-1.5-pro", "gemini-1.5-flash", "code-bison", "codechat-bison"]
        schema["properties"]["default_model"]["default"] = "gemini-1.5-pro"

        schema["properties"]["code_execution"] = {"type": "boolean", "title": "Enable Code Execution", "description": "Allow Gemini to execute code", "default": False}

        return schema
