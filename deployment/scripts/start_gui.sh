#!/bin/bash

# Start GUI services (SocketIO + Streamlit)
# Usage: ./start_gui.sh [dev|prod]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
if [ "$1" = "prod" ]; then
    ENVIRONMENT="prod"
fi

print_status "🚀 Starting Multi-Agent System GUI Services"
print_status "Environment: $ENVIRONMENT"

cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp "deployment/.env.production" ".env"
    print_error "Please edit .env with your actual API keys and MongoDB URI"
    exit 1
fi

# Check MongoDB and Redis connections
print_status "📊 Checking database connections..."
python3 -c "
import sys
sys.path.insert(0, '.')
from gui.database.models import init_database
if init_database():
    print('✅ Database connections successful')
else:
    print('❌ Database connection failed')
    exit(1)
"

if [ $? -ne 0 ]; then
    print_error "❌ Database connection failed. Make sure MongoDB and Redis are running."
    print_status "💡 Start services with: docker-compose up -d mongodb redis"
    exit 1
fi

# Start SocketIO server in background
print_status "🔌 Starting SocketIO server..."
if [ "$ENVIRONMENT" = "dev" ]; then
    python3 socketio_server.py &
    SOCKETIO_PID=$!
    echo $SOCKETIO_PID > /tmp/socketio_server.pid
else
    # For production, use docker-compose
    cd deployment
    docker-compose up -d socketio-server
    cd ..
fi

# Wait for SocketIO server to start
sleep 5

# Check if SocketIO server is running
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "✅ SocketIO server is running on port 8001"
else
    print_error "❌ SocketIO server failed to start"
    exit 1
fi

# Start Streamlit GUI
print_status "🎨 Starting Streamlit GUI..."
if [ "$ENVIRONMENT" = "dev" ]; then
    streamlit run gui/main.py --server.port 8501 --server.address 0.0.0.0 &
    STREAMLIT_PID=$!
    echo $STREAMLIT_PID > /tmp/streamlit_gui.pid
else
    # For production, use docker-compose
    cd deployment
    docker-compose up -d streamlit-gui
    cd ..
fi

# Wait for Streamlit to start
sleep 10

# Check if Streamlit is running
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    print_success "✅ Streamlit GUI is running on port 8501"
else
    print_error "❌ Streamlit GUI failed to start"
    exit 1
fi

print_success "🎉 All GUI services started successfully!"
print_status ""
print_status "📱 Access URLs:"
print_status "  🎨 Streamlit GUI: http://localhost:8501"
print_status "  🔌 SocketIO Server: http://localhost:8001"
print_status "  📚 SocketIO Docs: http://localhost:8001/docs"
print_status ""

if [ "$ENVIRONMENT" = "dev" ]; then
    print_status "💡 Development Mode:"
    print_status "  - SocketIO PID: $SOCKETIO_PID"
    print_status "  - Streamlit PID: $STREAMLIT_PID"
    print_status "  - Stop with: ./stop_gui.sh"
    print_status ""
    print_status "📋 Logs:"
    print_status "  - SocketIO: tail -f /tmp/socketio_server.log"
    print_status "  - Streamlit: tail -f /tmp/streamlit_gui.log"
fi

print_status "🔍 Health Check:"
print_status "  python3 deployment/scripts/health_check.py --url http://localhost:8001"
