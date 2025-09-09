# AI Provider Management

AI Provider 자동 탐지 및 관리 시스템에 대한 종합 가이드입니다.

## 📋 목차

1. [개요](#개요)
1. [지원하는 AI Provider](#지원하는-ai-provider)
1. [탐지 방식](#탐지-방식)
1. [Provider 상태](#provider-상태)
1. [사용 방법](#사용-방법)
1. [설정 관리](#설정-관리)
1. [Tauri vs Web 인터페이스](#tauri-vs-web-인터페이스)

## 🎯 개요

Yesman-Agent는 시스템에 설치된 AI 도구들을 자동으로 탐지하고 관리하는 포괄적인 시스템을 제공합니다. 이 시스템은 다양한 AI Provider를 통합하여 하나의 인터페이스에서 관리할 수 있도록 합니다.

### 핵심 기능

- **자동 탐지**: 시스템에 설치된 AI 도구 자동 검색
- **상태 관리**: Provider별 설치/등록/활성화 상태 추적
- **크로스 플랫폼**: Windows, macOS, Linux 지원
- **실시간 모니터링**: Provider 상태 실시간 업데이트
- **설정 통합**: 모든 Provider 설정을 중앙에서 관리

## 🤖 지원하는 AI Provider

### 현재 지원 Provider

1. **Claude Code**
   - CLI 도구: `claude`
   - 환경변수: `CLAUDE_API_KEY`, `ANTHROPIC_API_KEY`
   - 서비스: claude 관련 프로세스

1. **Ollama**
   - CLI 도구: `ollama`
   - 환경변수: `OLLAMA_HOST`
   - 서비스: `ollama serve`, `ollama` 프로세스

1. **OpenAI CLI**
   - CLI 도구: `openai`
   - 환경변수: `OPENAI_API_KEY`
   - 서비스: N/A

1. **GitHub Copilot**
   - CLI 도구: `gh copilot`, `github-copilot-cli`
   - 환경변수: N/A
   - 서비스: copilot 관련 프로세스

### 향후 추가 예정

- Hugging Face CLI
- Azure OpenAI
- Google AI Studio
- Cohere CLI
- Mistral AI

## 🔍 탐지 방식

AI Provider 탐지는 다음 3가지 방법을 조합하여 수행됩니다:

### 1. CLI 도구 탐지

시스템 PATH에서 명령어 도구를 검색합니다.

```bash
# 예시: which 명령어로 확인
which claude    # /usr/local/bin/claude
which ollama    # /opt/homebrew/bin/ollama
```

**탐지 대상**:
- `claude` (Claude Code CLI)
- `ollama` (Ollama CLI)
- `openai` (OpenAI CLI)
- `gh` (GitHub CLI - Copilot 기능 확인)

### 2. 환경변수 탐지

중요한 API 키 및 설정 환경변수를 확인합니다.

```bash
# 예시 환경변수들
echo $CLAUDE_API_KEY
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
echo $OLLAMA_HOST
```

**확인 대상**:
- `CLAUDE_API_KEY`, `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `OLLAMA_HOST`
- `GITHUB_TOKEN` (Copilot 용)

### 3. 실행 중인 서비스 탐지

시스템에서 실행 중인 AI 관련 프로세스를 확인합니다.

```bash
# 예시: pgrep으로 확인
pgrep -f "ollama serve"
pgrep -f "claude"
```

**확인 대상**:
- `ollama serve`, `ollama`
- `claude` 관련 프로세스
- `copilot` 관련 프로세스

## 📊 Provider 상태

각 AI Provider는 다음 4가지 상태 중 하나를 가집니다:

### 🔴 not_installed
- **의미**: Provider가 시스템에 설치되지 않음
- **탐지 결과**: CLI 도구, 환경변수, 실행 서비스 모두 없음
- **액션**: 설치 가이드 제공

### 🟡 detected  
- **의미**: Provider가 설치되었지만 설정되지 않음
- **탐지 결과**: CLI 도구는 있지만 환경변수나 설정 부족
- **액션**: 설정 가이드 제공

### 🟢 registered
- **의미**: Provider가 설치되고 설정 완료
- **탐지 결과**: CLI 도구 + 환경변수 설정 완료
- **액션**: 활성화 가능

### 🔵 active
- **의미**: Provider가 현재 실행 중
- **탐지 결과**: 설정 완료 + 실행 중인 서비스 확인
- **액션**: 모든 기능 사용 가능

## 💻 사용 방법

### Tauri 데스크톱 앱에서

1. **AI Providers 페이지 접근**:
   ```bash
   make dashboard-desktop
   ```

2. **자동 탐지 실행**:
   - "Detect Providers" 버튼 클릭
   - 시스템 전체 스캔 시작
   - 실시간으로 탐지 결과 업데이트

3. **Provider 관리**:
   - 각 Provider 카드에서 상태 확인
   - 설정 버튼으로 상세 설정
   - 실행/중지 컨트롤

### 웹 인터페이스에서

1. **웹 대시보드 실행**:
   ```bash
   make dashboard-web
   ```

2. **AI Providers 섹션**:
   - http://localhost:5173/ai-providers 접근
   - Mock 데이터로 UI 테스트
   - 실제 탐지는 Tauri에서만 지원

## ⚙️ 설정 관리

### Provider별 설정 예시

**Claude Code 설정**:
```json
{
  "api_key": "your-claude-api-key",
  "base_url": "https://api.anthropic.com",
  "model": "claude-3-opus-20240229",
  "timeout": 30
}
```

**Ollama 설정**:
```json
{
  "host": "http://localhost:11434",
  "model": "llama2",
  "temperature": 0.7,
  "context_length": 4096
}
```

**OpenAI 설정**:
```json
{
  "api_key": "your-openai-api-key",
  "organization": "org-xxxxxxxx",
  "model": "gpt-4",
  "max_tokens": 2048
}
```

### 설정 파일 위치

```bash
# 전역 설정
~/.scripton/yesman/ai-providers.yaml

# 프로젝트별 설정
./.scripton/yesman/ai-providers.yaml
```

### 설정 파일 구조

```yaml
providers:
  claude:
    enabled: true
    api_key: "${CLAUDE_API_KEY}"
    model: "claude-3-opus-20240229"
  
  ollama:
    enabled: true
    host: "http://localhost:11434"
    default_model: "llama2"
  
  openai:
    enabled: false
    api_key: "${OPENAI_API_KEY}"
    organization: "${OPENAI_ORG}"
```

## 🖥️ Tauri vs Web 인터페이스

### Tauri 데스크톱 앱

**장점**:
- ✅ 실제 시스템 탐지 기능
- ✅ 네이티브 성능
- ✅ 시스템 레벨 접근
- ✅ 파일 시스템 통합
- ✅ 실시간 프로세스 모니터링

**제약사항**:
- ❌ 원격 접속 불가
- ❌ 브라우저 기반 워크플로우 불가

### 웹 인터페이스  

**장점**:
- ✅ 브라우저에서 접근 가능
- ✅ 원격 모니터링 지원
- ✅ 팀 협업 기능
- ✅ 모바일 반응형

**제약사항**:
- ❌ 시스템 레벨 탐지 불가
- ❌ Mock 데이터만 표시
- ❌ 보안 제약 (브라우저 샌드박스)

### 권장사항

- **개발 및 일상 사용**: Tauri 데스크톱 앱 권장
- **원격 모니터링**: 웹 인터페이스 활용
- **팀 환경**: 웹 + Tauri 조합 사용

## 🔧 개발자 가이드

### 새로운 Provider 추가

1. **탐지 규칙 추가** (`tauri-dashboard/src/lib/ai-providers/types.ts`):
```typescript
export interface AIProvider {
  name: string;
  displayName: string;
  cliCommands: string[];
  envVars: string[];
  processes: string[];
  // ... 기타 속성
}
```

2. **Tauri 백엔드 확장** (`tauri-dashboard/src-tauri/src/python_bridge.rs`):
```rust
// 새로운 탐지 명령어 추가
#[command]
pub async fn detect_new_provider() -> Result<ProviderDetectionResult, String> {
    // Provider별 탐지 로직
}
```

3. **프론트엔드 통합** (`tauri-dashboard/src/routes/ai-providers/+page.svelte`):
```svelte
<!-- Provider 카드 컴포넌트 추가 -->
<ProviderCard provider={newProvider} />
```

### 테스트

```bash
# Provider 탐지 테스트
make test-ai-providers

# 통합 테스트
make test-integration
```

## 📚 참고 자료

- [Tauri 시스템 통합](https://tauri.app/v1/guides/features/system-tray)
- [Claude Code CLI 문서](https://claude.ai/code)
- [Ollama 설치 가이드](https://ollama.ai/download)
- [OpenAI CLI 문서](https://platform.openai.com/docs/guides/cli)

______________________________________________________________________

**마지막 업데이트**: 2025-01-09  
**버전**: v2.1  
**문서 레벨**: Integration Guide