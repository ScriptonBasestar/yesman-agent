# Multi-AI Provider Integration Guide

Yesman-Claude에서 다양한 AI 제공업체를 통합 관리하는 가이드입니다.

## 🎯 개요

Multi-AI Provider 시스템을 통해 다음 AI 서비스들을 통합 관리할 수 있습니다:

- **Claude Code** 🚀 - 기본 제공업체 (Anthropic)
- **Ollama** 🦙 - 로컬 AI 모델 실행
- **OpenAI GPT** 💬 - ChatGPT API
- **Google Gemini** 💎 - Gemini Pro/Flash
- **Gemini Code** ⚡ - 코딩 전용 Gemini

## 🚀 빠른 시작

### 1. 기본 설정

```bash
# 설정 파일 복사
cp config/multi-ai-providers.example.yaml ~/.scripton/yesman/multi-ai-providers.yaml

# API 서버 시작
make start

# 웹 대시보드 실행
make dashboard-web
```

### 2. 웹 대시보드에서 설정

1. 브라우저에서 `http://localhost:10501` 접속
2. 사이드바에서 "AI Providers" 클릭
3. "Register Provider" 버튼 클릭
4. 제공업체 선택 및 설정 입력

## 📋 제공업체별 설정

### Claude Code (기본)

```json
{
  "claude_binary_path": "/opt/homebrew/bin/claude",
  "workspace_base": "/tmp/yesman-workspaces",
  "max_workspace_size_mb": 1000,
  "max_workspaces": 10,
  "ANTHROPIC_API_KEY": "your-anthropic-api-key"
}
```

**필수 설정:**
- `claude_binary_path`: Claude CLI 바이너리 경로
- `workspace_base`: 작업공간 기본 디렉토리
- `ANTHROPIC_API_KEY`: Anthropic API 키

### Ollama (로컬 AI)

```json
{
  "base_url": "http://localhost:11434",
  "timeout": 300,
  "default_model": "llama3.1"
}
```

**사전 준비:**
```bash
# Ollama 설치 및 실행
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &

# 모델 다운로드
ollama pull llama3.1
ollama pull codellama
```

### OpenAI ChatGPT

```json
{
  "api_key": "your-openai-api-key",
  "base_url": "https://api.openai.com/v1",
  "organization": ""
}
```

**API 키 발급:**
1. [OpenAI Platform](https://platform.openai.com) 접속
2. API Keys 섹션에서 새 키 생성
3. 결제 정보 등록 (사용량 기준 과금)

### Google Gemini

```json
{
  "api_key": "your-gemini-api-key",
  "base_url": "https://generativelanguage.googleapis.com/v1beta",
  "safety_settings": {
    "harassment": "BLOCK_MEDIUM_AND_ABOVE",
    "hate_speech": "BLOCK_MEDIUM_AND_ABOVE",
    "sexually_explicit": "BLOCK_MEDIUM_AND_ABOVE", 
    "dangerous_content": "BLOCK_MEDIUM_AND_ABOVE"
  }
}
```

**API 키 발급:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. API 키 생성
3. 무료 할당량 또는 유료 플랜 선택

## 💻 API 사용법

### REST API 엔드포인트

```bash
# 제공업체 목록 조회
curl http://localhost:10501/api/ai-providers/

# 제공업체 등록
curl -X POST http://localhost:10501/api/ai-providers/register \
  -H "Content-Type: application/json" \
  -d '{
    "provider_type": "ollama",
    "config": {
      "base_url": "http://localhost:11434"
    }
  }'

# AI 작업 실행
curl -X POST http://localhost:10501/api/ai-providers/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "provider": "ollama", 
    "model": "llama3.1",
    "temperature": 0.7
  }'
```

### Python 클라이언트 사용

```python
from libs.ai import ai_provider_manager, AITask, AIProviderType
import asyncio

async def example():
    # 작업 생성
    task = AITask(
        task_id="test-001",
        prompt="Python으로 피보나치 수열 함수를 작성해주세요",
        provider=AIProviderType.CLAUDE_CODE,
        model="claude-3-5-sonnet-20241022",
        temperature=0.0
    )
    
    # 작업 실행
    response = await ai_provider_manager.execute_task(task)
    print(f"응답: {response.content}")
    print(f"상태: {response.status}")

asyncio.run(example())
```

## 🔄 고급 설정

### 자동 장애 조치

```yaml
failover:
  enabled: true
  max_retries: 2
  timeout_threshold: 30
  
task_routing:
  coding:
    - "claude_code"
    - "gemini_code"
    - "openai_gpt"
```

### 모니터링 설정

```yaml
monitoring:
  health_check_interval: 60
  log_requests: true
  metrics_enabled: true
```

## 🛠️ 트러블슈팅

### Claude CLI 문제

**증상**: `Claude CLI not found`
```bash
# Claude CLI 설치 확인
which claude
claude --version

# PATH 설정 확인
echo $PATH
```

**해결책**:
```bash
# Claude CLI 설치
curl -L https://github.com/anthropics/claude-cli/releases/latest/download/claude-macos-arm64 -o claude
sudo mv claude /usr/local/bin/claude
sudo chmod +x /usr/local/bin/claude
```

### Ollama 연결 문제

**증상**: `Connection refused to localhost:11434`
```bash
# Ollama 서비스 상태 확인
ps aux | grep ollama
curl http://localhost:11434/api/version
```

**해결책**:
```bash
# Ollama 재시작
ollama serve &

# 방화벽 설정 확인
sudo lsof -i :11434
```

### API 키 오류

**증상**: `Invalid API key` 또는 `401 Unauthorized`

**해결책**:
1. API 키 유효성 확인
2. 환경변수 설정 확인
3. 요청 형식 검증
4. 할당량 및 결제 상태 점검

### 메모리 부족

**증상**: `Out of memory` 또는 성능 저하

**해결책**:
```yaml
# 작업공간 크기 제한
max_workspace_size_mb: 500
max_workspaces: 5

# 타임아웃 조정
timeout: 120
```

## 📊 성능 최적화

### 모델 선택 가이드

| 작업 유형 | 추천 모델 | 특징 |
|----------|----------|------|
| 코딩 | Claude Code, Gemini Code | 정확성, 컨텍스트 |
| 일반 질답 | GPT-4o, Gemini Pro | 창의성, 추론 |
| 빠른 응답 | Ollama, GPT-3.5 | 속도, 비용 |
| 대용량 텍스트 | Claude Sonnet | 긴 컨텍스트 |

### 비용 최적화

```yaml
# 모델별 비용 (참고용)
cost_optimization:
  claude_code: "토큰당 비용 확인"
  openai_gpt: "$0.03/1K tokens (GPT-4)"  
  gemini: "무료 할당량 후 유료"
  ollama: "로컬 실행 - 무료"
```

## 🔐 보안 고려사항

### API 키 관리

```bash
# 환경변수 설정
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"  
export GEMINI_API_KEY="your-key"

# 설정 파일 권한
chmod 600 ~/.scripton/yesman/multi-ai-providers.yaml
```

### 네트워크 보안

```yaml
security:
  request_rate_limit: 100  # 분당 요청 수 제한
  workspace_isolation: true  # 작업공간 격리
  api_key_rotation: false  # API 키 순환 (고급)
```

## 📚 추가 리소스

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Ollama Documentation](https://ollama.ai/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google AI Studio](https://makersuite.google.com)

## 🆘 지원

문제 발생 시:

1. **로그 확인**: `curl http://localhost:10501/api/logs?service=ai-providers`
2. **상태 점검**: `curl http://localhost:10501/api/status?detailed=true`
3. **헬스 체크**: `curl http://localhost:10501/api/ai-providers/health-check`
4. **이슈 리포트**: [GitHub Issues](https://github.com/your-repo/yesman-agent/issues)