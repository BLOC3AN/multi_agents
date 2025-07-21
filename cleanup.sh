#!/bin/bash
# Clean up development files and cache

echo "🧹 Cleaning up development files..."

# Remove Python cache
echo "🐍 Removing Python cache files..."
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

# Remove log files
echo "📋 Removing log files..."
find . -name "*.log" -delete 2>/dev/null || true

echo "✅ Cleanup completed!"
