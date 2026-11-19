#!/bin/bash
# Setup script for Testgen MCP Server (using uv)

echo "🚀 Setting up Testgen MCP Server with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Install dependencies with uv
echo "📥 Installing dependencies with uv..."
uv sync

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Point the server at your target repository (defaults to the current dir):"
echo "   export TESTGEN_REPO_ROOT='/path/to/cloudera-sense'"
echo "   export TESTGEN_SPEC_DIR='testspecs'        # optional (default: testspecs)"
echo "   export TESTGEN_COVERAGE_DIR='test-results' # optional (default: test-results)"
echo ""
echo "2. Run the MCP server:"
echo "   uv run testgen-mcp"
echo ""
echo "3. Run the tests:"
echo "   uv run pytest"
