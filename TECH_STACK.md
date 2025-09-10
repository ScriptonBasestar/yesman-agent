# TECH_STACK.md - 기술 스택 문서

## 프로젝트 개요

Yesman-Claude는 Claude Code 자동화 및 모니터링을 위한 멀티 기술 스택 프로젝트입니다. API 중심 아키텍처로 Web/Desktop 대시보드와 Python 백엔드를 제공합니다.

## 프로그래밍 언어

- **Python** (>=3.11): 메인 백엔드 언어, API 서버 및 핵심 자동화 로직
- **TypeScript/JavaScript**: Tauri + SvelteKit 프론트엔드 개발
- **Rust**: 네이티브 데스크톱 애플리케이션 백엔드 (Tauri 프레임워크)
- **HTML/CSS**: 프론트엔드 마크업 및 스타일링

## 백엔드 기술 스택

### Python 핵심 의존성

- **PyYAML** (>=5.4): YAML 설정 파일 파싱
- **tmuxp** (>=1.55.0): tmux 세션 관리
- **libtmux** (>=0.46.2): Python tmux 라이브러리 바인딩
- **psutil** (>=5.9.0): 시스템 및 프로세스 유틸리티
- **Jinja2** (>=3.1.6): 템플릿 엔진
- **requests** (>=2.32.4): HTTP 클라이언트 라이브러리

### API 서버 의존성

- **FastAPI** (>=0.116.0): 최신 Python 웹 프레임워크 (REST API)
- **Uvicorn** (>=0.35.0): FastAPI용 ASGI 서버
- **Pydantic** (>=2.0.0): 데이터 검증 및 설정 관리
- **pydantic-settings** (>=2.0.0): Pydantic 기반 설정 관리
- **Starlette** (>=0.47.2): FastAPI 기반 웹 프레임워크
- **sse-starlette** (>=3.0.2): Server-Sent Events 지원
- **python-multipart** (>=0.0.20): 멀티파트 폼 데이터 파싱

### AI/LLM 통합

- **LangChain** (>=0.3.27): LLM 체인 및 워크플로우 관리
- **aiohttp** (>=3.12.15): 비동기 HTTP 클라이언트

### 빌드 및 패키지 의존성

- **setuptools** (>=64): Python 패키지 빌드
- **wheel**: Python 패키지 배포 형식
- **urllib3** (>=2.5.0): HTTP 라이브러리

## 프론트엔드 기술 스택 (Tauri 대시보드)

### 핵심 프론트엔드 프레임워크

- **SvelteKit** (^2.27.3): 풀스택 Svelte 프레임워크
- **Svelte** (^5.38.0): 반응형 컴포넌트 프레임워크 (Svelte 5)
- **Vite** (^5.4.19): 빌드 도구 및 개발 서버
- **TypeScript** (^5.8.3): 타입 안전 JavaScript

### UI 및 스타일링

- **Tailwind CSS** (^3.4.17): 유틸리티 우선 CSS 프레임워크
- **DaisyUI** (^4.12.24): Tailwind CSS 컴포넌트 라이브러리
- **@tailwindcss/typography** (^0.5.16): 타이포그래피 플러그인
- **PostCSS** (^8.5.6): CSS 후처리
- **Autoprefixer** (^10.4.21): CSS 벤더 프리픽스

### Tauri 데스크톱 프레임워크

- **@tauri-apps/api** (^1.6.0): Tauri JavaScript API
- **@tauri-apps/cli** (^1.6.3): Tauri CLI 도구
- **@tauri-apps/plugin-fs** (^2.4.0): 파일 시스템 작업
- **@tauri-apps/plugin-shell** (^2.3.0): 쉘 명령 실행

### 데이터 시각화 및 UI 컴포넌트

- **Chart.js** (^4.5.0): 차트 라이브러리
- **svelte-chartjs** (^3.1.5): Svelte용 Chart.js 래퍼
- **chartjs-adapter-date-fns** (^3.0.0): 차트용 날짜 포맷팅
- **date-fns** (^2.30.0): 날짜 유틸리티 라이브러리
- **lucide-svelte** (^0.539.0): Svelte용 아이콘 라이브러리

### D3.js 데이터 시각화

- **d3-format** (^3.1.0): 숫자 포맷팅
- **d3-scale** (^4.0.2): 스케일 함수
- **d3-selection** (^3.0.0): DOM 선택 및 조작
- **d3-time-format** (^4.1.0): 시간 포맷팅

## Rust 의존성 (Tauri 백엔드)

- **tauri** (1.5): 크로스 플랫폼 데스크톱 애플리케이션 프레임워크
  - 기능: window 관리, notification, shell, fs 액세스
- **serde** (1.0): 직렬화 프레임워크 (derive 기능 포함)
- **serde_json** (1.0): JSON 직렬화
- **tokio** (1.0): 비동기 런타임 (full 기능)
- **chrono** (0.4): 날짜 및 시간 처리 (serde 기능 포함)
- **uuid** (1.0): UUID 생성 (v4 기능)
- **thiserror** (1.0): 에러 처리
- **lazy_static** (1.4): 정적 변수 초기화
- **tauri-build** (1.5): 빌드 타임 의존성

## 개발 도구 및 빌드 시스템

### 패키지 관리

- **uv**: Python 패키지 매니저 (개발 환경 권장)
- **pip**: Python 패키지 설치기
- **pnpm** (10.12.1): Node.js 패키지 매니저
- **setuptools**: Python 패키지 빌드

### 빌드 도구

- **Vite**: 프론트엔드 빌드 도구
- **Tauri**: 데스크톱 앱 번들러
- **esbuild**: JavaScript 번들러 (Vite 통해)
- **Make**: 빌드 자동화

### 개발 의존성

- **@sveltejs/adapter-static** (^3.0.8): 정적 사이트 어댑터
- **@sveltejs/vite-plugin-svelte** (^4.0.4): Svelte Vite 플러그인
- **@types/node** (^20.19.4): Node.js용 TypeScript 정의
- **@types/d3-format**, **@types/d3-scale**, **@types/d3-selection**, **@types/d3-time-format**: D3.js TypeScript 정의
- **concurrently** (^8.2.2): 다중 명령어 동시 실행
- **svelte-check** (^3.8.6): Svelte TypeScript 체크
- **tslib** (^2.8.1): TypeScript 헬퍼 라이브러리
- **vite-plugin-devtools-json** (^0.2.0): 개발 도구 JSON 플러그인
- **watchdog** (^0.8.0): 파일 시스템 감시

## 테스팅 프레임워크

### Python 테스팅

- **pytest** (>=8.3.5): 고급 Python 테스팅 프레임워크
- **pytest-cov** (>=4.1.0): 커버리지 측정
- **pytest-xdist** (>=3.5.0): 병렬 테스트 실행
- **pytest-timeout** (>=2.2.0): 테스트 타임아웃
- **pytest-mock** (>=3.12.0): 모킹 지원
- **pytest-asyncio** (>=0.23.0): 비동기 테스트 지원

### 향상된 테스팅 도구

- **Hypothesis** (>=6.100.0): Property-based 테스팅
- **factory-boy** (>=3.3.0): 테스트 데이터 팩토리
- **Faker** (>=26.0.0): 실제적인 가짜 데이터 생성
- **pytest-benchmark** (>=4.0.0): 성능 벤치마킹
- **pact-python** (>=2.0.0): 계약 테스팅 (선택적)
- **pytest-sugar** (>=1.0.0): 향상된 테스트 출력 포맷팅
- **pytest-html** (>=4.0.0): HTML 테스트 리포트

### TypeScript/JavaScript 테스팅

- Vitest (Vite 통합 테스팅 프레임워크)
- TypeScript 기반 테스트 작성

## 시스템 의존성

- **tmux**: 터미널 멀티플렉서
- **Claude Code**: Claude AI CLI 도구 통합
- **Linux/Unix**: 주요 운영 체제 지원

## 개발 도구 및 품질 관리

### Python 개발 도구

- **ruff** (>=0.12.3): 고성능 린터 및 코드 포매터
- **mypy** (>=1.13.0): 정적 타입 체커
- **bandit[toml]** (>=1.8.6): 보안 검증 도구
- **pre-commit** (>=4.0.0): Git 훅 관리
- **httpx** (>=0.28.1): 테스트용 HTTP 클라이언트
- **watchdog** (>=3.0.0): 파일 시스템 모니터링

### 문서화 도구

- **mdformat** (>=0.7.0): 마크다운 포매터
- **mdformat-gfm** (>=0.3.0): GitHub Flavored Markdown 지원
- **mdformat-tables** (>=0.4.0): 표 포맷팅

### 타입 정의

- **types-PyYAML** (>=6.0.0): PyYAML 타입 정의
- **types-requests** (>=2.32.4.20250611): Requests 타입 정의

## 설정 및 데이터 형식

- **YAML**: 설정 파일 형식 (tmux 세션, 프로젝트 설정)
- **JSON**: 데이터 교환 형식 (API 응답, 설정 캐시)
- **TOML**: Python 프로젝트 설정 (pyproject.toml)

## 로깅 및 모니터링

- **Python logging**: 표준 로깅 모듈
- **비동기 로깅**: 실시간 로그 처리
- **대시보드 모니터링**: Web/Desktop 인터페이스를 통한 실시간 모니터링

## 아키텍처 컴포넌트

### 핵심 애플리케이션 구조

- **API 중심 아키텍처**: FastAPI 기반 REST API 서버
- **웹 대시보드**: SvelteKit 기반 모니터링 인터페이스
- **네이티브 데스크톱 앱**: Tauri + SvelteKit 기반 크로스 플랫폼 애플리케이션
- **Tmux 통합**: 터미널 세션 관리 및 자동화
- **Claude Code 자동화**: AI 기반 상호작용 자동화
- **실시간 모니터링**: WebSocket/SSE 기반 실시간 업데이트
- **설정 관리**: YAML 기반 계층적 설정 시스템
- **의존성 주입**: 타입 안전 서비스 컨테이너

### 자동화 시스템

- **콘텐츠 수집**: tmux 패널 콘텐츠 실시간 캡처
- **프롬프트 감지**: 정규식 기반 고급 프롬프트 인식
- **자동 응답**: AI 적응형 응답 시스템 (LangChain 통합)
- **워크플로우 엔진**: 자동화 워크플로우 관리
- **세션 관리**: 자동 세션 생성, 모니터링 및 종료
- **대시보드 제어**: 다중 인터페이스 세션 제어 및 모니터링

### AI/LLM 통합

- **LangChain 워크플로우**: 복잡한 AI 체인 관리
- **컨텍스트 관리**: 세션별 컨텍스트 유지
- **적응형 학습**: 사용자 패턴 기반 응답 개선
- **MCP 통합**: Model Context Protocol 지원

## 패키지 관리 및 버전 관리

### Python 패키지 관리

- **프로젝트명**: `yesman-claude` (pyproject.toml)
- **Python 버전**: >=3.11
- **uv**: 권장 Python 패키지 매니저 (개발 환경)
- **pip**: 표준 Python 패키지 설치기

### Frontend 패키지 관리

- **pnpm** (10.12.1): Node.js 패키지 매니저 (권장)
- **pnpm workspace**: 모노레포 지원
- **esbuild 최적화**: 빌드 성능 향상

## 보안 및 품질 보증

### 보안 검증

- **bandit**: Python 코드 보안 스캔
- **ruff**: 보안 관련 린트 규칙
- **의존성 검증**: 정기적인 보안 업데이트

### 코드 품질

- **정적 분석**: mypy 기반 타입 체킹
- **코드 포맷팅**: ruff 자동 포맷팅
- **테스트 커버리지**: pytest-cov 커버리지 측정
- **pre-commit 훅**: 커밋 전 품질 검증

## 성능 및 확장성

### 성능 최적화

- **비동기 처리**: FastAPI + asyncio 기반 비동기 처리
- **실시간 통신**: WebSocket/SSE 실시간 업데이트
- **캐싱 시스템**: 설정 및 상태 캐싱
- **병렬 테스트**: pytest-xdist 병렬 실행

### 확장성

- **멀티 AI 지원**: 다양한 LLM 엔진 통합 가능
- **플러그인 아키텍처**: 확장 가능한 모듈 시스템
- **크로스 플랫폼**: Linux/macOS/Windows 지원

이 프로젝트는 최신 Python 백엔드 기술, 모던 웹 프론트엔드, 네이티브 데스크톱 개발을 결합하여 포괄적인 Claude Code 자동화 및 모니터링 솔루션을 제공합니다.
