"""
Eclair MCP Server

Main server implementation using FastMCP to provide dataset tools via MCP protocol.
"""
import argparse
import asyncio
import logging
import json
import os
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from .tools import (
    validate_croissant,
    download_dataset,
    get_datasets_preview_url,
    search_datasets,
    get_help,
    get_dataset_metadata,
    ping,
    cleanup
)

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class EclairServer:
    """Eclair MCP Server for dataset operations."""
    
    def __init__(self, config_path: str = None):
        """Initialize the Eclair server with configuration."""
        self.config = self._load_config(config_path)
        self.server_name = self.config.get("name", "Eclair Dataset MCP Server")
        self.mcp = FastMCP(self.server_name)
        self._setup_tools()
        
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from config.json."""
        if config_path is None:
            # Look for config.json in the current working directory
            config_path = "config.json"
            
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {config_path}: {e}. Using defaults.")
            return {}
    
    def _setup_tools(self):
        """Setup MCP tools for the server."""
        
        @self.mcp.tool("validate-croissant", description="Validate a Croissant metadata file")
        async def validate_croissant_tool(metadata_json: Dict[str, Any]) -> Dict[str, Any]:
            """Validate a Croissant metadata file."""
            return await validate_croissant(metadata_json)

        @self.mcp.tool("download-dataset", description="Download a dataset")
        async def download_dataset_tool(collection: str, dataset: str) -> Dict[str, Any]:
            """Download a dataset."""
            return await download_dataset(collection, dataset)

        @self.mcp.tool("datasets-preview-url", description="Get a download url for a dataset preview")
        async def datasets_preview_url_tool(collection: str, dataset: str) -> str:
            """Get a download url for a dataset preview."""
            return await get_datasets_preview_url(collection, dataset)

        @self.mcp.tool("search-datasets", description="Search for datasets using a query string")
        async def search_datasets_tool(query: str) -> List[Dict[str, Any]]:
            """Search for datasets using a query string."""
            return await search_datasets(query)

        @self.mcp.tool("help", description="Get help for the Eclair Dataset MCP server")
        async def help_tool() -> str:
            """Get help for the Eclair Dataset MCP server."""
            return await get_help()

        @self.mcp.tool("serve-croissant", description="Get the Croissant dataset metadata")
        async def get_dataset_metadata_tool(collection: str, dataset: str) -> Dict[str, Any]:
            """Get the Croissant dataset metadata."""
            return await get_dataset_metadata(collection, dataset)

        @self.mcp.tool("ping", description="Test that the Eclair server is working")
        async def ping_tool() -> str:
            """Simple ping test to verify the Eclair server is working."""
            return await ping()

        # Debug prompt
        @self.mcp.prompt()
        def debug_error(error: str) -> List[base.Message]:
            return [
                base.UserMessage("I'm seeing this error:"),
                base.UserMessage(error),
                base.AssistantMessage("I'll help debug that. What have you tried so far?"),
            ]
    
    def run(self, host: str = None, port: int = None, transport: str = None):
        """Run the Eclair server."""
        # Get values from config or use defaults
        host = host or self.config.get("server", {}).get("host", "0.0.0.0")
        port = port or self.config.get("server", {}).get("port", 8080)
        transport = transport or self.config.get("server", {}).get("transport", "streamable-http")
        
        # Configure the server
        self.mcp.settings.port = port
        self.mcp.settings.host = host

        # Print configuration
        url = f"http://{host}:{port}/mcp" if transport != "stdio" else "stdio"
        print(f"🖥️ Server name:     {self.mcp.name}")
        print(f"📦 Transport:       {transport}")
        print(f"☁️ Server URL:      {url}")
        print(f"☁️ Upstream MCP:    {self.config.get('upstream_server', {}).get('url', 'Not configured')}")
        print("")

        try:
            # Run the server with specified transport
            self.mcp.run(transport=transport)
        finally:
            # Cleanup on shutdown
            asyncio.run(cleanup())


def main():
    """CLI entry point for the server."""
    def print_welcome():
        """Print the colorful Eclair welcome message."""
        # ANSI color codes for gradient (blue to red)
        def get_gradient_color(pos, total_width):
            # Blue to red gradient
            factor = pos / (total_width - 1) if total_width > 1 else 0
            r = int(70 * (1 - factor) + 255 * factor)
            g = int(130 * (1 - factor) + 105 * factor)  
            b = int(255 * (1 - factor) + 97 * factor)
            return f"\033[38;2;{r};{g};{b}m"
        
        reset = "\033[0m"
        lines = [
            "     ______       __        _        ",
            "    / ____/ ____ / / _____ (_) ____  ",
            "   / __/  / ___// // __  // // ___/ ",
            "  / /___ / /__ / // /_/ // // /      ",
            " /_____/ \\___//_/ \\__,_//_//_/       ",
            "",
            " Helping AI models work with datasets",
            " (with a little help from Croissant) ",
            ""
        ]
        
        for line in lines:
            if line.strip():  # Skip empty lines for coloring
                colored_line = ""
                for i, char in enumerate(line):
                    if char == " ":
                        colored_line += " "
                    else:
                        color = get_gradient_color(i, 40)  # 40 is max width
                        colored_line += f"{color}{char}{reset}"
                print(colored_line)
            else:
                print()
    
    print_welcome()
    
    parser = argparse.ArgumentParser(description="Run Eclair MCP Server")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to listen on")
    parser.add_argument("--transport", help="Transport mode (stdio, sse, or streamable-http)")
    parser.add_argument("--config", help="Path to config file")
    args = parser.parse_args()

    server = EclairServer(config_path=args.config)
    server.run(host=args.host, port=args.port, transport=args.transport)


if __name__ == "__main__":
    main()
