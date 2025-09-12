"""
Eclair MCP Client

Base client for interacting with Eclair MCP servers.
"""
import asyncio
from typing import Any, Dict, Optional
from fastmcp import Client


class EclairClient:
    """Base client for interacting with Eclair MCP servers."""
    
    def __init__(self, server_url: str = "http://localhost:8080/mcp"):
        self.server_url = server_url
        self.client = None
        
    async def initialize(self):
        """Initialize the MCP client."""
        self.client = Client(self.server_url)

    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Call a tool on the Eclair server."""
        if arguments is None:
            arguments = {}
            
        if self.client is None:
            await self.initialize()
            
        async with self.client:
            return await self.client.call_tool(tool_name, arguments)
    
    async def search_datasets(self, query: str):
        """Search for datasets using a query string."""
        return await self.call_tool("search-datasets", {"query": query})
    
    async def download_dataset(self, collection: str, dataset: str):
        """Download a dataset."""
        return await self.call_tool("download-dataset", {"collection": collection, "dataset": dataset})
    
    async def datasets_preview_url(self, collection: str, dataset: str):
        """Get a download URL for a dataset preview."""
        return await self.call_tool("datasets-preview-url", {"collection": collection, "dataset": dataset})
    
    async def serve_croissant(self, collection: str, dataset: str):
        """Get the Croissant dataset metadata."""
        return await self.call_tool("serve-croissant", {"collection": collection, "dataset": dataset})
    
    async def validate_croissant(self, metadata_json: Dict[str, Any]):
        """Validate a Croissant metadata file."""
        return await self.call_tool("validate-croissant", {"metadata_json": metadata_json})
    
    async def get_help(self):
        """Get help for the MLC Bakery API."""
        return await self.call_tool("help")
    
    async def ping(self):
        """Test that the Eclair server is working."""
        return await self.call_tool("ping")


async def main():
    """Simple example of using the Eclair client."""
    client = EclairClient()
    
    try:
        # Test basic connectivity
        result = await client.ping()
        print(f"Ping result: {result}")
        
        # Search for datasets
        datasets = await client.search_datasets("image classification")
        print(f"Found {len(datasets) if isinstance(datasets, list) else 1} datasets")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
