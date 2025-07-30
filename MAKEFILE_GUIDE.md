# Makefile Guide - Multi-Agent System

## 🚀 Quick Start

### First Time Setup
```bash
# Complete development setup
make dev-setup

# Or step by step:
make check-deps    # Check if dependencies are installed
make install       # Install Python dependencies
make setup         # Setup environment and .env file
```

### Start Development
```bash
# Quick start (recommended)
make quick-start   # Setup + start all services

# Or manual start
make up           # Start all services (Redis + SocketIO + GUI)
```

### Stop Services
```bash
make quick-stop   # Stop and cleanup
# Or
make down         # Just stop services
```

## 📋 Available Commands

### 🔧 Setup & Installation
- `make check-deps` - Check if Python, Docker, Streamlit are installed
- `make install` - Install Python dependencies from requirements.txt
- `make setup` - Create logs directory, setup .env from template
- `make dev-setup` - Complete development setup (install + setup)

### 🏃 Quick Commands
- `make quick-start` - Setup and start everything
- `make quick-stop` - Stop and cleanup everything
- `make dev` - Quick development start (install + setup + up)

### 🔧 Service Management
- `make up` - Start all services (Redis + SocketIO + GUI)
- `make down` - Stop all services
- `make restart` - Restart all services
- `make status` - Show service status
- `make health` - Check service health

#### Individual Services
- `make up-redis` - Start Redis container only
- `make up-socketio` - Start SocketIO server (Python)
- `make up-gui` - Start Streamlit GUI
- `make down-redis` - Stop Redis container
- `make down-socketio` - Stop SocketIO server
- `make down-gui` - Stop Streamlit GUI
- `make restart-socketio` - Restart SocketIO server
- `make restart-gui` - Restart GUI

### 🐳 Docker Commands
- `make docker-build` - Build Docker images
- `make docker-up` - Start services with Docker
- `make docker-down` - Stop Docker services
- `make docker-logs` - Show Docker logs
- `make docker-status` - Show Docker service status
- `make docker-clean` - Clean up Docker containers and images

### 🧪 Development & Testing
- `make test` - Run all tests
- `make test-coverage` - Run tests with coverage report
- `make lint` - Run code linting (flake8 + mypy)
- `make format` - Format code with black
- `make format-check` - Check if code is properly formatted
- `make build` - Run full build pipeline (format + lint + test)
- `make dev-check` - Check code quality without making changes

### 📋 Logs & Monitoring
- `make logs` - Show all logs (follow mode)
- `make logs-socketio` - Show SocketIO logs
- `make logs-gui` - Show GUI logs
- `make logs-redis` - Show Redis logs

### 🧹 Cleanup
- `make clean` - Stop services and clean up logs/PIDs
- `make kill-all` - Force kill all processes

### 📚 Help
- `make help` - Show available commands
- `make help-detailed` - Show detailed help with examples

## 🌐 Access Points

After starting services, you can access:
- **GUI**: http://localhost:8501 (Streamlit interface)
- **SocketIO**: http://localhost:8001 (Real-time communication)
- **Redis**: localhost:6379 (Database)

## 🔧 Configuration

### Environment Variables
Edit `.env` file (created automatically from `.env.example`):

```bash
# LLM Provider Configuration
LLM_PROVIDER=gemini                    # "gemini" or "openai"
LLM_MODEL=gemini-2.0-flash            # Model name
LLM_TEMPERATURE=0.2                   # Temperature (0.0-1.0)

# API Keys (REQUIRED)
GOOGLE_API_KEY=your_google_api_key    # For Gemini
OPENAI_API_KEY=your_openai_api_key    # For OpenAI

# Application Settings
DEBUG=false                           # Debug mode
```

## 🛠️ Development Workflow

### Typical Development Session
```bash
# 1. First time setup
make dev-setup

# 2. Start development
make quick-start

# 3. During development
make test           # Run tests
make lint           # Check code quality
make format         # Format code

# 4. Before committing
make build          # Full pipeline check

# 5. Stop when done
make quick-stop
```

### Code Quality Checks
```bash
# Check everything without changes
make dev-check

# Fix formatting and run checks
make format
make lint
make test
```

## 🐳 Docker Development

### Using Docker for Services
```bash
# Build Docker images
make docker-build

# Start with Docker
make docker-up

# Check status
make docker-status

# View logs
make docker-logs

# Stop and cleanup
make docker-down
make docker-clean
```

## 🔍 Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   make status        # Check what's running
   make kill-all      # Force kill processes
   make clean         # Clean up
   make quick-start   # Try again
   ```

2. **Port conflicts**
   - Check if ports 8001, 8501, 6379 are in use
   - Use `make kill-all` to stop conflicting processes

3. **Dependencies missing**
   ```bash
   make check-deps    # Verify dependencies
   make install       # Reinstall if needed
   ```

4. **Environment issues**
   ```bash
   make setup         # Recreate .env and logs
   ```

## 📝 Notes

- All commands use emoji for better readability
- Process management uses PID files for reliable start/stop
- Logs are stored in `logs/` directory
- Docker services are optional - local development works without Docker
- Redis is the only Docker dependency for local development
