# 🔧 Troubleshooting Guide

This guide helps you resolve common issues with PR Buddy installation and usage.

## Table of Contents

- [Installation Issues](#installation-issues)
- [MCP Server Issues](#mcp-server-issues)
- [Authentication Problems](#authentication-problems)
- [Cursor Integration Issues](#cursor-integration-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)
- [Debug Mode](#debug-mode)

## Installation Issues

### UV Package Manager Not Found

**Problem**: `uv: command not found`

**Solution**:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if not automatic)
source "$HOME/.cargo/env"

# Verify
uv --version
```

### Git Submodules Not Initialized

**Problem**: Server directories are empty

**Solution**:

```bash
# Initialize and update submodules
git submodule init
git submodule update --recursive

# Or clone with submodules
git clone --recursive https://github.com/YOUR_USERNAME/pr-buddy.git
```

### Python Version Too Old

**Problem**: `Python 3.10+ required`

**Solution**:

```bash
# macOS
brew install python@3.10

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.10

# Verify
python3 --version
```

### Go Build Fails for GitHub Server

**Problem**: GitHub server build fails

**Solution**:

```bash
# Install Go 1.21+
brew install go  # macOS
# Or download from https://go.dev/dl/

# Rebuild
cd servers/github-mcp-server
go mod download
go build -o github-mcp-server cmd/github-mcp-server/main.go

# Alternative: Use Docker
docker pull ghcr.io/github/github-mcp-server
```

## MCP Server Issues

### Server Not Starting

**Problem**: MCP servers fail to start in Cursor

**Diagnosis**:

```bash
# Check MCP logs
tail -f ~/Library/Logs/Cursor/mcp*.log  # macOS
tail -f ~/.config/Cursor/logs/mcp*.log  # Linux

# Test server manually
uv --directory servers/cve-search run python main.py
```

**Common Solutions**:

1. Check file paths in `~/.cursor/mcp.json`
2. Verify Python/UV installation
3. Check server dependencies: `cd servers/[server-name] && uv sync`

### Server Connection Timeout

**Problem**: `Server failed to respond within timeout`

**Solution**:

```json
// In ~/.cursor/mcp.json, increase timeout
{
  "mcpServers": {
    "pr-buddy-git": {
      "timeout": 30000,  // Increase from default 10000ms
      ...
    }
  }
}
```

### Multiple Server Instances

**Problem**: Multiple instances of the same server running

**Solution**:

```bash
# Kill all Python MCP servers
pkill -f "mcp-server"

# Kill specific server
pkill -f "mcp-server-git"

# Restart Cursor
```

## Authentication Problems

### GitHub Token Invalid

**Problem**: `Bad credentials` or `401 Unauthorized`

**Diagnosis**:

```bash
# Test token
curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
  https://api.github.com/user
```

**Solutions**:

1. Regenerate token: [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Check token permissions (needs `repo`, `workflow` scopes)
3. Verify no extra spaces/quotes in token
4. Update in `~/.pr-buddy/.env`

### Jira Connection Failed

**Problem**: Cannot connect to Jira

**Diagnosis**:

```bash
# Test connection
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/3/myself"
```

**Solutions**:

1. Verify base URL format: `https://company.atlassian.net`
2. Check API token is valid (not password)
3. Ensure email matches Jira account
4. Verify API access is enabled for your account

### GitHub Enterprise Issues

**Problem**: Cannot connect to GitHub Enterprise

**Solution**:

```bash
# Update configuration
export GITHUB_HOST="https://github.enterprise.com"

# Test with correct API path
curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
  "$GITHUB_HOST/api/v3/user"  # Note: /api/v3 for Enterprise
```

## Cursor Integration Issues

### Rules Not Working

**Problem**: `@pr-creation.mdc` not recognized

**Solutions**:

1. Check rules are installed:

   ```bash
   ls ~/.cursor/rules/pr-*.mdc
   ```

2. Reinstall rules:

   ```bash
   cp /path/to/pr-buddy/rules/*.mdc ~/.cursor/rules/
   ```

3. Restart Cursor

4. Enable Agent Mode: `Cmd+Shift+P` → "Toggle Agent Mode"

### MCP Servers Not Showing

**Problem**: Servers don't appear in Cursor

**Solutions**:

1. Verify MCP configuration:

   ```bash
   cat ~/.cursor/mcp.json | jq .  # Pretty print to check syntax
   ```

2. Check Cursor version supports MCP

3. Restart Cursor after configuration changes

### Context Window Errors

**Problem**: `Context window exceeded`

**Solution**:

- Break large PRs into smaller reviews
- Use specific file paths instead of wildcards
- Clear conversation history and start fresh

## Runtime Errors

### Rate Limiting

**Problem**: `API rate limit exceeded`

**Solutions**:

1. Check remaining quota:

   ```bash
   curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
     https://api.github.com/rate_limit
   ```

2. Wait for reset (usually 1 hour)

3. Use different token for different operations

4. Implement caching in workflow

### Memory Issues

**Problem**: High memory usage or crashes

**Solutions**:

```bash
# Monitor memory usage
top -o mem  # macOS
top -o %MEM  # Linux

# Limit server memory (example)
ulimit -v 2097152  # 2GB limit

# Restart problematic servers
pkill -f "mcp-server-[name]"
```

### File Permission Errors

**Problem**: `Permission denied` errors

**Solution**:

```bash
# Fix permissions
chmod 755 ~/.pr-buddy
chmod 600 ~/.pr-buddy/.env
chmod 755 ~/path/to/pr-buddy/setup_pr_buddy.sh
```

## Performance Issues

### Slow Server Response

**Diagnosis**:

```bash
# Time server response
time curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
  https://api.github.com/user
```

**Solutions**:

1. Use local build instead of Docker for GitHub server
2. Enable only needed toolsets:

   ```json
   {
     "env": {
       "GITHUB_TOOLSETS": "repos,pull_requests" // Not all toolsets
     }
   }
   ```

3. Check network connectivity
4. Clear cache if implemented

### High CPU Usage

**Problem**: Servers consuming too much CPU

**Solution**:

```bash
# Identify culprit
top -c

# Restart specific server
pkill -f "specific-server-name"

# Limit CPU usage
nice -n 10 uv run mcp-server-git  # Lower priority
```

## Debug Mode

### Enable Verbose Logging

**In MCP configuration** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "pr-buddy-git": {
      "env": {
        "MCP_LOG_LEVEL": "DEBUG",
        "PYTHONPATH": ".",
        "DEBUG": "true"
      }
    }
  }
}
```

### Debug Commands

```bash
# Test individual server
cd servers/cve-search
uv run python -m mcp_server_cve_search

# Check server health
curl http://localhost:3000/health  # If server exposes health endpoint

# Monitor file descriptors
lsof -p [PID]  # Check open files/connections

# Trace system calls
strace -p [PID]  # Linux
dtruss -p [PID]  # macOS (requires sudo)
```

### Log Locations

- **Cursor MCP Logs**:

  - macOS: `~/Library/Logs/Cursor/`
  - Linux: `~/.config/Cursor/logs/`
  - Windows: `%APPDATA%\Cursor\logs\`

- **Server Logs**: Check individual server directories for `.log` files

- **System Logs**:
  - macOS: `Console.app` or `/var/log/system.log`
  - Linux: `/var/log/syslog` or `journalctl`

## Getting Help

If these solutions don't resolve your issue:

1. **Check existing issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/pr-buddy/issues)

2. **Create detailed bug report** with:

   - Error messages (full text)
   - Steps to reproduce
   - System information: `uname -a`, `python3 --version`, `uv --version`
   - Relevant log files
   - Configuration files (remove sensitive tokens)

3. **Community Support**:
   - Discord: [Join our server](https://discord.gg/pr-buddy)
   - Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/pr-buddy/discussions)

## Quick Diagnostic Script

Save as `diagnose_pr_buddy.sh`:

```bash
#!/bin/bash

echo "PR Buddy Diagnostic Report"
echo "=========================="
echo

echo "System Information:"
uname -a
echo

echo "Python Version:"
python3 --version
echo

echo "UV Version:"
uv --version 2>/dev/null || echo "UV not found"
echo

echo "Go Version:"
go version 2>/dev/null || echo "Go not found"
echo

echo "Docker Version:"
docker --version 2>/dev/null || echo "Docker not found"
echo

echo "Git Version:"
git --version
echo

echo "Checking Servers:"
for server in cve-search git github-mcp-server jira-mcp; do
    if [ -d "servers/$server" ]; then
        echo "✓ $server directory exists"
    else
        echo "✗ $server directory missing"
    fi
done
echo

echo "Configuration Files:"
[ -f ~/.pr-buddy/.env ] && echo "✓ Environment file exists" || echo "✗ Environment file missing"
[ -f ~/.cursor/mcp.json ] && echo "✓ MCP config exists" || echo "✗ MCP config missing"
[ -d ~/.cursor/rules ] && echo "✓ Rules directory exists" || echo "✗ Rules directory missing"
echo

echo "Testing Connections:"
if [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    curl -s -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
      https://api.github.com/user > /dev/null 2>&1 && \
      echo "✓ GitHub connection OK" || echo "✗ GitHub connection failed"
fi

if [ -n "$JIRA_API_TOKEN" ]; then
    curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
      "$JIRA_BASE_URL/rest/api/3/myself" > /dev/null 2>&1 && \
      echo "✓ Jira connection OK" || echo "✗ Jira connection failed"
fi

echo
echo "Diagnostic complete!"
```
