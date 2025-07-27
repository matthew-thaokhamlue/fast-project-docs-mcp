"""
FastMCP server implementation for the Document Generator.

This module sets up the MCP server with proper configuration,
tool registration, and transport support.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.server.sse import sse_server

from ..services.document_generator import DocumentGeneratorService
from ..templates.manager import TemplateManager
from .tools import register_tools


logger = logging.getLogger(__name__)


class DocumentGeneratorMCPServer:
    """MCP server for document generation."""
    
    def __init__(self, 
                 output_directory: Optional[Path] = None,
                 custom_templates_path: Optional[Path] = None,
                 server_name: str = "Document Generator",
                 server_version: str = "0.1.0"):
        """Initialize the MCP server."""
        self.output_directory = output_directory or Path.cwd()
        self.custom_templates_path = custom_templates_path
        self.server_name = server_name
        self.server_version = server_version
        
        # Initialize FastMCP server
        self.mcp = FastMCP(server_name)
        
        # Initialize services
        self._initialize_services()
        
        # Register tools
        self._register_tools()
        
        # Register resources
        self._register_resources()
    
    def _initialize_services(self) -> None:
        """Initialize all required services."""
        try:
            # Initialize template manager
            template_manager = TemplateManager(self.custom_templates_path)
            
            # Initialize document generator service
            self.document_service = DocumentGeneratorService(
                template_manager=template_manager,
                output_directory=self.output_directory
            )
            
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _register_tools(self) -> None:
        """Register all MCP tools."""
        try:
            register_tools(self.mcp, self.document_service)
            logger.info("Tools registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register tools: {e}")
            raise
    
    def _register_resources(self) -> None:
        """Register MCP resources."""
        @self.mcp.resource("reference://resources")
        def get_resource_summary() -> str:
            """Get summary of analyzed reference resources"""
            try:
                # This would return a summary of the last analyzed resources
                return "Reference resources summary - use analyze_resources tool for detailed analysis"
            except Exception as e:
                logger.error(f"Failed to get resource summary: {e}")
                return f"Error getting resource summary: {str(e)}"
        
        logger.info("Resources registered successfully")
    
    async def run_stdio(self) -> None:
        """Run the server with STDIO transport."""
        logger.info("Starting MCP server with STDIO transport")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.mcp.run(
                    read_stream, 
                    write_stream,
                    self.mcp.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"STDIO server error: {e}")
            raise
    
    async def run_sse(self, host: str = "localhost", port: int = 8000) -> None:
        """Run the server with SSE transport."""
        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")
        
        try:
            async with sse_server(host, port) as server:
                await server.serve()
        except Exception as e:
            logger.error(f"SSE server error: {e}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": self.server_name,
            "version": self.server_version,
            "output_directory": str(self.output_directory),
            "custom_templates_path": str(self.custom_templates_path) if self.custom_templates_path else None,
            "capabilities": {
                "document_types": ["prd", "spec", "design"],
                "transports": ["stdio", "sse"],
                "features": [
                    "document_generation",
                    "resource_analysis", 
                    "template_customization",
                    "multi_format_processing"
                ]
            }
        }


def create_server_from_config(config: Dict[str, Any]) -> DocumentGeneratorMCPServer:
    """Create server instance from configuration."""
    output_dir = None
    if config.get('output_directory'):
        output_dir = Path(config['output_directory'])
    
    templates_path = None
    if config.get('custom_templates_path'):
        templates_path = Path(config['custom_templates_path'])
    
    return DocumentGeneratorMCPServer(
        output_directory=output_dir,
        custom_templates_path=templates_path,
        server_name=config.get('server_name', 'Document Generator'),
        server_version=config.get('server_version', '0.1.0')
    )


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )


async def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Document Generator MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"], 
        default="stdio",
        help="Transport protocol to use"
    )
    parser.add_argument(
        "--host", 
        default="localhost",
        help="Host for SSE transport"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port for SSE transport"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path,
        help="Output directory for generated documents"
    )
    parser.add_argument(
        "--templates-dir", 
        type=Path,
        help="Directory containing custom templates"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create server
    server = DocumentGeneratorMCPServer(
        output_directory=args.output_dir,
        custom_templates_path=args.templates_dir
    )
    
    logger.info(f"Server info: {server.get_server_info()}")
    
    # Run server with specified transport
    try:
        if args.transport == "stdio":
            await server.run_stdio()
        elif args.transport == "sse":
            await server.run_sse(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
