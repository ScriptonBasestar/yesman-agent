# ⚙️ Configuration Guide

## 1. 파일 위치
- 글로벌 설정: `$HOME/.scripton/yesman/yesman.yaml`
- 세션 템플릿: `$HOME/.scripton/yesman/templates/*.yaml`
- 워크플로: `templates/workflows/*.yaml` 또는 저장소 내 커스텀 경로

## 2. 기본 yesman.yaml 예시
```yaml
llm:
  provider: claude
  model: claude-code-3-sonnet
  api_key: ${CLAUDE_API_KEY}
  streaming: true

agents:
  default:
    retry_limit: 3
    guardrails:
      mask_sensitive: true
      allow_shell: false

workflows:
  docs-sync:
    steps:
      - task: summary
        input: docs/README.md
      - task: notify
        channel: slack
```

## 3. 템플릿 설정 스니펫
```yaml
session_name: "demo"
workspace_config:
  base_dir: "~/workspace/demo"
windows:
  - window_name: api
    panes:
      - shell_command: "uv run uvicorn api.main:app --reload"
  - window_name: dashboard
    panes:
      - shell_command: "cd tauri-dashboard && pnpm dev"
```

## 4. Provider & Plugin 정의
```yaml
providers:
  claude:
    type: claude
    cli_path: $HOME/.local/bin/claude
    headless: true
  ollama:
    type: ollama
    endpoint: http://localhost:11434

plugins:
  - name: summary
    module: plugins.summary
    max_tokens: 2048
  - name: translate
    module: plugins.translate
    locale: ko-KR
```

## 5. 환경 변수 & Secret 관리
- `.env` 또는 시스템 환경 변수를 통해 API Key를 주입합니다.
- `yesman.py configure --mask` 옵션으로 민감 값을 마스킹한 상태로 저장할 수 있습니다.
- CI에서는 `UV_PROJECT_ENVIRONMENT=ci`를 설정해 테스트용 Provider Key를 분리하십시오.
