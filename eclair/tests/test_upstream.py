from fastmcp import Client
import asyncio
import sys
import json
import os
import pytest


async def upstream_connection_test():
    """Test function to check if the MCP client can connect to upstream server."""
    try:
        # Load upstream server URL from config.json
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        upstream_url = config['upstream_server']['url']
        
        mcp_client = Client(upstream_url)
        async with mcp_client:
            result = await mcp_client.call_tool("help")
            print("✅ Successfully connected to MCP server! Here's the start of the help response:")
            print(f"\033[92m{result.content[0].text}\033[0m")
        return True
    except TimeoutError:
        print("❌ Error: Connection to MCP server timed out. Please check if the server is running and accessible.")
        return False
    except ConnectionError:
        print("❌ Error: Failed to connect to MCP server. Please check your network connection and server URL.")
        return False
    except Exception as e:
        print(f"❌ Error: An unexpected error occurred: {str(e)}")
        return False


@pytest.mark.asyncio
async def test_upstream_mcp_connection():
    """Pytest test for upstream MCP server connectivity."""
    success = await upstream_connection_test()
    assert success, "Failed to connect to upstream MCP server"


# Allow running as standalone script
if __name__ == "__main__":
    success = asyncio.run(upstream_connection_test())
    if not success:
        sys.exit(1)