#!/bin/bash

# Release preparation script for Channels DVR Player
# This script prepares the project for distribution

set -e

echo "🚀 Preparing Channels DVR Player for Distribution"
echo "================================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Version information
VERSION=$(python -c "from config.app_config import AppConfig; print(AppConfig.APP_VERSION)")
echo "📦 Version: $VERSION"

# Clean up development files
echo "🧹 Cleaning up development files..."
rm -rf __pycache__ app/__pycache__ config/__pycache__ app/main/__pycache__
rm -rf app/models/__pycache__ app/services/__pycache__
rm -rf .pytest_cache
rm -f *.log
rm -f .env

# Reset database and setup flags for fresh installation
echo "🗄️  Resetting database for clean installation..."
rm -f config/channels.db
rm -f config/setup.flag

# Ensure required directories exist
mkdir -p config

# Create distribution directory
DIST_DIR="dist/channels-dvr-player-v${VERSION}"
echo "📁 Creating distribution directory: $DIST_DIR"
rm -rf dist
mkdir -p "$DIST_DIR"

# Copy files (excluding items in .distignore)
echo "📋 Copying files..."
rsync -av --progress . "$DIST_DIR/" --exclude-from=.distignore

# Create version info file
cat > "$DIST_DIR/VERSION.txt" << EOF
Channels DVR Player v${VERSION}
Built on: $(date)
Platform: Cross-platform (Python 3.7+)

This is a production-ready distribution.
See README.md for installation and setup instructions.
EOF

# Create quick start script for different platforms
cat > "$DIST_DIR/quick-start.sh" << 'EOF'
#!/bin/bash
echo "🚀 Channels DVR Player - Quick Start"
echo "====================================="

# Check if setup was already run
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists. Activating..."
    source venv/bin/activate
else
    echo "📦 Setting up for first time..."
    ./setup_venv.sh
    source venv/bin/activate
fi

echo "🌐 Starting Channels DVR Player..."
echo "Open your browser to: http://localhost:7734"
python start.py
EOF

cat > "$DIST_DIR/quick-start.bat" << 'EOF'
@echo off
echo 🚀 Channels DVR Player - Quick Start
echo =====================================

if exist "venv" (
    echo ✅ Virtual environment exists. Activating...
    call venv\Scripts\activate
) else (
    echo 📦 Setting up for first time...
    call setup_venv.bat
    call venv\Scripts\activate
)

echo 🌐 Starting Channels DVR Player...
echo Open your browser to: http://localhost:7734
python start.py
pause
EOF

chmod +x "$DIST_DIR/quick-start.sh"

# Create distribution package
echo "📦 Creating distribution archive..."
cd dist
tar -czf "channels-dvr-player-v${VERSION}.tar.gz" "channels-dvr-player-v${VERSION}/"
zip -r "channels-dvr-player-v${VERSION}.zip" "channels-dvr-player-v${VERSION}/" > /dev/null

# Calculate file sizes
TAR_SIZE=$(du -h "channels-dvr-player-v${VERSION}.tar.gz" | cut -f1)
ZIP_SIZE=$(du -h "channels-dvr-player-v${VERSION}.zip" | cut -f1)

echo ""
echo "✅ Distribution packages created:"
echo "   📁 Directory: $DIST_DIR"
echo "   📦 TAR.GZ: channels-dvr-player-v${VERSION}.tar.gz ($TAR_SIZE)"
echo "   📦 ZIP: channels-dvr-player-v${VERSION}.zip ($ZIP_SIZE)"
echo ""
echo "🎉 Ready for distribution!"
echo ""
echo "📋 Next steps:"
echo "   1. Test the distribution package on a clean system"
echo "   2. Update release notes and documentation"
echo "   3. Create GitHub release with these archives"
echo "   4. Update project website/documentation"
