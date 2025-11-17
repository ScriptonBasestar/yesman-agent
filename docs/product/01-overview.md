# 🧠 Yesman Agent — Overview

Yesman Agent는 Claude Code Headless 모드, tmux 기반 개발 세션, FastAPI API 서버, SvelteKit/Tauri 대시보드를 하나의 자동화 워크플로로 묶어 주는 **LLM 기반 운영/자동화 플랫폼**입니다. 반복적인 CLI 상호작용을 에이전트화하고, 실시간으로 관찰하고, 팀 표준 템플릿으로 재사용할 수 있습니다.

## 🎯 미션
- 개발자와 SRE가 **스크립트를 작성하지 않고도** 복잡한 세션·워크플로를 자동화하도록 돕습니다.
- 로컬, 원격, CI 등 실행 환경에 상관없이 **일관된 에이전트 경험**을 제공합니다.
- 구성 요소(LLM, 플러그인, 템플릿)를 모듈화하여 **조합 가능한 자동화 허브**를 만듭니다.

## ⭐ 차별점
1. **Headless Claude Code 제어**: CLI 명령과 프롬프트 이력을 자동으로 관리하고 JSON 스트리밍으로 진행 상황을 관찰합니다.
2. **tmux 기반 세션 오케스트레이션**: 템플릿 YAML 한 장으로 프로젝트별 창/패널, 부트스트랩 명령, 리소스 제한을 정의합니다.
3. **하나의 설정 → 모든 인터페이스**: CLI, FastAPI, Web/Tauri가 같은 `yesman.yaml` 구성을 공유합니다.
4. **플러그인·워크플로 레이어**: 반복되는 업무를 Task/Workflow 형태로 캡슐화해 재사용하고, 다중 에이전트도 쉽게 구성합니다.

## 🧭 설계 원칙
- **Declarative First**: YAML/JSON 설정으로 대부분의 동작을 기술하고, 코드 수정 없이 현장 피드백을 반영합니다.
- **Observability Everywhere**: 모든 명령, 로그, 상태를 API/Dashboard/CLI에서 동일하게 노출합니다.
- **LLM Safety**: Prompt Guardrail, Retry, Context Masking을 내장해 운영 환경에서도 신뢰할 수 있도록 설계했습니다.
- **Composable Automation**: 템플릿→에이전트→워크플로→대시보드로 이어지는 계층을 조합 가능하도록 유지합니다.
