#!/usr/bin/env python3
"""
Test script for Tax Return Processor packaging.
Verifies that the packaged application works correctly.
"""

import os
import sys
import time
import requests
import subprocess
import tempfile
import shutil
from pathlib import Path
import signal
import psutil

class PackagingTest:
    """Test suite for packaged application."""
    
    def __init__(self):
        self.test_workspace = None
        self.server_process = None
        self.base_url = "http://localhost:8000"
        
    def setup_test_workspace(self):
        """Create a temporary test workspace."""
        self.test_workspace = Path(tempfile.mkdtemp(prefix="tax_test_"))
        print(f"Created test workspace: {self.test_workspace}")
        return self.test_workspace
    
    def cleanup_test_workspace(self):
        """Clean up test workspace."""
        if self.test_workspace and self.test_workspace.exists():
            shutil.rmtree(self.test_workspace)
            print(f"Cleaned up test workspace: {self.test_workspace}")
    
    def start_server(self, executable_path: Path):
        """Start the packaged server."""
        if not executable_path.exists():
            raise FileNotFoundError(f"Executable not found: {executable_path}")
        
        cmd = [
            str(executable_path),
            "--workspace", str(self.test_workspace),
            "--port", "8000",
            "--no-browser",
            "--dev"
        ]
        
        print(f"Starting server: {' '.join(cmd)}")
        
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        for i in range(30):  # 30 second timeout
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=1)
                if response.status_code == 200:
                    print("Server started successfully")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            
            # Check if process is still running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                print(f"Server process exited early:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
        
        print("Server failed to start within timeout")
        return False
    
    def stop_server(self):
        """Stop the server process."""
        if self.server_process:
            try:
                # Try graceful shutdown first
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.server_process.kill()
                self.server_process.wait()
            
            print("Server stopped")
    
    def test_health_endpoint(self):
        """Test the health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "workspace" in data
            print("✓ Health endpoint test passed")
            return True
        except Exception as e:
            print(f"✗ Health endpoint test failed: {e}")
            return False
    
    def test_workspace_endpoint(self):
        """Test the workspace info endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/workspace")
            assert response.status_code == 200
            data = response.json()
            assert "workspace_path" in data
            assert data["exists"] == True
            print("✓ Workspace endpoint test passed")
            return True
        except Exception as e:
            print(f"✗ Workspace endpoint test failed: {e}")
            return False
    
    def test_static_files(self):
        """Test that static files are served."""
        try:
            # Test root path (should serve index.html)
            response = requests.get(self.base_url)
            assert response.status_code == 200
            # Should contain HTML content
            assert "html" in response.text.lower()
            print("✓ Static files test passed")
            return True
        except Exception as e:
            print(f"✗ Static files test failed: {e}")
            return False
    
    def test_api_routes(self):
        """Test basic API routes."""
        try:
            # Test returns endpoint
            response = requests.get(f"{self.base_url}/api/returns")
            # Should return 422 (validation error) or 200, not 404
            assert response.status_code in [200, 422]
            
            print("✓ API routes test passed")
            return True
        except Exception as e:
            print(f"✗ API routes test failed: {e}")
            return False
    
    def test_workspace_structure(self):
        """Test that workspace structure is created correctly."""
        try:
            expected_dirs = ["uploads", "exports", "logs", ".kiro"]
            for dir_name in expected_dirs:
                dir_path = self.test_workspace / dir_name
                assert dir_path.exists(), f"Directory {dir_name} not created"
            
            # Check .env file
            env_file = self.test_workspace / ".env"
            assert env_file.exists(), ".env file not created"
            
            print("✓ Workspace structure test passed")
            return True
        except Exception as e:
            print(f"✗ Workspace structure test failed: {e}")
            return False
    
    def run_all_tests(self, executable_path: Path):
        """Run all tests."""
        print("="*60)
        print("Tax Return Processor - Packaging Tests")
        print("="*60)
        
        success = True
        
        try:
            # Setup
            self.setup_test_workspace()
            
            # Start server
            if not self.start_server(executable_path):
                print("✗ Failed to start server")
                return False
            
            # Run tests
            tests = [
                self.test_workspace_structure,
                self.test_health_endpoint,
                self.test_workspace_endpoint,
                self.test_static_files,
                self.test_api_routes,
            ]
            
            for test in tests:
                if not test():
                    success = False
            
        except Exception as e:
            print(f"✗ Test suite failed: {e}")
            success = False
        
        finally:
            # Cleanup
            self.stop_server()
            self.cleanup_test_workspace()
        
        print("="*60)
        if success:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed!")
        print("="*60)
        
        return success

def find_executable():
    """Find the packaged executable."""
    possible_paths = [
        Path("dist/TaxReturnProcessor/TaxReturnProcessor.exe"),
        Path("dist/TaxReturnProcessor/TaxReturnProcessor"),
        Path("apps/api/dist/TaxReturnProcessor.exe"),
        Path("apps/api/dist/TaxReturnProcessor"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test packaged Tax Return Processor")
    parser.add_argument("--executable", type=str, help="Path to executable")
    parser.add_argument("--build-first", action="store_true", help="Build before testing")
    
    args = parser.parse_args()
    
    # Build if requested
    if args.build_first:
        print("Building application first...")
        if os.name == 'nt':  # Windows
            result = subprocess.run(["scripts\\build_server.bat"], shell=True)
        else:  # Unix-like
            result = subprocess.run(["bash", "scripts/build_server.sh"])
        
        if result.returncode != 0:
            print("Build failed!")
            return 1
    
    # Find executable
    if args.executable:
        executable_path = Path(args.executable)
    else:
        executable_path = find_executable()
    
    if not executable_path:
        print("Executable not found. Please build first or specify path with --executable")
        print("Available options:")
        print("  python test_packaging.py --build-first")
        print("  python test_packaging.py --executable path/to/executable")
        return 1
    
    if not executable_path.exists():
        print(f"Executable not found: {executable_path}")
        return 1
    
    # Run tests
    tester = PackagingTest()
    success = tester.run_all_tests(executable_path)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())