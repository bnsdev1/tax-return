#!/bin/bash
# Build script for Tax Return Processor - Single Executable
# Creates a standalone executable that serves both API and web UI

set -e  # Exit on any error

echo "=========================================="
echo "Building Tax Return Processor"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/apps/api"
WEB_DIR="$PROJECT_ROOT/apps/web"

echo "Project root: $PROJECT_ROOT"
echo "API directory: $API_DIR"
echo "Web directory: $WEB_DIR"

# Check if required directories exist
if [ ! -d "$API_DIR" ]; then
    echo "Error: API directory not found at $API_DIR"
    exit 1
fi

if [ ! -d "$WEB_DIR" ]; then
    echo "Error: Web directory not found at $WEB_DIR"
    exit 1
fi

# Step 1: Build the web application
echo ""
echo "Step 1: Building web application..."
echo "----------------------------------------"

cd "$WEB_DIR"

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing web dependencies..."
    npm install
fi

# Build the web app
echo "Building web app for production..."
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "Error: Web build failed - dist directory not found"
    exit 1
fi

echo "Web build completed successfully"

# Step 2: Copy web build to API static directory
echo ""
echo "Step 2: Copying web build to API static directory..."
echo "----------------------------------------"

cd "$API_DIR"

# Remove existing static directory
if [ -d "static" ]; then
    echo "Removing existing static directory..."
    rm -rf static
fi

# Copy web build to static
echo "Copying web build files..."
cp -r "$WEB_DIR/dist" static

echo "Web files copied to static directory"

# Step 3: Install Python dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
echo "----------------------------------------"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip first
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install PyInstaller if not already installed
pip install pyinstaller

# Install additional dependencies for packaging
pip install python-dotenv

echo "Python dependencies installed"

# Step 4: Build executable with PyInstaller
echo ""
echo "Step 4: Building executable with PyInstaller..."
echo "----------------------------------------"

# Clean previous builds
if [ -d "build" ]; then
    echo "Cleaning previous build..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "Cleaning previous dist..."
    rm -rf dist
fi

# Run PyInstaller
echo "Running PyInstaller..."
pyinstaller pyinstaller.spec --clean --noconfirm

# Check if build was successful
if [ ! -f "dist/TaxReturnProcessor.exe" ] && [ ! -f "dist/TaxReturnProcessor" ]; then
    echo "Error: PyInstaller build failed - executable not found"
    exit 1
fi

echo "Executable built successfully"

# Step 5: Create distribution package
echo ""
echo "Step 5: Creating distribution package..."
echo "----------------------------------------"

DIST_DIR="$PROJECT_ROOT/dist"
PACKAGE_DIR="$DIST_DIR/TaxReturnProcessor"

# Create distribution directory
mkdir -p "$PACKAGE_DIR"

# Copy executable
if [ -f "dist/TaxReturnProcessor.exe" ]; then
    cp dist/TaxReturnProcessor.exe "$PACKAGE_DIR/"
    EXECUTABLE_NAME="TaxReturnProcessor.exe"
else
    cp dist/TaxReturnProcessor "$PACKAGE_DIR/"
    EXECUTABLE_NAME="TaxReturnProcessor"
fi

# Copy additional files
echo "Copying additional files..."

# Copy README
cat > "$PACKAGE_DIR/README.txt" << 'EOF'
Tax Return Processor - Offline Application
==========================================

QUICK START:
1. Double-click TaxReturnProcessor.exe (or TaxReturnProcessor on Linux/Mac)
2. Select or create a workspace directory
3. The application will open in your browser at http://localhost:8000
4. Upload your tax documents and process your return

WORKSPACE:
- All your data is stored in the workspace directory you select
- Default location: ~/ITR-Workspaces/default
- You can have multiple workspaces for different years or clients

FEATURES:
- Completely offline - no internet required for basic functionality
- Supports Form 26AS, Form 16, AIS, bank statements
- Automatic reconciliation and validation
- Export ready-to-file returns

LLM FEATURES (Optional):
- Install Ollama from https://ollama.ai for advanced document parsing
- Run 'ollama pull llama2' to download a model
- Enable cloud LLM in settings for better accuracy (requires internet)

TROUBLESHOOTING:
- If the browser doesn't open automatically, go to http://localhost:8000
- Check the console output for any error messages
- Ensure port 8000 is not in use by another application
- For support, check the logs in your workspace/logs directory

VERSION: 1.0.0
EOF

# Copy license if it exists
if [ -f "$PROJECT_ROOT/LICENSE" ]; then
    cp "$PROJECT_ROOT/LICENSE" "$PACKAGE_DIR/"
fi

# Create launcher script for easier execution
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    cat > "$PACKAGE_DIR/start.bat" << 'EOF'
@echo off
echo Starting Tax Return Processor...
TaxReturnProcessor.exe
pause
EOF
else
    cat > "$PACKAGE_DIR/start.sh" << 'EOF'
#!/bin/bash
echo "Starting Tax Return Processor..."
./TaxReturnProcessor
EOF
    chmod +x "$PACKAGE_DIR/start.sh"
fi

# Create one-click Ollama starter (optional)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    cat > "$PACKAGE_DIR/start-with-ollama.bat" << 'EOF'
@echo off
echo Checking for Ollama...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama not found. Please install from https://ollama.ai
    echo Starting without Ollama...
) else (
    echo Starting Ollama service...
    start /B ollama serve
    timeout /t 3 /nobreak >nul
)

echo Starting Tax Return Processor...
TaxReturnProcessor.exe
pause
EOF
else
    cat > "$PACKAGE_DIR/start-with-ollama.sh" << 'EOF'
#!/bin/bash
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 3
else
    echo "Ollama not found. Please install from https://ollama.ai"
    echo "Starting without Ollama..."
fi

echo "Starting Tax Return Processor..."
./TaxReturnProcessor
EOF
    chmod +x "$PACKAGE_DIR/start-with-ollama.sh"
fi

echo "Distribution package created at: $PACKAGE_DIR"

# Step 6: Create archive
echo ""
echo "Step 6: Creating archive..."
echo "----------------------------------------"

cd "$DIST_DIR"

if command -v zip &> /dev/null; then
    ARCHIVE_NAME="TaxReturnProcessor-$(date +%Y%m%d).zip"
    echo "Creating ZIP archive: $ARCHIVE_NAME"
    zip -r "$ARCHIVE_NAME" TaxReturnProcessor/
    echo "Archive created: $DIST_DIR/$ARCHIVE_NAME"
elif command -v tar &> /dev/null; then
    ARCHIVE_NAME="TaxReturnProcessor-$(date +%Y%m%d).tar.gz"
    echo "Creating TAR archive: $ARCHIVE_NAME"
    tar -czf "$ARCHIVE_NAME" TaxReturnProcessor/
    echo "Archive created: $DIST_DIR/$ARCHIVE_NAME"
else
    echo "No archive tool found (zip or tar). Package available at: $PACKAGE_DIR"
fi

# Final summary
echo ""
echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo "Executable: $PACKAGE_DIR/$EXECUTABLE_NAME"
echo "Package: $PACKAGE_DIR"
if [ -n "$ARCHIVE_NAME" ]; then
    echo "Archive: $DIST_DIR/$ARCHIVE_NAME"
fi
echo ""
echo "To test the build:"
echo "1. cd $PACKAGE_DIR"
echo "2. ./$EXECUTABLE_NAME"
echo "3. Open http://localhost:8000 in your browser"
echo ""
echo "The application is ready for distribution!"
echo "=========================================="