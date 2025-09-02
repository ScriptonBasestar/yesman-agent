"""Claude Code Provider Implementation.

Claude Code CLI를 통한 AI 제공업체 구현
기존 HeadlessAdapter를 확장하여 통합 인터페이스에 맞춤
"""

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from ...claude.headless_adapter import HeadlessAdapter
from ..provider_interface import AIProvider, AIProviderType, AIResponse, AITask, TaskStatus


class ClaudeCodeProvider(AIProvider):
    """Claude Code 제공업체."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.headless_adapter = None
        self.workspace_manager = None
        self._active_processes: dict[str, asyncio.subprocess.Process] = {}

    def _get_provider_type(self) -> AIProviderType:
        return AIProviderType.CLAUDE_CODE

    async def initialize(self) -> bool:
        """Claude Code 제공업체 초기화."""
        try:
            # HeadlessAdapter 초기화
            yesman_config = YesmanConfig.from_yaml(self.config.get("config_path"))
            self.headless_adapter = HeadlessAdapter(yesman_config)

            # WorkspaceSecurityManager 초기화
            self.workspace_manager = WorkspaceSecurityManager(
                base_path=Path(self.config.get("workspace_base", "/tmp/yesman-workspaces")),
                max_workspace_size_mb=self.config.get("max_workspace_size_mb", 1000),
                max_workspaces=self.config.get("max_workspaces", 10),
            )

            # Claude CLI 존재 확인
            claude_binary = self.config.get("claude_binary_path", "claude")
            if not await self._check_claude_binary(claude_binary):
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Failed to initialize Claude Code provider: {e}")
            return False

    async def _check_claude_binary(self, binary_path: str) -> bool:
        """Claude CLI 바이너리 존재 확인."""
        try:
            process = await asyncio.create_subprocess_exec(binary_path, "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    async def health_check(self) -> dict[str, Any]:
        """Claude Code 제공업체 상태 확인."""
        if not self._initialized:
            return {"status": "not_initialized", "initialized": False}

        try:
            # Claude CLI 버전 확인
            claude_binary = self.config.get("claude_binary_path", "claude")
            process = await asyncio.create_subprocess_exec(claude_binary, "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                version = stdout.decode().strip()
                return {
                    "status": "healthy",
                    "claude_version": version,
                    "active_processes": len(self._active_processes),
                    "workspace_count": len(self.workspace_manager.get_all_workspaces()) if self.workspace_manager else 0,
                }
            else:
                return {"status": "unhealthy", "error": stderr.decode().strip()}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_available_models(self) -> list[str]:
        """사용 가능한 Claude 모델 반환."""
        return ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]

    async def execute_task(self, task: AITask) -> AIResponse:
        """단일 작업 실행."""
        try:
            # 워크스페이스 생성
            workspace_path = None
            if task.workspace_path:
                workspace_path = Path(task.workspace_path)
            else:
                workspace_path = await self.workspace_manager.create_workspace(f"task-{task.task_id[:8]}")

            # Claude CLI 명령 구성
            claude_binary = self.config.get("claude_binary_path", "claude")
            cmd = [claude_binary, "--output-format", "json", "--model", task.model, "--verbose"]

            if task.tools:
                cmd.extend(["--tools", ",".join(task.tools)])

            if task.temperature != 0.0:
                cmd.extend(["--temperature", str(task.temperature)])

            if task.max_tokens:
                cmd.extend(["--max-tokens", str(task.max_tokens)])

            cmd.append(task.prompt)

            # 환경 변수 준비
            env = os.environ.copy()
            if "ANTHROPIC_API_KEY" in self.config:
                env["ANTHROPIC_API_KEY"] = self.config["ANTHROPIC_API_KEY"]

            # 프로세스 실행
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=workspace_path, env=env)

            self._active_processes[task.task_id] = process

            try:
                # 타임아웃과 함께 대기
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=task.timeout)

                if process.returncode == 0:
                    # 성공적인 실행
                    content = stdout.decode().strip()

                    # JSON 출력인 경우 파싱 시도
                    try:
                        json_output = json.loads(content)
                        if "content" in json_output:
                            content = json_output["content"]
                        usage_info = json_output.get("usage", {})
                    except json.JSONDecodeError:
                        usage_info = {}

                    return AIResponse(
                        content=content,
                        status=TaskStatus.COMPLETED,
                        provider=AIProviderType.CLAUDE_CODE,
                        model=task.model,
                        usage=usage_info,
                        metadata={"workspace_path": str(workspace_path), "command": " ".join(cmd)},
                    )
                else:
                    # 실행 오류
                    error_msg = stderr.decode().strip()
                    return AIResponse(
                        content="",
                        status=TaskStatus.FAILED,
                        provider=AIProviderType.CLAUDE_CODE,
                        model=task.model,
                        error=error_msg,
                        metadata={"workspace_path": str(workspace_path), "return_code": process.returncode},
                    )

            except TimeoutError:
                # 타임아웃
                process.terminate()
                await process.wait()

                return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.CLAUDE_CODE, model=task.model, error=f"Task timed out after {task.timeout} seconds")

        except Exception as e:
            return AIResponse(content="", status=TaskStatus.FAILED, provider=AIProviderType.CLAUDE_CODE, model=task.model, error=str(e))
        finally:
            # 프로세스 정리
            self._active_processes.pop(task.task_id, None)

    async def stream_task(self, task: AITask) -> AsyncGenerator[str, None]:
        """스트리밍 작업 실행."""
        try:
            # 워크스페이스 생성
            workspace_path = None
            if task.workspace_path:
                workspace_path = Path(task.workspace_path)
            else:
                workspace_path = await self.workspace_manager.create_workspace(f"stream-{task.task_id[:8]}")

            # Claude CLI 명령 구성 (스트림 모드)
            claude_binary = self.config.get("claude_binary_path", "claude")
            cmd = [claude_binary, "--output-format", "stream-json", "--model", task.model, "--verbose"]

            if task.tools:
                cmd.extend(["--tools", ",".join(task.tools)])

            if task.temperature != 0.0:
                cmd.extend(["--temperature", str(task.temperature)])

            if task.max_tokens:
                cmd.extend(["--max-tokens", str(task.max_tokens)])

            cmd.append(task.prompt)

            # 환경 변수 준비
            env = os.environ.copy()
            if "ANTHROPIC_API_KEY" in self.config:
                env["ANTHROPIC_API_KEY"] = self.config["ANTHROPIC_API_KEY"]

            # 프로세스 실행
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=workspace_path, env=env)

            self._active_processes[task.task_id] = process

            try:
                # 스트림 출력 읽기
                async for line in self._read_stream_lines(process.stdout):
                    if line.strip():
                        yield line.strip()

                # 프로세스 종료 대기
                await process.wait()

                if process.returncode != 0:
                    stderr_content = await process.stderr.read()
                    error_msg = stderr_content.decode().strip()
                    yield json.dumps({"error": error_msg, "status": "failed", "return_code": process.returncode})

            except Exception as e:
                yield json.dumps({"error": str(e), "status": "failed"})

        except Exception as e:
            yield json.dumps({"error": str(e), "status": "failed"})
        finally:
            # 프로세스 정리
            self._active_processes.pop(task.task_id, None)

    async def _read_stream_lines(self, stream) -> AsyncGenerator[str, None]:
        """스트림에서 라인 단위로 읽기."""
        while True:
            try:
                line = await stream.readline()
                if not line:
                    break
                yield line.decode()
            except Exception:
                break

    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소."""
        process = self._active_processes.get(task_id)
        if process:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
                return True
            except TimeoutError:
                process.kill()
                await process.wait()
                return True
            except Exception:
                return False
            finally:
                self._active_processes.pop(task_id, None)
        return False

    async def cleanup(self) -> None:
        """리소스 정리."""
        # 모든 활성 프로세스 종료
        for task_id, process in list(self._active_processes.items()):
            try:
                if process.returncode is None:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
            except Exception:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

        self._active_processes.clear()

        # 워크스페이스 정리
        if self.workspace_manager:
            await self.workspace_manager.cleanup_old_workspaces(max_age_hours=24)

    def get_required_config_keys(self) -> list[str]:
        """필수 설정 키 목록."""
        return ["claude_binary_path", "workspace_base"]

    def get_config_schema(self) -> dict[str, Any]:
        """설정 스키마 반환."""
        return {
            "type": "object",
            "properties": {
                "claude_binary_path": {"type": "string", "title": "Claude CLI Path", "description": "Path to Claude CLI binary", "default": "/opt/homebrew/bin/claude"},
                "workspace_base": {"type": "string", "title": "Workspace Base Directory", "description": "Base directory for workspaces", "default": "/tmp/yesman-workspaces"},
                "max_workspace_size_mb": {"type": "integer", "title": "Max Workspace Size (MB)", "description": "Maximum size per workspace in MB", "default": 1000},
                "max_workspaces": {"type": "integer", "title": "Max Workspaces", "description": "Maximum number of workspaces", "default": 10},
                "ANTHROPIC_API_KEY": {"type": "string", "title": "Anthropic API Key", "description": "API key for Claude Code", "format": "password"},
            },
            "required": ["claude_binary_path", "workspace_base"],
        }
