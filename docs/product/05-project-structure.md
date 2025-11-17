# 📦 Project Structure

```
yesman-agent/
├── PRODUCT.md                # 요약 문서
├── yesman.py                 # CLI 엔트리포인트
├── api/                      # FastAPI 서버 (REST/SSE/WebSocket)
├── libs/                     # CLI/Workflow/Prompt 관련 Python 라이브러리
├── tauri-dashboard/          # SvelteKit + Tauri 대시보드
├── templates/                # Workflow / Agent 템플릿 샘플
├── docs/product/             # 상세 제품 문서 (본 문서 집합)
├── docs/00-overview~70-...   # 세부 가이드, 운영, 예제, 아키텍처
├── scripts/                  # 설치/운영/CI 스크립트
├── tests/                    # pytest 기반 테스트 스위트
└── Makefile*.mk              # 설치·품질·테스트 자동화 타깃
```

## 디렉터리별 설명
- **api/**: FastAPI 라우터, SSE 브로드캐스터, Provider 상태 점검, 인증 훅 등을 포함합니다.
- **libs/**: CLI 명령, 템플릿 파서, workflow 엔진, config 로더 등 핵심 Python 코드가 위치합니다.
- **tauri-dashboard/**: `src/` (SvelteKit UI), `src-tauri/` (Rust 백엔드)로 구성되어 Web/Tauri 앱을 동시에 빌드합니다.
- **templates/**: tmux 세션, Workflow, Provider 설정을 빠르게 시작할 수 있는 YAML 예제가 들어 있습니다.
- **docs/**: `product/` 외에도 API 가이드, 운영 지침, 예제가 하위 폴더로 구분되어 있습니다.
- **scripts/**: `install.sh`, `bootstrap.py` 등 환경 구성과 배포 자동화를 돕는 도구 모음입니다.
- **tests/**: 단위·통합·E2E 테스트 및 pytest fixture가 들어 있습니다.
