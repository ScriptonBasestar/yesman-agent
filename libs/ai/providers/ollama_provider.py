"""
Ollama Provider Implementation

Ollama 로컬 AI 모델을 통한 제공업체 구현
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from ..provider_interface import AIProvider, AIProviderType, AITask, AIResponse, TaskStatus


class OllamaProvider(AIProvider):
    """Ollama 제공업체"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.session: Optional[aiohttp.ClientSession] = None
        self._available_models: List[str] = []
    
    def _get_provider_type(self) -> AIProviderType:
        return AIProviderType.OLLAMA
    
    async def initialize(self) -> bool:
        """Ollama 제공업체 초기화"""
        try:
            # HTTP 클라이언트 세션 생성
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Ollama 서버 연결 확인
            health_status = await self.health_check()
            if health_status.get('status') != 'healthy':
                return False
            
            # 사용 가능한 모델 목록 로드
            self._available_models = await self._fetch_available_models()
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize Ollama provider: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Ollama 서버 상태 확인"""
        if not self.session:
            return {
                "status": "not_initialized",
                "initialized": False
            }
        
        try:
            async with self.session.get(f"{self.base_url}/api/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    return {
                        "status": "healthy",
                        "ollama_version": version_data.get("version", "unknown"),
                        "available_models": len(self._available_models),
                        "base_url": self.base_url
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _fetch_available_models(self) -> List[str]:
        """Ollama에서 사용 가능한 모델 목록 가져오기"""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    return models
                else:
                    print(f"Failed to fetch Ollama models: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []
    
    async def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 반환"""
        if not self._available_models and self._initialized:
            self._available_models = await self._fetch_available_models()
        return self._available_models
    
    async def execute_task(self, task: AITask) -> AIResponse:
        """단일 작업 실행"""
        if not self.session:
            return AIResponse(
                content="",
                status=TaskStatus.FAILED,
                provider=AIProviderType.OLLAMA,
                model=task.model,
                error="Ollama provider not initialized"
            )
        
        try:
            # 요청 데이터 구성
            request_data = {
                "model": task.model,
                "prompt": task.prompt,
                "stream": False,
                "options": {
                    "temperature": task.temperature
                }
            }
            
            if task.max_tokens:
                request_data["options"]["num_predict"] = task.max_tokens
            
            # Ollama API 호출
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=task.timeout)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    return AIResponse(
                        content=data.get("response", ""),
                        status=TaskStatus.COMPLETED,
                        provider=AIProviderType.OLLAMA,
                        model=task.model,
                        usage={
                            "total_duration": data.get("total_duration", 0),
                            "load_duration": data.get("load_duration", 0),
                            "prompt_eval_count": data.get("prompt_eval_count", 0),
                            "eval_count": data.get("eval_count", 0)
                        },
                        metadata={
                            "done": data.get("done", False),
                            "context": data.get("context", [])
                        }
                    )
                else:
                    error_text = await response.text()
                    return AIResponse(
                        content="",
                        status=TaskStatus.FAILED,
                        provider=AIProviderType.OLLAMA,
                        model=task.model,
                        error=f"HTTP {response.status}: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            return AIResponse(
                content="",
                status=TaskStatus.FAILED,
                provider=AIProviderType.OLLAMA,
                model=task.model,
                error=f"Task timed out after {task.timeout} seconds"
            )
        except Exception as e:
            return AIResponse(
                content="",
                status=TaskStatus.FAILED,
                provider=AIProviderType.OLLAMA,
                model=task.model,
                error=str(e)
            )
    
    async def stream_task(self, task: AITask) -> AsyncGenerator[str, None]:
        """스트리밍 작업 실행"""
        if not self.session:
            yield json.dumps({
                "error": "Ollama provider not initialized",
                "status": "failed"
            })
            return
        
        try:
            # 요청 데이터 구성 (스트림 모드)
            request_data = {
                "model": task.model,
                "prompt": task.prompt,
                "stream": True,
                "options": {
                    "temperature": task.temperature
                }
            }
            
            if task.max_tokens:
                request_data["options"]["num_predict"] = task.max_tokens
            
            # 스트리밍 요청
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=task.timeout)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    yield json.dumps({
                        "error": f"HTTP {response.status}: {error_text}",
                        "status": "failed"
                    })
                    return
                
                # 스트림 응답 처리
                async for line in response.content:
                    try:
                        line_str = line.decode().strip()
                        if line_str:
                            data = json.loads(line_str)
                            
                            # Ollama 스트림 형식을 통합 형식으로 변환
                            chunk_data = {
                                "content": data.get("response", ""),
                                "done": data.get("done", False),
                                "status": "running"
                            }
                            
                            if data.get("done"):
                                chunk_data["status"] = "completed"
                                chunk_data["usage"] = {
                                    "total_duration": data.get("total_duration", 0),
                                    "eval_count": data.get("eval_count", 0)
                                }
                            
                            yield json.dumps(chunk_data)
                            
                            if data.get("done"):
                                break
                                
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        yield json.dumps({
                            "error": str(e),
                            "status": "failed"
                        })
                        return
                        
        except asyncio.TimeoutError:
            yield json.dumps({
                "error": f"Task timed out after {task.timeout} seconds",
                "status": "failed"
            })
        except Exception as e:
            yield json.dumps({
                "error": str(e),
                "status": "failed"
            })
    
    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소 (Ollama는 기본적으로 취소 기능이 제한적)"""
        # Ollama API는 명시적인 취소 기능이 없음
        # 클라이언트 측에서 연결을 끊는 것으로 처리
        return True
    
    async def cleanup(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()
            self.session = None
        self._available_models.clear()
    
    def get_required_config_keys(self) -> List[str]:
        """필수 설정 키 목록"""
        return ["base_url"]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """설정 스키마 반환"""
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "title": "Ollama Server URL",
                    "description": "Base URL for Ollama server",
                    "default": "http://localhost:11434"
                },
                "timeout": {
                    "type": "integer",
                    "title": "Request Timeout (seconds)",
                    "description": "Timeout for API requests",
                    "default": 300,
                    "minimum": 10
                },
                "default_model": {
                    "type": "string",
                    "title": "Default Model",
                    "description": "Default model to use if not specified",
                    "default": "llama3.1"
                }
            },
            "required": ["base_url"]
        }