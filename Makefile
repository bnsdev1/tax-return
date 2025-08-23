# Tax Return Processor - Build System
# Provides convenient commands for building the application

.PHONY: help build-server build-web install-deps clean test dev

# Default target
help:
	@echo "Tax Return Processor - Build Commands"
	@echo "====================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make build-server    Build standalone executable (API + Web UI)"
	@echo "  make build-web       Build web application only"
	@echo "  make install-deps    Install all dependencies"
	@echo "  make clean          Clean build artifacts"
	@echo "  make test           Run tests"
	@echo "  make dev            Start development servers"
	@echo "  make help           Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install-deps"
	@echo "  2. make build-server"
	@echo "  3. Run the executable from dist/TaxReturnProcessor/"

# Build standalone server executable
build-server:
	@echo "Building standalone Tax Return Processor executable..."
ifeq ($(OS),Windows_NT)
	@scripts/build_server.bat
else
	@bash scripts/build_server.sh
endif

# Build web application only
build-web:
	@echo "Building web application..."
	@cd apps/web && npm install && npm run build

# Install all dependencies
install-deps:
	@echo "Installing dependencies..."
	@echo "Installing web dependencies..."
	@cd apps/web && npm install
	@echo "Installing Python dependencies..."
	@cd apps/api && python -m venv venv
ifeq ($(OS),Windows_NT)
	@cd apps/api && venv\Scripts\activate && pip install -r requirements.txt
else
	@cd apps/api && source venv/bin/activate && pip install -r requirements.txt
endif
	@echo "Installing core package dependencies..."
	@cd packages/core && pip install -e .
	@cd packages/llm && pip install -e .

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf apps/api/build apps/api/dist apps/api/static
	@rm -rf apps/web/dist apps/web/node_modules/.cache
	@rm -rf dist
	@rm -rf packages/core/build packages/core/dist packages/core/src/core.egg-info
	@rm -rf packages/llm/build packages/llm/dist packages/llm/src/llm.egg-info
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed"

# Run tests
test:
	@echo "Running tests..."
	@cd packages/core && python -m pytest tests/ -v
	@cd packages/llm && python -m pytest tests/ -v
	@cd apps/api && python -m pytest tests/ -v
	@cd apps/web && npm test

# Start development servers
dev:
	@echo "Starting development servers..."
	@echo "This will start both API and web servers in development mode"
	@echo "API will be available at http://localhost:8000"
	@echo "Web UI will be available at http://localhost:5173"
	@echo ""
	@echo "Starting API server..."
	@cd apps/api && python main_packaged.py --dev --no-browser &
	@sleep 3
	@echo "Starting web development server..."
	@cd apps/web && npm run dev

# Development setup (first time)
setup-dev: install-deps
	@echo "Setting up development environment..."
	@mkdir -p dev-workspace
	@echo "Development environment ready!"
	@echo "Run 'make dev' to start development servers"

# Quick build and test
quick-test: build-web
	@echo "Quick testing build..."
	@cd apps/api && python main_packaged.py --dev --workspace ./test-workspace --no-browser &
	@sleep 5
	@curl -f http://localhost:8000/api/health || (echo "Health check failed" && exit 1)
	@echo "Quick test passed!"
	@pkill -f "main_packaged.py" || true

# Package for distribution
package: build-server
	@echo "Packaging for distribution..."
	@echo "Build completed! Package available in dist/TaxReturnProcessor/"
	@echo ""
	@echo "Distribution contents:"
	@ls -la dist/TaxReturnProcessor/ 2>/dev/null || dir dist\TaxReturnProcessor\ 2>nul || echo "Package directory not found"

# Install system dependencies (Ubuntu/Debian)
install-system-deps-ubuntu:
	@echo "Installing system dependencies for Ubuntu/Debian..."
	@sudo apt-get update
	@sudo apt-get install -y python3 python3-pip python3-venv nodejs npm
	@echo "System dependencies installed"

# Install system dependencies (macOS)
install-system-deps-macos:
	@echo "Installing system dependencies for macOS..."
	@brew install python3 node npm
	@echo "System dependencies installed"

# Check system requirements
check-requirements:
	@echo "Checking system requirements..."
	@python3 --version || (echo "Python 3 not found" && exit 1)
	@node --version || (echo "Node.js not found" && exit 1)
	@npm --version || (echo "npm not found" && exit 1)
	@echo "All requirements satisfied!"

# Show build status
status:
	@echo "Tax Return Processor - Build Status"
	@echo "==================================="
	@echo ""
	@echo "Web build status:"
	@if [ -d "apps/web/dist" ]; then echo "  ✓ Web app built"; else echo "  ✗ Web app not built"; fi
	@echo ""
	@echo "API static files:"
	@if [ -d "apps/api/static" ]; then echo "  ✓ Static files ready"; else echo "  ✗ Static files missing"; fi
	@echo ""
	@echo "Executable:"
	@if [ -f "dist/TaxReturnProcessor/TaxReturnProcessor.exe" ] || [ -f "dist/TaxReturnProcessor/TaxReturnProcessor" ]; then echo "  ✓ Executable built"; else echo "  ✗ Executable not built"; fi
	@echo ""
	@echo "Dependencies:"
	@if [ -d "apps/web/node_modules" ]; then echo "  ✓ Web dependencies installed"; else echo "  ✗ Web dependencies missing"; fi
	@if [ -d "apps/api/venv" ]; then echo "  ✓ Python virtual environment ready"; else echo "  ✗ Python virtual environment missing"; fi