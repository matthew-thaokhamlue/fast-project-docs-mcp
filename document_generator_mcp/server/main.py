"""
Main entry point for the Document Generator MCP Server.

This module provides the main function that can be called from the command line
or used as a package entry point.
"""

import asyncio
import sys
from .mcp_server import main as server_main


def main():
    """Main entry point for the document generator MCP server."""
    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\nServer shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
