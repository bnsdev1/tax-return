# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Tax Return Processing Application.
Creates a single executable that serves both API and web UI.
"""

import os
import sys
from pathlib import Path

# Get the current directory (apps/api)
current_dir = Path(SPECPATH)
project_root = current_dir.parent.parent

# Add packages to Python path
sys.path.insert(0, str(project_root / "packages" / "core" / "src"))
sys.path.insert(0, str(project_root / "packages" / "llm"))

block_cipher = None

# Define data files to include
datas = [
    # Include web build files
    (str(current_dir / "static"), "static"),
    
    # Include database migration files
    (str(current_dir / "alembic"), "alembic"),
    (str(current_dir / "alembic.ini"), "."),
    
    # Include schema files
    (str(project_root / "packages" / "schemas"), "packages/schemas"),
    
    # Include fixtures for testing
    (str(project_root / "fixtures"), "fixtures"),
    
    # Include any template files
    (str(current_dir / "templates"), "templates") if (current_dir / "templates").exists() else None,
]

# Filter out None entries
datas = [d for d in datas if d is not None]

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    # FastAPI and dependencies
    'fastapi',
    'uvicorn',
    'uvicorn.workers',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'starlette',
    'starlette.applications',
    'starlette.middleware',
    'starlette.routing',
    'starlette.staticfiles',
    
    # Database
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'alembic',
    'alembic.runtime.migration',
    
    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic.validators',
    
    # Core packages
    'core',
    'core.parsers',
    'core.parsers.form26as',
    'core.parsers.form26as_llm',
    'core.reconcile.taxes_paid',
    'core.compute',
    'core.validate',
    'core.exporter',
    
    # LLM packages
    'packages.llm',
    'packages.llm.router',
    'packages.llm.contracts',
    'packages.llm.clients',
    
    # PDF processing
    'pdfplumber',
    'PyPDF2',
    
    # Other dependencies
    'python-multipart',
    'python-dotenv',
    'pathlib',
    'datetime',
    'decimal',
    'typing',
    'logging',
    'json',
    're',
]

# Binaries to include (empty for now)
binaries = []

a = Analysis(
    ['main_packaged.py'],  # Entry point script
    pathex=[str(current_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TaxReturnProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(current_dir / "icon.ico") if (current_dir / "icon.ico").exists() else None,
)