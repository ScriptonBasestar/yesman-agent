# Agents API 500 Error Fix

## 발견 날짜
2025-09-08

## 문제 요약
/agents 페이지 접속 시 HTTP 500 Internal Server Error 발생

## 상세 문제

### 1. 오류 현상
- **URL**: `http://localhost:5173/agents`
- **응답**: `{"error":{"code":"HTTP_500","message":"Internal server error"...}}`
- **API 엔드포인트**: `GET /api/agents/` 500 에러 반환

### 2. 근본 원인
- `libs/core/services.py`의 `create_claude_service()` 함수에서 `config._config_schema.claude` 속성 접근 시도
- `YesmanConfigSchema`에 `claude` 속성이 정의되지 않아 `AttributeError` 발생
- 구체적 에러: `'YesmanConfigSchema' object has no attribute 'claude'`

### 3. 디버깅 과정
```bash
# 1. API 직접 테스트
curl -s http://localhost:10501/api/agents/ | jq .
# 결과: {"error": {"code": "HTTP_500"...}}

# 2. 디버그 스크립트 생성 및 실행
uv run python tmp/debug_agents.py
# 결과: AttributeError 발생 확인

# 3. 설정 파일 구조 확인
# config/claude-headless.example.yaml에서 claude 설정 구조 확인
```

### 4. 설정 구조 분석
- **예상되는 구조** (`claude-headless.example.yaml`):
  ```yaml
  claude:
    mode: "headless"
    headless:
      enabled: true
      claude_binary_path: "/usr/local/bin/claude"
      workspace_root: "~/.scripton/yesman/workspaces"
      # 기타 설정...
  ```
- **실제 구조** (`YesmanConfigSchema`): `claude` 속성 미정의

## 해결 방법

### 수정된 코드
**파일**: `libs/core/services.py:49`

**변경 전**:
```python
claude_config = config._config_schema.claude
```

**변경 후**:
```python
# Check if claude config exists
claude_config = getattr(config._config_schema, 'claude', None)

if claude_config and hasattr(claude_config, 'mode') and claude_config.mode == "headless" and hasattr(claude_config, 'headless') and claude_config.headless.enabled:
```

### 수정 내용
1. **안전한 속성 접근**: `getattr()` 사용으로 AttributeError 방지
2. **조건부 검사**: claude 설정이 없을 때 graceful 처리
3. **폴백 동작**: claude 설정이 없으면 InteractiveAdapter로 폴백

## 검증 결과

### 1. API 테스트
```bash
curl -s http://localhost:10501/api/agents/ | jq .
# 결과: [] (빈 배열 - 정상)
```

### 2. 웹 인터페이스 테스트
- ✅ `/agents` 페이지 정상 로드
- ✅ "Headless Agents" 제목 표시
- ✅ "Active Agents (0)" 상태 표시
- ✅ "Create Agent", "Refresh" 버튼 활성화
- ✅ "No agents found" 메시지 정상 표시

### 3. 스크린샷 확인
- 캡처 파일: `.playwright-mcp/agents-page-fixed.png`
- 모든 UI 구성요소 정상 렌더링 확인

## 영향

### 긍정적 영향
- ✅ 에이전트 페이지 접근 가능
- ✅ Claude headless 설정이 없어도 기본 기능 동작
- ✅ 향후 claude 설정 추가 시 자동으로 headless 모드 활성화

### 주의사항
- Claude headless 기능을 사용하려면 별도 설정 파일에 claude 섹션 추가 필요
- 현재는 InteractiveAdapter로 동작 (실제 headless 에이전트 생성 불가)

## 관련 파일
- `libs/core/services.py` - 수정된 서비스 팩토리
- `config/claude-headless.example.yaml` - Claude 설정 예제
- `libs/core/config_schema.py` - 설정 스키마 정의
- `api/routers/agents.py` - 에이전트 API 라우터

## 상태
**완료** - 2025-09-08

## 후속 작업 권장
1. YesmanConfigSchema에 claude 설정 스키마 추가 고려
2. Claude headless 모드 설정 가이드 문서 작성
3. 에이전트 생성 UI에 설정 상태 표시 추가