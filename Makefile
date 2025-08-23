.PHONY: dev test api web install-api install-web lint format clean

# Development - start both services
dev:
	@echo "Starting development servers..."
	@make -j2 api web

# Start FastAPI server
api:
	@echo "Starting FastAPI server on http://localhost:8000"
	cd apps/api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start React dev server
web:
	@echo "Starting React dev server on http://localhost:5173"
	cd apps/web && npm run dev

# Install all dependencies
install: install-api install-web

# Install Python dependencies
install-api:
	cd apps/api && pip install -r requirements.txt
	cd packages/core && pip install -e .

# Install Node dependencies
install-web:
	cd apps/web && npm install

# Run all tests
test:
	@echo "Running Python tests..."
	cd apps/api && python -m pytest
	cd packages/core && python -m pytest
	@echo "Running web tests..."
	cd apps/web && npm run test

# Lint all code
lint:
	@echo "Linting Python code..."
	cd apps/api && ruff check . && mypy .
	cd packages/core && ruff check . && mypy .
	@echo "Linting web code..."
	cd apps/web && npm run lint

# Format all code
format:
	@echo "Formatting Python code..."
	cd apps/api && black . && ruff format .
	cd packages/core && black . && ruff format .
	@echo "Formatting web code..."
	cd apps/web && npm run format

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +