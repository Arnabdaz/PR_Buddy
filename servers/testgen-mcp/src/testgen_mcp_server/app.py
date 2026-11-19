"""FastMCP application instance — imported by both server.py and tools.py."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("testgen-mcp")
