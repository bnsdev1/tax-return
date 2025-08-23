"""
Main entry point for the packaged Tax Return Processing Application.
This serves both the API and the web UI from a single executable.
"""

import os
import sys
import logging
import asyncio
import webbrowser
from pathlib import Path
from threading import Timer
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in development
        base_path = Path(__file__).parent
    
    return base_path / relative_path

def setup_workspace(workspace_path: Path) -> None:
    """Set up workspace directory structure."""
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (workspace_path / "uploads").mkdir(exist_ok=True)
    (workspace_path / "exports").mkdir(exist_ok=True)
    (workspace_path / "logs").mkdir(exist_ok=True)
    (workspace_path / ".kiro").mkdir(exist_ok=True)
    (workspace_path / ".kiro" / "steering").mkdir(exist_ok=True)
    (workspace_path / ".kiro" / "settings").mkdir(exist_ok=True)
    
    # Create default .env if it doesn't exist
    env_file = workspace_path / ".env"
    if not env_file.exists():
        env_content = """# Tax Return Processor Configuration
DATABASE_URL=sqlite:///./tax_returns.db
LLM_ENABLED=true
CLOUD_ALLOWED=false
PRIMARY_LLM=ollama
LOG_LEVEL=INFO
"""
        env_file.write_text(env_content)
    
    logger.info(f"Workspace set up at: {workspace_path}")

def create_app(workspace_path: Path) -> FastAPI:
    """Create and configure the FastAPI application."""
    # Change working directory to workspace
    os.chdir(workspace_path)
    
    # Load environment variables from workspace
    from dotenv import load_dotenv
    load_dotenv(workspace_path / ".env")
    
    # Import routers after setting up the environment
    from routers import returns, artifacts, review, challan, rules, export, settings_llm
    
    app = FastAPI(
        title="Tax Return Processor",
        version="1.0.0",
        description="Offline Tax Return Processing Application"
    )
    
    # Configure CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for packaged app
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(returns.router)
    app.include_router(artifacts.router)
    app.include_router(review.router)
    app.include_router(challan.router)
    app.include_router(rules.router)
    app.include_router(export.router)
    app.include_router(settings_llm.router)
    
    # Serve static files (web app)
    static_path = get_resource_path("static")
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Serve the web app at root
        @app.get("/")
        async def serve_webapp():
            return FileResponse(str(static_path / "index.html"))
        
        # Catch-all route for SPA routing
        @app.get("/{path:path}")
        async def serve_webapp_routes(path: str):
            # Check if it's an API route
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
            return {
                "message": "Tax Return Processor API",
                "status": "running",
                "workspace": str(workspace_path),
                "note": "Web UI not available - static files not found"
            }
    
    @app.get("/api/health")
    async def health():
        return {
            "status": "healthy",
            "workspace": str(workspace_path),
            "static_files": static_path.exists()
        }
    
    @app.get("/api/workspace")
    async def get_workspace_info():
        return {
            "workspace_path": str(workspace_path),
            "exists": workspace_path.exists(),
            "writable": os.access(workspace_path, os.W_OK) if workspace_path.exists() else False
        }
    
    return app

def open_browser(url: str, delay: float = 2.0):
    """Open browser after a delay."""
    def _open():
        try:
            webbrowser.open(url)
            logger.info(f"Opened browser to {url}")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
    
    Timer(delay, _open).start()

def select_workspace() -> Path:
    """Interactive workspace selection."""
    default_workspace = Path.home() / "ITR-Workspaces" / "default"
    
    print("\n" + "="*60)
    print("Tax Return Processor - Workspace Selection")
    print("="*60)
    print(f"Default workspace: {default_workspace}")
    print("\nOptions:")
    print("1. Use default workspace")
    print("2. Enter custom workspace path")
    print("3. Browse recent workspaces")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                return default_workspace
            
            elif choice == "2":
                custom_path = input("Enter workspace path: ").strip()
                if custom_path:
                    return Path(custom_path)
                else:
                    print("Invalid path. Please try again.")
            
            elif choice == "3":
                # Show recent workspaces
                recent_file = Path.home() / ".tax-processor-recent"
                if recent_file.exists():
                    recent_workspaces = recent_file.read_text().strip().split('\n')
                    print("\nRecent workspaces:")
                    for i, workspace in enumerate(recent_workspaces[:5], 1):
                        if Path(workspace).exists():
                            print(f"{i}. {workspace}")
                    
                    try:
                        idx = int(input("Select workspace number: ")) - 1
                        if 0 <= idx < len(recent_workspaces):
                            return Path(recent_workspaces[idx])
                    except (ValueError, IndexError):
                        pass
                
                print("No recent workspaces found or invalid selection.")
            
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def save_recent_workspace(workspace_path: Path):
    """Save workspace to recent list."""
    recent_file = Path.home() / ".tax-processor-recent"
    
    # Read existing recent workspaces
    recent_workspaces = []
    if recent_file.exists():
        recent_workspaces = recent_file.read_text().strip().split('\n')
    
    # Add current workspace to top
    workspace_str = str(workspace_path)
    if workspace_str in recent_workspaces:
        recent_workspaces.remove(workspace_str)
    recent_workspaces.insert(0, workspace_str)
    
    # Keep only last 10
    recent_workspaces = recent_workspaces[:10]
    
    # Save back
    recent_file.write_text('\n'.join(recent_workspaces))

def check_ollama():
    """Check if Ollama is available and offer to start it."""
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("Ollama is available")
            return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    print("\nOllama not detected. For LLM features:")
    print("1. Install Ollama from https://ollama.ai")
    print("2. Run 'ollama pull llama2' or similar model")
    print("3. Restart this application")
    return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Tax Return Processor")
    parser.add_argument("--workspace", type=str, help="Workspace directory path")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    
    args = parser.parse_args()
    
    # Determine workspace
    if args.workspace:
        workspace_path = Path(args.workspace)
    elif args.dev:
        workspace_path = Path.cwd() / "dev-workspace"
    else:
        workspace_path = select_workspace()
    
    # Set up workspace
    try:
        setup_workspace(workspace_path)
        save_recent_workspace(workspace_path)
    except Exception as e:
        logger.error(f"Failed to set up workspace: {e}")
        sys.exit(1)
    
    # Check Ollama availability
    check_ollama()
    
    # Create app
    try:
        app = create_app(workspace_path)
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        sys.exit(1)
    
    # Start server
    server_url = f"http://{args.host}:{args.port}"
    
    print(f"\n{'='*60}")
    print("Tax Return Processor Started")
    print(f"{'='*60}")
    print(f"Server: {server_url}")
    print(f"Workspace: {workspace_path}")
    print(f"{'='*60}")
    print("Press Ctrl+C to stop the server")
    
    # Open browser
    if not args.no_browser:
        open_browser(server_url)
    
    # Start server
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info" if args.dev else "warning",
            access_log=args.dev
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()