# User Guide — Getting Started

> 이 문서는 [`docs/product/06-getting-started.md`](../product/06-getting-started.md)에 있는 설치·기본 실행 절차를 **사용자 여정**
> 관점에서 확장합니다. 제품 문서에서 이미 다룬 항목은 반복하지 않고, 실제 워크플로와 문제 해결 팁을 집중적으로 다룹니다.

---

## 1. 사전 점검
| 체크 항목 | 요약 | 상세 참조 |
| --- | --- | --- |
| 지원 환경 | macOS/Linux, Python ≥ 3.11, tmux ≥ 3.2 | [필수 조건](../product/06-getting-started.md#%F0%9F%93%84-%ED%95%84%EC%9A%94-%EC%83%81%ED%99%A9) |
| 설치 | `make dev-install` → `./yesman.py --help` | [Quick Start](../product/06-getting-started.md#%F0%9F%9A%80-quick-start) |
| 기본 설정 | `~/.scripton/yesman/yesman.yaml`, `projects.yaml` | [구성 가이드](../product/07-configuration.md) |
| 템플릿 | `templates/*.yaml` (필수 아님) | [템플릿 가이드](33-templates.md) |

> 🔁 **동일 명령을 반복 실행하기 전에** `make clean-tmux` 또는 `./yesman.py teardown <session>`으로 이전 세션을 정리하면 캐시·로그가
> 엉키는 문제를 줄일 수 있습니다.

---

## 2. 런타임 프로파일 빠르게 파악하기
| 사용 목적 | 필수 명령 | 주요 출력 | 다음 단계 |
| --- | --- | --- | --- |
| CLI 단일 작업 | `./yesman.py setup demo` | tmux 세션 + Claude Code 자동화 | `./yesman.py enter demo` 로 확인 |
| FastAPI 백엔드 | `make start` 또는 `uv run uvicorn api.main:app` | `http://localhost:10501` REST/SSE | [API 문서](../20-api/21-endpoints.md) |
| Web Dashboard | `make dashboard-web` | http://localhost:5173 UI | API 서버 연결 상태 확인 |
| Tauri Desktop | `make dashboard-desktop` | 네이티브 앱 | 운영/관측 모드, 알림 |
| 배치 Workflow | `./yesman.py workflow run <file.yaml>` | YAML에 정의된 작업 체인 | [Plugin/System](../product/08-plugin-system.md) |

모든 프로파일은 동일한 설정 파일을 공유하므로, **CLI로 검증 → API/Dashboard로 확장**하는 것이 가장 빠른 흐름입니다.

---

## 3. 60분 완주 플로우
1. **환경 준비 (10분)**
   - `make dev-install` 후 `uv run pytest -q tests/smoke`로 핵심 의존성 확인.
   - `./yesman.py doctor` (추가 예정) 대신 `./yesman.py --help` + `./yesman.py version`으로 CLI 준비 상태 체크.

2. **샘플 세션 배포 (20분)**
   - `~/.scripton/yesman/projects.yaml`에 `demo` 항목이 없다면 `scripts/bootstrap/demo-projects.yaml`을 복사합니다.
   - `./yesman.py setup demo` → `./yesman.py show demo` → `./yesman.py enter demo` 순서로 CLI/tmux 동작을 검증합니다.

3. **API/Dashboard 접속 (20분)**
   - `make start`로 FastAPI를 띄우고 `curl http://localhost:10501/healthz`가 `200 OK`인지 확인합니다.
   - 브라우저에서 Swagger (`/docs`) 확인 → `POST /api/agents/` 호출로 Claude Code headless가 등록되는지 확인합니다.
   - `make dashboard-web`으로 실시간 세션 타일이 보이는지 체크합니다.

4. **자동화 워크플로 실행 (10분)**
   - `examples/workflows/*.yaml` 중 하나를 복사하여 `./yesman.py workflow run <file>`을 실행합니다.
   - 실패 시 `logs/` 디렉터리 링크를 Dashboard에서 클릭하거나 `./yesman.py logs <session>`으로 바로 확인합니다.

---

## 4. 상황별 가이드
| 상황 | 빠른 해결 | 근거 문서 |
| --- | --- | --- |
| tmux 세션이 누락됨 | `./yesman.py ls`로 템플릿/프로젝트를 검증 → `./yesman.py setup <name> --force` | [구성 가이드](../product/07-configuration.md#%EC%84%B8%EC%85%98-%EC%84%A4%EC%A0%95) |
| Claude Code 권한 프롬프트 반복 | `defaults.trust_prompts: true` 설정 또는 `./yesman.py controller auto` 사용 | [Plugin System](../product/08-plugin-system.md) |
| Dashboard에서 데이터 없음 | API 서버 로그(`logs/api/*.log`) 확인 후 `make start` 재실행 | [API Endpoints](../20-api/21-endpoints.md#%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98) |
| FastAPI 포트 충돌 | `uvicorn ... --port 0` 또는 `.env`에서 `API_PORT` 지정 | [구성 가이드](../product/07-configuration.md#%ED%99%98%EA%B2%BD-%EB%B3%80%EC%88%98) |
| 템플릿 변수 미치환 | `projects.yaml`에서 `override`가 누락되었는지 확인 → `./yesman.py render-template`로 미리보기 | [Template Guide](33-templates.md) |

---

## 5. 문제 해결 루프
1. **CLI 명령 확인**: `./yesman.py --verbose ...` 로 실행하여 stdout/stderr를 확보합니다.
2. **로그 위치 파악**: 기본 경로는 `~/.scripton/yesman/logs/*.log`, API는 `logs/api/`, Dashboard는 `tauri-dashboard/logs/` 입니다.
3. **설정 diff**: `yesman config inspect --source <global|local>` (추가 예정) 대신, 현재는 `cat ~/.scripton/yesman/yesman.yaml`과 프로젝트 루트의 `.scripton/`을 비교합니다.
4. **재현 정보 정리**: 문제 보고 시 `PRODUCT.md` 버전, 사용한 워크플로, OS/터미널 정보를 함께 공유해주세요.

---

## 6. 다음 문서
- 설치·구성 심화: [`docs/product/07-configuration.md`](../product/07-configuration.md)
- 템플릿 및 세션 재사용: [`docs/30-user-guide/33-templates.md`](33-templates.md)
- API/자동화 확장: [`docs/20-api/21-endpoints.md`](../20-api/21-endpoints.md)
- 운영 모니터링: [`docs/50-operations/51-monitoring-setup.md`](../50-operations/51-monitoring-setup.md)

“Getting Started”에서 다룬 시나리오 외에 필요한 흐름이 있으면 Issue/Discussion으로 알려주세요.
