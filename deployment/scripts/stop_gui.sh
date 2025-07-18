#!/bin/bash

# Stop GUI services
# Usage: ./stop_gui.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_status "🛑 Stopping Multi-Agent System GUI Services"

# Stop Streamlit
if [ -f "/tmp/streamlit_gui.pid" ]; then
    STREAMLIT_PID=$(cat /tmp/streamlit_gui.pid)
    if kill -0 $STREAMLIT_PID 2>/dev/null; then
        print_status "🎨 Stopping Streamlit GUI (PID: $STREAMLIT_PID)..."
        kill $STREAMLIT_PID
        rm /tmp/streamlit_gui.pid
        print_success "✅ Streamlit GUI stopped"
    else
        print_status "🎨 Streamlit GUI not running"
        rm -f /tmp/streamlit_gui.pid
    fi
else
    print_status "🎨 Streamlit GUI PID file not found"
fi

# Stop SocketIO server
if [ -f "/tmp/socketio_server.pid" ]; then
    SOCKETIO_PID=$(cat /tmp/socketio_server.pid)
    if kill -0 $SOCKETIO_PID 2>/dev/null; then
        print_status "🔌 Stopping SocketIO server (PID: $SOCKETIO_PID)..."
        kill $SOCKETIO_PID
        rm /tmp/socketio_server.pid
        print_success "✅ SocketIO server stopped"
    else
        print_status "🔌 SocketIO server not running"
        rm -f /tmp/socketio_server.pid
    fi
else
    print_status "🔌 SocketIO server PID file not found"
fi

# Kill any remaining processes
print_status "🧹 Cleaning up remaining processes..."
pkill -f "streamlit run gui/main.py" 2>/dev/null || true
pkill -f "socketio_server.py" 2>/dev/null || true

print_success "🎉 All GUI services stopped successfully!"
