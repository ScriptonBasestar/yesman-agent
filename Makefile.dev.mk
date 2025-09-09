# Makefile.dev.mk - Development Workflow for yesman-claude
# Development environment, workflow automation, and quick iteration

# ==============================================================================
# Development Configuration
# ==============================================================================

# Colors are exported from main Makefile

# ==============================================================================
# Quick Start Commands
# ==============================================================================

.PHONY: start stop restart dev-status logs debug-api

# Core application control - most frequently used commands
start: ## Start API server in background
	@echo -e "$(CYAN)Starting API Server...$(RESET)"
	@if pgrep -f "uvicorn.*api.main:app" > /dev/null; then \
		echo -e "$(YELLOW)⚠️  API server already running$(RESET)"; \
	else \
		nohup uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 & \
		echo -e "$(GREEN)✅ API server started in background (see api.log)$(RESET)"; \
		echo -e "$(BLUE)🌐 API available at: http://localhost:10501$(RESET)"; \
	fi

stop: ## Stop all running servers and processes
	@echo -e "$(YELLOW)Stopping all servers...$(RESET)"
	@pkill -f "uvicorn.*api.main:app" || echo -e "$(BLUE)No API server running$(RESET)"
	@pkill -f "vite.*tauri-dashboard" || echo -e "$(BLUE)No Vite server running$(RESET)"
	@pkill -f "tauri dev" || echo -e "$(BLUE)No Tauri dev server running$(RESET)"
	@echo -e "$(GREEN)✅ All servers stopped$(RESET)"

restart: stop start ## Restart all servers

dev-status: ## Check status of development services (API, Vite, Tauri)
	@echo -e "$(CYAN)Development Service Status:$(RESET)"
	@echo ""
	@echo -n -e "  API Server:         "; \
	if pgrep -f "uvicorn.*api.main:app" > /dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET) (port 10501)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
	@echo -n -e "  Vite Dev Server:    "; \
	if netstat -tlnp 2>/dev/null | grep -q ":5173.*LISTEN" || ss -tlnp 2>/dev/null | grep -q ":5173.*LISTEN"; then \
		echo -e "$(GREEN)✅ Running$(RESET) (port 5173)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
	@echo -n -e "  Tauri Dev:          "; \
	if ps aux | grep -E "(tauri|tauri dev)" | grep -v grep > /dev/null 2>&1; then \
		echo -e "$(GREEN)✅ Running$(RESET)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi

logs: ## Show recent log files
	@echo -e "$(CYAN)Recent log files:$(RESET)"
	@find . -name "*.log" -type f -mtime -7 -exec ls -la {} \; 2>/dev/null || echo -e "$(YELLOW)No recent log files found$(RESET)"

debug-api: ## Debug API server in foreground with detailed logs
	@echo -e "$(CYAN)Starting API Server in Debug Mode...$(RESET)"
	@echo -e "$(YELLOW)Press Ctrl+C to stop$(RESET)"
	uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 --log-level debug

# ==============================================================================
# Dashboard Management
# ==============================================================================

.PHONY: dashboard dashboard-web dashboard-desktop dashboard-full dashboard-open

# Smart dashboard launcher with auto-detection
dashboard: ## Start dashboard (auto-detect best interface)
	@echo -e "$(CYAN)Checking Dashboard Status...$(RESET)"
	@if ps aux | grep -E "(tauri|tauri dev)" | grep -v grep > /dev/null 2>&1; then \
		echo -e "$(GREEN)✅ Tauri dashboard is already running!$(RESET)"; \
		echo -e "$(BLUE)🖥️  Desktop app should be visible on your screen$(RESET)"; \
	elif netstat -tlnp 2>/dev/null | grep -q ":5173.*LISTEN" || ss -tlnp 2>/dev/null | grep -q ":5173.*LISTEN"; then \
		echo -e "$(GREEN)✅ Vite dev server is running$(RESET)"; \
		echo -e "$(BLUE)🌐 Web dashboard available at: http://localhost:5173$(RESET)"; \
	else \
		echo -e "$(CYAN)Starting Web Dashboard...$(RESET)"; \
		make dashboard-web; \
	fi

dashboard-web: ## Start web dashboard (Vite dev server)
	@echo -e "$(CYAN)Starting Web Dashboard (Vite dev server)...$(RESET)"
	@if netstat -tlnp 2>/dev/null | grep -q ":5173.*LISTEN" || ss -tlnp 2>/dev/null | grep -q ":5173.*LISTEN"; then \
		echo -e "$(GREEN)✅ Web dashboard is already running!$(RESET)"; \
		echo -e "$(BLUE)🌐 Available at: http://localhost:5173$(RESET)"; \
	elif [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run dev; \
	else \
		echo -e "$(RED)❌ tauri-dashboard directory not found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make install-dashboard-deps' first$(RESET)"; \
	fi

dashboard-desktop: ## Start Tauri desktop app
	@echo -e "$(CYAN)Starting Tauri Desktop App...$(RESET)"
	@if ps aux | grep -E "(tauri|tauri dev)" | grep -v grep > /dev/null 2>&1; then \
		echo -e "$(GREEN)✅ Tauri desktop app is already running!$(RESET)"; \
		echo -e "$(BLUE)🖥️  Desktop app should be visible on your screen$(RESET)"; \
	elif [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run tauri dev; \
	else \
		echo -e "$(RED)❌ tauri-dashboard directory not found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make install-dashboard-deps' first$(RESET)"; \
	fi

dashboard-full: start dashboard-web ## Full development environment (API + Web dashboard)
	@echo -e "$(GREEN)✅ Full development environment started!$(RESET)"

dashboard-open: ## Open web dashboard in browser (if running)
	@if pgrep -f "vite.*tauri-dashboard" > /dev/null; then \
		echo -e "$(CYAN)Opening web dashboard in browser...$(RESET)"; \
		python -c "import webbrowser; webbrowser.open('http://localhost:5173')"; \
	else \
		echo -e "$(RED)❌ Web dashboard is not running$(RESET)"; \
		echo -e "$(YELLOW)Run 'make dashboard-web' first$(RESET)"; \
	fi

# ==============================================================================
# Development Workflow
# ==============================================================================

.PHONY: dev dev-fast dev-full dev-verify dev-ci

# Development workflow commands with clear hierarchy
dev: lint-check test ## Standard development workflow (lint + test)
	@echo -e "$(GREEN)✅ Standard development workflow completed!$(RESET)"

dev-fast: lint-fast test-unit ## Fast development cycle (quick lint + unit tests only)
	@echo -e "$(GREEN)✅ Fast development cycle completed!$(RESET)"

dev-full: lint test-coverage ## Full quality check (comprehensive lint + test with coverage)
	@echo -e "$(GREEN)✅ Full quality check completed!$(RESET)"

dev-verify: lint test cover-report ## Complete verification before PR submission
	@echo -e "$(GREEN)✅ Complete verification completed - ready for PR!$(RESET)"

dev-ci: clean-all lint-strict test-all cover-check ## Run full CI pipeline locally
	@echo -e "$(GREEN)✅ Local CI pipeline completed!$(RESET)"

# Legacy alias support (will be deprecated)
quick: dev-fast ## [DEPRECATED] Use 'dev-fast' instead

# ==============================================================================
# Development Tools
# ==============================================================================

.PHONY: shell console format profile commit-helper

shell: ## Start Python shell with project context
	@echo -e "$(CYAN)Starting Python shell...$(RESET)"
	@uv run python

console: ## Start IPython console with project loaded
	@echo -e "$(CYAN)Starting IPython console...$(RESET)"
	@command -v ipython >/dev/null 2>&1 || pip install ipython
	@uv run ipython

format: ## Format and organize code (imports + formatting)
	@echo -e "$(CYAN)Formatting code and organizing imports...$(RESET)"
	@command -v isort >/dev/null 2>&1 || pip install isort
	@isort . --profile black
	@echo -e "$(GREEN)✅ Code formatted and imports organized$(RESET)"

profile: ## Profile the application performance
	@echo -e "$(CYAN)Starting profiler...$(RESET)"
	@echo -e "$(YELLOW)Run: python -m cProfile -o profile.stats yesman.py$(RESET)"
	@echo -e "$(YELLOW)Then: python -m pstats profile.stats$(RESET)"

commit-helper: ## Run commit organization helper script
	@echo -e "$(CYAN)Running commit organization helper...$(RESET)"
	@if [ -f "scripts/commit_helper.sh" ]; then \
		chmod +x scripts/commit_helper.sh && ./scripts/commit_helper.sh; \
	else \
		echo -e "$(RED)❌ Commit helper script not found$(RESET)"; \
	fi

# ==============================================================================
# Information & Help
# ==============================================================================

.PHONY: dev-info env-status help

dev-info: ## Show complete development environment information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                         $(YELLOW)Development Information$(CYAN)                         ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)🚀 Quick Start Commands:$(RESET)"
	@echo -e "  • $(CYAN)start$(RESET)               Start API server"
	@echo -e "  • $(CYAN)stop$(RESET)                Stop all services"
	@echo -e "  • $(CYAN)restart$(RESET)             Restart services"
	@echo -e "  • $(CYAN)dev-status$(RESET)          Check development service status"
	@echo ""
	@echo -e "$(GREEN)🖥️  Dashboard Commands:$(RESET)"
	@echo -e "  • $(CYAN)dashboard$(RESET)           Smart dashboard launcher (auto-detect)"
	@echo -e "  • $(CYAN)dashboard-web$(RESET)       Web dashboard (Vite dev server)"
	@echo -e "  • $(CYAN)dashboard-desktop$(RESET)   Desktop dashboard (Tauri app)"
	@echo -e "  • $(CYAN)dashboard-full$(RESET)      Full development environment (API + Web)"
	@echo -e "  • $(CYAN)dashboard-open$(RESET)      Open web dashboard in browser"
	@echo ""
	@echo -e "$(GREEN)🛠️  Development Workflow:$(RESET)"
	@echo -e "  • $(CYAN)dev$(RESET)                 Standard development workflow (lint + test)"
	@echo -e "  • $(CYAN)dev-fast$(RESET)            Quick check (fast lint + unit tests)"
	@echo -e "  • $(CYAN)dev-full$(RESET)            Full quality check (comprehensive)"
	@echo -e "  • $(CYAN)dev-verify$(RESET)          Complete verification before PR"
	@echo -e "  • $(CYAN)dev-ci$(RESET)              Run full CI pipeline locally"
	@echo ""
	@echo -e "$(GREEN)🔧 Development Tools:$(RESET)"
	@echo -e "  • $(CYAN)shell$(RESET)               Python shell with project context"
	@echo -e "  • $(CYAN)console$(RESET)             IPython console"
	@echo -e "  • $(CYAN)format$(RESET)              Format code and organize imports"
	@echo -e "  • $(CYAN)debug-api$(RESET)           Debug API server with detailed logs"
	@echo -e "  • $(CYAN)logs$(RESET)                Show recent log files"
	@echo ""
	@echo -e "$(GREEN)📊 Current Status:$(RESET)"
	@echo -e "  Python:         $$(python --version 2>&1)"
	@echo -e "  Git branch:     $$(git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo -e "  Git status:     $$(git status --porcelain 2>/dev/null | wc -l | xargs echo) files changed"
	@echo -e "  Last commit:    $$(git log -1 --format='%h %s' 2>/dev/null || echo 'N/A')"
	@echo ""
	@echo -e "$(GREEN)🌐 Server Ports:$(RESET)"
	@echo -e "  API Server:     $(YELLOW)10501$(RESET)"
	@echo -e "  Dev Server:     $(YELLOW)5173$(RESET)"

env-status: ## Show current development environment status  
	@echo -e "$(CYAN)Development Environment Status$(RESET)"
	@echo -e "$(BLUE)================================$(RESET)"
	@echo ""
	@echo -e "$(GREEN)📊 Project Status:$(RESET)"
	@echo -n -e "  Git Status:         "; if git status --porcelain | grep -q .; then echo -e "$(YELLOW)Modified files$(RESET)"; else echo -e "$(GREEN)Clean$(RESET)"; fi
	@echo -n -e "  Current Branch:     "; git branch --show-current 2>/dev/null || echo -e "$(RED)Unknown$(RESET)"
	@echo -n -e "  Last Commit:        "; git log -1 --format="%h %s" 2>/dev/null | cut -c1-50 || echo -e "$(RED)No commits$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🔧 Development Status:$(RESET)"
	@echo -n -e "  Tests Passing:      "; if make test-unit > /dev/null 2>&1; then echo -e "$(GREEN)Yes$(RESET)"; else echo -e "$(RED)No$(RESET)"; fi
	@echo -n -e "  Coverage File:      "; if [ -f ".coverage" ]; then echo -e "$(GREEN)Yes$(RESET)"; else echo -e "$(YELLOW)No$(RESET)"; fi
	@echo -n -e "  Virtual Env:        "; if [ -n "$$VIRTUAL_ENV" ]; then echo -e "$(GREEN)Active$(RESET)"; else echo -e "$(YELLOW)None$(RESET)"; fi

help: dev-info ## Show this help message (alias for dev-info)