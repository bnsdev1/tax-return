#!/usr/bin/env python3
"""
Setup script for LLM helpers in ITR Prep app.

This script helps set up the LLM system by:
1. Installing required dependencies
2. Running database migrations
3. Creating default LLM settings
4. Testing provider connectivity
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def install_dependencies():
    """Install Python dependencies."""
    print("\n=== Installing Dependencies ===")
    
    # Install API dependencies
    print("Installing API dependencies...")
    run_command("pip install -r requirements.txt", cwd="apps/api")
    
    # Install core package
    print("Installing core package...")
    run_command("pip install -e .", cwd="packages/core")
    
    # Install LLM package
    print("Installing LLM package...")
    run_command("pip install -e .", cwd="packages/llm")


def setup_database():
    """Run database migrations."""
    print("\n=== Setting Up Database ===")
    
    # Run Alembic migrations
    print("Running database migrations...")
    run_command("alembic upgrade head", cwd="apps/api")


def create_env_file():
    """Create .env file if it doesn't exist."""
    print("\n=== Environment Configuration ===")
    
    env_file = Path(".env")
    env_sample = Path(".env.sample")
    
    if not env_file.exists() and env_sample.exists():
        print("Creating .env file from .env.sample...")
        env_file.write_text(env_sample.read_text())
        print("✓ Created .env file")
        print("⚠️  Please edit .env file and add your API keys")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("⚠️  No .env.sample file found")


def check_ollama():
    """Check if Ollama is available."""
    print("\n=== Checking Ollama ===")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running")
            
            # Check if required model is available
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            if any("llama3.1" in name for name in model_names):
                print("✓ Llama 3.1 model is available")
            else:
                print("⚠️  Llama 3.1 model not found")
                print("Run: ollama pull llama3.1:8b-instruct-q4_0")
        else:
            print("⚠️  Ollama is running but returned error")
    except requests.exceptions.ConnectionError:
        print("⚠️  Ollama is not running")
        print("Install Ollama from: https://ollama.ai/")
        print("Then run: ollama serve")
    except Exception as e:
        print(f"⚠️  Error checking Ollama: {e}")


def test_api_server():
    """Test if API server is running."""
    print("\n=== Testing API Server ===")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ API server is running")
            return True
        else:
            print("⚠️  API server returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  API server is not running")
        print("Start with: make api")
        return False
    except Exception as e:
        print(f"⚠️  Error testing API server: {e}")
        return False


def create_default_llm_settings():
    """Create default LLM settings via API."""
    print("\n=== Creating LLM Settings ===")
    
    if not test_api_server():
        print("Skipping LLM settings creation (API server not available)")
        return
    
    try:
        # Check if settings already exist
        response = requests.get("http://localhost:8000/api/settings/llm")
        
        if response.status_code == 200:
            print("✓ LLM settings already exist")
            settings = response.json()
            print(f"  LLM Enabled: {settings.get('llm_enabled')}")
            print(f"  Cloud Allowed: {settings.get('cloud_allowed')}")
            print(f"  Primary Provider: {settings.get('primary')}")
        else:
            print("Creating default LLM settings...")
            default_settings = {
                "llm_enabled": True,
                "cloud_allowed": True,
                "primary": "openai",
                "long_context_provider": "gemini",
                "local_provider": "ollama",
                "redact_pii": True,
                "long_context_threshold_chars": 8000,
                "confidence_threshold": 0.7,
                "max_retries": 2,
                "timeout_ms": 40000
            }
            
            response = requests.put(
                "http://localhost:8000/api/settings/llm",
                json=default_settings
            )
            
            if response.status_code == 200:
                print("✓ Created default LLM settings")
            else:
                print(f"⚠️  Failed to create LLM settings: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️  Error creating LLM settings: {e}")


def test_llm_providers():
    """Test LLM provider connectivity."""
    print("\n=== Testing LLM Providers ===")
    
    if not test_api_server():
        print("Skipping provider tests (API server not available)")
        return
    
    providers = ["openai", "gemini", "ollama"]
    
    for provider in providers:
        try:
            response = requests.post(
                "http://localhost:8000/api/settings/llm/ping",
                json={"provider": provider},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    print(f"✓ {provider.title()} is working")
                    if result.get("response_time_ms"):
                        print(f"  Response time: {result['response_time_ms']}ms")
                else:
                    print(f"⚠️  {provider.title()} failed: {result.get('error')}")
            else:
                print(f"⚠️  {provider.title()} test failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Error testing {provider}: {e}")


def print_next_steps():
    """Print next steps for the user."""
    print("\n=== Next Steps ===")
    print("1. Edit .env file and add your API keys:")
    print("   - OPENAI_API_KEY=your_key_here")
    print("   - GEMINI_API_KEY=your_key_here")
    print("")
    print("2. Start the development servers:")
    print("   make dev")
    print("")
    print("3. Access the LLM settings UI:")
    print("   http://localhost:5173/settings/llm")
    print("")
    print("4. Run integration tests:")
    print("   python test_llm_integration.py")
    print("")
    print("5. Test with a complex Form 16B or bank statement")


def main():
    """Main setup function."""
    print("=== LLM Helpers Setup ===")
    print("Setting up LLM system for ITR Prep app...")
    
    # Check prerequisites
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Setup database
    setup_database()
    
    # Create environment file
    create_env_file()
    
    # Check external services
    check_ollama()
    
    # Create LLM settings (if API is running)
    create_default_llm_settings()
    
    # Test providers (if API is running)
    test_llm_providers()
    
    # Print next steps
    print_next_steps()
    
    print("\n✓ LLM setup completed!")


if __name__ == "__main__":
    main()