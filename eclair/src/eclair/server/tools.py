"""
Eclair Server Tools

MCP tool implementations that relay to upstream servers.
"""
import logging
import json
import os
from typing import Any, Dict, List
from fastmcp import Client
from .validation import validate

# Configure logging
logger = logging.getLogger(__name__)

class MCPRelay:
    """Relay MCP tool calls to the upstream server using proper MCP streamable-http protocol."""
    
    def __init__(self, upstream_url: str):
        self.upstream_url = upstream_url
        self.client = None
    
    async def ensure_client(self):
        """Ensure we have an MCP client available."""
        if self.client is None:
            self.client = Client(self.upstream_url)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Relay a tool call to the upstream MCP server using proper MCP protocol."""
        await self.ensure_client()
        
        try:
            logger.info(f"Relaying tool call {tool_name} to upstream server via MCP")
            
            # Use proper MCP client to call the tool
            async with self.client:
                result = await self.client.call_tool(tool_name, arguments)
                
                # Extract the actual content from the CallToolResult
                if hasattr(result, 'content') and result.content:
                    # Collect all text results from all content items
                    all_text = []
                    for item in result.content:
                        if item.text:
                            text_result = item.text
                            try:
                                if text_result.strip().startswith('['):
                                    # If it's a JSON array, parse and extend
                                    parsed = json.loads(text_result)
                                    if isinstance(parsed, list):
                                        all_text.extend(parsed)
                                    else:
                                        all_text.append(parsed)
                                elif text_result.strip().startswith('{'):
                                    # If it's a JSON object, parse and append
                                    all_text.append(json.loads(text_result))
                                else:
                                    all_text.append(text_result)
                            except json.JSONDecodeError:
                                all_text.append(text_result)
                    # If only one result, return it; else return all
                    if len(all_text) == 1:
                        return all_text[0]
                    return all_text
                elif hasattr(result, 'structured_content'):
                    return result.structured_content
                else:
                    return str(result)
                
        except Exception as e:
            logger.error(f"Error calling upstream MCP server: {e}")
            return {"error": f"Failed to connect to upstream MCP server: {str(e)}"}
    
    async def close(self):
        """Close the MCP client."""
        # The fastmcp Client handles its own cleanup in the async context manager
        self.client = None


def _load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.json")
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        # Configuration for the upstream mlcbakery server
        upstream_url = config.get("upstream_server", {}).get("url", "https://mcp.jetty.io/mcp")
        logger.info(f"Using upstream server URL from config: {upstream_url}")
        return upstream_url
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading configuration: {e}")
        # Default configuration for the upstream mlcbakery server
        upstream_url = "https://mcp.jetty.io/mcp"
        logger.warning(f"Using default upstream server URL: {upstream_url}")
        return upstream_url

# Create the relay instance
UPSTREAM_SERVER_URL = _load_config()
relay = MCPRelay(UPSTREAM_SERVER_URL)

# Tool functions 
async def validate_croissant(metadata_json: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a Croissant metadata file using local validation."""
    try:
        # Convert the metadata to JSON string for validation
        json_string = json.dumps(metadata_json)
        
        # Run local validation
        results = validate(json_string)
        
        # Format the response
        validation_result = {
            "valid": all(result[1] for result in results if result[3] in ["pass", "warning"]),
            "results": [
                {
                    "test": result[0],
                    "passed": result[1],
                    "message": result[2],
                    "status": result[3]
                } for result in results
            ]
        }
        
        logger.info("Croissant validation completed locally")
        return validation_result
        
    except Exception as e:
        logger.error(f"Error during local Croissant validation: {e}")
        return {
            "valid": False,
            "error": str(e),
            "results": [],
            "report": None
        }


async def download_dataset(collection: str, dataset: str) -> Dict[str, Any]:
    """Download a dataset."""
    return await relay.call_tool("download-dataset", {"collection": collection, "dataset": dataset})


async def get_datasets_preview_url(collection: str, dataset: str) -> str:
    """Get a download url for a dataset preview."""
    result = await relay.call_tool("datasets-preview-url", {"collection": collection, "dataset": dataset})
    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"
    return str(result)

async def search_datasets(query: str) -> List[Dict[str, Any]]:
    """Search for datasets using a query string."""
    result = await relay.call_tool("search-datasets", {"query": query})
    if isinstance(result, dict) and "error" in result:
        return [{"error": result["error"]}]
    return result if isinstance(result, list) else [result]

async def get_help() -> str:
    """Get help for the Eclair Dataset MCP server."""
    # Read cached help content from file instead of relaying to upstream
    help_file_path = os.path.join(os.path.dirname(__file__), "context", "help.md")
    
    try:
        with open(help_file_path, 'r', encoding='utf-8') as f:
            help_content = f.read()
        logger.info("Served cached help content from local file")
        return help_content
    except FileNotFoundError:
        logger.warning(f"Help content file not found at {help_file_path}, falling back to upstream")
        # Fallback to upstream server if file doesn't exist
        result = await relay.call_tool("help", {})
        if isinstance(result, dict) and "error" in result:
            return f"Error: {result['error']}"
        return str(result)
    except Exception as e:
        logger.error(f"Error reading help content file: {e}")
        return f"Error loading help content: {str(e)}"

async def get_dataset_metadata(collection: str, dataset: str) -> Dict[str, Any]:
    """Get the Croissant dataset metadata."""
    return await relay.call_tool("dataset/mlcroissant", {"collection": collection, "dataset": dataset})

async def ping() -> str:
    """Simple ping test to verify the Eclair server is working."""
    return "Pong! Eclair MCP Server is running successfully."

async def cleanup():
    """Cleanup resources on shutdown."""
    await relay.close()
