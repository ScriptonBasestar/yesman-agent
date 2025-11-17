# 🚀 Getting Started

## 1. 필수 조건
- Python 3.11+, `uv` (권장), `tmux` 3.x, Node.js 20+ (대시보드 개발 시), Rust/Cargo (Tauri).
- Claude CLI 또는 선택한 LLM Provider 자격 증명.

## 2. 설치
````bash
git clone https://github.com/ScriptonBasestar/yesman-agent.git
cd yesman-agent
make dev-install        # uv + Python 의존성 설치
make install-dashboard  # (옵션) 대시보드 의존성 설치
````

## 3. 초기 설정
````bash
./yesman.py configure              # yesman.yaml 생성 위저드 (또는 직접 작성)
./yesman.py templates list         # 기본 템플릿 확인
cp templates/example.yaml ~/.scripton/yesman/templates/demo.yaml
````

## 4. 실행 예시
````bash
./yesman.py setup demo             # 템플릿 기반 tmux 세션 생성
./yesman.py run workflow docs-sync # Workflow 실행
make start                         # FastAPI 서버 기동 (REST/SSE)
make dashboard-web                 # 웹 대시보드
make dashboard-desktop             # Tauri 앱 (옵션)
````

## 5. 상태 확인 및 종료
````bash
./yesman.py show        # 실행 중 세션 목록
./yesman.py enter demo  # tmux 세션 접속
./yesman.py stop demo   # 세션 종료 및 리소스 정리
make stop               # API/대시보드 종료
````

> ✅ 더 많은 예시는 `examples/`, `templates/` 디렉터리와 `docs/30-user-guide`를 참고하세요.
