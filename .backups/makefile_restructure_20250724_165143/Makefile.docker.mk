# Makefile.docker.mk - Docker operations for yesman-claude
# Container building, running, and management

# ==============================================================================
# Docker Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# Docker settings
DOCKER_IMAGE_NAME ?= yesman-claude
DOCKER_TAG ?= $(VERSION)
DOCKER_REGISTRY ?= ghcr.io/yourusername
DOCKER_FULL_IMAGE = $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)
DOCKER_LATEST = $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME):latest

# Docker build args
DOCKER_BUILD_ARGS ?= \
	--build-arg PYTHON_VERSION=3.11 \
	--build-arg PROJECT_NAME=$(PROJECT_NAME)

# ==============================================================================
# Docker Build Targets
# ==============================================================================

.PHONY: docker-build docker-build-dev docker-build-prod docker-build-multi

docker-build: ## build Docker image for local development
	@echo -e "$(CYAN)Building Docker image: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)$(RESET)"
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) \
		-t $(DOCKER_IMAGE_NAME):latest \
		$(DOCKER_BUILD_ARGS) \
		-f Dockerfile \
		.
	@echo -e "$(GREEN)✅ Docker image built successfully$(RESET)"

docker-build-dev: ## build Docker image for development
	@echo -e "$(CYAN)Building development Docker image...$(RESET)"
	docker build -t $(DOCKER_IMAGE_NAME):dev \
		$(DOCKER_BUILD_ARGS) \
		--target development \
		-f Dockerfile.dev \
		.
	@echo -e "$(GREEN)✅ Development image built$(RESET)"

docker-build-prod: ## build Docker image for production
	@echo -e "$(CYAN)Building production Docker image...$(RESET)"
	docker build -t $(DOCKER_IMAGE_NAME):prod \
		$(DOCKER_BUILD_ARGS) \
		--target production \
		-f Dockerfile \
		.
	@echo -e "$(GREEN)✅ Production image built$(RESET)"

docker-build-multi: ## build multi-platform Docker image
	@echo -e "$(CYAN)Building multi-platform Docker image...$(RESET)"
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-t $(DOCKER_FULL_IMAGE) \
		$(DOCKER_BUILD_ARGS) \
		-f Dockerfile \
		.
	@echo -e "$(GREEN)✅ Multi-platform image built$(RESET)"

# ==============================================================================
# Docker Run Targets
# ==============================================================================

.PHONY: docker-run docker-run-interactive docker-run-detached docker-stop

docker-run: ## run Docker container
	@echo -e "$(CYAN)Running Docker container...$(RESET)"
	docker run --rm \
		--name $(DOCKER_IMAGE_NAME) \
		-p 8000:8000 \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)

docker-run-interactive: ## run Docker container in interactive mode
	@echo -e "$(CYAN)Running Docker container (interactive)...$(RESET)"
	docker run --rm -it \
		--name $(DOCKER_IMAGE_NAME)-interactive \
		-p 8000:8000 \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME):$(DOCKER_TAG) \
		/bin/bash

docker-run-detached: ## run Docker container in background
	@echo -e "$(CYAN)Running Docker container in background...$(RESET)"
	docker run -d \
		--name $(DOCKER_IMAGE_NAME)-detached \
		-p 8000:8000 \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)
	@echo -e "$(GREEN)✅ Container running in background$(RESET)"

docker-stop: ## stop running Docker containers
	@echo -e "$(CYAN)Stopping Docker containers...$(RESET)"
	@docker stop $(DOCKER_IMAGE_NAME) 2>/dev/null || true
	@docker stop $(DOCKER_IMAGE_NAME)-interactive 2>/dev/null || true
	@docker stop $(DOCKER_IMAGE_NAME)-detached 2>/dev/null || true
	@echo -e "$(GREEN)✅ Containers stopped$(RESET)"

# ==============================================================================
# Docker Compose Targets
# ==============================================================================

.PHONY: compose-up compose-down compose-restart compose-logs compose-ps

compose-up: ## start services with docker-compose
	@echo -e "$(CYAN)Starting services with docker-compose...$(RESET)"
	docker-compose up -d
	@echo -e "$(GREEN)✅ Services started$(RESET)"

compose-down: ## stop services with docker-compose
	@echo -e "$(CYAN)Stopping services with docker-compose...$(RESET)"
	docker-compose down
	@echo -e "$(GREEN)✅ Services stopped$(RESET)"

compose-restart: compose-down compose-up ## restart docker-compose services
	@echo -e "$(GREEN)✅ Services restarted$(RESET)"

compose-logs: ## show docker-compose logs
	@echo -e "$(CYAN)Showing docker-compose logs...$(RESET)"
	docker-compose logs -f

compose-ps: ## show docker-compose status
	@echo -e "$(CYAN)Docker-compose services status:$(RESET)"
	docker-compose ps

# ==============================================================================
# Docker Management
# ==============================================================================

.PHONY: docker-clean docker-prune docker-logs docker-shell docker-exec

docker-clean: ## clean up Docker containers and images
	@echo -e "$(CYAN)Cleaning up Docker resources...$(RESET)"
	@docker stop $(shell docker ps -q --filter name=$(DOCKER_IMAGE_NAME)) 2>/dev/null || true
	@docker rm $(shell docker ps -aq --filter name=$(DOCKER_IMAGE_NAME)) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE_NAME):latest 2>/dev/null || true
	@echo -e "$(GREEN)✅ Docker cleanup completed$(RESET)"

docker-prune: ## prune unused Docker resources
	@echo -e "$(CYAN)Pruning unused Docker resources...$(RESET)"
	docker system prune -f
	@echo -e "$(GREEN)✅ Docker prune completed$(RESET)"

docker-logs: ## show container logs
	@echo -e "$(CYAN)Showing container logs...$(RESET)"
	@container=$$(docker ps -q --filter name=$(DOCKER_IMAGE_NAME) | head -1); \
	if [ -n "$$container" ]; then \
		docker logs -f $$container; \
	else \
		echo "$(YELLOW)No running container found$(RESET)"; \
	fi

docker-shell: ## open shell in running container
	@echo -e "$(CYAN)Opening shell in container...$(RESET)"
	@container=$$(docker ps -q --filter name=$(DOCKER_IMAGE_NAME) | head -1); \
	if [ -n "$$container" ]; then \
		docker exec -it $$container /bin/bash; \
	else \
		echo "$(YELLOW)No running container found$(RESET)"; \
	fi

docker-exec: ## execute command in container (CMD="command")
	@if [ -z "$(CMD)" ]; then \
		echo "$(RED)Usage: make docker-exec CMD=\"your command\"$(RESET)"; \
		exit 1; \
	fi
	@container=$$(docker ps -q --filter name=$(DOCKER_IMAGE_NAME) | head -1); \
	if [ -n "$$container" ]; then \
		docker exec $$container $(CMD); \
	else \
		echo "$(YELLOW)No running container found$(RESET)"; \
	fi

# ==============================================================================
# Docker Registry
# ==============================================================================

.PHONY: docker-push docker-pull docker-tag docker-login

docker-push: ## push Docker image to registry
	@echo -e "$(CYAN)Pushing Docker image to registry...$(RESET)"
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_FULL_IMAGE)
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_LATEST)
	docker push $(DOCKER_FULL_IMAGE)
	docker push $(DOCKER_LATEST)
	@echo -e "$(GREEN)✅ Docker image pushed$(RESET)"

docker-pull: ## pull Docker image from registry
	@echo -e "$(CYAN)Pulling Docker image from registry...$(RESET)"
	docker pull $(DOCKER_FULL_IMAGE)
	@echo -e "$(GREEN)✅ Docker image pulled$(RESET)"

docker-tag: ## tag Docker image
	@echo -e "$(CYAN)Tagging Docker image...$(RESET)"
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_FULL_IMAGE)
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_LATEST)
	@echo -e "$(GREEN)✅ Docker image tagged$(RESET)"

docker-login: ## login to Docker registry
	@echo -e "$(CYAN)Logging in to Docker registry...$(RESET)"
	@echo -e "$(YELLOW)Please provide your registry credentials$(RESET)"
	docker login $(DOCKER_REGISTRY)

# ==============================================================================
# Docker Analysis
# ==============================================================================

.PHONY: docker-scan docker-optimize docker-inspect docker-size

docker-scan: ## scan Docker image for vulnerabilities
	@echo -e "$(CYAN)Scanning Docker image for vulnerabilities...$(RESET)"
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image $(DOCKER_IMAGE_NAME):$(DOCKER_TAG); \
	else \
		docker scan $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || \
		echo "$(YELLOW)Install trivy or enable docker scan for vulnerability scanning$(RESET)"; \
	fi

docker-optimize: ## analyze Docker image for optimization
	@echo -e "$(CYAN)Analyzing Docker image for optimization...$(RESET)"
	@if command -v dive >/dev/null 2>&1; then \
		dive $(DOCKER_IMAGE_NAME):$(DOCKER_TAG); \
	else \
		echo "$(YELLOW)Install 'dive' tool for image analysis: https://github.com/wagoodman/dive$(RESET)"; \
		docker history $(DOCKER_IMAGE_NAME):$(DOCKER_TAG); \
	fi

docker-inspect: ## inspect Docker image
	@echo -e "$(CYAN)Inspecting Docker image...$(RESET)"
	docker inspect $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) | jq '.[0] | {Id, RepoTags, Size, Architecture, Os, Created}'

docker-size: ## show Docker image sizes
	@echo -e "$(CYAN)Docker Image Sizes:$(RESET)"
	@docker images --filter "reference=$(DOCKER_IMAGE_NAME)" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.Created}}"

# ==============================================================================
# Dockerfile Generation
# ==============================================================================

.PHONY: dockerfile-generate dockerfile-check

dockerfile-generate: ## generate Dockerfile if not exists
	@if [ ! -f Dockerfile ]; then \
		echo "$(CYAN)Generating Dockerfile...$(RESET)"; \
		echo "# Dockerfile for $(PROJECT_NAME)" > Dockerfile; \
		echo "FROM python:3.11-slim" >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "WORKDIR /app" >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "# Install system dependencies" >> Dockerfile; \
		echo "RUN apt-get update && apt-get install -y \\\\" >> Dockerfile; \
		echo "    git \\\\" >> Dockerfile; \
		echo "    && rm -rf /var/lib/apt/lists/*" >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "# Copy requirements first for better caching" >> Dockerfile; \
		echo "COPY pyproject.toml README.md ./" >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "# Install Python dependencies" >> Dockerfile; \
		echo "RUN pip install --no-cache-dir -e ." >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "# Copy application code" >> Dockerfile; \
		echo "COPY . ." >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "# Expose port" >> Dockerfile; \
		echo "EXPOSE 8000" >> Dockerfile; \
		echo "" >> Dockerfile; \
		echo "# Run the application" >> Dockerfile; \
		echo "CMD [\"python\", \"yesman.py\"]" >> Dockerfile; \
		echo "$(GREEN)✅ Dockerfile generated$(RESET)"; \
	else \
		echo "$(YELLOW)Dockerfile already exists$(RESET)"; \
	fi

dockerfile-check: ## check Dockerfile best practices
	@echo -e "$(CYAN)Checking Dockerfile...$(RESET)"
	@if command -v hadolint >/dev/null 2>&1; then \
		hadolint Dockerfile; \
	else \
		echo "$(YELLOW)Install hadolint for Dockerfile linting: https://github.com/hadolint/hadolint$(RESET)"; \
	fi

# ==============================================================================
# Docker Information
# ==============================================================================

.PHONY: docker-info docker-status

docker-info: ## show Docker information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Docker Information$(CYAN)                              ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo -e "$(GREEN)🐳 Docker Configuration:$(RESET)"
	@echo "  Image Name:     $(YELLOW)$(DOCKER_IMAGE_NAME)$(RESET)"
	@echo "  Tag:            $(YELLOW)$(DOCKER_TAG)$(RESET)"
	@echo "  Registry:       $(YELLOW)$(DOCKER_REGISTRY)$(RESET)"
	@echo "  Full Image:     $(YELLOW)$(DOCKER_FULL_IMAGE)$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🏗️  Build Commands:$(RESET)"
	@echo "  • $(CYAN)docker-build$(RESET)        Build local image"
	@echo "  • $(CYAN)docker-build-dev$(RESET)    Build development image"
	@echo "  • $(CYAN)docker-build-prod$(RESET)   Build production image"
	@echo "  • $(CYAN)docker-build-multi$(RESET)  Build multi-platform"
	@echo ""
	@echo -e "$(GREEN)🚀 Run Commands:$(RESET)"
	@echo "  • $(CYAN)docker-run$(RESET)          Run container"
	@echo "  • $(CYAN)docker-run-interactive$(RESET) Run interactive"
	@echo "  • $(CYAN)docker-run-detached$(RESET) Run in background"
	@echo "  • $(CYAN)docker-stop$(RESET)         Stop containers"
	@echo ""
	@echo -e "$(GREEN)📦 Management:$(RESET)"
	@echo "  • $(CYAN)docker-push$(RESET)         Push to registry"
	@echo "  • $(CYAN)docker-scan$(RESET)         Security scan"
	@echo "  • $(CYAN)docker-clean$(RESET)        Clean resources"

docker-status: ## show Docker container status
	@echo -e "$(CYAN)Docker Status$(RESET)"
	@echo -e "$(BLUE)==============$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)Running Containers:$(RESET)"
	@docker ps --filter name=$(DOCKER_IMAGE_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "  None"
	@echo ""
	@echo -e "$(YELLOW)Images:$(RESET)"
	@docker images --filter reference=$(DOCKER_IMAGE_NAME) --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.Created}}" || echo "  None"
	@echo ""
	@echo -e "$(YELLOW)Docker Version:$(RESET)"
	@docker version --format "  Client: {{.Client.Version}}\n  Server: {{.Server.Version}}"