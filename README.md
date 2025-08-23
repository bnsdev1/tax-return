# FastAPI + React Monorepo

A modern monorepo with FastAPI backend, React frontend, and shared Python packages.

## Structure

- `apps/api/` - FastAPI backend (Python 3.11)
- `apps/web/` - React + Vite + TypeScript + Tailwind frontend
- `packages/core/` - Shared Python library (models, rules, exporter)
- `packages/schemas/` - Data schemas and types

## Quick Start

```bash
# Install dependencies and start development servers
make dev

# Run all tests
make test

# Start individual services
make api    # FastAPI on http://localhost:8000
make web    # React on http://localhost:5173
```

## Development

- FastAPI docs: http://localhost:8000/docs
- React app: http://localhost:5173
- All linting/formatting configured with pre-commit hooks