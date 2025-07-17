#!/bin/bash

# Multi-Agent System Deployment Script
# Usage: ./deploy.sh [dev|prod] [--build] [--logs]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
BUILD_FLAG=""
SHOW_LOGS=false
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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if required files exist
check_requirements() {
    local env_file=""
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        env_file="$PROJECT_ROOT/deployment/.env"
        if [ ! -f "$env_file" ]; then
            print_warning "Production .env file not found. Creating from template..."
            cp "$PROJECT_ROOT/deployment/.env.production" "$env_file"
            print_error "Please edit $env_file with your actual API keys and configuration"
            exit 1
        fi
    fi
    
    # Check if API keys are set
    if [ "$ENVIRONMENT" = "prod" ]; then
        source "$env_file"
        if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
            print_error "GOOGLE_API_KEY is not set in $env_file"
            exit 1
        fi
    fi
    
    print_success "Requirements check passed"
}

# Function to build and start services
deploy_services() {
    local compose_file=""
    local env_file=""
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        compose_file="docker-compose.dev.yml"
        print_status "Deploying in DEVELOPMENT mode..."
    else
        compose_file="docker-compose.yml"
        env_file="--env-file .env"
        print_status "Deploying in PRODUCTION mode..."
    fi
    
    cd "$PROJECT_ROOT/deployment"
    
    # Stop existing services
    print_status "Stopping existing services..."
    docker-compose -f "$compose_file" down --remove-orphans
    
    # Build if requested
    if [ "$BUILD_FLAG" = "--build" ]; then
        print_status "Building images..."
        docker-compose -f "$compose_file" build --no-cache
    fi
    
    # Start services
    print_status "Starting services..."
    docker-compose -f "$compose_file" $env_file up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    print_status "Running health check..."
    if python3 "$SCRIPT_DIR/health_check.py" --timeout 60; then
        print_success "Health check passed!"
    else
        print_error "Health check failed!"
        print_status "Showing logs..."
        docker-compose -f "$compose_file" logs --tail=50
        exit 1
    fi
}

# Function to show service status
show_status() {
    cd "$PROJECT_ROOT/deployment"
    
    local compose_file=""
    if [ "$ENVIRONMENT" = "dev" ]; then
        compose_file="docker-compose.dev.yml"
    else
        compose_file="docker-compose.yml"
    fi
    
    print_status "Service Status:"
    docker-compose -f "$compose_file" ps
    
    print_status "\nService URLs:"
    echo "  🚀 API: http://localhost:8000"
    echo "  📚 API Docs: http://localhost:8000/docs"
    echo "  ❤️  Health Check: http://localhost:8000/health"
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        echo "  📊 Grafana: http://localhost:3000 (admin/admin)"
        echo "  📈 Prometheus: http://localhost:9090"
    fi
}

# Function to show logs
show_logs() {
    cd "$PROJECT_ROOT/deployment"
    
    local compose_file=""
    if [ "$ENVIRONMENT" = "dev" ]; then
        compose_file="docker-compose.dev.yml"
    else
        compose_file="docker-compose.yml"
    fi
    
    print_status "Showing logs (Ctrl+C to exit)..."
    docker-compose -f "$compose_file" logs -f
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [dev|prod] [--build] [--logs]"
            echo ""
            echo "Options:"
            echo "  dev|prod     Environment to deploy (default: dev)"
            echo "  --build      Force rebuild of Docker images"
            echo "  --logs       Show logs after deployment"
            echo "  -h|--help    Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "🚀 Multi-Agent System Deployment"
    print_status "Environment: $ENVIRONMENT"
    
    check_docker
    check_requirements
    deploy_services
    show_status
    
    if [ "$SHOW_LOGS" = true ]; then
        show_logs
    fi
    
    print_success "🎉 Deployment completed successfully!"
    print_status "Run './deploy.sh --logs' to view logs"
    print_status "Run 'docker-compose down' to stop services"
}

# Run main function
main
