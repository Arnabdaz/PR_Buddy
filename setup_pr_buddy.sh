#!/bin/bash

# PR Buddy Interactive Setup Script
# This script provides a comprehensive, interactive setup experience for PR Buddy

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVERS_DIR="$SCRIPT_DIR/servers"

# Banner
clear
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║             🚀 PR BUDDY INTERACTIVE SETUP 🚀                      ║"
echo "║                                                                  ║"
echo "║         AI-Powered Pull Request Assistant Installation           ║"
echo "║                           Version 1.0                            ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to prompt for yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    local response
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    echo -en "${BLUE}$prompt${NC}"
    read -r response
    response=${response:-$default}
    
    case "$response" in
        [Yy]* ) return 0;;
        * ) return 1;;
    esac
}

# Function to prompt for input with optional default
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    local is_secret="${4:-false}"
    local input
    
    if [ -n "$default" ]; then
        echo -en "${BLUE}$prompt ${CYAN}[$default]${BLUE}: ${NC}"
    else
        echo -en "${BLUE}$prompt: ${NC}"
    fi
    
    if [ "$is_secret" = "true" ]; then
        read -rs input
        echo
    else
    read -r input
    fi
    
    if [ -z "$input" ] && [ -n "$default" ]; then
        eval "$var_name='$default'"
    else
        eval "$var_name='$input'"
    fi
}

# Progress indicator
show_progress() {
    local pid=$1
    local delay=0.1
    local spinstr='⣾⣽⣻⢿⡿⣟⣯⣷'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# ============================================================================
# STEP 1: System Requirements Check
# ============================================================================

print_step "STEP 1: Checking System Requirements"

MISSING_DEPS=()
OPTIONAL_MISSING=()

# Check Git
echo -n "Checking Git... "
if command_exists git; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_success "Found (v$GIT_VERSION)"
else
    print_error "Not found"
    MISSING_DEPS+=("git")
fi

# Check Python
echo -n "Checking Python 3.10+... "
if check_python_version; then
    print_success "Found (v$PYTHON_VERSION)"
else
if command_exists python3; then
        print_error "Found Python $(python3 --version 2>&1 | cut -d' ' -f2) but need 3.10+"
    else
        print_error "Not found"
    fi
    MISSING_DEPS+=("python3.10+")
fi

# Check UV
echo -n "Checking UV package manager... "
if command_exists uv; then
    UV_VERSION=$(uv --version 2>/dev/null | cut -d' ' -f2 || echo "unknown")
    print_success "Found (v$UV_VERSION)"
    UV_INSTALLED=true
else
    print_warning "Not found (will install)"
    UV_INSTALLED=false
fi

# Check Docker (optional)
echo -n "Checking Docker (optional)... "
DOCKER_AVAILABLE=false
if command_exists docker; then
    if docker info >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,$//')
        print_success "Found and running (v$DOCKER_VERSION)"
        DOCKER_AVAILABLE=true
    else
        print_warning "Found but not running"
        OPTIONAL_MISSING+=("Docker daemon not running")
    fi
else
    print_warning "Not found"
    OPTIONAL_MISSING+=("docker")
fi

# Check Go (for GitHub server local build)
echo -n "Checking Go (for GitHub server)... "
if command_exists go; then
    GO_VERSION=$(go version | cut -d' ' -f3 | sed 's/go//')
    print_success "Found (v$GO_VERSION)"
    CAN_BUILD_GITHUB=true
else
    print_warning "Not found"
    OPTIONAL_MISSING+=("go")
    CAN_BUILD_GITHUB=false
fi

# Ask user preference for GitHub server installation
USE_DOCKER=false
if [ "$DOCKER_AVAILABLE" = true ] && [ "$CAN_BUILD_GITHUB" = true ]; then
    echo
    print_info "Both Docker and Go are available for GitHub server."
    if prompt_yes_no "Use Docker for GitHub server? (No = use local build)" "n"; then
        USE_DOCKER=true
        print_info "Will use Docker for GitHub server"
    else
        USE_DOCKER=false
        print_info "Will use local build for GitHub server"
    fi
elif [ "$DOCKER_AVAILABLE" = true ] && [ "$CAN_BUILD_GITHUB" = false ]; then
    echo
    print_warning "Go not available. Docker is required for GitHub server."
    if prompt_yes_no "Use Docker for GitHub server?" "y"; then
        USE_DOCKER=true
    else
        print_error "Cannot install GitHub server without Go or Docker"
        MISSING_DEPS+=("go or docker for GitHub server")
    fi
elif [ "$DOCKER_AVAILABLE" = false ] && [ "$CAN_BUILD_GITHUB" = true ]; then
    USE_DOCKER=false
    print_info "Will use local build for GitHub server (Docker not available)"
elif [ "$DOCKER_AVAILABLE" = false ] && [ "$CAN_BUILD_GITHUB" = false ]; then
    print_error "Neither Docker nor Go available for GitHub server"
    OPTIONAL_MISSING+=("GitHub server (needs Docker or Go)")
fi

# Report missing dependencies
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo
    print_error "Missing required dependencies:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    echo
    echo "Please install the missing dependencies and run this script again."
    echo "See: https://github.com/YOUR_USERNAME/pr-buddy#prerequisites"
    exit 1
fi

if [ ${#OPTIONAL_MISSING[@]} -gt 0 ]; then
    echo
    print_warning "Optional dependencies missing:"
    for dep in "${OPTIONAL_MISSING[@]}"; do
        echo "  - $dep"
    done
    echo
    if prompt_yes_no "Continue without optional dependencies?"; then
        echo "Continuing..."
    else
        echo "Please install optional dependencies and run again."
        exit 0
    fi
fi

# ============================================================================
# STEP 2: Repository Setup
# ============================================================================

print_step "STEP 2: Setting Up Repository"

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/README.md" ] || [ ! -f "$SCRIPT_DIR/.gitmodules" ]; then
    print_error "This script must be run from the PR Buddy repository root!"
    echo "Current directory: $SCRIPT_DIR"
    exit 1
fi

# Initialize and update submodules
echo "Checking git submodules..."
if [ ! -d "$SERVERS_DIR/cve-search/.git" ] || \
   [ ! -d "$SERVERS_DIR/git/.git" ] || \
   [ ! -d "$SERVERS_DIR/github-mcp-server/.git" ] || \
   [ ! -d "$SERVERS_DIR/jira-mcp/.git" ]; then
    
    print_info "Initializing git submodules..."
    git submodule init 2>/dev/null &
    show_progress $!
    
    print_info "Updating git submodules..."
    git submodule update --recursive 2>/dev/null &
    show_progress $!
    
    print_success "Submodules initialized"
else
    print_success "All submodules already initialized"
    
    if prompt_yes_no "Update submodules to latest versions?" "n"; then
        print_info "Updating submodules..."
        git submodule update --remote --merge 2>/dev/null &
        show_progress $!
        print_success "Submodules updated"
    fi
fi

# ============================================================================
# STEP 3: Install UV Package Manager
# ============================================================================

if [ "$UV_INSTALLED" = false ]; then
    print_step "STEP 3: Installing UV Package Manager"
    
    if prompt_yes_no "Install UV package manager now?"; then
        print_info "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null &
        show_progress $!
        
        # Source the env to get uv in PATH
        if [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        fi
        
        if command_exists uv; then
            print_success "UV installed successfully"
        else
            print_error "UV installation failed. Please install manually:"
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi
    else
        print_error "UV is required for Python package management"
        echo "Please install UV and run this script again"
        exit 1
    fi
else
    print_step "STEP 3: UV Package Manager"
    print_success "UV already installed, skipping..."
fi

# ============================================================================
# STEP 4: Install MCP Servers
# ============================================================================

print_step "STEP 4: Installing MCP Servers"

FAILED_SERVERS=()

# Function to install a server
install_server() {
    local server_name="$1"
    local server_path="$2"
    local test_import="$3"
    
    echo
    echo -e "${CYAN}[$server_name]${NC}"
    
    if [ ! -d "$server_path" ]; then
        print_error "Server directory not found: $server_path"
        FAILED_SERVERS+=("$server_name")
        return 1
    fi
    
    cd "$server_path"
    
    # Check if dependencies are already installed
    if [ -d ".venv" ] || [ -d "venv" ]; then
        print_info "Virtual environment exists, checking dependencies..."
    fi
    
    print_info "Installing dependencies..."
    if uv sync >/dev/null 2>&1; then
        print_success "Dependencies installed"
    else
        print_warning "uv sync failed, trying pip install..."
        if [ -f "requirements.txt" ]; then
            uv pip install -r requirements.txt >/dev/null 2>&1
        elif [ -f "pyproject.toml" ]; then
            uv pip install -e . >/dev/null 2>&1
        fi
    fi
    
    # Test the installation
    print_info "Testing installation..."
    if uv run python -c "import $test_import" 2>/dev/null; then
        print_success "$server_name ready!"
        return 0
    else
        print_warning "$server_name test failed (may still work)"
        return 0
    fi
}

# Install each server
install_server "CVE Search Server" "$SERVERS_DIR/cve-search" "mcp_server_cve_search"
install_server "Git Server" "$SERVERS_DIR/git" "mcp_server_git"
install_server "Jira Server" "$SERVERS_DIR/jira-mcp" "jira_mcp_server"

# GitHub Server
echo
echo -e "${CYAN}[GitHub Server]${NC}"
if [ "$USE_DOCKER" = true ]; then
    print_info "Using Docker for GitHub server..."
    print_info "Pulling Docker image..."
    if docker pull ghcr.io/github/github-mcp-server >/dev/null 2>&1; then
        print_success "GitHub server Docker image ready"
    else
        print_warning "Failed to pull Docker image, trying to build locally..."
        if [ "$CAN_BUILD_GITHUB" = true ]; then
            cd "$SERVERS_DIR/github-mcp-server"
            print_info "Building from source as fallback..."
            if go build -o github-mcp-server cmd/github-mcp-server/main.go 2>/dev/null; then
                print_success "GitHub server built locally"
                USE_DOCKER=false  # Update flag since we're using local build
            else
                print_warning "Build failed"
                FAILED_SERVERS+=("GitHub")
            fi
        else
            print_error "Cannot build locally (Go not available)"
            FAILED_SERVERS+=("GitHub")
        fi
    fi
elif [ "$CAN_BUILD_GITHUB" = true ]; then
    cd "$SERVERS_DIR/github-mcp-server"
    print_info "Building GitHub server from source (local build)..."
    if go build -o github-mcp-server cmd/github-mcp-server/main.go 2>/dev/null; then
        print_success "GitHub server built successfully"
    else
        print_warning "Build failed"
        FAILED_SERVERS+=("GitHub (Build)")
    fi
else
    print_warning "GitHub server cannot be installed (no Docker or Go available)"
    FAILED_SERVERS+=("GitHub")
fi

cd "$SCRIPT_DIR"

# Report installation status
if [ ${#FAILED_SERVERS[@]} -gt 0 ]; then
    echo
    print_warning "Some servers had issues:"
    for server in "${FAILED_SERVERS[@]}"; do
        echo "  - $server"
    done
fi

# ============================================================================
# STEP 5: Configuration
# ============================================================================

print_step "STEP 5: Configuration Setup"

echo
echo "Now let's configure your PR Buddy installation."
echo "You can leave fields blank and configure them later in the generated config."
echo

# GitHub Configuration
echo -e "${BOLD}GitHub Configuration:${NC}"
prompt_input "GitHub hostname (e.g., https://github.com)" "GITHUB_HOST" "https://github.com"
prompt_input "GitHub Personal Access Token (ghp_...)" "GITHUB_TOKEN" "" true

if [ -z "$GITHUB_TOKEN" ]; then
    print_warning "No GitHub token provided. You'll need to add it later for GitHub operations."
    echo "  Create one at: https://github.com/settings/tokens"
fi

echo

# Jira Configuration
echo -e "${BOLD}Jira Configuration:${NC}"
prompt_input "Jira base URL (e.g., https://company.atlassian.net)" "JIRA_BASE_URL" ""
if [ -n "$JIRA_BASE_URL" ]; then
    prompt_input "Jira email" "JIRA_EMAIL" ""
    prompt_input "Jira API token" "JIRA_TOKEN" "" true
else
    print_info "Skipping Jira configuration (not using Jira)"
    JIRA_EMAIL=""
    JIRA_TOKEN=""
fi

echo

# Git server will work with any repository - no default needed
DEFAULT_GIT_REPO=""

# ============================================================================
# STEP 6: Install PR Buddy Rules
# ============================================================================

print_step "STEP 6: Installing PR Buddy Rules"

RULES_DIR="$SCRIPT_DIR/rules"
CURSOR_RULES_DIR="$HOME/.cursor/rules"

if [ -d "$RULES_DIR" ] && [ "$(ls -A $RULES_DIR/*.mdc 2>/dev/null)" ]; then
    print_info "Found PR Buddy rules in $RULES_DIR"
    
    if prompt_yes_no "Install PR Buddy rules globally for Cursor?"; then
        # Create Cursor rules directory if it doesn't exist
        mkdir -p "$CURSOR_RULES_DIR"
        
        # Copy rules
        print_info "Copying rules to Cursor's global rules directory..."
        cp "$RULES_DIR"/*.mdc "$CURSOR_RULES_DIR/" 2>/dev/null
        
        # List installed rules
        echo "Installed rules:"
        for rule in "$CURSOR_RULES_DIR"/pr-*.mdc; do
            if [ -f "$rule" ]; then
                basename "$rule"
            fi
        done
        
        print_success "PR Buddy rules installed globally"
        print_info "These rules will be available in ALL your Cursor projects"
    else
        print_warning "Skipping rules installation"
        echo "You can install them later with:"
        echo "  cp $RULES_DIR/*.mdc ~/.cursor/rules/"
    fi
else
    print_warning "No rules found in $RULES_DIR"
    echo "Rules can be added later to: ~/.cursor/rules/"
fi

# ============================================================================
# STEP 7: Generate Configuration
# ============================================================================

print_step "STEP 7: Generating Configuration"

# Create config directory
CONFIG_DIR="$HOME/.pr-buddy"
mkdir -p "$CONFIG_DIR"

# Save environment configuration
ENV_FILE="$CONFIG_DIR/.env"
cat > "$ENV_FILE" << EOF
# PR Buddy Environment Configuration
# Generated on $(date)

# GitHub Configuration
GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_TOKEN}"
GITHUB_HOST="${GITHUB_HOST}"

# Jira Configuration
JIRA_BASE_URL="${JIRA_BASE_URL}"
JIRA_EMAIL="${JIRA_EMAIL}"
JIRA_API_TOKEN="${JIRA_TOKEN}"

# Repository Configuration
# Git server works with any repository - no default needed
# DEFAULT_GIT_REPO="${DEFAULT_GIT_REPO}"

# Installation Paths
PR_BUDDY_HOME="${SCRIPT_DIR}"
SERVERS_DIR="${SERVERS_DIR}"
EOF

print_success "Environment configuration saved to: $ENV_FILE"

# Generate MCP configuration for Cursor
MCP_CONFIG="$CONFIG_DIR/mcp.json"

cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
EOF

# Add CVE server
cat >> "$MCP_CONFIG" << EOF
    "pr-buddy-cve": {
      "command": "uv",
      "args": [
        "--directory",
        "${SERVERS_DIR}/cve-search",
        "run",
        "python",
        "main.py"
      ],
      "name": "CVE Security Scanner",
      "description": "Scans for vulnerabilities and CVEs in PR dependencies"
    },
EOF

# Add Git server (no default repository - will work with any repo)
cat >> "$MCP_CONFIG" << EOF
    "pr-buddy-git": {
      "command": "uv",
      "args": [
        "--directory", 
        "${SERVERS_DIR}/git",
        "run",
        "mcp-server-git"
      ],
      "name": "Git Operations",
      "description": "Handles local git operations and branch management"
    },
EOF

# Add GitHub server
if [ "$USE_DOCKER" = true ]; then
    # Docker version with GitHub host support
    DOCKER_ARGS='[
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN${GITHUB_TOKEN:+=${GITHUB_TOKEN}}",'
    
    # Add GitHub host environment variable if not default
    if [ "$GITHUB_HOST" != "https://github.com" ] && [ -n "$GITHUB_HOST" ]; then
        DOCKER_ARGS+='
        "-e",
        "GITHUB_HOST=${GITHUB_HOST}",'
    fi
    
    DOCKER_ARGS+='
        "-e",
        "GITHUB_TOOLSETS=repos,issues,pull_requests,actions,code_security",
        "ghcr.io/github/github-mcp-server"
      ]'
    
    cat >> "$MCP_CONFIG" << EOF
    "pr-buddy-github": {
      "command": "docker",
      "args": ${DOCKER_ARGS},
      "name": "GitHub Integration",
      "description": "Manages GitHub PRs, issues, and repository operations"
    }${JIRA_BASE_URL:+,}
EOF
else
    # Build args array for non-Docker version
    GITHUB_ARGS='['
    
    # Add GitHub host argument if not default
    if [ "$GITHUB_HOST" != "https://github.com" ] && [ -n "$GITHUB_HOST" ]; then
        GITHUB_ARGS+='
        "--gh-host",
        "'${GITHUB_HOST}'",'
    fi
    
    GITHUB_ARGS+='
        "stdio"
      ]'
    
    cat >> "$MCP_CONFIG" << EOF
    "pr-buddy-github": {
      "command": "${SERVERS_DIR}/github-mcp-server/github-mcp-server",
      "args": ${GITHUB_ARGS},
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      },
      "name": "GitHub Integration",
      "description": "Manages GitHub PRs, issues, and repository operations"
    }${JIRA_BASE_URL:+,}
EOF
fi

# Add Jira server if configured
if [ -n "$JIRA_BASE_URL" ]; then
    cat >> "$MCP_CONFIG" << EOF
    "pr-buddy-jira": {
      "command": "uv",
      "args": [
        "--directory",
        "${SERVERS_DIR}/jira-mcp",
        "run",
        "jira-mcp"
      ],
      "env": {
        "JIRA_BASE_URL": "${JIRA_BASE_URL}",
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_TOKEN}"
      },
      "name": "Jira Integration",
      "description": "Syncs with Jira tickets and requirements"
    }
EOF
fi

cat >> "$MCP_CONFIG" << EOF
  }
}
EOF

print_success "MCP configuration generated: $MCP_CONFIG"

# ============================================================================
# STEP 8: Test Configuration
# ============================================================================

print_step "STEP 8: Testing Configuration"

if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_HOST" ]; then
    echo -n "Testing GitHub connection... "
    # Determine the correct API endpoint based on the GitHub host
    if [ "$GITHUB_HOST" = "https://github.com" ]; then
        API_ENDPOINT="${GITHUB_HOST}/user"
    else
        # GitHub Enterprise uses /api/v3 prefix
        API_ENDPOINT="${GITHUB_HOST}/api/v3/user"
    fi
    
    if curl -s -H "Authorization: token $GITHUB_TOKEN" \
         "$API_ENDPOINT" 2>/dev/null | grep -q "login"; then
        print_success "Connected"
    else
        print_warning "Failed (check token and hostname)"
    fi
fi

if [ -n "$JIRA_BASE_URL" ] && [ -n "$JIRA_EMAIL" ] && [ -n "$JIRA_TOKEN" ]; then
    echo -n "Testing Jira connection... "
    if curl -s -u "$JIRA_EMAIL:$JIRA_TOKEN" \
         "$JIRA_BASE_URL/rest/api/3/myself" 2>/dev/null | grep -q "emailAddress"; then
        print_success "Connected"
    else
        print_warning "Failed (check credentials)"
    fi
fi

# ============================================================================
# FINAL INSTRUCTIONS
# ============================================================================

echo
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}║              🎉 PR BUDDY SETUP COMPLETE! 🎉                     ║${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo

echo -e "${BOLD}📋 Next Steps:${NC}"
echo
echo "1. Copy the MCP configuration to Cursor:"
echo -e "   ${CYAN}cp $MCP_CONFIG ~/.cursor/mcp.json${NC}"
echo
echo "   Or manually copy the contents:"
echo -e "   ${CYAN}cat $MCP_CONFIG${NC}"
echo
echo "2. Restart Cursor and enable Agent Mode"
echo
echo "3. Test with commands like:"
echo -e "   ${CYAN}@pr-creation.mdc Create a PR for my change on master branch${NC}"
echo -e "   ${CYAN}@pr-review.mdc Review PR Sense/cloudera-sense/123${NC}"
echo -e "   ${CYAN}@pr-update.mdc Update PR Sense/cloudera-sense/456 description${NC}"
echo

if [ -z "$GITHUB_TOKEN" ] || [ -z "$JIRA_BASE_URL" ]; then
    echo -e "${YELLOW}⚠️  Remember to configure:${NC}"
    [ -z "$GITHUB_TOKEN" ] && echo "   - GitHub Personal Access Token in $ENV_FILE"
    [ -z "$JIRA_BASE_URL" ] && echo "   - Jira credentials in $ENV_FILE"
    echo
fi

echo -e "${BOLD}📁 Configuration Files:${NC}"
echo "   - Environment: $ENV_FILE"
echo "   - MCP Config: $MCP_CONFIG"
echo
echo -e "${GREEN}Happy coding with PR Buddy! 🚀${NC}"

# Option to display the configuration
echo
if prompt_yes_no "Display the generated MCP configuration now?" "y"; then
    echo
    echo -e "${BOLD}Generated MCP Configuration:${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    cat "$MCP_CONFIG"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
fi

# Create a test script for later use
TEST_SCRIPT="$CONFIG_DIR/test_connection.sh"
cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash

source ~/.pr-buddy/.env

echo "Testing PR Buddy connections..."

# Test GitHub
if [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo -n "GitHub: "
    # Determine the correct API endpoint based on the GitHub host
    if [ "$GITHUB_HOST" = "https://github.com" ]; then
        API_ENDPOINT="${GITHUB_HOST}/user"
    else
        # GitHub Enterprise uses /api/v3 prefix
        API_ENDPOINT="${GITHUB_HOST}/api/v3/user"
    fi
    
    if curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
         "$API_ENDPOINT" 2>/dev/null | grep -q "login"; then
        echo "✅ Connected"
    else
        echo "❌ Failed"
    fi
fi

# Test Jira
if [ -n "$JIRA_API_TOKEN" ]; then
echo -n "Jira: "
    if curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
         "$JIRA_BASE_URL/rest/api/3/myself" 2>/dev/null | grep -q "emailAddress"; then
        echo "✅ Connected"
    else
        echo "❌ Failed"
    fi
fi

echo "Done!"
EOF
chmod +x "$TEST_SCRIPT"

echo
print_info "Test your connections anytime with: ${CYAN}$TEST_SCRIPT${NC}"