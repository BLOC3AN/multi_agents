#!/bin/bash

# Start MongoDB and Redis for development
# Usage: ./start_databases.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
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

print_status "🔄 Starting Redis for Multi-Agent System (MongoDB is online)"

cd "$PROJECT_ROOT"

# Check if docker-compose or docker compose is available
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    print_error "Neither 'docker-compose' nor 'docker compose' is available"
    print_error "Please install Docker Compose"
    exit 1
fi

print_status "Using Docker Compose command: $DOCKER_COMPOSE_CMD"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Start Redis using docker-compose
print_status "🚀 Starting Redis container..."

cd deployment

# Start only Redis (MongoDB is online)
$DOCKER_COMPOSE_CMD up -d redis

# Wait for services to be ready
print_status "⏳ Waiting for services to be ready..."

# Wait for Redis
print_status "🔄 Waiting for Redis..."
for i in {1..30}; do
    if $DOCKER_COMPOSE_CMD exec -T redis redis-cli ping &> /dev/null; then
        print_success "✅ Redis is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "❌ Redis failed to start"
        exit 1
    fi
    sleep 2
done

print_success "🎉 Redis service started successfully!"
print_status ""
print_status "📊 Service Status:"
print_status "  🗄️ MongoDB: Online (Cloud)"
print_status "  🔄 Redis: http://localhost:6379"
print_status ""
print_status "🔍 Check Status:"
print_status "  $DOCKER_COMPOSE_CMD ps"
print_status ""
print_status "📋 View Logs:"
print_status "  $DOCKER_COMPOSE_CMD logs redis"
print_status ""
print_status "🛑 Stop Services:"
print_status "  ./stop_databases.sh"
print_status "  or: $DOCKER_COMPOSE_CMD down"
