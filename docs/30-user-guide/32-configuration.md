# User Guide — Configuration Playbook

> 기본 개념·필수 키·샘플 설정은 [`docs/product/07-configuration.md`](../product/07-configuration.md)가 **단일 출처**입니다. 이 문서는
> 현업에서 자주 묻는 “어떤 파일을 언제 수정해야 하는가?”에 대한 실행 가이드를 제공합니다.

---

## 1. 구성 계층 요약
| 우선순위 | 위치 | 용도 | 권장 사용 |
| --- | --- | --- | --- |
| 1️⃣ 기본값 | 패키지 내부 (`config/*.yaml`) | 비편집 영역, 릴리스 기본값 | 참고만 하고 직접 수정하지 않습니다. |
| 2️⃣ 사용자 전역 | `~/.scripton/yesman/yesman.yaml` | 로컬 사용자 기본 동작 | 로그인 사용자별 공통 옵션 (로그, Dashboard 테마 등) |
| 3️⃣ 프로젝트 전역 | `~/.scripton/yesman/projects.yaml` | 템플릿 묶음/세션 정의 | 여러 저장소에 재사용할 템플릿/세션 |
| 4️⃣ 저장소 전역 | `<repo>/.scripton/yesman/*.yaml` | 팀별 표준 값 | CI/리포지터리 공유 설정 |
| 5️⃣ 실행 시점 | 환경 변수, CLI 플래그 | 임시 변경 | 디버깅/테스트용 override |

> ⚙️ `merge_mode: merge`가 기본이며, 특정 프로젝트를 완전히 격리하고 싶다면 `merge_mode: isolated`를 프로젝트 루트에 두세요.

---

## 2. 주요 파일별 체크리스트
| 파일 | 핵심 필드 | 언제 수정? | 관련 문서 |
| --- | --- | --- | --- |
| `yesman.yaml` | `logging`, `dashboard`, `defaults` | 사용자별 선호(로그 레벨, 신뢰 프롬프트 응답) | [제품 문서 § Logging](../product/07-configuration.md#%EB%A1%9C%EA%B9%85) |
| `projects.yaml` | `sessions`, `template_name`, `override` | 동일 템플릿 기반 여러 세션 운영 | [Getting Started § Demo](../product/06-getting-started.md#%F0%9F%9A%80-quick-start) |
| `templates/*.yaml` | `windows`, `before_script`, `environment` | 세션 레이아웃/자동화 정의 | [Template Guide](33-templates.md) |
| `.env` 또는 `env.d/*.env` | `OPENAI_API_KEY`, `API_PORT` 등 | CI/서버 배포 시 비밀·포트 관리 | [Security Doc](../product/10-security.md) |
| `config/*.yaml` (repo) | `claude-headless.example.yaml` 등 | 새 기여자가 바로 복제할 기본값 제공 | 기여 시 README/PRODUCT 링크 유지 |

---

## 3. 자주 쓰는 Override 패턴
```yaml
# ~/.scripton/yesman/projects.yaml
merge_mode: merge
sessions:
  docs-demo:
    template_name: smart-frontend
    override:
      session_name: yesman-docs
      start_directory: ~/workspace/yesman-agent
      environment:
        API_PORT: "10501"
      windows:
        - window_name: api
          panes:
            - shell_command: |
                uv run python -m uvicorn api.main:app --host 0.0.0.0 --port ${API_PORT}
```

| 설정 포인트 | 설명 | 대안 |
| --- | --- | --- |
| `merge_mode` | 글로벌 기본값을 유지하면서 필요한 값만 덮어씀 | 완전 격리하려면 루트 `.scripton/yesman/projects.yaml`에서 `isolated` |
| `override.environment` | 템플릿에 노출된 변수 외에 임시 환경 변수를 추가 | `.env` 파일을 사용하려면 `env_file` 옵션 추가 |
| `windows[].panes[].shell_command` | 조건부 로직을 넣고 싶다면 멀티라인 쉘을 사용 | 반복 사용 시 `templates/*.yaml`에 승격 |

> 더 많은 패턴은 [`docs/70-examples/71-configuration-examples.md`](../70-examples/71-configuration-examples.md)에서 확인할 수 있습니다.

---

## 4. 환경 변수 맵
| 변수 | 설명 | 기본값 | 영향 범위 |
| --- | --- | --- | --- |
| `YESMAN_HOME` | 설정 루트 강제 지정 | `~/.scripton/yesman` | 모든 CLI/대시보드 |
| `YESMAN_CONFIG` | 전역 `yesman.yaml` 경로 | `YESMAN_HOME/yesman.yaml` | CLI, API |
| `YESMAN_PROJECTS` | `projects.yaml` 경로 | `YESMAN_HOME/projects.yaml` | 세션/템플릿 로딩 |
| `API_PORT` | FastAPI 포트 | `10501` | FastAPI, Dashboard |
| `DASHBOARD_URL` | Dashboard 접근 URL | `http://localhost:5173` | 링크 공유/알림 |
| `YESMAN_LOG_LEVEL` | 기본 로그 레벨 | `INFO` | CLI/API 공통 |
| `YESMAN_TMUX_SOCKET` | tmux 소켓 경로 | 시스템 기본 | CLI 세션 탐색 |

환경 변수는 항상 CLI 플래그보다 우선합니다. 여러 값을 실험해야 한다면 `env.d/local.env`를 만든 뒤 `set -a && source env.d/local.env && set +a`
형태로 로드하면 안전합니다.

---

## 5. 성능/보안 특화 설정
| 목표 | 권장 옵션 | 부작용/주의 |
| --- | --- | --- |
| 빠른 Dashboard 업데이트 | `dashboard.update_interval: 0.5` | tmux 서버 폴링 비용 증가 → CPU 모니터 필요 |
| LLM 트래픽 절감 | `defaults.max_tokens`, `automation.enabled: false` | 일부 자동 응답 비활성화 → 수동 입력 필요 |
| 팀 공유 로그 | `logging.directory`를 프로젝트 공유 위치로 지정 | 권한 700 이상 권장, 민감정보 마스킹 확인 |
| Zero Trust | `security.enable_auth: true`, `trusted_hosts` 설정 | Dashboard/CLI 모두 토큰 필요, CI에 토큰 전달 필요 |

보다 심화된 보안 시나리오는 [`docs/product/10-security.md`](../product/10-security.md)를 참고하세요.

---

## 6. 검증 루틴
1. `./yesman.py config lint` (예정) 전에는 `python scripts/config/validate.py`로 YAML 스키마를 미리 확인합니다.
2. `./yesman.py setup <session>`을 `--dry-run` 모드로 실행하면 템플릿 렌더링 결과만 출력합니다.
3. `./yesman.py show --json`으로 현재 세션 상태와 적용된 환경 변수를 확인해 설정이 의도대로 적용됐는지 검증합니다.
4. CI에서 `uv run pytest tests/config`를 추가하면 설정 파일 구조가 깨졌을 때 바로 감지할 수 있습니다.

---

## 7. 문제 해결 & 참고
- 설정 충돌: `projects.yaml`의 `session_name`이 중복되면 가장 마지막 항목만 유지되므로, 이름 앞에 팀/서비스 Prefix를 붙입니다.
- 템플릿 캐싱: 템플릿을 수정하고도 반영되지 않으면 `./yesman.py cache clear templates`를 실행하거나 `~/.cache/yesman`을 제거합니다.
- LLM Provider 교체: `llm.provider`/`llm.model`을 수정한 뒤에는 `./yesman.py controller restart`로 Claude Manager를 재시작하세요.

추가로 필요한 구성 시나리오가 있다면 예제 디렉터리에 Issue/PR로 제안해주세요.
