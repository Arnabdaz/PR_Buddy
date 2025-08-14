# 📋 Prerequisites & System Requirements

## Required Software

### 🐍 Python 3.10+

Python is required for running the MCP servers.

**Installation:**

- **macOS**: `brew install python@3.10` or download from [python.org](https://www.python.org/downloads/)
- **Linux**: `sudo apt-get install python3.10` (Ubuntu/Debian) or `sudo yum install python310` (RHEL/CentOS)
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

**Verify Installation:**

```bash
python3 --version
# Should output: Python 3.10.x or higher
```

### 📦 UV Package Manager

UV is a fast Python package installer and resolver.

**Installation:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verify Installation:**

```bash
uv --version
```

### 🔧 Git

Git is required for repository management and submodule handling.

**Installation:**

- **macOS**: `brew install git` or `xcode-select --install`
- **Linux**: `sudo apt-get install git` (Ubuntu/Debian) or `sudo yum install git` (RHEL/CentOS)
- **Windows**: Download from [git-scm.com](https://git-scm.com/downloads)

**Verify Installation:**

```bash
git --version
```

### 💻 Cursor IDE

Latest version with MCP support is required.

**Download:** [cursor.com](https://cursor.com)

## Optional Software

### 🐹 Go 1.21+ (Recommended)

Required for building the GitHub MCP server locally. Provides better performance than Docker.

**Installation:**

- **macOS**: `brew install go`
- **Linux**: Follow instructions at [go.dev/doc/install](https://go.dev/doc/install)
- **Windows**: Download from [go.dev/dl](https://go.dev/dl/)

**Verify Installation:**

```bash
go version
# Should output: go version go1.21.x or higher
```

### 🐳 Docker (Alternative to Go)

Only needed if Go is not available for the GitHub MCP server.

**Installation:**

- **macOS**: Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- **Linux**: Follow [Docker Engine installation](https://docs.docker.com/engine/install/)
- **Windows**: Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

**Verify Installation:**

```bash
docker --version
docker info  # Should run without errors
```

## System Requirements

### Minimum Requirements

- **OS**: macOS 11+, Ubuntu 20.04+, Windows 10+
- **RAM**: 4GB
- **Disk Space**: 2GB free
- **Internet**: Required for API access

### Recommended Requirements

- **OS**: macOS 13+, Ubuntu 22.04+, Windows 11
- **RAM**: 8GB+
- **Disk Space**: 5GB free
- **Internet**: Stable broadband connection

## Quick Check Script

Save this as `check_requirements.sh` and run it to verify your system:

```bash
#!/bin/bash

echo "Checking PR Buddy Prerequisites..."
echo "=================================="

# Check Python
if command -v python3 &> /dev/null; then
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        echo "✅ Python 3.10+: $(python3 --version)"
    else
        echo "❌ Python: Found $(python3 --version) but need 3.10+"
    fi
else
    echo "❌ Python 3.10+: Not found"
fi

# Check Git
if command -v git &> /dev/null; then
    echo "✅ Git: $(git --version)"
else
    echo "❌ Git: Not found"
fi

# Check UV
if command -v uv &> /dev/null; then
    echo "✅ UV: $(uv --version)"
else
    echo "⚠️  UV: Not found (will be installed during setup)"
fi

# Check Go (optional)
if command -v go &> /dev/null; then
    echo "✅ Go (optional): $(go version)"
else
    echo "ℹ️  Go (optional): Not found"
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "✅ Docker (optional): $(docker --version)"
    else
        echo "⚠️  Docker (optional): Found but not running"
    fi
else
    echo "ℹ️  Docker (optional): Not found"
fi

echo "=================================="
echo "Note: Go or Docker is required for GitHub MCP server"
```

## Next Steps

Once all prerequisites are installed:

1. [Set up GitHub Access Token](./SETUP_GITHUB.md)
2. [Set up Jira Access Token](./SETUP_JIRA.md) (optional)
3. Return to the [main README](../README.md#-complete-setup-guide) for installation
