# 🧩 Core Features

## 1. Agent & Workflow Runtime
- **tmux Session Orchestrator**: YAML 템플릿으로 창/패널/명령/경로를 선언하면 CLI가 자동으로 프로비저닝합니다.
- **Claude Code Headless Runner**: LLM 상호작용, Prompt Chain, Retry/Guardrail을 내장한 자동 응답 엔진.
- **Workflow Builder**: 다중 Task를 순차/병렬로 구성하고, 결과를 파일/로그/웹훅으로 출력.

## 2. Platform Interfaces
- **CLI & Make Targets**: `./yesman.py`, `make start`, `make dashboard-web` 등 명령으로 개발부터 운영까지 일관된 진입점을 제공합니다.
- **FastAPI REST/SSE**: Agent 상태, 로그, 작업 메트릭을 API로 노출하고 외부 시스템과 통합합니다.
- **SvelteKit/Tauri Dashboard**: Web/Tauri 모두 같은 코드베이스를 사용하여 실시간 세션 상태, 작업 이력, Provider 상태를 시각화합니다.

## 3. Extensibility & Plugins
- **LLM Provider Layer**: Claude, OpenAI, Ollama 등 다양한 Provider를 환경 변수 또는 설정 파일로 선언.
- **Plugin Registry**: Summary/Translate/Code Analyzer 등 기능을 독립 모듈로 분리하여 선택적으로 로드.
- **Automation Hooks**: Workflow 단계마다 Before/After Hook을 설정해 외부 스크립트나 Slack/Notion 등과 연동.

## 4. 운영 품질
- **Observability**: 모든 명령은 JSON 로그/이벤트 스트림으로 수집되어 대시보드와 CLI에서 동시에 조회됩니다.
- **Configuration Safety**: 템플릿 Validation, Secret Masking, Prompt Injection 방어 체계를 내장했습니다.
- **Developer Experience**: `uv`, `ruff`, `pytest` 기반 품질 도구와 CI-friendly Make 타깃을 제공합니다.
