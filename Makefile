# Makefile for Multi-Agent System (Local Development - No Docker)
# Services: SocketIO Server, React Frontend, Redis (Docker minimal)

.PHONY: help install setup dev up down restart logs clean clean-all status health
.PHONY: up-redis up-socketio up-auth up-react down-redis down-socketio down-auth down-react
.PHONY: logs-socketio logs-auth logs-redis logs-react restart-socketio restart-auth restart-react
.PHONY: test test-coverage lint format format-check build docker-build docker-clean docker-up docker-down
.PHONY: dev-setup dev-check quick-start quick-stop help-detailed open-socketio open-auth open-react
.PHONY: install-react setup-react dev-react build-react

# Process management
SOCKETIO_PID_FILE := .socketio.pid
AUTH_PID_FILE := .auth.pid
REACT_PID_FILE := .react.pid

# Python executable detection
PYTHON := $(shell command -v python3.10 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3.12 2>/dev/null || echo python3)

# Default target
help: ## Show available commands
	@echo "🚀 Multi-Agent System Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Check dependencies
check-deps: ## Check if Python and required tools are installed
	@echo "🔍 Checking dependencies..."
	@echo "🐍 Detected Python: $(PYTHON)"
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "❌ Python not found"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }
	@command -v streamlit >/dev/null 2>&1 || { echo "⚠️  Streamlit not installed (will be installed with dependencies)"; }
	@echo "✅ Python: $$($(PYTHON) --version)"
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" || { echo "❌ Python 3.10+ required (current: $$($(PYTHON) --version))"; echo "� Try: python3.10 --version or see PYTHON_UPGRADE_GUIDE.md"; exit 1; }
	@echo "✅ Docker: $$(docker --version)"
	@if command -v streamlit >/dev/null 2>&1; then echo "✅ Streamlit: $$(streamlit --version)"; fi

# Install dependencies
install: check-deps ## Install Python dependencies
	@echo "📦 Installing dependencies..."
	@$(PYTHON) -m pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Setup environment
setup: ## Setup environment (create directories, check .env)
	@echo "🔧 Setting up environment..."
	@mkdir -p logs
	@touch logs/socketio.log logs/auth.log logs/react.log
	@if [ ! -f ".env" ]; then \
	    echo "⚠️  .env not found, copying from template..."; \
	    if [ -f ".env.example" ]; then \
	        cp .env.example .env; \
	    else \
	        echo "❌ No .env template found. Please create .env manually"; \
	        exit 1; \
	    fi; \
	    echo "❗ Please edit .env with your API keys"; \
	fi
	@echo "✅ Environment setup completed"

# Development mode (recommended)
dev: dev-react ## Quick development start with React

# Start all services with React (recommended)
up: up-redis up-socketio up-auth up-react ## Start all services with React
	@echo "✅ All services started!"
	@make status

# Start Redis (minimal Docker)
up-redis: ## Start Redis container only
	@echo "🔄 Starting Redis..."
	@./deployment/scripts/start_databases.sh

# Start SocketIO server
up-socketio: ## Start SocketIO server (Python)
	@echo "🔌 Starting SocketIO server..."
	@if [ -f $(SOCKETIO_PID_FILE) ]; then \
	    echo "⚠️  SocketIO already running (PID: $$(cat $(SOCKETIO_PID_FILE)))"; \
	else \
	    echo "$$(date '+%Y-%m-%d %H:%M:%S') - Starting SocketIO server..." >> logs/socketio.log; \
	    $(PYTHON) socketio_server.py >> logs/socketio.log 2>&1 & echo $$! > $(SOCKETIO_PID_FILE); \
	    echo "✅ SocketIO started on port 8001 (PID: $$(cat $(SOCKETIO_PID_FILE)))"; \
	    echo "📋 Logs: tail -f logs/socketio.log"; \
	fi

# Start Authentication API server
up-auth: ## Start Authentication API server
	@echo "🔐 Starting Authentication API server..."
	@if [ -f $(AUTH_PID_FILE) ] && [ -s $(AUTH_PID_FILE) ] && ps -p $$(cat $(AUTH_PID_FILE)) > /dev/null 2>&1; then \
	    echo "⚠️  Auth API already running (PID: $$(cat $(AUTH_PID_FILE)))"; \
	else \
	    echo "$$(date '+%Y-%m-%d %H:%M:%S') - Starting Auth API server..." >> logs/auth.log; \
	    python3 auth_server.py >> logs/auth.log 2>&1 & echo $$! > $(AUTH_PID_FILE); \
	    echo "✅ Auth API started on port 8000 (PID: $$(cat $(AUTH_PID_FILE)))"; \
	    echo "📋 Logs: tail -f logs/auth.log"; \
	fi

# Legacy GUI commands removed - migrated to React frontend

# React Frontend Commands
install-react: ## Install React frontend dependencies
	@echo "📦 Installing React frontend dependencies..."
	@cd frontend && npm install
	@echo "✅ React dependencies installed"

setup-react: install-react ## Setup React frontend environment
	@echo "🔧 Setting up React frontend..."
	@cd frontend && [ -f .env ] || cp .env.example .env
	@echo "✅ React frontend setup completed"

# Start React development server
up-react: ## Start React development server
	@echo "⚛️  Starting React development server..."
	@if [ -f $(REACT_PID_FILE) ] && [ -s $(REACT_PID_FILE) ] && ps -p $$(cat $(REACT_PID_FILE)) > /dev/null 2>&1; then \
	    echo "⚠️  React already running (PID: $$(cat $(REACT_PID_FILE)))"; \
	else \
	    echo "$$(date '+%Y-%m-%d %H:%M:%S') - Starting React dev server..." >> logs/react.log; \
	    cd frontend && npm run dev >> ../logs/react.log 2>&1 & \
	    REACT_PID=$$!; \
	    echo $$REACT_PID > ../$(REACT_PID_FILE); \
	    echo "✅ React started on port 3000 (PID: $$REACT_PID)"; \
	    echo "📋 Logs: tail -f logs/react.log"; \
	    echo "🌐 Access: http://localhost:3000"; \
	fi

# Build React for production
build-react: ## Build React frontend for production
	@echo "🏗️  Building React frontend for production..."
	@cd frontend && npm run build
	@echo "✅ React build completed"

# Development mode with React
dev-react: install setup-react up-redis up-socketio up-react ## Quick development start with React
	@echo "🎉 React development environment ready!"
	@echo "Services:"
	@echo "  - React Frontend: http://localhost:3000"
	@echo "  - SocketIO: http://localhost:8001"

# Stop all services
down: down-react down-auth down-socketio down-redis ## Stop all services
	@echo "✅ All services stopped!"

# Stop Redis
down-redis: ## Stop Redis container
	@echo "🛑 Stopping Redis..."
	@./deployment/scripts/stop_databases.sh

# Stop SocketIO server
down-socketio: ## Stop SocketIO server
	@echo "🛑 Stopping SocketIO server..."
	@if [ -f $(SOCKETIO_PID_FILE) ]; then \
	    kill $$(cat $(SOCKETIO_PID_FILE)) 2>/dev/null || true; \
	    rm -f $(SOCKETIO_PID_FILE); \
	    echo "✅ SocketIO stopped"; \
	else \
	    echo "⚠️  SocketIO not running"; \
	fi

# Stop Authentication API server
down-auth: ## Stop Authentication API server
	@echo "🛑 Stopping Auth API server..."
	@if [ -f $(AUTH_PID_FILE) ]; then \
	    kill $$(cat $(AUTH_PID_FILE)) 2>/dev/null || true; \
	    rm -f $(AUTH_PID_FILE); \
	    echo "✅ Auth API stopped"; \
	else \
	    echo "⚠️  Auth API not running"; \
	fi

# Legacy GUI stop command removed

# Stop React
down-react: ## Stop React development server
	@echo "🛑 Stopping React development server..."
	@if [ -f $(REACT_PID_FILE) ]; then \
	    kill $$(cat $(REACT_PID_FILE)) 2>/dev/null || true; \
	    rm -f $(REACT_PID_FILE); \
	    echo "✅ React stopped"; \
	else \
	    echo "⚠️  React not running"; \
	fi

# Restart services
restart: down up ## Restart all services (legacy)

restart-react: down-react up-react ## Restart React development server

restart-socketio: down-socketio up-socketio ## Restart SocketIO server

restart-auth: down-auth up-auth ## Restart Authentication API server

# Legacy GUI restart command removed

# Show logs
logs: ## Show all logs (follow mode)
	@echo "📋 Showing all logs (Ctrl+C to exit)..."
	@echo "📁 Log files: logs/socketio.log logs/auth.log logs/react.log"
	@tail -f logs/socketio.log logs/auth.log logs/react.log 2>/dev/null || echo "⚠️  Some log files may not exist"

logs-react: ## Show React logs
	@echo "📋 React development server logs:"
	@tail -f logs/react.log 2>/dev/null || echo "⚠️  React log not found"

logs-socketio: ## Show SocketIO logs
	@echo "📋 SocketIO logs:"
	@tail -f logs/socketio.log 2>/dev/null || echo "⚠️  SocketIO log not found"

logs-auth: ## Show Authentication API logs
	@echo "📋 Auth API logs:"
	@tail -f logs/auth.log 2>/dev/null || echo "⚠️  Auth API log not found"

# Legacy GUI logs command removed

logs-redis: ## Show Redis logs
	@echo "📋 Redis logs:"
	@cd deployment && docker-compose logs -f redis

# Service status
status: ## Show service status
	@echo "📊 Service Status:"
	@echo "=================="
	@if [ -f $(SOCKETIO_PID_FILE) ]; then \
	    if ps -p $$(cat $(SOCKETIO_PID_FILE)) > /dev/null 2>&1; then \
	        echo "✅ SocketIO: Running (PID: $$(cat $(SOCKETIO_PID_FILE))) - http://localhost:8001"; \
	    else \
	        echo "❌ SocketIO: Dead process"; rm -f $(SOCKETIO_PID_FILE); \
	    fi \
	else \
	    echo "⭕ SocketIO: Not running"; \
	fi
	@if [ -f $(AUTH_PID_FILE) ]; then \
	    if ps -p $$(cat $(AUTH_PID_FILE)) > /dev/null 2>&1; then \
	        echo "✅ Auth API: Running (PID: $$(cat $(AUTH_PID_FILE))) - http://localhost:8000"; \
	    else \
	        echo "❌ Auth API: Dead process"; rm -f $(AUTH_PID_FILE); \
	    fi \
	else \
	    echo "⭕ Auth API: Not running"; \
	fi
	# Legacy GUI status check removed
	@if [ -f $(REACT_PID_FILE) ]; then \
	    if ps -p $$(cat $(REACT_PID_FILE)) > /dev/null 2>&1; then \
	        echo "✅ React Frontend: Running (PID: $$(cat $(REACT_PID_FILE))) - http://localhost:3000"; \
	    else \
	        echo "❌ React: Dead process"; rm -f $(REACT_PID_FILE); \
	    fi \
	else \
	    echo "⭕ React Frontend: Not running"; \
	fi
	@echo -n "🔄 Redis: "
	@cd deployment && docker-compose ps redis --format "table" | grep -q "Up" && echo "✅ Running" || echo "❌ Not running"

# Health check
health: ## Check service health
	@echo "🏥 Health Check:"
	@echo "=================="
	@echo -n "SocketIO (http://localhost:8001/health): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null | grep -q "200" && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo -n "GUI (http://localhost:8501/_stcore/health): "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health 2>/dev/null | grep -q "200" && echo "✅ Healthy" || echo "❌ Unhealthy"

# Clean up
clean: down ## Stop services and clean up
	@echo "🧹 Cleaning up..."
	@rm -f logs/*.log .*.pid
	@echo "✅ Cleanup completed"

clean-all: down ## Deep cleanup (logs, cache, temp files)
	@echo "🧹 Deep cleaning..."
	@rm -f logs/*.log .*.pid
	@chmod +x cleanup.sh
	@./cleanup.sh
	@echo "✅ Deep cleanup completed"

# Force kill all processes
kill-all: ## Force kill all processes
	@echo "💀 Force killing processes..."
	@pkill -f "socketio_server.py" 2>/dev/null || echo "No SocketIO processes"
	@pkill -f "streamlit run gui/main.py" 2>/dev/null || echo "No GUI processes"
	@rm -f .*.pid
	@echo "✅ All processes killed"

# Testing
test: ## Run all tests
	@echo "🧪 Running tests..."
	@$(PYTHON) -m pytest tests/ -v --tb=short
	@echo "✅ Tests completed"

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/"

# Code Quality
lint: ## Run code linting
	@echo "🔍 Running linting..."
	@echo "📝 Checking with flake8..."
	@flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "🔍 Checking with mypy..."
	@mypy src/ --ignore-missing-imports
	@echo "✅ Linting completed"

format: ## Format code with black
	@echo "🎨 Formatting code..."
	@black src/ tests/ gui/ --line-length=88
	@echo "✅ Code formatted"

format-check: ## Check if code is properly formatted
	@echo "🎨 Checking code format..."
	@black src/ tests/ gui/ --check --line-length=88
	@echo "✅ Code format check completed"

# Docker Management
docker-build: ## Build Docker images
	@echo "🐳 Building Docker images..."
	@cd deployment && docker-compose build --no-cache
	@echo "✅ Docker images built"

docker-up: ## Start services with Docker
	@echo "🐳 Starting services with Docker..."
	@if [ ! -f ".env" ]; then \
	    echo "❌ .env file not found. Run 'make setup' first"; \
	    exit 1; \
	fi
	@cd deployment && docker-compose up -d redis socketio-server streamlit-gui
	@echo "⏳ Waiting for services..."
	@sleep 10
	@make docker-status
	@echo "✅ Docker services started"

docker-down: ## Stop Docker services
	@echo "🐳 Stopping Docker services..."
	@cd deployment && docker-compose down
	@echo "✅ Docker services stopped"

docker-logs: ## Show Docker logs
	@echo "📋 Docker logs:"
	@cd deployment && docker-compose logs -f

docker-status: ## Show Docker service status
	@echo "📊 Docker Service Status:"
	@cd deployment && docker-compose ps

docker-clean: ## Clean up Docker containers and images
	@echo "🧹 Cleaning Docker resources..."
	@cd deployment && docker-compose down --volumes --remove-orphans
	@docker system prune -f
	@echo "✅ Docker cleanup completed"

# Build targets
build: format lint test ## Run full build pipeline (format, lint, test)
	@echo "🏗️  Build pipeline completed successfully!"

# Development workflow
dev-setup: install setup ## Complete development setup
	@echo "🎉 Development environment ready!"

dev-check: format-check lint test ## Check code quality without making changes
	@echo "✅ Development checks passed!"

# Quick commands
quick-start: dev-setup up ## Quick start for development
	@echo "🚀 Quick start completed!"

quick-stop: down clean ## Quick stop and cleanup
	@echo "🛑 Quick stop completed!"



# Help with more details
help-detailed: ## Show detailed help with examples
	@echo "🚀 Multi-Agent System - Detailed Commands:"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make dev-setup     - Complete development setup"
	@echo "  make install       - Install Python dependencies"
	@echo "  make setup         - Setup environment and .env"
	@echo ""
	@echo "🏃 Quick Commands:"
	@echo "  make quick-start   - Setup and start everything"
	@echo "  make quick-stop    - Stop and cleanup everything"
	@echo "  make dev           - Quick development start"
	@echo ""
	@echo "🔧 Service Management:"
	@echo "  make up            - Start all services (local)"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make status        - Show service status"
	@echo "  make health        - Check service health"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make docker-up     - Start with Docker"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-clean  - Clean Docker resources"
	@echo ""
	@echo "🧪 Development:"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Check code quality"
	@echo "  make format        - Format code"
	@echo "  make build         - Full build pipeline"
	@echo ""
	@echo "📋 Logs & Monitoring:"
	@echo "  make logs          - Show all logs"
	@echo "  make logs-socketio - Show SocketIO logs"
	@echo "  make logs-gui      - Show GUI logs"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean         - Clean logs and PIDs"
	@echo "  make kill-all      - Force kill all processes"
	@echo ""
	@echo "🌐 Access Points:"
	@echo "  - React Frontend: http://localhost:3000"
	@echo "  - Auth API: http://localhost:8000"
	@echo "  - SocketIO: http://localhost:8001"
	@echo "  - Redis: localhost:6379"

# Open services in browser
open-react: ## Open React frontend in browser
	@echo "🌐 Opening React frontend..."
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 manually"

open-auth: ## Open Auth API in browser
	@echo "🌐 Opening Auth API..."
	@open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs manually"

# Legacy GUI open command removed

open-socketio: ## Open SocketIO health check in browser
	@echo "🌐 Opening SocketIO health check..."
	@open http://localhost:8001/health 2>/dev/null || xdg-open http://localhost:8001/health 2>/dev/null || echo "Please open http://localhost:8001/health manually"