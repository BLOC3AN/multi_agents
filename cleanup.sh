#!/bin/bash
# Enhanced cleanup script for Multi-Agent System
# Usage: ./cleanup.sh [--deep] [--logs] [--help]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
DEEP_CLEAN=false
CLEAN_LOGS=false
SHOW_HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --deep)
            DEEP_CLEAN=true
            shift
            ;;
        --logs)
            CLEAN_LOGS=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Show help
if [ "$SHOW_HELP" = true ]; then
    echo "Enhanced Cleanup Script for Multi-Agent System"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --deep    Perform deep cleanup (includes node_modules, build files)"
    echo "  --logs    Clean log files (use with caution)"
    echo "  --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Basic cleanup"
    echo "  $0 --deep        # Deep cleanup including dependencies"
    echo "  $0 --logs        # Clean logs only"
    echo "  $0 --deep --logs # Full cleanup"
    exit 0
fi

echo -e "${BLUE}🧹 Starting cleanup...${NC}"

# Remove Python cache
echo -e "${YELLOW}🐍 Removing Python cache files...${NC}"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
find . -name ".Python" -delete 2>/dev/null || true

# Remove test cache
echo "🧪 Removing test cache..."
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".coverage" -delete 2>/dev/null || true
find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove IDE files
echo "💻 Removing IDE files..."
find . -name ".vscode" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".idea" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true

# Remove OS files
echo "🖥️ Removing OS files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

# Remove temporary files
echo "📄 Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true

# Remove local database files
echo "🗄️ Removing local database files..."
find . -name "*.db" -delete 2>/dev/null || true
find . -name "*.sqlite" -delete 2>/dev/null || true
find . -name "*.sqlite3" -delete 2>/dev/null || true

# Remove log files (only if --logs flag is used)
if [ "$CLEAN_LOGS" = true ]; then
    echo -e "${YELLOW}📋 Removing log files...${NC}"
    find . -name "*.log" -delete 2>/dev/null || true
    rm -rf logs/*.log 2>/dev/null || true
fi

# Deep cleanup (only if --deep flag is used)
if [ "$DEEP_CLEAN" = true ]; then
    echo -e "${YELLOW}🔥 Performing deep cleanup...${NC}"

    # Remove node_modules
    echo -e "${YELLOW}📦 Removing node_modules...${NC}"
    find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true

    # Remove build directories
    echo -e "${YELLOW}🏗️ Removing build directories...${NC}"
    find . -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true

    # Remove package-lock files
    echo -e "${YELLOW}🔒 Removing lock files...${NC}"
    find . -name "package-lock.json" -delete 2>/dev/null || true
    find . -name "yarn.lock" -delete 2>/dev/null || true
fi

# Remove PID files
echo -e "${YELLOW}🔄 Removing PID files...${NC}"
find . -name "*.pid" -delete 2>/dev/null || true

# Summary
echo ""
echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
echo "  - Python cache files removed"
echo "  - Test cache removed"
echo "  - IDE files removed"
echo "  - OS files removed"
echo "  - Temporary files removed"
echo "  - Database files removed"
echo "  - PID files removed"

if [ "$CLEAN_LOGS" = true ]; then
    echo "  - Log files removed"
fi

if [ "$DEEP_CLEAN" = true ]; then
    echo "  - Node modules removed"
    echo "  - Build directories removed"
    echo "  - Lock files removed"
fi

echo ""
echo -e "${BLUE}💡 Tip: Use 'make clean' for basic cleanup or 'make clean-all' for deep cleanup${NC}"
