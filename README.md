# Yesman Claude

Yesman-Claude is a comprehensive CLI automation tool that manages tmux sessions and automates interactions with Claude
Code. It features modern dashboard interfaces (Web, Tauri), AI-powered learning system, and extensive session management
capabilities using YAML configuration templates.

## 🚀 Key Features

### Core Functionality

- **Claude Code Automation**: Automated responses and AI-powered learning system
- **Session Management**: Create and manage tmux sessions using YAML templates
- **AI Provider Management**: Auto-discovery and management of AI tools (Claude Code, Ollama, etc.)
- **FastAPI Backend Server**: RESTful API for session and workspace management
- **SvelteKit Web Interface**: Modern web interface for monitoring and control
- **Tauri Desktop Application**: Native desktop app with system integration
- **Real-time Monitoring**: Live session activity tracking and health monitoring

### Architecture

- **Python CLI Core**: Comprehensive automation engine with AI learning
- **FastAPI Server**: High-performance async backend
- **SvelteKit Frontend**: Shared codebase for both web and desktop interfaces
- **Tauri Native Wrapper**: Desktop application with native system integration
- **AI Learning System**: Adaptive response system with confidence scoring
- **Configuration Management**: Pydantic-based configuration with environment support
- **Error Handling**: Centralized error handling with recovery hints

## 📊 Interface Options

### 🌐 Web Interface (SvelteKit)

Modern web dashboard served via FastAPI backend.

```bash
# Start API server
make start

# Start web development server
make dashboard-web
# Access at: http://localhost:5173
```

### 🖱️ Desktop Application (Tauri + SvelteKit)

Native desktop app with the same SvelteKit codebase as web interface.

```bash
# Start Tauri development mode
make dashboard-desktop

# Full development environment (API + Web)
make dashboard-full
```

## 🔧 Quick Start

### Installation

```bash
# Development installation (recommended)
make dev-install
# or directly:
pip install -e . --config-settings editable_mode=compat

# Using uv (fastest, preferred for development)
uv run ./yesman.py --help

# Install all development dependencies
make install-all
```

### Basic Commands

```bash
# Core session management
./yesman.py ls                    # List templates and projects
./yesman.py setup [session-name]  # Create tmux sessions
./yesman.py show                  # List running sessions
./yesman.py enter [session-name]  # Attach to session

# Dashboard interfaces
make dashboard                    # Auto-detect best interface
make dashboard-web               # SvelteKit web interface
make dashboard-desktop           # Native desktop app

# Development workflow
make start                       # Start API server
make dev-status                  # Check server status
make stop                        # Stop all servers
```

## 📋 Interface Comparison

| Feature | Web | Tauri | |---------|-----|-------| | **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐ | | **Resource Usage** | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cross-platform** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | | **Remote Access** | ⭐⭐⭐⭐⭐ | ⭐ | | **User Experience** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | |
**Customization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | | **System Integration** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | | **AI Provider Management** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐
|

### When to Use Each Interface

- **Web**: Remote monitoring, team collaboration, browser-based workflows, development
- **Tauri**: Daily use, best user experience, desktop integration, system-level provider detection

## 설정 파일

### 글로벌 설정

글로벌 설정 파일은 다음 경로에 위치합니다:

```bash
$HOME/.scripton/yesman/yesman.yaml
$HOME/.scripton/yesman/sessions/   # Individual session files
```

파일 구조 examples/ 참고

## 템플릿 시스템

Yesman-Claude는 재사용 가능한 tmux 세션 템플릿을 지원합니다. 템플릿을 사용하면 여러 프로젝트에서 일관된 개발 환경을 쉽게 구성할 수 있습니다.

### 템플릿 위치

템플릿 파일은 `~/.scripton/yesman/templates/` 디렉터리에 YAML 형식으로 저장됩니다.

### 기본 템플릿 구조

```yaml
session_name: "{{ session_name }}"
workspace_config:
  base_dir: "{{ base_dir }}"
workspace_definitions:
  main:
    rel_dir: "."
    allowed_paths: ["."]
    description: "Main project workspace"
windows:
  - window_name: main
    layout: even-horizontal
    panes:
      - shell_command: "npm run dev"
```

### Smart Templates

"스마트 템플릿"은 조건부 명령 실행을 지원합니다:

```yaml
panes:
  - shell_command: |
      # 의존성이 없거나 오래된 경우에만 설치
      if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
        echo "Dependencies missing or outdated, installing..."
        pnpm install
      else
        echo "Dependencies up to date, skipping install"
      fi
      pnpm dev
```

### 템플릿 사용하기

개별 세션 파일에서 템플릿을 참조하고 필요한 값을 오버라이드할 수 있습니다:

```yaml
# ~/.scripton/yesman/sessions/my_project.yaml
session_name: "my_project"
template_name: "django"
override:
  session_name: my_django_app
  workspace_config:
    base_dir: "~/projects/django-app"
```

자세한 내용은 [템플릿 문서](docs/user-guide/templates.md)를 참조하세요.

## 🏗️ Development

### Architecture Overview

Yesman Claude는 현대적이고 유지보수 가능한 아키텍처로 구축되었습니다:

- **FastAPI Backend**: 고성능 비동기 Python 백엔드 서버
- **SvelteKit Frontend**: 반응형 웹 인터페이스 (Web + Tauri 공유)
- **Tauri Desktop**: 네이티브 데스크톱 앱 래퍼
- **Configuration Management**: Pydantic 스키마 기반의 검증 가능한 설정 시스템
- **Error Handling**: 중앙화된 에러 처리와 사용자 친화적인 복구 힌트

### Quick Start for Developers

```bash
# 개발 환경 설정
git clone <repository-url>
cd yesman-agent

# Development installation
make dev-install

# API server 시작
make start

# 웹 개발 서버 시작 (다른 터미널에서)
make dashboard-web

# 또는 Tauri 개발 모드
make dashboard-desktop

# 전체 개발 환경 (API + Web)
make dashboard-full
```

### Development Commands

```bash
# Core CLI commands
./yesman.py ls                    # List templates and projects
./yesman.py setup [session-name]  # Create tmux sessions
./yesman.py status               # Quick status overview
./yesman.py ai status           # Show AI learning status

# Development workflow
make dashboard                   # Smart dashboard launcher
make dev-status                 # Check development service status
make stop                       # Stop all servers
make debug-api                  # API server debug mode

# Quality checks
make dev-fast                   # Quick check (lint-fast + unit tests)
make dev-full                   # Full quality check
make format                     # Code formatting
```

### Documentation

- 📚 [Developer Guide](docs/developer-guide.md) - 개발자를 위한 상세 가이드
- 🏗️ [Architecture Decision Records](docs/adr/) - 아키텍처 결정 기록
- 🧪 [Testing Guide](docs/developer-guide.md#%ED%85%8C%EC%8A%A4%ED%8A%B8-%EA%B0%80%EC%9D%B4%EB%93%9C) - 테스트 작성 및 실행 가이드
- ⚙️ [Configuration](docs/developer-guide.md#%EC%84%A4%EC%A0%95-%EA%B4%80%EB%A6%AC) - 설정 관리 가이드

### Contributing

1. Fork the repository
1. Create a feature branch: `git checkout -b feature/my-feature`
1. Make your changes following the [Developer Guide](docs/developer-guide.md)
1. Add tests for new functionality
1. Ensure all tests pass: `make test`
1. Format code: `make format`
1. Commit changes: `git commit -m 'feat: add my feature'`
1. Push to the branch: `git push origin feature/my-feature`
1. Create a Pull Request

### Project Structure

```
yesman-agent/
├── yesman.py          # Main CLI entry point
├── commands/          # CLI command implementations
├── libs/              # Core library modules
│   ├── core/             # Core architecture components
│   ├── ai/               # AI learning and automation
│   └── dashboard/        # Dashboard integrations
├── api/               # FastAPI backend server
├── tauri-dashboard/   # SvelteKit frontend (Web + Tauri)
│   ├── src/routes/       # SvelteKit pages (Projects, AI Providers)
│   ├── src/lib/          # Reusable components
│   └── src-tauri/        # Rust backend for desktop
├── tests/             # Test suites
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/              # Documentation
└── examples/          # Configuration examples
```

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.
