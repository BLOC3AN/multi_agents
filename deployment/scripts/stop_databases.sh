#!/bin/bash

# Stop MongoDB and Redis
# Usage: ./stop_databases.sh

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

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_status "🛑 Stopping Redis (MongoDB is online)"

cd "$PROJECT_ROOT/deployment"

# Check if docker-compose or docker compose is available
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    print_status "Neither 'docker-compose' nor 'docker compose' is available"
    print_status "Skipping Redis stop"
    exit 0
fi

# Stop Redis container
print_status "🔄 Stopping Redis..."
$DOCKER_COMPOSE_CMD stop redis

print_success "✅ Redis service stopped successfully!"

print_status ""
print_status "💡 To completely remove containers and volumes:"
print_status "  $DOCKER_COMPOSE_CMD down -v"
