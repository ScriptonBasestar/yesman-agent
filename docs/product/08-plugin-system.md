# 🔌 Plug-in System

## 1. 개념
- **Plugin**: 특정 작업(요약, 번역, 코드 분석 등)을 담당하는 모듈. Agent Runtime이 Context + Input을 전달하면 결과를 반환합니다.
- **Workflow Hook**: Workflow 단계별 Before/After 동작. 파일 아카이빙, Slack 알림, 외부 API 호출 등을 처리합니다.
- **Provider Adapter**: Claude/Ollama/OpenAI 등 모델별 정책을 캡슐화해 Prompt 엔진이 동일한 인터페이스를 사용하도록 합니다.

## 2. 구조
```text
agents/
  └─ summary.py      # Plugin 예시
plugins/
  └─ __init__.py     # Plugin Registry
workflows/
  └─ docs-sync.yaml  # Plugin을 호출하는 워크플로
```

## 3. Plugin 인터페이스 예시
```python
class Plugin(Protocol):
    name: str

    def supports(self, task: str) -> bool: ...

    async def run(self, context: PluginContext) -> PluginResult:
        ...
```

## 4. 개발 순서
1. `plugins/` 폴더에 모듈 생성 후 `Plugin` 프로토콜 구현.
2. `plugins/__init__.py` 또는 레지스트리에 플러그인을 등록.
3. `yesman.yaml`의 `plugins` 섹션 또는 Workflow 단계에서 이름을 참조.
4. 필요 시 FastAPI/CLI에 새로운 명령을 추가해 입력값을 수집.

## 5. 베스트 프랙티스
- **Idempotent**: 동일 입력에 대해 동일 결과를 보장하여 재시도 시 안전하도록 합니다.
- **Structured Result**: JSON/Dict 형태로 결과를 반환해 Dashboard/CLI가 재사용할 수 있게 합니다.
- **Observability**: 실행 시간, 모델 사용량, 오류를 로깅하고 필요 시 `events` 채널에 게시합니다.
- **Isolation**: 외부 명령 실행 시 sandbox 경로를 명시하고, 권한을 최소화하세요.
