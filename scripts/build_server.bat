@echo off
REM Build script for Tax Return Processor - Single Executable
REM Creates a standalone executable that serves both API and web UI

setlocal enabledelayedexpansion

echo ==========================================
echo Building Tax Return Processor
echo ==========================================

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "API_DIR=%PROJECT_ROOT%\apps\api"
set "WEB_DIR=%PROJECT_ROOT%\apps\web"

echo Project root: %PROJECT_ROOT%
echo API directory: %API_DIR%
echo Web directory: %WEB_DIR%

REM Check if required directories exist
if not exist "%API_DIR%" (
    echo Error: API directory not found at %API_DIR%
    exit /b 1
)

if not exist "%WEB_DIR%" (
    echo Error: Web directory not found at %WEB_DIR%
    exit /b 1
)

REM Step 1: Build the web application
echo.
echo Step 1: Building web application...
echo ----------------------------------------

cd /d "%WEB_DIR%"

REM Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo Installing web dependencies...
    call npm install
    if errorlevel 1 (
        echo Error: Failed to install web dependencies
        exit /b 1
    )
)

REM Build the web app
echo Building web app for production...
call npm run build
if errorlevel 1 (
    echo Error: Web build failed
    exit /b 1
)

REM Check if build was successful
if not exist "dist" (
    echo Error: Web build failed - dist directory not found
    exit /b 1
)

echo Web build completed successfully

REM Step 2: Copy web build to API static directory
echo.
echo Step 2: Copying web build to API static directory...
echo ----------------------------------------

cd /d "%API_DIR%"

REM Remove existing static directory
if exist "static" (
    echo Removing existing static directory...
    rmdir /s /q static
)

REM Copy web build to static
echo Copying web build files...
xcopy "%WEB_DIR%\dist" static\ /e /i /y
if errorlevel 1 (
    echo Error: Failed to copy web build files
    exit /b 1
)

echo Web files copied to static directory

REM Step 3: Install Python dependencies
echo.
echo Step 3: Installing Python dependencies...
echo ----------------------------------------

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install Python dependencies
    exit /b 1
)

REM Install PyInstaller if not already installed
pip install pyinstaller
if errorlevel 1 (
    echo Error: Failed to install PyInstaller
    exit /b 1
)

REM Install additional dependencies for packaging
pip install python-dotenv
if errorlevel 1 (
    echo Error: Failed to install python-dotenv
    exit /b 1
)

echo Python dependencies installed

REM Step 4: Build executable with PyInstaller
echo.
echo Step 4: Building executable with PyInstaller...
echo ----------------------------------------

REM Clean previous builds
if exist "build" (
    echo Cleaning previous build...
    rmdir /s /q build
)

if exist "dist" (
    echo Cleaning previous dist...
    rmdir /s /q dist
)

REM Run PyInstaller
echo Running PyInstaller...
pyinstaller pyinstaller.spec --clean --noconfirm
if errorlevel 1 (
    echo Error: PyInstaller build failed
    exit /b 1
)

REM Check if build was successful
if not exist "dist\TaxReturnProcessor.exe" (
    echo Error: PyInstaller build failed - executable not found
    exit /b 1
)

echo Executable built successfully

REM Step 5: Create distribution package
echo.
echo Step 5: Creating distribution package...
echo ----------------------------------------

set "DIST_DIR=%PROJECT_ROOT%\dist"
set "PACKAGE_DIR=%DIST_DIR%\TaxReturnProcessor"

REM Create distribution directory
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%PACKAGE_DIR%" mkdir "%PACKAGE_DIR%"

REM Copy executable
copy "dist\TaxReturnProcessor.exe" "%PACKAGE_DIR%\"
if errorlevel 1 (
    echo Error: Failed to copy executable
    exit /b 1
)

REM Copy additional files
echo Copying additional files...

REM Create README
(
echo Tax Return Processor - Offline Application
echo ==========================================
echo.
echo QUICK START:
echo 1. Double-click TaxReturnProcessor.exe
echo 2. Select or create a workspace directory
echo 3. The application will open in your browser at http://localhost:8000
echo 4. Upload your tax documents and process your return
echo.
echo WORKSPACE:
echo - All your data is stored in the workspace directory you select
echo - Default location: ~/ITR-Workspaces/default
echo - You can have multiple workspaces for different years or clients
echo.
echo FEATURES:
echo - Completely offline - no internet required for basic functionality
echo - Supports Form 26AS, Form 16, AIS, bank statements
echo - Automatic reconciliation and validation
echo - Export ready-to-file returns
echo.
echo LLM FEATURES ^(Optional^):
echo - Install Ollama from https://ollama.ai for advanced document parsing
echo - Run 'ollama pull llama2' to download a model
echo - Enable cloud LLM in settings for better accuracy ^(requires internet^)
echo.
echo TROUBLESHOOTING:
echo - If the browser doesn't open automatically, go to http://localhost:8000
echo - Check the console output for any error messages
echo - Ensure port 8000 is not in use by another application
echo - For support, check the logs in your workspace/logs directory
echo.
echo VERSION: 1.0.0
) > "%PACKAGE_DIR%\README.txt"

REM Copy license if it exists
if exist "%PROJECT_ROOT%\LICENSE" (
    copy "%PROJECT_ROOT%\LICENSE" "%PACKAGE_DIR%\"
)

REM Create launcher script for easier execution
(
echo @echo off
echo echo Starting Tax Return Processor...
echo TaxReturnProcessor.exe
echo pause
) > "%PACKAGE_DIR%\start.bat"

REM Create one-click Ollama starter
(
echo @echo off
echo echo Checking for Ollama...
echo ollama list ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo Ollama not found. Please install from https://ollama.ai
echo     echo Starting without Ollama...
echo ^) else ^(
echo     echo Starting Ollama service...
echo     start /B ollama serve
echo     timeout /t 3 /nobreak ^>nul
echo ^)
echo.
echo echo Starting Tax Return Processor...
echo TaxReturnProcessor.exe
echo pause
) > "%PACKAGE_DIR%\start-with-ollama.bat"

echo Distribution package created at: %PACKAGE_DIR%

REM Step 6: Create archive
echo.
echo Step 6: Creating archive...
echo ----------------------------------------

cd /d "%DIST_DIR%"

REM Create timestamp for archive name
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "ARCHIVE_NAME=TaxReturnProcessor-%YYYY%%MM%%DD%.zip"

REM Try to create ZIP archive using PowerShell
echo Creating ZIP archive: %ARCHIVE_NAME%
powershell -command "Compress-Archive -Path 'TaxReturnProcessor' -DestinationPath '%ARCHIVE_NAME%' -Force"
if errorlevel 1 (
    echo Warning: Failed to create ZIP archive. Package available at: %PACKAGE_DIR%
) else (
    echo Archive created: %DIST_DIR%\%ARCHIVE_NAME%
)

REM Final summary
echo.
echo ==========================================
echo Build completed successfully!
echo ==========================================
echo Executable: %PACKAGE_DIR%\TaxReturnProcessor.exe
echo Package: %PACKAGE_DIR%
if exist "%ARCHIVE_NAME%" (
    echo Archive: %DIST_DIR%\%ARCHIVE_NAME%
)
echo.
echo To test the build:
echo 1. cd %PACKAGE_DIR%
echo 2. TaxReturnProcessor.exe
echo 3. Open http://localhost:8000 in your browser
echo.
echo The application is ready for distribution!
echo ==========================================

pause