"""
OpenAI ChatGPT Provider Implementation

OpenAI API를 통한 ChatGPT 제공업체 구현
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Optional, AsyncGenerator

from ..provider_interface import AIProvider, AIProviderType, AITask, AIResponse, TaskStatus, AIMessage


class OpenAIProvider(AIProvider):
    """OpenAI ChatGPT 제공업체"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.session: Optional[aiohttp.ClientSession] = None
        self._available_models = [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def _get_provider_type(self) -> AIProviderType:
        return AIProviderType.OPENAI_GPT
    
    async def initialize(self) -> bool:
        """OpenAI 제공업체 초기화"""
        if not self.api_key:
            print("OpenAI API key not provided")
            return False
        
        try:
            # HTTP 클라이언트 세션 생성
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            
            # API 연결 확인
            health_status = await self.health_check()
            if health_status.get('status') != 'healthy':
                return False
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """OpenAI API 상태 확인"""
        if not self.session:
            return {
                "status": "not_initialized",
                "initialized": False
            }
        
        try:
            # 모델 목록 요청으로 API 상태 확인
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    available_models = [model['id'] for model in data.get('data', [])]
                    
                    return {
                        "status": "healthy",
                        "available_models": len(available_models),
                        "base_url": self.base_url
                    }
                elif response.status == 401:
                    return {
                        "status": "unauthorized",
                        "error": "Invalid API key"
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
    
    async def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 반환"""
        if not self.session:
            return self._available_models
        
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['id'] for model in data.get('data', []) 
                             if 'gpt' in model['id'].lower()]
                    return models if models else self._available_models
                else:
                    return self._available_models
                    
        except Exception:
            return self._available_models
    
    def _prepare_messages(self, task: AITask) -> List[Dict[str, str]]:
        """작업을 OpenAI 메시지 형식으로 변환"""
        messages = []
        
        # 컨텍스트 메시지 추가
        if task.context:
            for msg in task.context:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 현재 프롬프트 추가
        messages.append({
            "role": "user",
            "content": task.prompt
        })
        
        return messages
    
    async def execute_task(self, task: AITask) -> AIResponse:
        """단일 작업 실행"""
        if not self.session:
            return AIResponse(
                content="",
                status=TaskStatus.FAILED,
                provider=AIProviderType.OPENAI_GPT,
                model=task.model,
                error="OpenAI provider not initialized"
            )
        
        try:
            messages = self._prepare_messages(task)
            
            # 요청 데이터 구성
            request_data = {
                "model": task.model,
                "messages": messages,
                "temperature": task.temperature,
                "stream": False
            }
            
            if task.max_tokens:
                request_data["max_tokens"] = task.max_tokens
            
            # OpenAI API 호출
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=task.timeout)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    choice = data['choices'][0]
                    content = choice['message']['content']
                    
                    return AIResponse(
                        content=content,
                        status=TaskStatus.COMPLETED,
                        provider=AIProviderType.OPENAI_GPT,
                        model=task.model,
                        usage=data.get('usage', {}),
                        metadata={
                            "finish_reason": choice.get('finish_reason'),
                            "created": data.get('created'),
                            "id": data.get('id')
                        }
                    )
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status}')
                    
                    return AIResponse(
                        content="",
                        status=TaskStatus.FAILED,
                        provider=AIProviderType.OPENAI_GPT,
                        model=task.model,
                        error=error_msg
                    )
                    
        except asyncio.TimeoutError:
            return AIResponse(
                content="",
                status=TaskStatus.FAILED,
                provider=AIProviderType.OPENAI_GPT,
                model=task.model,
                error=f"Task timed out after {task.timeout} seconds"
            )
        except Exception as e:
            return AIResponse(
                content="",
                status=TaskStatus.FAILED,
                provider=AIProviderType.OPENAI_GPT,
                model=task.model,
                error=str(e)
            )
    
    async def stream_task(self, task: AITask) -> AsyncGenerator[str, None]:
        """스트리밍 작업 실행"""
        if not self.session:
            yield json.dumps({
                "error": "OpenAI provider not initialized",
                "status": "failed"
            })
            return
        
        try:
            messages = self._prepare_messages(task)
            
            # 요청 데이터 구성 (스트림 모드)
            request_data = {
                "model": task.model,
                "messages": messages,
                "temperature": task.temperature,
                "stream": True
            }
            
            if task.max_tokens:
                request_data["max_tokens"] = task.max_tokens
            
            # 스트리밍 요청
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=task.timeout)
            ) as response:
                
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status}')
                    yield json.dumps({
                        "error": error_msg,
                        "status": "failed"
                    })
                    return
                
                # 스트림 응답 처리
                async for line in response.content:
                    line_str = line.decode().strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 'data: ' 제거
                        
                        if data_str == '[DONE]':
                            yield json.dumps({
                                "content": "",
                                "done": True,
                                "status": "completed"
                            })
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            if 'choices' in data and data['choices']:
                                choice = data['choices'][0]
                                delta = choice.get('delta', {})
                                content = delta.get('content', '')
                                
                                chunk_data = {
                                    "content": content,
                                    "done": False,
                                    "status": "running"
                                }
                                
                                # 완료 확인
                                if choice.get('finish_reason'):
                                    chunk_data["done"] = True
                                    chunk_data["status"] = "completed"
                                    chunk_data["finish_reason"] = choice['finish_reason']
                                
                                yield json.dumps(chunk_data)
                                
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
        """작업 취소 (OpenAI API는 명시적 취소 기능 없음)"""
        # 클라이언트 측에서 연결을 끊는 것으로 처리
        return True
    
    async def cleanup(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def get_required_config_keys(self) -> List[str]:
        """필수 설정 키 목록"""
        return ["api_key"]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """설정 스키마 반환"""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "OpenAI API Key",
                    "description": "Your OpenAI API key",
                    "format": "password"
                },
                "base_url": {
                    "type": "string",
                    "title": "API Base URL",
                    "description": "OpenAI API base URL (for custom endpoints)",
                    "default": "https://api.openai.com/v1"
                },
                "organization": {
                    "type": "string",
                    "title": "Organization ID",
                    "description": "OpenAI organization ID (optional)"
                },
                "default_model": {
                    "type": "string",
                    "title": "Default Model",
                    "description": "Default model to use",
                    "default": "gpt-4o",
                    "enum": [
                        "gpt-4o",
                        "gpt-4o-mini",
                        "gpt-4-turbo",
                        "gpt-4",
                        "gpt-3.5-turbo",
                        "gpt-3.5-turbo-16k"
                    ]
                }
            },
            "required": ["api_key"]
        }