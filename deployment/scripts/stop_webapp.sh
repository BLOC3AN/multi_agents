#!/bin/bash

# Stop FastAPI + HTMX Web App
# Usage: ./stop_webapp.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_status "🛑 Stopping FastAPI + HTMX Web App..."

# Stop FastAPI Web App
if [ -f "/tmp/webapp_gui.pid" ]; then
    WEBAPP_PID=$(cat /tmp/webapp_gui.pid)
    if ps -p $WEBAPP_PID > /dev/null 2>&1; then
        kill $WEBAPP_PID
        rm -f /tmp/webapp_gui.pid
        print_success "✅ FastAPI Web App stopped (PID: $WEBAPP_PID)"
    else
        print_warning "⚠️  FastAPI Web App process not found"
        rm -f /tmp/webapp_gui.pid
    fi
else
    print_warning "⚠️  No FastAPI Web App PID file found"
fi

# Stop SocketIO server if we started it
if [ -f "/tmp/socketio_server.pid" ]; then
    SOCKETIO_PID=$(cat /tmp/socketio_server.pid)
    if ps -p $SOCKETIO_PID > /dev/null 2>&1; then
        kill $SOCKETIO_PID
        rm -f /tmp/socketio_server.pid
        print_success "✅ SocketIO server stopped (PID: $SOCKETIO_PID)"
    else
        print_warning "⚠️  SocketIO server process not found"
        rm -f /tmp/socketio_server.pid
    fi
else
    print_status "ℹ️  SocketIO server PID file not found (may be running separately)"
fi

# Check if any processes are still running on the ports
if lsof -ti:8502 > /dev/null 2>&1; then
    print_warning "⚠️  Something is still running on port 8502"
    print_status "💡 You may need to manually kill: sudo lsof -ti:8502 | xargs kill -9"
fi

if lsof -ti:8001 > /dev/null 2>&1; then
    print_status "ℹ️  SocketIO server still running on port 8001 (may be intentional)"
fi

print_success "🎉 FastAPI + HTMX Web App shutdown complete!"
