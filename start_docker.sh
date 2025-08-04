#!/bin/bash

# Start Multi-Agent System with Docker Compose
# Usage: ./start_docker.sh [up|down|logs|restart]

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Please create .env file with your configuration"
    exit 1
fi

# Default action
ACTION=${1:-up}

case $ACTION in
    "up")
        print_status "🚀 Starting Multi-Agent System..."
        docker compose -f deployment/docker-compose.yml --env-file .env up -d redis socketio-server
        
        print_status "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Health checks
        if curl -f http://localhost:8001/health > /dev/null 2>&1; then
            print_success "✅ SocketIO Server: http://localhost:8001"
        else
            print_error "❌ SocketIO Server failed"
        fi
        
        print_success "🎉 Multi-Agent System is ready!"
        print_status "📱 Access React Frontend: http://localhost:3000 (run 'make up-react' separately)"
        ;;
        
    "down")
        print_status "🛑 Stopping Multi-Agent System..."
        docker compose -f deployment/docker-compose.yml --env-file .env down
        print_success "✅ All services stopped"
        ;;
        
    "logs")
        print_status "📋 Showing logs..."
        docker compose -f deployment/docker-compose.yml --env-file .env logs -f
        ;;
        
    "restart")
        print_status "🔄 Restarting Multi-Agent System..."
        docker compose -f deployment/docker-compose.yml --env-file .env restart
        print_success "✅ Services restarted"
        ;;
        
    "status")
        print_status "📊 Service Status:"
        docker compose -f deployment/docker-compose.yml --env-file .env ps
        ;;
        
    *)
        print_error "Unknown action: $ACTION"
        print_status "Usage: $0 [up|down|logs|restart|status]"
        exit 1
        ;;
esac
