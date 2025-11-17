# 🧠 Yesman Agent — PRODUCT Overview
AI 기반 자동화 에이전트 프레임워크

---

## ⚡ 한눈에 보기
- Claude Code·CLI·Dashboard를 아우르는 **자동화·관측·운영 에이전트 허브**입니다.
- tmux 기반 개발 세션, FastAPI 백엔드, Web/Tauri 대시보드를 **단일 워크플로**로 묶어 반복 업무를 자동화합니다.
- `uv`·`make`·CLI 만으로 **로컬/CI 어디서든 실행**하고, 에이전트·플러그인·워크플로를 스크립트 없이 조립합니다.

---

## 🧩 핵심 구성요소
| 영역 | 역할 |
| --- | --- |
| CLI Runtime | `yesman.py` 기반 세션 자동화, 템플릿·tmux 제어, 워크플로 실행 |
| Agent Engine | Context Loader, Retry/Recovery, Headless Claude Code 연동 |
| FastAPI Server | REST/SSE API, 작업 스트리밍, 상태 모니터링 |
| Dashboard Layer | SvelteKit Web + Tauri Desktop, 실시간 로그/상태 뷰 |
| Plugin / Workflow System | YAML 템플릿, 플러그인·LLM 제공자 구성, CI 파이프라인 접목 |

---

## 🏗 아키텍처 스냅샷
- CLI·API·Dashboard가 **Agent Runtime**을 중심으로 같은 설정을 공유하여 동일한 자동화 경험을 제공합니다.
- FastAPI ↔ SvelteKit/Tauri ↔ tmux/Claude CLI가 **이벤트 스트림**으로 연결되어 작업 생성→모니터링→정리에 이르는 전 과정을 자동화합니다.
- Provider/Plugin 레이어는 YAML 설정 한 곳에서 선언돼 환경에 따라 **동적으로 활성화**됩니다.

---

## 🚀 빠른 시작
````bash
git clone https://github.com/ScriptonBasestar/yesman-agent.git
cd yesman-agent
make dev-install       # uv 및 Python 의존성 설치
./yesman.py --help     # CLI 기능 확인
./yesman.py setup demo # 샘플 템플릿으로 tmux 세션 생성
````

---

## 📚 자세한 문서 (Full Documentation)
- [Overview](docs/product/01-overview.md)
- [Target Users & Use Cases](docs/product/02-target-users.md)
- [Core Features](docs/product/03-features.md)
- [Architecture](docs/product/04-architecture.md)
- [Project Structure](docs/product/05-project-structure.md)
- [Getting Started](docs/product/06-getting-started.md)
- [Configuration](docs/product/07-configuration.md)
- [Plug-in System](docs/product/08-plugin-system.md)
- [Testing Strategy](docs/product/09-testing.md)
- [Security & Privacy](docs/product/10-security.md)
- [Roadmap](docs/product/11-roadmap.md)
