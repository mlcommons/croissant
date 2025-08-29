"""
Claude MCP Client

Client that connects Claude to the Eclair MCP Server.
"""
import json
import os
import warnings
from typing import Optional

from fastmcp import Client

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables only
    pass


class ClaudeMCPClient:
    """Client that connects Claude to the Eclair MCP Server."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080/mcp", claude_api_key: Optional[str] = None):
        if not CLAUDE_AVAILABLE:
            raise ImportError("anthropic is not installed. Install it with: pip install anthropic")
            
        self.mcp_server_url = mcp_server_url
        self.claude_api_key = claude_api_key or os.getenv("CLAUDE_API_KEY")
        self.mcp_client = None
        self.claude_client = None
        
        # Load configuration from config.json
        self._load_config()
        
        # Load system prompt from claude.md
        self._load_system_prompt()
        
    def _load_config(self):
        """Load configuration from config.json file."""
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            claude_config = config.get('claude', {})
            self.model_name = claude_config.get('model', 'claude-3-5-sonnet-20241022')
            self.default_temperature = claude_config.get('temperature', 0.3)
            self.max_tokens = claude_config.get('max_tokens', 4096)
            
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
            # Use defaults
            self.model_name = "claude-3-5-sonnet-20241022"
            self.default_temperature = 0.3
            self.max_tokens = 4096
    
    def _load_system_prompt(self):
        """Load system prompt from claude.md file."""
        system_prompt_path = os.path.join(os.path.dirname(__file__), "claude.md")
        try:
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract the main prompt content, removing markdown headers
            # Keep the core instructions but clean up formatting
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Skip markdown headers but keep the content
                if line.startswith('#'):
                    continue
                cleaned_lines.append(line)
            
            self.system_prompt = '\n'.join(cleaned_lines).strip()
            return True
            
        except Exception as e:
            print(f"Warning: Could not load system prompt from claude.md: {e}")
            # Use a basic fallback prompt
            self.system_prompt = """You are a helpful data scientist AI assistant. You have access to MCP tools for finding and analyzing datasets. Always try to use the available tools to search for and analyze real data to answer user questions."""
            return False
        
    async def initialize(self):
        """Initialize both MCP and Claude clients."""
        # Initialize MCP client to connect to our Eclair server
        self.mcp_client = Client(self.mcp_server_url)
        
        # Initialize Claude client if API key is available
        if self.claude_api_key:
            # This would initialize the Claude client
            # self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
            pass
        else:
            print("No Claude API key found. Only MCP functionality will be available.")
    
    async def close(self):
        """Clean up resources."""
        # The MCP client will be closed automatically when exiting the context manager
        # Claude client doesn't need explicit cleanup
        pass

    async def ask_claude_with_tools(self, prompt: str, temperature: Optional[float] = None):
        """Use Claude with MCP tools and system prompt."""
        if not self.claude_client:
            raise ValueError("Claude client not available (no API key)")
        
        # Use provided temperature or default from config
        temp = temperature if temperature is not None else self.default_temperature
            
        async with self.mcp_client:
            try:
                # Create the full conversation with system prompt embedded in user message
                full_prompt = f"""{self.system_prompt}

---

User Request: {prompt}

Available MCP Tools:
- search-datasets: Search for datasets using a query string
- serve-croissant: Get Croissant metadata for a dataset
- download-dataset: Download dataset files
- datasets-preview-url: Get preview URLs for datasets
- validate-croissant: Validate Croissant metadata

Instructions: Follow your data scientist workflow by searching for relevant datasets and analyzing their metadata based on the user's request."""

                # This would use Claude to generate a response
                # response = self.claude_client.messages.create(
                #     model=self.model_name,
                #     max_tokens=self.max_tokens,
                #     temperature=temp,
                #     system=self.system_prompt,
                #     messages=[{"role": "user", "content": full_prompt}]
                # )
                # return response.content[0].text
                
                # Placeholder for now
                return "Claude integration not yet implemented. Install anthropic package and implement."
                
            except Exception as e:
                return f"⚠️ Claude API error: {e}"

    async def search_datasets(self, query: str) -> dict:
        """Search for datasets using the MCP server."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("search-datasets", {"query": query})

    async def serve_croissant(self, collection: str, dataset: str) -> dict:
        """Get Croissant metadata for a specific dataset."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("serve-croissant", {
                "collection": collection,
                "dataset": dataset
            })

    async def download_dataset(self, collection: str, dataset: str) -> dict:
        """Download a dataset."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("download-dataset", {
                "collection": collection,
                "dataset": dataset
            })

    async def datasets_preview_url(self, collection: str, dataset: str) -> dict:
        """Get preview URL for a dataset."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("datasets-preview-url", {
                "collection": collection,
                "dataset": dataset
            })

    async def validate_croissant(self, metadata_json: dict) -> dict:
        """Validate Croissant metadata."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("validate-croissant", {"metadata_json": metadata_json})

    async def ping(self) -> dict:
        """Ping the MCP server."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("ping")

    async def get_help(self) -> dict:
        """Get help information from the MCP server."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("help")

    async def call_mcp_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Generic method to call any MCP tool."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool(tool_name, arguments or {})


# Example usage (only if running this file directly)
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            client = ClaudeMCPClient()
            await client.initialize()
            
            # Example: Search for datasets
            print("Searching for image datasets...")
            results = await client.search_datasets("image classification")
            print(f"Found datasets: {results}")
            
            await client.close()
        except ImportError as e:
            print(f"Claude client not available: {e}")
    
    asyncio.run(main())
