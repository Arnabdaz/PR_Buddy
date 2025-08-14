#!/bin/bash
# Test script to show JSON output with proper quotation

SERVERS_DIR="/path/to/pr-buddy/servers"
DEFAULT_GIT_REPO="/path/to/my/repo"

echo "When DEFAULT_GIT_REPO is set:"
echo "=============================="

cat << JSON
    "pr-buddy-git": {
      "command": "uv",
      "args": [
        "--directory", 
        "${SERVERS_DIR}/git",
        "run",
        "mcp-server-git",
        "--repository",
        "${DEFAULT_GIT_REPO}"
      ],
      "name": "Git Operations",
      "description": "Handles local git operations and branch management"
    }
JSON

echo ""
echo "When DEFAULT_GIT_REPO is empty:"
echo "================================"

DEFAULT_GIT_REPO=""

cat << JSON
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
    }
JSON
