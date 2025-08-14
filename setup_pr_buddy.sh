#!/bin/bash

# PR Buddy Setup Script
# This script automates the setup process for PR Buddy

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║            🚀 PR Buddy Setup Script 🚀                  ║"
echo "║                                                          ║"
echo "║    AI-Powered Pull Request Assistant Installation       ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo -en "${BLUE}$prompt [$default]: ${NC}"
    read -r input
    if [ -z "$input" ]; then
        eval "$var_name='$default'"
    else
        eval "$var_name='$input'"
    fi
}

# Function to prompt for secret input
prompt_secret() {
    local prompt="$1"
    local var_name="$2"
    
    echo -en "${BLUE}$prompt: ${NC}"
    read -rs input
    echo
    eval "$var_name='$input'"
}

# Check prerequisites
print_info "Checking prerequisites..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    if [ "$(echo "$PYTHON_VERSION >= 3.10" | bc)" -eq 1 ]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Git
if command_exists git; then
    print_success "Git found"
else
    print_error "Git not found. Please install Git"
    exit 1
fi

# Check Docker (optional)
if command_exists docker; then
    print_success "Docker found (optional)"
    USE_DOCKER=true
else
    print_warning "Docker not found. Will use local installation for GitHub MCP server"
    USE_DOCKER=false
fi

# Install UV if not present
if ! command_exists uv; then
    print_info "Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env to get uv in PATH
    source "$HOME/.cargo/env" 2>/dev/null || true
    print_success "UV installed"
else
    print_success "UV already installed"
fi

# Create PR Buddy directory structure
print_info "Setting up directory structure..."
PR_BUDDY_HOME="${PR_BUDDY_HOME:-$HOME/.pr-buddy}"
mkdir -p "$PR_BUDDY_HOME"
mkdir -p "$PR_BUDDY_HOME/config"
mkdir -p "$PR_BUDDY_HOME/logs"
mkdir -p "$PR_BUDDY_HOME/rules"

# Get the current directory (where servers are located)
SERVERS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Initialize submodules if needed
print_info "Initializing git submodules..."
git submodule update --init --recursive
print_success "Submodules initialized"

# Install each MCP server
print_info "Installing MCP servers..."

# CVE Search Server
if [ -d "$SERVERS_DIR/servers/cve-search" ]; then
    print_info "Setting up CVE Search server..."
    cd "$SERVERS_DIR/servers/cve-search"
    uv sync
    print_success "CVE Search server installed"
fi

# Git Server
if [ -d "$SERVERS_DIR/servers/git" ]; then
    print_info "Setting up Git server..."
    cd "$SERVERS_DIR/servers/git"
    uv sync
    print_success "Git server installed"
fi

# Jira Server
if [ -d "$SERVERS_DIR/servers/jira-mcp" ]; then
    print_info "Setting up Jira server..."
    cd "$SERVERS_DIR/servers/jira-mcp"
    uv sync
    print_success "Jira server installed"
fi

# GitHub Server
if [ "$USE_DOCKER" = true ]; then
    print_info "Pulling GitHub MCP server Docker image..."
    docker pull ghcr.io/github/github-mcp-server
    print_success "GitHub server Docker image ready"
else
    if [ -d "$SERVERS_DIR/servers/github-mcp-server" ]; then
        print_info "Building GitHub server from source..."
        cd "$SERVERS_DIR/servers/github-mcp-server"
        if command_exists go; then
            go build -o github-mcp-server cmd/github-mcp-server/main.go
            print_success "GitHub server built"
        else
            print_warning "Go not found. Skipping GitHub server build"
        fi
    fi
fi

# Configure environment variables
print_info "Configuring environment variables..."
echo
echo "Please provide the following configuration details:"
echo

# GitHub Configuration
prompt_with_default "GitHub hostname" "https://github.com" GITHUB_HOST
prompt_secret "GitHub Personal Access Token (ghp_...)" GITHUB_TOKEN

# Jira Configuration
prompt_with_default "Jira base URL" "https://yourcompany.atlassian.net" JIRA_BASE_URL
prompt_with_default "Jira email" "your-email@company.com" JIRA_EMAIL
prompt_secret "Jira API token" JIRA_TOKEN

# Default repository
prompt_with_default "Default Git repository path" "$(pwd)" DEFAULT_GIT_REPO

# Create .env file
cat > "$PR_BUDDY_HOME/config/.env" << EOF
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
DEFAULT_GIT_REPO="${DEFAULT_GIT_REPO}"

# Server Paths
PR_BUDDY_HOME="${PR_BUDDY_HOME}"
SERVERS_DIR="${SERVERS_DIR}"
EOF

print_success "Environment configuration saved"

# Copy PR rules
print_info "Installing PR Buddy rules..."

# Check if rules exist in the expected location
RULES_SOURCE="/Users/ardas/Documents/Cloudera/src/github.infra.cloudera.com/cloudera-sense/.cursor/rules"
if [ -d "$RULES_SOURCE" ]; then
    cp "$RULES_SOURCE"/*.mdc "$PR_BUDDY_HOME/rules/" 2>/dev/null || true
    print_success "PR rules copied"
else
    print_warning "PR rules not found at expected location. Please copy them manually."
fi

# Generate Cursor configuration
print_info "Generating Cursor configuration..."

CURSOR_CONFIG="$PR_BUDDY_HOME/config/cursor_mcp_settings.json"

cat > "$CURSOR_CONFIG" << EOF
{
  "mcpServers": {
    "pr-buddy-cve": {
      "command": "uv",
      "args": [
        "--directory",
        "${SERVERS_DIR}/servers/cve-search",
        "run",
        "python",
        "main.py"
      ],
      "name": "CVE Security Scanner",
      "description": "Scans for vulnerabilities and CVEs in PR dependencies"
    },
    "pr-buddy-git": {
      "command": "uv",
      "args": [
        "--directory", 
        "${SERVERS_DIR}/servers/git",
        "run",
        "mcp-server-git",
        "--repository",
        "${DEFAULT_GIT_REPO}"
      ],
      "name": "Git Operations",
      "description": "Handles local git operations and branch management"
    },
EOF

if [ "$USE_DOCKER" = true ]; then
    cat >> "$CURSOR_CONFIG" << EOF
    "pr-buddy-github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_TOKEN}",
        "-e",
        "GITHUB_TOOLSETS=repos,issues,pull_requests,actions,code_security",
        "ghcr.io/github/github-mcp-server"
      ],
      "name": "GitHub Integration",
      "description": "Manages GitHub PRs, issues, and repository operations"
    },
EOF
else
    cat >> "$CURSOR_CONFIG" << EOF
    "pr-buddy-github": {
      "command": "${SERVERS_DIR}/servers/github-mcp-server/github-mcp-server",
      "args": ["stdio"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      },
      "name": "GitHub Integration",
      "description": "Manages GitHub PRs, issues, and repository operations"
    },
EOF
fi

cat >> "$CURSOR_CONFIG" << EOF
    "pr-buddy-jira": {
      "command": "uv",
      "args": [
        "--directory",
        "${SERVERS_DIR}/servers/jira-mcp",
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
  }
}
EOF

print_success "Cursor configuration generated"

# Test installations
print_info "Testing installations..."

# Test CVE server
if uv run --directory "$SERVERS_DIR/servers/cve-search" python -c "import mcp_server_cve_search" 2>/dev/null; then
    print_success "CVE server test passed"
else
    print_warning "CVE server test failed"
fi

# Test Git server
if uv run --directory "$SERVERS_DIR/servers/git" python -c "import mcp_server_git" 2>/dev/null; then
    print_success "Git server test passed"
else
    print_warning "Git server test failed"
fi

# Test Jira server
if uv run --directory "$SERVERS_DIR/servers/jira-mcp" python -c "import jira_mcp_server" 2>/dev/null; then
    print_success "Jira server test passed"
else
    print_warning "Jira server test failed"
fi

# Create helper scripts
print_info "Creating helper scripts..."

# Start script
cat > "$PR_BUDDY_HOME/start_pr_buddy.sh" << 'EOF'
#!/bin/bash
source ~/.pr-buddy/config/.env
echo "Starting PR Buddy servers..."
# Add startup commands here if needed
echo "PR Buddy ready! Open Cursor and enable Agent Mode."
EOF
chmod +x "$PR_BUDDY_HOME/start_pr_buddy.sh"

# Test script
cat > "$PR_BUDDY_HOME/test_pr_buddy.sh" << 'EOF'
#!/bin/bash
source ~/.pr-buddy/config/.env
echo "Testing PR Buddy connections..."

# Test GitHub
echo -n "GitHub: "
curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
  https://api.github.com/user | jq -r .login || echo "Failed"

# Test Jira
echo -n "Jira: "
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself" | jq -r .displayName || echo "Failed"

echo "Tests complete."
EOF
chmod +x "$PR_BUDDY_HOME/test_pr_buddy.sh"

# Final instructions
echo
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║         🎉 PR Buddy Setup Complete! 🎉                  ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo

print_info "Next steps:"
echo
echo "1. Copy Cursor configuration to your Cursor settings:"
echo "   ${BLUE}cp $CURSOR_CONFIG ~/.cursor/mcp_settings.json${NC}"
echo
echo "2. Copy PR rules to your project or Cursor directory:"
echo "   ${BLUE}cp $PR_BUDDY_HOME/rules/*.mdc .cursor/rules/${NC}"
echo
echo "3. Test your setup:"
echo "   ${BLUE}$PR_BUDDY_HOME/test_pr_buddy.sh${NC}"
echo
echo "4. Open Cursor and enable Agent Mode"
echo
echo "5. Start using PR Buddy with commands like:"
echo "   ${BLUE}@agent Create a PR for my changes${NC}"
echo "   ${BLUE}@agent Review PR #123${NC}"
echo
print_success "Configuration files saved to: $PR_BUDDY_HOME"
print_success "Cursor config available at: $CURSOR_CONFIG"
echo
print_info "For more information, see README.md"
echo
echo "Happy coding with PR Buddy! 🚀"
