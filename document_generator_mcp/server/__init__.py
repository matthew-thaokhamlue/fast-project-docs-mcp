"""
MCP server implementation for the Document Generator.

This module contains the FastMCP server setup and tool registration.
"""

from .mcp_server import DocumentGeneratorMCPServer
from .tools import register_tools

__all__ = [
    "DocumentGeneratorMCPServer",
    "register_tools",
]
