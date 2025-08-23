#!/usr/bin/env python3
"""
Script to run database migration for challan fields.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_migration():
    """Run the database migration for challan fields."""
    print("🔄 Running database migration for challan fields...")
    
    # Change to API directory
    api_dir = Path("apps/api")
    if not api_dir.exists():
        print("❌ API directory not found. Run this script from the project root.")
        return False
    
    original_dir = os.getcwd()
    
    try:
        os.chdir(api_dir)
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database migration completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Database migration failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure it's installed:")
        print("   pip install alembic")
        return False
    except Exception as e:
        print(f"❌ Migration failed with error: {str(e)}")
        return False
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    success = run_migration()
    if not success:
        sys.exit(1)