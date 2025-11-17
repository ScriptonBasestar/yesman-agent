# 🧪 Testing Strategy

## 1. 도구 체계
- **pytest + uv**: `uv run python -m pytest`로 빠른 가상환경 실행.
- **pytest-cov**: 핵심 라이브러리(`libs`, `commands`) 커버리지 측정.
- **pytest-asyncio / pytest-mock**: 비동기 API, CLI 상호작용 테스트.
- **ruff / mypy**: 정적 분석 및 스타일 체크.

## 2. Make 타깃
| 명령 | 설명 |
| --- | --- |
| `make test` | 전체 테스트 + 커버리지 |
| `make test-unit` | 단위 테스트만 실행 |
| `make test-integration` | 통합 테스트 (FastAPI, Dashboard 연동) |
| `make test-e2e` | tmux + CLI 시나리오 테스트 |
| `make cover-html` | HTML 커버리지 리포트 생성 |
| `make test-watch` | 변경 감지 모드 |

## 3. 권장 워크플로
1. **pre-commit** 단계에서 `ruff check`, `ruff format`, `mypy` 실행.
2. 기능 개발 시 `make test-unit`으로 빠르게 검증.
3. API/CLI/대시보드를 건드린 경우 `make test-integration`, `make test-e2e`를 추가 실행.
4. PR 직전에 `make test`로 전체 스위트를 돌리고 커버리지 리포트를 첨부.

## 4. 테스트 범위
- **CLI/Workflow**: 템플릿 파서, 명령 실행, 세션 상태 머신.
- **Agent Runtime**: Prompt Builder, Context Loader, Retry/Guardrail.
- **API Layer**: REST/SSE 응답, 인증/권한 훅, 에러 핸들링.
- **Dashboard Contracts**: API 스키마 Snapshot, Provider 상태 스트림 Mock.
- **Plugins**: Task 입력/출력, 재시도, 실패 격리.
