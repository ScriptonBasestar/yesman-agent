# Makefile.dev.mk - Development Workflow for yesman-claude
# Development environment, workflow automation, and quick iteration

# ==============================================================================
# Development Configuration
# ==============================================================================

# Colors are exported from main Makefile

# PID file management
PID_DIR := tmp
API_PID_FILE := $(PID_DIR)/api.pid
WEB_PID_FILE := $(PID_DIR)/web.pid
TAURI_PID_FILE := $(PID_DIR)/tauri.pid

# ==============================================================================
# Quick Start Commands
# ==============================================================================

.PHONY: dev dev-api dev-web dev-tauri stop stop-api stop-web stop-tauri status logs debug-api

# Core development commands - most frequently used commands
dev-api: ## Start API server in background
	@echo -e "$(CYAN)Starting API Server...$(RESET)"
	@mkdir -p $(PID_DIR)
	@if [ -f "$(API_PID_FILE)" ] && kill -0 `cat $(API_PID_FILE)` 2>/dev/null; then \
		echo -e "$(YELLOW)⚠️  API server already running (PID: `cat $(API_PID_FILE)`)$(RESET)"; \
	else \
		rm -f $(API_PID_FILE); \
		nohup uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 & \
		echo $$! > $(API_PID_FILE); \
		echo -e "$(GREEN)✅ API server started in background (PID: `cat $(API_PID_FILE)`)$(RESET)"; \
		echo -e "$(BLUE)🌐 API available at: http://localhost:10501$(RESET)"; \
	fi

dev-web: ## Start web dashboard (Vite dev server)
	@echo -e "$(CYAN)Starting Web Dashboard...$(RESET)"
	@mkdir -p $(PID_DIR)
	@if [ -f "$(WEB_PID_FILE)" ] && kill -0 `cat $(WEB_PID_FILE)` 2>/dev/null; then \
		echo -e "$(YELLOW)⚠️  Web server already running (PID: `cat $(WEB_PID_FILE)`)$(RESET)"; \
	elif [ -d "tauri-dashboard" ]; then \
		rm -f $(WEB_PID_FILE); \
		cd tauri-dashboard && nohup npm run dev > ../web.log 2>&1 & \
		echo $$! > ../$(WEB_PID_FILE); \
		echo -e "$(GREEN)✅ Web server started in background (PID: `cat $(WEB_PID_FILE)`)$(RESET)"; \
		echo -e "$(BLUE)🌐 Web available at: http://localhost:5173$(RESET)"; \
	else \
		echo -e "$(RED)❌ tauri-dashboard directory not found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make install-dashboard-deps' first$(RESET)"; \
	fi

dev-tauri: ## Start Tauri desktop app
	@echo -e "$(CYAN)Starting Tauri Desktop App...$(RESET)"
	@mkdir -p $(PID_DIR)
	@if [ -f "$(TAURI_PID_FILE)" ] && kill -0 `cat $(TAURI_PID_FILE)` 2>/dev/null; then \
		echo -e "$(YELLOW)⚠️  Tauri app already running (PID: `cat $(TAURI_PID_FILE)`)$(RESET)"; \
	elif [ -d "tauri-dashboard" ]; then \
		rm -f $(TAURI_PID_FILE); \
		cd tauri-dashboard && nohup npm run tauri dev > ../tauri.log 2>&1 & \
		echo $$! > ../$(TAURI_PID_FILE); \
		echo -e "$(GREEN)✅ Tauri app started in background (PID: `cat $(TAURI_PID_FILE)`)$(RESET)"; \
		echo -e "$(BLUE)🖥️  Desktop app should be visible on your screen$(RESET)"; \
	else \
		echo -e "$(RED)❌ tauri-dashboard directory not found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make install-dashboard-deps' first$(RESET)"; \
	fi

dev: dev-api dev-web ## Start API and Web servers together
	@echo -e "$(GREEN)✅ Development environment started!$(RESET)"

stop: stop-api stop-web stop-tauri ## Stop all running servers and processes
	@echo -e "$(GREEN)✅ All servers stopped$(RESET)"

stop-api: ## Stop API server only
	@echo -e "$(YELLOW)Stopping API server...$(RESET)"
	@if [ -f "$(API_PID_FILE)" ]; then \
		if kill -0 `cat $(API_PID_FILE)` 2>/dev/null; then \
			kill `cat $(API_PID_FILE)` && echo -e "$(GREEN)✅ API server stopped (PID: `cat $(API_PID_FILE)`)$(RESET)"; \
		else \
			echo -e "$(BLUE)API server not running (stale PID file)$(RESET)"; \
		fi; \
		rm -f $(API_PID_FILE); \
	else \
		pkill -f "uvicorn.*api.main:app" || echo -e "$(BLUE)No API server running$(RESET)"; \
	fi

stop-web: ## Stop web server only
	@echo -e "$(YELLOW)Stopping web server...$(RESET)"
	@if [ -f "$(WEB_PID_FILE)" ]; then \
		if kill -0 `cat $(WEB_PID_FILE)` 2>/dev/null; then \
			kill `cat $(WEB_PID_FILE)` && echo -e "$(GREEN)✅ Web server stopped (PID: `cat $(WEB_PID_FILE)`)$(RESET)"; \
		else \
			echo -e "$(BLUE)Web server not running (stale PID file)$(RESET)"; \
		fi; \
		rm -f $(WEB_PID_FILE); \
	else \
		pkill -f "vite.*tauri-dashboard" || echo -e "$(BLUE)No web server running$(RESET)"; \
	fi

stop-tauri: ## Stop Tauri app only
	@echo -e "$(YELLOW)Stopping Tauri app...$(RESET)"
	@if [ -f "$(TAURI_PID_FILE)" ]; then \
		if kill -0 `cat $(TAURI_PID_FILE)` 2>/dev/null; then \
			kill `cat $(TAURI_PID_FILE)` && echo -e "$(GREEN)✅ Tauri app stopped (PID: `cat $(TAURI_PID_FILE)`)$(RESET)"; \
		else \
			echo -e "$(BLUE)Tauri app not running (stale PID file)$(RESET)"; \
		fi; \
		rm -f $(TAURI_PID_FILE); \
	else \
		pkill -f "tauri dev" || echo -e "$(BLUE)No Tauri app running$(RESET)"; \
	fi

status: ## Check status of development services (API, Web, Tauri)
	@echo -e "$(CYAN)Development Service Status:$(RESET)"
	@echo ""
	@echo -n -e "  API Server:         "; \
	if [ -f "$(API_PID_FILE)" ] && kill -0 `cat $(API_PID_FILE)` 2>/dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET) (PID: `cat $(API_PID_FILE)`, port 10501)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
	@echo -n -e "  Web Server:         "; \
	if [ -f "$(WEB_PID_FILE)" ] && kill -0 `cat $(WEB_PID_FILE)` 2>/dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET) (PID: `cat $(WEB_PID_FILE)`, port 5173)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
	@echo -n -e "  Tauri App:          "; \
	if [ -f "$(TAURI_PID_FILE)" ] && kill -0 `cat $(TAURI_PID_FILE)` 2>/dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET) (PID: `cat $(TAURI_PID_FILE)`)"; \
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

# format command moved to Makefile.quality.mk to avoid duplication

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
	@echo -e "$(GREEN)🚀 Development Commands:$(RESET)"
	@echo -e "  • $(CYAN)dev$(RESET)                 Start API + Web servers"
	@echo -e "  • $(CYAN)dev-api$(RESET)             Start API server only"
	@echo -e "  • $(CYAN)dev-web$(RESET)             Start web server only"
	@echo -e "  • $(CYAN)dev-tauri$(RESET)           Start Tauri desktop app"
	@echo -e "  • $(CYAN)stop$(RESET)                Stop all servers"
	@echo -e "  • $(CYAN)stop-api$(RESET)            Stop API server only"
	@echo -e "  • $(CYAN)stop-web$(RESET)            Stop web server only"
	@echo -e "  • $(CYAN)stop-tauri$(RESET)          Stop Tauri app only"
	@echo -e "  • $(CYAN)status$(RESET)              Check server status"
	@echo ""
	@echo -e "$(GREEN)🔧 Development Tools:$(RESET)"
	@echo -e "  • $(CYAN)shell$(RESET)               Python shell with project context"
	@echo -e "  • $(CYAN)console$(RESET)             IPython console"
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
	@echo -e "  Web Server:     $(YELLOW)5173$(RESET)"

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