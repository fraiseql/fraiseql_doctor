# FraiseQL Doctor - Monorepo Makefile
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Colors for terminal output
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
RESET := \033[0m

##@ Setup Commands
.PHONY: setup
setup: setup-backend setup-frontend  ## Setup both backend and frontend dependencies
	@echo "$(GREEN)✅ Full project setup complete!$(RESET)"

.PHONY: setup-backend
setup-backend:  ## Setup Python backend dependencies
	@echo "$(BLUE)🔧 Setting up Python backend...$(RESET)"
	cd backend && uv sync

.PHONY: setup-frontend  
setup-frontend:  ## Setup Vue.js frontend dependencies
	@echo "$(BLUE)🔧 Setting up Vue.js frontend...$(RESET)"
	cd frontend && npm install

##@ Development Commands
.PHONY: dev
dev:  ## Start both backend and frontend in development mode
	@echo "$(GREEN)🚀 Starting development servers...$(RESET)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Frontend: http://localhost:5173$(RESET)"
	# Run both services concurrently (requires 'concurrently' package)
	npx concurrently -n "backend,frontend" -c "blue,green" \
		"cd backend && uv run uvicorn src.fraiseql_doctor.main:app --reload --port 8000" \
		"cd frontend && npm run dev"

.PHONY: dev-backend
dev-backend:  ## Start only backend development server
	@echo "$(GREEN)🚀 Starting backend server at http://localhost:8000$(RESET)"
	cd backend && uv run uvicorn src.fraiseql_doctor.main:app --reload --port 8000

.PHONY: dev-frontend
dev-frontend:  ## Start only frontend development server
	@echo "$(GREEN)🚀 Starting frontend server at http://localhost:5173$(RESET)"
	cd frontend && npm run dev

##@ Testing Commands  
.PHONY: test
test: test-backend test-frontend  ## Run all tests (backend + frontend)

.PHONY: test-backend
test-backend:  ## Run backend tests
	@echo "$(BLUE)🧪 Running backend tests...$(RESET)"
	cd backend && make test

.PHONY: test-frontend
test-frontend:  ## Run frontend tests
	@echo "$(BLUE)🧪 Running frontend tests...$(RESET)"
	cd frontend && npm test

##@ Code Quality
.PHONY: lint
lint: lint-backend lint-frontend  ## Run linting on both backend and frontend

.PHONY: lint-backend
lint-backend:  ## Run backend linting (ruff + mypy)
	@echo "$(BLUE)🔍 Linting backend code...$(RESET)"
	cd backend && make lint

.PHONY: lint-frontend  
lint-frontend:  ## Run frontend linting (ESLint + TypeScript)
	@echo "$(BLUE)🔍 Linting frontend code...$(RESET)"
	cd frontend && npm run lint
	cd frontend && npm run type-check

.PHONY: format
format: format-backend format-frontend  ## Format code in both projects

.PHONY: format-backend
format-backend:  ## Format backend code with ruff
	@echo "$(BLUE)✨ Formatting backend code...$(RESET)"
	cd backend && make format

.PHONY: format-frontend
format-frontend:  ## Format frontend code with prettier
	@echo "$(BLUE)✨ Formatting frontend code...$(RESET)"
	cd frontend && npm run format

##@ Build Commands
.PHONY: build
build: build-backend build-frontend  ## Build both backend and frontend for production

.PHONY: build-backend  
build-backend:  ## Build backend Python package
	@echo "$(BLUE)📦 Building backend package...$(RESET)"
	cd backend && make build

.PHONY: build-frontend
build-frontend:  ## Build frontend Vue.js application
	@echo "$(BLUE)📦 Building frontend application...$(RESET)"
	cd frontend && npm run build

##@ Help
.PHONY: help
help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(GREEN)FraiseQL Doctor - Monorepo Commands$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""