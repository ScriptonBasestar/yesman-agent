# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yesman-Claude is a comprehensive CLI automation tool that manages tmux sessions and automates interactions with Claude
Code. It features multiple dashboard interfaces (Web, Tauri), AI-powered learning system, AI provider management with
auto-discovery, and extensive session management capabilities using YAML configuration templates.

## Development Commands

### Environment Setup

```bash
# Development installation (recommended approach)
make install             # Install in development mode with basic deps
make install-dev         # Install with development dependencies
make install-all         # Install with all dependencies (dev + test)

# Using uv (fastest, preferred for development)
uv run python -m pytest   # Run tests with uv
export UV_SYSTEM_PYTHON=true  # Use system Python with uv

# All commands should use uv instead of direct python execution

# Frontend dependencies
make install-dashboard-deps    # Install Tauri dashboard dependencies
cd tauri-dashboard && npm install  # Or install directly
```

### Core Commands

**Note**: The CLI interface is managed through Make commands and the API server. Direct Python module execution may not be available for all commands.

```bash
# Primary interface through Make commands
make start                              # Start API server
make stop                               # Stop all services
make status                             # Check service status
make dashboard                          # Launch dashboard interface

# Session management (via API or dashboard)
# Note: Direct CLI commands may not be implemented - use dashboard interface

# Dashboard interfaces
make dashboard                              # Smart dashboard launcher
make dashboard-web                          # SvelteKit web interface
make dashboard-desktop                      # Native desktop app
make dashboard-full                         # Full development environment

# AI learning system (via dashboard interface)
# Access dashboard for AI configuration and monitoring
# Web interface provides full AI management capabilities

# AI provider management (via dashboard)
# Access /ai-providers page for:
# - Auto-discovery of installed AI tools (Claude Code, Ollama, etc.)  
# - Provider registration and configuration
# - System-level detection via Tauri commands

# Status and monitoring
make dev-status                         # Check development service status
# Use dashboard for comprehensive monitoring and status
```

### Development Workflow

```bash
# Build and development
make build-all                  # Build complete project
make build-dashboard            # Build SvelteKit components only
cd tauri-dashboard && npm run build  # Build frontend assets

# Development servers
make start                      # Start API server in background
make stop                       # Stop all running servers
make restart                    # Restart all servers
make dashboard-full             # Full development environment (API + Web)
make dashboard-web              # Web dashboard only (Vite dev server)
make dashboard-desktop          # Tauri development mode
make dev-status                 # Check development service status

# API development
make debug-api                  # Start API server with debug logs in foreground
cd api && uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 10501

# Quality checks
make quick                      # Quick check (fast lint + unit tests) - alias for dev-fast
make dev-fast                   # Fast development cycle
make dev-full                   # Full quality check (comprehensive lint + test with coverage)
make full                       # Full quality check - alias for lint + test-coverage
make format                     # Code formatting and import organization
make test                       # Run all tests with coverage
make test-unit                  # Unit tests only
make test-integration           # Integration tests only
```

### Testing

```bash
# Test execution
pytest tests/                           # All tests
pytest tests/unit/                      # Unit tests only
pytest tests/integration/               # Integration tests only
pytest tests/test_specific_file.py      # Single test file
pytest -k "test_session"                # Tests matching pattern
pytest --cov=libs --cov=api             # With coverage (note: covers libs and api, not commands)

# Test categories (via markers from pyproject.toml)
pytest -m "unit"                        # Unit tests
pytest -m "integration"                 # Integration tests  
pytest -m "slow"                        # Long-running tests
pytest -m "security"                    # Security validation tests
pytest -m "performance"                 # Performance monitoring tests
pytest -m "property"                    # Property-based tests using Hypothesis
pytest -m "benchmark"                   # Performance benchmark tests
pytest -m "smoke"                       # Basic functionality validation

# Additional test options (configured in pyproject.toml)
pytest --timeout=120                    # Tests timeout after 120 seconds
pytest -n=auto                         # Run tests in parallel
pytest --maxfail=5                      # Stop after 5 failures
```

## Library Documentation with Context7

Use Context7 to get up-to-date documentation for project dependencies:

### Python Libraries

**Core Frameworks:**

- FastAPI: `/tiangolo/fastapi` - topics: `middleware`, `dependency-injection`, `websocket`
- Pydantic: `/pydantic/pydantic` - topics: `validators`, `settings`, `models`
- Click: `/pallets/click` - topics: `commands`, `groups`, `options`

**Note**: TUI libraries (Rich/Textual) were removed - the project now uses Web and Tauri interfaces only.

**Session Management:**

- tmuxp: `/tmux-python/tmuxp` - topics: `session`, `config`, `builder`
- libtmux: `/tmux-python/libtmux` - topics: `server`, `session`, `window`

**Testing:**

- pytest: `/pytest-dev/pytest` - topics: `fixtures`, `markers`, `plugins`
- Hypothesis: `/HypothesisWorks/hypothesis` - topics: `strategies`, `stateful`, `properties`

### JavaScript/Frontend Libraries

**Frameworks:**

- SvelteKit: `/sveltejs/kit` - topics: `routing`, `load`, `server`
- Tauri: `/tauri-apps/tauri` - topics: `commands`, `events`, `window`

**Visualization:**

- Chart.js: `/chartjs/Chart.js` - topics: `datasets`, `scales`, `plugins`
- D3.js: `/d3/d3` - topics: `selection`, `scale`, `transition`

**Styling:**

- TailwindCSS: `/tailwindlabs/tailwindcss` - topics: `utilities`, `components`, `responsive`
- DaisyUI: `/saadeghi/daisyui` - topics: `themes`, `components`, `modifiers`

**Package Management:**

- The project uses **pnpm** as the package manager for frontend dependencies (see `packageManager` in package.json)
- Python dependencies managed through `pyproject.toml` with `uv` as the preferred tool
- Development dependencies are organized in `[dependency-groups]` sections
- **Project package name**: `yesman-claude` (not `yesman-agent`) as defined in pyproject.toml

### Context7 Usage Examples

When working with specific libraries, use Context7 like this:

```bash
# Get FastAPI middleware documentation
# Use: resolve-library-id("fastapi") then get-library-docs with topic "middleware"

# Get SvelteKit routing patterns
# Use: get-library-docs("/sveltejs/kit", topic="routing")

# Get pytest fixture best practices
# Use: get-library-docs("/pytest-dev/pytest", topic="fixtures")
```

### Best Practices

1. **Always check latest docs** when implementing new features with these libraries
1. **Specify topics** for focused documentation retrieval
1. **Cross-reference** with project's existing patterns in codebase
1. **Prefer official Context7 IDs** over general web searches for accuracy

## Architecture Overview

### Core Design Patterns

**API-First Architecture**: The project uses a web API and dashboard-centric approach:

- FastAPI backend server as the primary interface
- Web and desktop dashboards for user interaction
- Service-based architecture with dependency injection
- Consistent error handling with recovery hints
- Type-safe service resolution through container pattern

**Dependency Injection**: Central DI container (`libs/core/container.py`) manages:

- Service lifecycle (singletons vs factories)
- Type-safe service resolution
- Circular dependency detection
- Configuration-based service registration

**Configuration Management**: Pydantic-based system (`libs/core/config_*`) with:

- Schema validation for YAML configs
- Environment-specific overrides
- Hierarchical config merging (global → local → project)
- Runtime configuration caching

### Key Architectural Components

**Session Management**:

- `libs/core/session_manager.py` - Core session lifecycle
- `libs/tmux_manager.py` - tmux integration layer
- YAML-based session templates with Jinja2-style variables
- Smart dependency optimization for faster session creation

**Claude Code Automation**:

- `libs/core/claude_manager.py` - Main automation controller
- `libs/core/prompt_detector.py` - Pattern-based prompt recognition
- `libs/core/content_collector.py` - Real-time content capture
- AI learning system with confidence scoring and pattern adaptation

**Multi-Interface Dashboard**:

- **Web**: SvelteKit + FastAPI serving static assets
- **Tauri**: Native desktop app sharing SvelteKit codebase
- Interface auto-detection based on environment capabilities

**Error Handling**:

- Centralized error system (`libs/core/error_handling.py`)
- Categorized error types with severity levels
- Automatic recovery hint generation
- Context preservation across error boundaries

### Data Flow Architecture

1. **Command Execution**: CLI commands → BaseCommand → Service resolution → Business logic
1. **Configuration Loading**: YAML files → Pydantic validation → Config cache → Service injection
1. **Session Creation**: Template selection → Variable substitution → tmux session creation → Claude automation setup
1. **Real-time Monitoring**: Content collection → Pattern detection → AI decision → Automated response
1. **Dashboard Updates**: Service events → FastAPI/WebSocket → Frontend updates

### File Structure Logic

```
libs/core/              # Core architecture components
├── container.py           # Dependency injection system
├── config_*.py           # Configuration management (schema, loader, cache, validator)
├── error_handling.py     # Centralized error handling
├── services.py           # Service registration and factories
├── interfaces.py         # Type definitions and contracts
├── models.py             # Data models and types
├── claude_manager.py     # Claude Code automation controller
├── session_manager.py    # Session lifecycle management
└── mixins.py             # Shared functionality mixins

api/                   # FastAPI web service
├── main.py              # FastAPI app with CORS and middleware
├── routers/             # API endpoint groupings
├── middleware/          # Custom middleware
└── background_tasks.py  # Async task management

tauri-dashboard/       # SvelteKit frontend (shared by web/tauri)
├── src/routes/          # SvelteKit pages and layouts
├── src/lib/            # Reusable components
├── src-tauri/          # Rust backend for desktop app
└── package.json        # Frontend dependencies and scripts

tests/                 # Test suites
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests
└── conftest.py        # Pytest configuration and fixtures
```

### Service Registration Pattern

Services are registered in `libs/core/services.py` using the DI container:

```python
# Singleton services (shared state)
container.register_singleton(YesmanConfig, config_instance)

# Factory services (new instance per request) 
container.register_factory(TmuxManager, lambda: TmuxManager(config))

# Type-safe resolution in commands
config = container.resolve(YesmanConfig)
```

### Configuration Hierarchy

1. **Global**: `~/.scripton/yesman/yesman.yaml` (logging, defaults)
1. **Templates**: `~/.scripton/yesman/templates/*.yaml` (reusable patterns)
1. **Sessions**: `~/.scripton/yesman/sessions/*.yaml` (individual session configs)
1. **Local**: `./.scripton/yesman/*` (project-specific overrides)

Templates support variable substitution and conditional logic for intelligent session creation.

### AI Learning System

The adaptive response system (`libs/ai/`) learns user patterns:

- Response confidence scoring with adjustable thresholds
- Pattern classification for different prompt types
- JSON-based persistence of learned behaviors
- Export/import capabilities for data portability

### Dashboard Interface Strategy

**Interface Selection Logic**:

1. Tauri (best UX) if desktop environment detected
1. Web (universal access) as fallback

**Shared Frontend**: SvelteKit codebase serves both web and Tauri interfaces, with Tauri providing native desktop
integration (system tray, notifications, file system access).

### Error Recovery Design

Errors include context-aware recovery hints:

- Configuration errors → suggest config file locations
- Missing dependencies → provide installation commands
- Session conflicts → offer resolution strategies
- Permission issues → suggest ownership fixes

This architecture emphasizes maintainability, testability, and extensibility while providing consistent behavior across
all interfaces and deployment scenarios.
