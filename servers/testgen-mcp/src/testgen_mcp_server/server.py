"""Testgen MCP Server — entry point."""

from __future__ import annotations

import argparse
import logging

from .app import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import tools module to trigger @mcp.tool() registration via side effects
from . import tools  # noqa: E402, F401


def main() -> None:
    """Parse CLI arguments and start the MCP server."""
    parser = argparse.ArgumentParser(description="Testgen MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport mechanism (default: stdio)",
    )
    args = parser.parse_args()
    logger.info("Starting Testgen MCP Server with %s transport", args.transport)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
