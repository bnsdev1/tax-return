# Tax Return Processor - Packaging Guide

This guide explains how to build and distribute the Tax Return Processor as a single executable application.

## Overview

The Tax Return Processor can be packaged into a standalone executable that includes:
- FastAPI backend server
- React web UI
- All Python dependencies
- Database and file storage
- Offline functionality

## Quick Start

### Prerequisites

1. **Python 3.8+** with pip
2. **Node.js 16+** with npm
3. **Git** (for cloning the repository)

### Build Commands

```bash
# Install all dependencies
make install-deps

# Build standalone executable
make build-server

# The executable will be created in dist/TaxReturnProcessor/
```

### Alternative Build Methods

**Windows:**
```cmd
scripts\build_server.bat
```

**Linux/macOS:**
```bash
bash scripts/build_server.sh
```

## Build Process

The build process consists of several steps:

### 1. Web Application Build
- Installs Node.js dependencies
- Builds React app for production
- Creates optimized static files in `apps/web/dist/`

### 2. Static File Preparation
- Copies web build to `apps/api/static/`
- Configures FastAPI to serve static files

### 3. Python Environment Setup
- Creates virtual environment
- Installs Python dependencies
- Installs PyInstaller for packaging

### 4. Executable Creation
- Uses PyInstaller to create standalone executable
- Bundles all dependencies and static files
- Creates single executable file

### 5. Distribution Package
- Creates distribution directory
- Copies executable and support files
- Generates README and launcher scripts
- Creates ZIP archive for distribution

## Distribution Package Contents

The final package includes:

```
TaxReturnProcessor/
├── TaxReturnProcessor.exe          # Main executable
├── README.txt                      # User instructions
├── start.bat                       # Simple launcher
├── start-with-ollama.bat          # Launcher with Ollama support
└── LICENSE                        # License file (if present)
```

## Usage Instructions

### For End Users

1. **Download and Extract**
   - Extract the ZIP file to desired location
   - No installation required

2. **Run the Application**
   - Double-click `TaxReturnProcessor.exe`
   - Or run `start.bat` for easier launching
   - Or use `start-with-ollama.bat` if you have Ollama installed

3. **Select Workspace**
   - Choose or create a workspace directory
   - All data will be stored in this location
   - Default: `~/ITR-Workspaces/default`

4. **Access Web Interface**
   - Application opens browser automatically
   - Manual access: http://localhost:8000
   - Completely offline - no internet required

### Workspace Management

The application uses a workspace-based approach:

- **Workspace Directory**: Contains all user data
- **Database**: SQLite database in workspace root
- **Uploads**: Document uploads stored in `uploads/`
- **Exports**: Generated files in `exports/`
- **Logs**: Application logs in `logs/`
- **Settings**: Configuration in `.kiro/settings/`

### LLM Features (Optional)

For advanced document parsing:

1. **Install Ollama**
   - Download from https://ollama.ai
   - Install and run `ollama pull llama2`

2. **Cloud LLM (Optional)**
   - Configure API keys in settings
   - Requires internet connection
   - Better accuracy for complex documents

## Development

### Development Build

```bash
# Start development servers
make dev

# API: http://localhost:8000
# Web: http://localhost:5173
```

### Testing the Build

```bash
# Quick test of packaged app
make quick-test

# Full test suite
make test
```

### Build Customization

Edit `apps/api/pyinstaller.spec` to customize:
- Hidden imports
- Data files to include
- Executable name and icon
- Build options

## Troubleshooting

### Common Build Issues

1. **Web Build Fails**
   ```bash
   cd apps/web
   rm -rf node_modules
   npm install
   npm run build
   ```

2. **Python Dependencies Missing**
   ```bash
   cd apps/api
   pip install -r requirements.txt
   ```

3. **PyInstaller Errors**
   ```bash
   cd apps/api
   pyinstaller --clean pyinstaller.spec
   ```

### Runtime Issues

1. **Port Already in Use**
   - Change port: `TaxReturnProcessor.exe --port 8001`
   - Or kill process using port 8000

2. **Workspace Permissions**
   - Ensure write access to workspace directory
   - Try running as administrator (Windows)

3. **Browser Doesn't Open**
   - Manually navigate to http://localhost:8000
   - Check console output for errors

### Logs and Debugging

- **Console Output**: Shows startup and error messages
- **Workspace Logs**: `workspace/logs/` directory
- **Development Mode**: `TaxReturnProcessor.exe --dev`

## Advanced Configuration

### Command Line Options

```bash
TaxReturnProcessor.exe [options]

Options:
  --workspace PATH     Specify workspace directory
  --port PORT         Server port (default: 8000)
  --host HOST         Server host (default: 127.0.0.1)
  --no-browser        Don't open browser automatically
  --dev               Development mode with verbose logging
```

### Environment Variables

Create `.env` file in workspace:

```env
# Database configuration
DATABASE_URL=sqlite:///./tax_returns.db

# LLM configuration
LLM_ENABLED=true
CLOUD_ALLOWED=false
PRIMARY_LLM=ollama

# Logging
LOG_LEVEL=INFO
```

### Custom Workspace Structure

```
workspace/
├── .env                    # Environment configuration
├── tax_returns.db         # SQLite database
├── uploads/               # Uploaded documents
├── exports/               # Generated exports
├── logs/                  # Application logs
└── .kiro/
    ├── settings/          # Application settings
    │   └── mcp.json      # MCP configuration
    └── steering/          # AI steering rules
```

## Security Considerations

### Data Privacy
- All data stored locally in workspace
- No cloud storage by default
- Optional cloud LLM can be disabled

### Network Security
- Server binds to localhost only
- No external network access required
- Firewall-friendly (single port)

### File Security
- Workspace permissions control access
- Database encryption available
- Secure file handling for uploads

## Performance Optimization

### Startup Time
- First run may be slower (database setup)
- Subsequent runs are faster
- SSD storage recommended

### Memory Usage
- Base usage: ~100MB
- Increases with document processing
- LLM features require more memory

### Storage Requirements
- Base installation: ~50MB
- Workspace grows with usage
- Document storage as uploaded

## Distribution

### Creating Releases

1. **Version Tagging**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Build Release**
   ```bash
   make build-server
   ```

3. **Test Package**
   ```bash
   cd dist/TaxReturnProcessor
   ./TaxReturnProcessor.exe --dev
   ```

4. **Create Archive**
   - ZIP file created automatically
   - Upload to release platform

### Deployment Options

1. **Direct Download**
   - Provide ZIP file download
   - Include installation instructions

2. **Installer Creation**
   - Use NSIS (Windows) or similar
   - Create proper installer package

3. **Auto-Update**
   - Implement update checking
   - Download and replace executable

## Support and Maintenance

### User Support
- Include comprehensive README.txt
- Provide troubleshooting guide
- Set up support channels

### Updates
- Regular security updates
- Feature enhancements
- Bug fixes and improvements

### Monitoring
- Error reporting (optional)
- Usage analytics (privacy-compliant)
- Performance monitoring

## License and Legal

- Ensure all dependencies are properly licensed
- Include license files in distribution
- Comply with open source requirements
- Consider commercial licensing needs

---

For technical support or questions about packaging, please refer to the project documentation or contact the development team.