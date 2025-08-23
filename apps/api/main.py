from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from routers import returns, artifacts, review, challan, rules, export, settings_llm

app = FastAPI(title="Tax Return Processing API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(returns.router)
app.include_router(artifacts.router)
app.include_router(review.router)
app.include_router(challan.router)
app.include_router(rules.router)
app.include_router(export.router)
app.include_router(settings_llm.router)

# Serve static files if they exist (for packaged version)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    @app.get("/")
    async def serve_webapp():
        return FileResponse(str(static_path / "index.html"))
    
    # Catch-all route for SPA routing (must be last)
    @app.get("/{path:path}")
    async def serve_webapp_routes(path: str):
        # Skip API routes
        if path.startswith("api/"):
            return {"error": "API endpoint not found"}
        
        # Check if it's a static file
        file_path = static_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # Default to index.html for SPA routing
        return FileResponse(str(static_path / "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Tax Return Processing API"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}