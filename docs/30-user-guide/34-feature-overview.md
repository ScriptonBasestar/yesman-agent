# Feature Guide — 실행 관점 요약

> 기능 설명의 전체 목록은 [`docs/product/03-features.md`](../product/03-features.md)가 담당합니다. 이 문서는 "어떤 기능을 언제 활용하" 
> 는가?"를 사용자 흐름별로 정리하고 관련 문서로 연결합니다.

---

## 1. 기능 맵 (Feature-to-Doc Matrix)
| 기능 영역 | 핵심 행동 | 참조 문서 |
| --- | --- | --- |
| CLI Runtime | `setup`, `enter`, `workflow run`, `controller auto` | [User Guide — Getting Started](31-getting-started.md) |
| FastAPI/SSE | `/api/agents/*`, `/sessions/*`, `/healthz` | [API Endpoints](../20-api/21-endpoints.md) |
| Dashboard (Web/Tauri) | 실시간 세션, 로그 링크, 에이전트 제어 | [Getting Started § 런타임 프로파일](31-getting-started.md#2-%EB%9F%B0%ED%83%80%EC%9E%84-%ED%94%84%EB%A1%9C%ED%8C%8C%EC%9D%BC-%EB%B9%A0%EB%A5%B4%EA%B2%8C-%ED%8C%8C%EC%95%85%ED%95%98%EA%B8%B0) |
| 템플릿/세션 | YAML 기반 레이아웃, Smart Command | [Template Guide](33-templates.md) |
| 플러그인/워크플로 | `plugins/*`, YAML workflow orchestrator | [Product — Plug-in System](../product/08-plugin-system.md) |
| 모니터링/보안 | 로그 수집, 토큰 인증, Trusted Hosts | [Security Doc](../product/10-security.md), [Monitoring Setup](../50-operations/51-monitoring-setup.md) |

---

## 2. 핵심 루프별 하이라이트
### A. 개발 세션 자동화
1. `projects.yaml`에서 템플릿 선택
2. `./yesman.py setup <session>` 실행 → tmux 창 자동 배치
3. Claude Controller가 권한 프롬프트, 선택지를 자동 응답
4. Dashboard에서 세션 카드 확인, 필요 시 `enter`로 바로 접속

> ✅ **팁**: 템플릿에 `before_script`를 추가하면 pnpm install, database migration 등 반복 작업을 조건부로 실행할 수 있습니다.

### B. API 기반 대규모 실행
1. `make start`로 FastAPI 기동
2. `/api/agents/`에 작업을 POST하여 Claude Code를 비동기 실행
3. `/api/events/stream`(SSE) 또는 Dashboard 로그 스트림으로 상태 확인
4. 완료 후 `/api/agents/{id}` DELETE로 리소스 회수

> 실시간 응답 구조는 `docs/20-api/21-endpoints.md#%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98` 섹션의 표를 참고하세요.

### C. 워크플로/배치 자동화
1. `examples/workflows/*.yaml`을 복사하여 Task Chain 정의
2. `./yesman.py workflow run path/to/file.yaml` 실행
3. 각 스텝은 `plugins`/`llm` 설정에 따라 Claude, OpenAI, HTTP 등을 조합
4. 실패 시 `logs/workflows/<name>.log`에서 재시도 전략을 확인

> `workflow` 실행은 CLI와 FastAPI 모두 동일한 YAML을 사용하므로, GitOps 파이프라인에서 재사용이 쉽습니다.

---

## 3. 기능 심화 가이드
| 주제 | 요약 | 추가 자료 |
| --- | --- | --- |
| 자동 응답 정책 | `defaults.trust_prompts`, `automation.workflow_chains` 설정으로 Claude Code 프롬프트를 자동 처리 | [Configuration Playbook](32-configuration.md#5-%EC%84%B1%EB%8A%A5%EB%B3%B4%EC%95%88-%ED%8A%B9%ED%99%94-%EC%84%A4%EC%A0%95) |
| 세션 상태 감시 | Dashboard 타일 ↔ API `/sessions` 응답 구조는 동일하며, `status`, `windows`, `panes` 필드를 공유 | [API Endpoints](../20-api/21-endpoints.md#%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EA%B4%80%EB%A6%AC) |
| 로그/감사 추적 | `logging.directory`, `YESMAN_LOG_LEVEL`, Dashboard 로그 링크 | [Security Doc](../product/10-security.md), [Monitoring Setup](../50-operations/51-monitoring-setup.md) |
| 템플릿 재사용 | Smart Template 패턴, 조건부 쉘, override 전략 | [Template Guide](33-templates.md), [Examples](../70-examples/71-configuration-examples.md) |

---

## 4. 기능 변경 추적
- 주요 기능 추가/제거 시 `docs/product/03-features.md`를 먼저 업데이트합니다.
- 사용자 가이드에서는 **시나리오가 어떻게 바뀌었는지**(필요한 명령, 설정 등)에 집중합니다.
- Dashboard 또는 API 스냅샷이 바뀌면 화면/엔드포인트 캡처를 `docs/20-api/` 또는 `tauri-dashboard/docs/`에 추가한 뒤 여기에서 링크하세요.

---

## 5. 피드백 루프
1. 기능 요청 → Issue/Discussion에서 라벨 `feature-docs` 사용
2. 재현 단계, 필요한 설정 파일, 기대/실제 결과를 함께 적어주세요.
3. 제품 문서와 사용자 가이드 중 어느 곳을 수정해야 하는지 명확히 합의한 뒤 PR을 올리면 리뷰가 빨라집니다.

필요한 기능이 목록에 없다면 위 절차를 따라 추가 요청해주세요.
