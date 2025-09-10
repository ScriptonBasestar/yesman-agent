# Development Setup Guide

Yesman-Claude 개발 환경 설정 및 개발 워크플로우 가이드입니다.

## 📋 목차

1. [개발 환경 설정](#%EA%B0%9C%EB%B0%9C-%ED%99%98%EA%B2%BD-%EC%84%A4%EC%A0%95)
1. [프로젝트 구조](#%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EA%B5%AC%EC%A1%B0)
1. [개발 명령어](#%EA%B0%9C%EB%B0%9C-%EB%AA%85%EB%A0%B9%EC%96%B4)
1. [아키텍처 개요](#%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98-%EA%B0%9C%EC%9A%94)
1. [새로운 기능 추가](#%EC%83%88%EB%A1%9C%EC%9A%B4-%EA%B8%B0%EB%8A%A5-%EC%B6%94%EA%B0%80)
1. [코딩 가이드라인](#%EC%BD%94%EB%94%A9-%EA%B0%80%EC%9D%B4%EB%93%9C%EB%9D%BC%EC%9D%B8)

## 🛠️ 개발 환경 설정

### 요구 사항

- Python 3.11+
- tmux
- Git
- Node.js (Tauri 대시보드용)

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd yesman-agent

# uv 사용 설치 (권장)
uv sync                             # 기본 의존성 설치
uv sync --group dev                 # 개발 의존성 포함
uv sync --all-groups               # 모든 의존성 설치

# 대시보드 프론트엔드 의존성 설치
cd tauri-dashboard && pnpm install
```

### 개발 환경 설정

```bash
# 개발 환경 설정
export YESMAN_ENV=development

# 설정 파일 생성 (선택적)
mkdir -p ~/.scripton/yesman
cp config/claude-headless.example.yaml ~/.scripton/yesman/yesman.yaml

# Claude CLI 설치 (headless 모드용)
./scripts/install-claude-cli.sh

# API 서버 시작
uv run python -m uvicorn api.main:app --host 127.0.0.1 --port 10501

# 코드 품질 검사
make lint        # Ruff 린팅
make format      # Ruff 포맷팅
```

## 📁 프로젝트 구조

### Directory Structure

- `api/` - FastAPI REST API 서버 (주요 백엔드)
- `tauri-dashboard/` - SvelteKit/Tauri 대시보드 (주요 프론트엔드)
- `libs/core/` - Agent 관리 및 Claude Code Headless 통합
- `libs/ai/` - AI 학습 및 적응형 응답 시스템
- `libs/dashboard/` - 대시보드 컴포넌트 및 상태 모니터링
- `libs/logging/` - 비동기 로깅 시스템
- `libs/` - 설정 관리 및 유틸리티 (YesmanConfig)
- `config/` - 설정 템플릿 및 예제 (claude-headless.example.yaml)
- `scripts/` - 설치 및 배포 스크립트
- `debug/` - 디버깅 유틸리티
- `tests/` - 단위 및 통합 테스트
- `docs/` - 프로젝트 문서

### Configuration Hierarchy (Claude Code Headless)

1. Global config: `~/.scripton/yesman/yesman.yaml` (Claude CLI 설정, 로깅)
1. Claude CLI binary: `/opt/homebrew/bin/claude` (Headless SDK)
1. Workspace directories: 격리된 Agent 작업공간
1. Security policies: 금지 경로, 도구 제한, 할당량
1. Local overrides: `./.scripton/yesman/*` (프로젝트별 설정)

Configuration merge modes:

- `merge` (default): Local configs override global
- `local`: Use only local configs

## 🚀 개발 명령어

### Installation

```bash
# uv 사용 설치 (권장)
uv sync                             # 기본 의존성
uv sync --group dev                 # 개발 의존성
uv sync --all-groups               # 전체 의존성

# API 서버 상태 확인
curl http://localhost:10501/healthz

# Agent 생성 테스트
curl -X POST http://localhost:10501/api/agents/ \
  -H 'Content-Type: application/json' \
  -d '{"workspace_path": "/tmp/test", "model": "claude-3-5-sonnet-20241022"}'
```

### Running Commands

**주요 명령어는 API 서버와 대시보드를 통해 실행됩니다:**

```bash
# API 서버 시작
make start                          # 백그라운드 실행
make debug-api                      # 포그라운드 디버그 모드

# 대시보드 실행 (주요 인터페이스)
make dashboard                      # 스마트 대시보드 (자동 선택)
make dashboard-web                  # 웹 대시보드 (http://localhost:5173)
make dashboard-desktop              # Tauri 데스크톱 앱

# Agent 생성 및 관리 (API 또는 대시보드)
curl -X POST http://localhost:10501/api/agents/ \
  -H 'Content-Type: application/json' \
  -d '{"workspace_path": "/tmp/test", "model": "claude-3-5-sonnet-20241022"}'

# 상태 확인
curl http://localhost:10501/api/agents/health    # Agent 상태
curl http://localhost:10501/healthz              # 시스템 상태
make status                                     # Make 명령어로 상태 확인

# 서비스 관리
make stop                           # 모든 서비스 중단
make restart                        # 서비스 재시작
```

### Testing and Development Commands

```bash
# 테스트 실행 (uv 사용)
uv run pytest tests/test_prompt_detector.py      # 특정 테스트
uv run pytest tests/integration/                # 통합 테스트
uv run pytest -m "unit"                        # 단위 테스트만
uv run pytest --cov=libs --cov=api             # 커버리지 포함

# 개발 서버 실행
make start                          # API 서버 백그라운드
make debug-api                      # API 서버 디버그 모드
make dashboard-desktop              # Tauri 개발 모드
make dashboard-web                  # 웹 개발 서버

# 디버깅 스크립트 (uv로 실행)
uv run python debug/debug_content.py      # 콘텐츠 수집 디버깅
uv run python debug/debug_controller.py   # 대시보드 컨트롤러 디버깅
uv run python debug/debug_agent.py        # Agent 라이프사이클 디버깅

# FastAPI 서버 직접 실행
uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501

# Tauri 개발 모드 직접 실행
cd tauri-dashboard && pnpm tauri dev
```

### Code Quality Tools

The project uses comprehensive code quality tools:

- **Ruff** for linting, formatting, and import sorting (replaces Black + isort)
- **mypy** for static type checking
- **pytest** for testing with coverage reports
- **bandit** for security vulnerability scanning
- **pre-commit** for automatic quality checks

빠른 명령어 (전부 uv 기반):

```bash
make format      # Ruff로 코드 포맷팅 및 import 정리
make lint        # Ruff + mypy 코드 품질 검사
make lint-fix    # 린팅 문제 자동 수정
make test        # 모든 테스트 실행 (pytest)
make dev-full    # 완전한 품질 검사 (lint + test + coverage)
make quick       # 빠른 검사 (dev-fast 별칭)
```

## 🏗️ 아키텍처 개요

Yesman Claude는 다음과 같은 핵심 패턴들을 사용합니다:

### Command Pattern

모든 API 엔드포인트는 FastAPI 라우터를 통해 표준화된 방식으로 구현됩니다.

```python
from fastapi import APIRouter
from libs.core.agent_manager import AgentManager

router = APIRouter()

@router.post("/agents/")
async def create_agent(request: AgentRequest):
    # Agent 생성 로직
    agent_id = agent_manager.create_agent(request.workspace_path)
    return {"agent_id": agent_id, "status": "created"}
```

### Dependency Injection

서비스들은 DI 컨테이너를 통해 관리되며, 테스트와 유지보수를 용이하게 합니다.

```python
from libs.core.services import get_config, get_agent_manager

config = get_config()           # YesmanConfig 인스턴스
agent_manager = get_agent_manager()  # AgentManager 인스턴스 (Claude CLI)
```

### Configuration Management

Pydantic 스키마 기반의 타입 안전한 설정 관리를 제공합니다.

```python
# 타입 안전한 설정 접근
log_level = config.schema.logging.level
claude_binary = config.schema.claude.headless.claude_binary_path
```

### Error Handling

중앙화된 에러 처리 시스템으로 일관된 에러 응답을 제공합니다.

```python
from libs.core.error_handling import SessionError

raise AgentError(
    "Agent를 찾을 수 없습니다",
    agent_id="agent_123",
    recovery_hint="GET /api/agents/로 Agent 목록을 확인하세요"
)
```

### Key Components

**YesmanConfig** (`libs/yesman_config.py`):

- Loads and merges global/local configurations
- Sets up logging based on config
- Provides config access methods

**AgentManager** (`libs/core/agent_manager.py`):

- Claude CLI Headless 모드를 통한 Agent 생성/관리
- 격리된 워크스페이스에서 안전한 Task 실행
- 실시간 JSON 스트리밍으로 진행 상황 모니터링

**HeadlessAdapter** (`libs/core/headless_adapter.py`):

- Claude CLI SDK 통합 및 명령어 실행
- 보안 샌드박스 내에서 안전한 코드 실행
- JSON 기반 스트리밍으로 실시간 Task 모니터링
- 자동 리소스 정리 및 에러 복구
- 워크스페이스 격리 및 권한 관리

**Tauri Desktop Dashboard** (`tauri-dashboard/`):

- SvelteKit + Tauri 기반 네이티브 데스크톱 애플리케이션
- Agent 상태 및 Task 실행 실시간 모니터링
- WebSocket을 통한 실시간 업데이트
- Agent 생성/삭제/Task 실행 인터페이스
- 시스템 트레이 통합 및 네이티브 알림

**FastAPI Server** (`api/main.py`):

- Agent 라이프사이클 관리 REST API (8개 주요 엔드포인트)
- Claude CLI Headless 모드 통합 백엔드
- WebSocket/SSE를 통한 실시간 통신
- CORS, 미들웨어, 에러 처리 완전 구현

**AI Learning System** (`libs/ai/`):

- **ResponseAnalyzer** (`libs/ai/response_analyzer.py`): Pattern analysis and learning engine
- **AdaptiveResponse** (`libs/ai/adaptive_response.py`): AI-powered auto-response system
- Learns from user behavior and improves response accuracy over time
- Pattern classification for different prompt types (yes/no, numbered selections, etc.)
- Confidence scoring and prediction algorithms
- JSON-based persistence for learned patterns and responses

## ➕ 새로운 명령어 추가

### 1. 명령어 클래스 생성

새로운 명령어를 `commands/` 디렉토리에 생성합니다:

```python
# commands/example.py
"""Example command implementation"""

import click
from libs.core.base_command import BaseCommand
from libs.core.error_handling import ValidationError


class ExampleCommand(BaseCommand):
    """예시 명령어 클래스"""

    def execute(self, name: str = None, **kwargs) -> dict:
        """
        명령어 실행 로직
        
        Args:
            name: 예시 매개변수
            **kwargs: 추가 매개변수들
            
        Returns:
            실행 결과 딕셔너리
            
        Raises:
            ValidationError: 잘못된 입력값
        """
        if not name:
            raise ValidationError(
                "이름이 필요합니다",
                field_name="name",
                recovery_hint="--name 옵션으로 이름을 지정하세요"
            )
        
        # 실제 명령어 로직
        self.print_info(f"안녕하세요, {name}님!")
        
        return {
            "success": True,
            "message": f"{name}님에게 인사했습니다",
            "data": {"name": name}
        }


@click.command()
@click.option("--name", help="인사할 대상의 이름")
def example(name):
    """예시 명령어"""
    command = ExampleCommand()
    command.run(name=name)
```

### 2. API 라우터에 엔드포인트 등록

```python
# api/main.py
from api.routers import agents

app.include_router(
    agents.router, 
    prefix="/api/agents", 
    tags=["agents"]
)
```

### 3. 명령어 믹스인 사용

공통 기능이 필요한 경우 믹스인을 사용합니다:

```python
from libs.core.base_command import BaseCommand, SessionCommandMixin

@router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Agent 상태 조회"""
    
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}'를 찾을 수 없습니다"
        )
    
    return {"agent_id": agent_id, "status": agent.status}
```

## 🌐 API 엔드포인트 추가

### 1. 라우터 생성

```python
# api/routers/example.py
"""Example API endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from libs.core.services import get_config
from libs.core.error_handling import ValidationError

router = APIRouter()


class ExampleRequest(BaseModel):
    name: str
    message: str | None = None


class ExampleResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


@router.post("/example", response_model=ExampleResponse)
async def create_example(request: ExampleRequest):
    """예시 API 엔드포인트"""
    try:
        # DI를 통한 서비스 접근
        config = get_config()
        
        # 비즈니스 로직
        result = process_example(request.name, request.message)
        
        return ExampleResponse(
            success=True,
            message="처리 완료",
            data=result
        )
    except ValidationError as e:
        # YesmanError는 자동으로 적절한 HTTP 상태코드로 변환됩니다
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. main.py에 라우터 등록

```python
# api/main.py
from api.routers import example

app.include_router(example.router, prefix="/api", tags=["example"])
```

## ⚙️ 설정 관리

### 환경별 설정

```yaml
# config/development.yaml
logging:
  level: DEBUG
  
confidence_threshold: 0.5
auto_cleanup_days: 7

# config/production.yaml
logging:
  level: WARNING
  max_size: 52428800  # 50MB
  
confidence_threshold: 0.9
auto_cleanup_days: 30
```

### 환경변수 사용

```bash
# 특정 설정을 환경변수로 오버라이드
export YESMAN_LOGGING_LEVEL=ERROR
export YESMAN_TMUX_DEFAULT_SHELL=/bin/zsh
export YESMAN_CONFIDENCE_THRESHOLD=0.95
```

## 🚨 에러 처리

### 표준 에러 클래스 사용

```python
from libs.core.error_handling import (
    ConfigurationError,
    SessionError,
    ValidationError,
    NetworkError
)

# 설정 관련 에러
raise ConfigurationError(
    "설정 파일을 찾을 수 없습니다",
    config_file="/path/to/config.yaml"
)

# 세션 관련 에러
raise AgentError(
    "Agent가 이미 실행 중입니다",
    agent_id="agent_123",
    recovery_hint="기존 Agent를 종료하거나 다른 워크스페이스를 사용하세요"
)

# 검증 에러
raise ValidationError(
    "포트 번호가 유효하지 않습니다",
    field_name="port",
    recovery_hint="1-65535 범위의 포트 번호를 입력하세요"
)
```

## 📝 코딩 가이드라인

### 코드 스타일

프로젝트는 Ruff를 사용하여 일관된 코드 스타일을 유지합니다:

```bash
# 코드 포맷팅 (Ruff 사용)
make format

# 린팅 검사
make lint

# 자동 수정 포함 린팅
make lint-fix

# 타입 체킹
make type-check

# 전체 품질 검사
make full
```

### 커밋 메시지

```
feat(commands): add example command
fix(api): resolve agent creation error
docs(adr): add configuration management decision
test(integration): add API endpoint tests
refactor(core): improve error handling
```

### 브랜치 전략

- `main`: 안정된 프로덕션 코드
- `develop`: 개발 브랜치
- `feature/task-name`: 기능 개발
- `hotfix/issue-name`: 긴급 수정

## 🔍 디버깅 팁

### 로깅 설정

```python
# 개발 시 상세 로깅
export YESMAN_LOGGING_LEVEL=DEBUG

# 특정 모듈만 로깅
import logging
logging.getLogger("yesman.agent_manager").setLevel(logging.DEBUG)
```

### 에러 추적

```python
# 에러 컨텍스트 확인
try:
    command.execute()
except YesmanError as e:
    print(f"에러 코드: {e.error_code}")
    print(f"복구 힌트: {e.recovery_hint}")
    print(f"컨텍스트: {e.context}")
```

## 🔧 Development Workflow

When working on this codebase:

1. **Adding New API Endpoints**: Create new router files in `api/routers/` directory and register them in `api/main.py`
1. **Claude Manager Modifications**:
   - Core logic in `libs/core/claude_manager.py` (DashboardController class)
   - Pattern detection in `libs/core/prompt_detector.py` (ClaudePromptDetector class)
   - Content collection in `libs/core/content_collector.py`
   - Auto-response patterns stored in `patterns/` subdirectories
   - Caching system components in `libs/core/cache_*.py` modules
1. **Dashboard Updates**:
   - Tauri: Native desktop app components in `tauri-dashboard/src/`
   - FastAPI: REST API endpoints in `api/routers/`
   - Web Interface: Browser-based components via Tauri's embedded WebView
1. **Configuration Changes**: Global config structure defined in `YesmanConfig` class (`libs/yesman_config.py`)
1. **Testing**: Use debug scripts in `debug/` directory and test files in `tests/` for component testing

## 📚 추가 리소스

- [테스트 가이드](42-testing-guide.md)
- [API 문서](../20-api/21-rest-api-reference.md) (서버 실행 시)
- [설정 스키마](../../libs/core/config_schema.py)
- [에러 처리](../../libs/core/error_handling.py)

## 🤝 기여하기

1. 이슈 생성 또는 기존 이슈 확인
1. 기능 브랜치 생성: `git checkout -b feature/my-feature`
1. 변경사항 커밋: `git commit -m 'feat: add my feature'`
1. 브랜치 푸시: `git push origin feature/my-feature`
1. Pull Request 생성

### PR 체크리스트

- [ ] 테스트가 모두 통과하는가?
- [ ] 코드 스타일 가이드를 따르는가?
- [ ] 문서가 업데이트되었는가?
- [ ] 새로운 기능에 대한 테스트가 추가되었는가?
- [ ] CHANGELOG가 업데이트되었는가?
