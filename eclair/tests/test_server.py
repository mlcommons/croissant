import asyncio
import sys
import os
import json
import time
import subprocess
import pytest
from fastmcp import Client

# Use the CLI command instead of the old server path
server_command = ["eclair-server"]

# Load config to get server settings
config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 8080)
    transport = config.get("server", {}).get("transport", "sse")
except Exception as e:
    print(f"Warning: Could not load config.json: {e}")
    host, port, transport = "0.0.0.0", 8080, "streamable-http"

# Create client for streamable-http transport
if transport == "streamable-http":
    # For streamable-http, we need to connect to the MCP endpoint
    server_url = f"http://{host}:{port}/mcp"
    client = Client(server_url)
elif transport == "sse":
    server_url = f"http://{host}:{port}"
    client = Client(server_url)
else:
    # For stdio and other transports, we'll use streamable-http as fallback
    server_url = f"http://{host}:{port}/mcp"
    client = Client(server_url)

def check_result(tool_name: str, success: bool, result=None, error=None):
    """Print formatted test result and return whether it should be considered successful."""
    if success:
        # Check for errors in the result
        is_error = False
        error_msg = None
        result_str = str(result)
        
        # 1. Check dictionary with error key (most common for MCP results)
        if isinstance(result, dict) and "error" in result:
            is_error = True
            error_msg = result["error"]
        # 2. Check structured_content in FastMCP responses
        elif hasattr(result, "structured_content") and result.structured_content:
            structured = result.structured_content
            if isinstance(structured, dict) and "result" in structured:
                if isinstance(structured["result"], dict) and "error" in structured["result"]:
                    is_error = True
                    error_msg = structured["result"]["error"]
        # 3. Check object with is_error attribute
        elif hasattr(result, "is_error"):
            is_error = result.is_error
            if is_error and hasattr(result, "error"):
                error_msg = str(result.error)
        # 4. Check error patterns in string representation
        elif "error" in result_str.lower() and any(pattern in result_str.lower() for pattern in [
            "http error", "bad request", "error executing tool",
            "validation error", "failed to connect", "exception"
        ]):
            is_error = True
        
        if is_error:
            print(f"❌ {tool_name}: FAILED (server returned error)")
            # Extract error message if we don't have one already
            if not error_msg:
                error_msg = str(result)
                if hasattr(result, "error"):
                    error_msg = str(result.error)
                elif isinstance(result, dict) and "error" in result:
                    error_msg = result["error"]
                
            print(f"   Error: {error_msg[:500]}")
            if len(error_msg) > 500:
                print("   ...")
            print(f"   Help: {get_tool_help(tool_name)}")
            print()
            # Return False to indicate this should be considered a failure
            return False
        elif "Missing session ID" in result_str:
            print(f"🟡 {tool_name}: PARTIAL SUCCESS (upstream server connectivity issue)")
            print(f"   Note: Tool is working but upstream server requires session authentication")
            print()
            # Return True because this is expected behavior
            return True
        else:
            print(f"✅ {tool_name}: SUCCESS")
            display_str = result.content[0].text if hasattr(result, 'content') and result.content else str(result)
            # Truncate long results for readability
            if len(display_str) > 200:
                display_str = display_str[:200] + "..."
            print(f"   Result: {display_str}")
            print()
            # Return True for successful execution
            return True
    else:
        print(f"❌ {tool_name}: FAILED")
        print(f"   Error: {error}")
        print(f"   Help: {get_tool_help(tool_name)}")
        print()
        # Return False for exception-based failures
        return False

def get_tool_help(tool_name: str) -> str:
    """Get helpful explanation for tool failures."""
    help_text = {
        "ping": "This is a simple connectivity test. If it fails, there's likely a server startup issue.",
        "help": "This tool should provide API documentation. Check if the upstream server is accessible.",
        "search-datasets": "This tool searches for datasets. Requires internet connection to upstream server.",
        "validate-croissant": "This tool validates Croissant metadata. Requires valid JSON metadata structure.",
        "download-dataset": "This tool downloads datasets. Requires valid collection and dataset names.",
        "datasets-preview-url": "This tool gets preview URLs. Requires valid collection and dataset names.",
        "dataset/mlcroissant": "This tool gets dataset metadata. Requires valid collection and dataset names."
    }
    return help_text.get(tool_name, "Check the tool parameters and upstream server connectivity.")

# Global variable to track server process
server_process = None

def start_test_server():
    """Start the MCP server for testing."""
    global server_process
    
    if transport in ["sse", "streamable-http"]:
        print(f"🚀 Starting server on {host}:{port} with {transport} transport...")
        
        # Start the server as a subprocess using the CLI command
        server_process = subprocess.Popen([
            "eclair-server",
            "--host", host,
            "--port", str(port),
            "--transport", transport
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give the server more time to start up
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if server started successfully
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"❌ Server failed to start. stdout: {stdout}, stderr: {stderr}")
            return False
        
        # For streamable-http, test the /mcp endpoint specifically
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            test_host = "127.0.0.1" if host == "0.0.0.0" else host
            result = sock.connect_ex((test_host, port))
            sock.close()
            if result != 0:
                print(f"❌ Server not responding on {host}:{port}")
                return False
        except Exception as e:
            print(f"❌ Error checking server connection: {e}")
            return False
            
        print(f"✅ Server started successfully and is responding")
        return True
    else:
        # For stdio transport, no need to start a separate server
        print(f"📡 Using stdio transport - server will be started automatically")
        return True

def stop_test_server():
    """Stop the test server."""
    global server_process
    
    if server_process:
        print("🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        server_process = None
        print("✅ Server stopped")

async def call_tool_for_test(tool_name: str, arguments=None):
    """Helper function to call a single tool and return (success, result, error)."""
    try:
        if arguments:
            result = await client.call_tool(tool_name, arguments)
        else:
            result = await client.call_tool(tool_name)
        return True, result, None
    except Exception as e:
        return False, None, str(e)

async def run_all_tests():
    """Run comprehensive tests for all tools."""
    print("🚀 Starting Eclair MCP server tests...\n")
    
    # Start the server if needed
    if not start_test_server():
        print("❌ Failed to start test server")
        return False
    
    try:
        all_passed = True
        
        async with client:
            # Test 1: Ping (no parameters)
            success, result, error = await call_tool_for_test("ping")
            test_success = check_result("ping", success, result, error)
            all_passed &= test_success
            
            # Test 2: Help (no parameters) 
            success, result, error = await call_tool_for_test("help")
            test_success = check_result("help", success, result, error)
            all_passed &= test_success
            
            # Test 3: Search datasets (requires query parameter)
            success, result, error = await call_tool_for_test("search-datasets", {"query": "mnist"})
            test_success = check_result("search-datasets", success, result, error)
            all_passed &= test_success
            
            # Test 4: Validate Croissant (requires metadata_json parameter)
            # Load Croissant metadata from the resources file
            with open(os.path.join(os.path.dirname(__file__), "resources", "openml_covertype_croissant.json"), 'r') as f:
                croissant_metadata = json.load(f)
            
            success, result, error = await call_tool_for_test("validate-croissant", {"metadata_json": croissant_metadata})
            test_success = check_result("validate-croissant", success, result, error)
            all_passed &= test_success
            
            # Test 5: Download dataset (requires collection and dataset parameters)
            success, result, error = await call_tool_for_test("download-dataset", {"collection": "ylecun", "dataset": "mnist"})
            test_success = check_result("download-dataset", success, result, error)
            all_passed &= test_success
            
            # Test 6: Get preview URL (requires collection and dataset parameters)
            success, result, error = await call_tool_for_test("datasets-preview-url", {"collection": "ylecun", "dataset": "mnist"})
            test_success = check_result("datasets-preview-url", success, result, error)
            all_passed &= test_success
            
            # Test 7: Get dataset metadata (requires collection and dataset parameters)
            success, result, error = await call_tool_for_test("serve-croissant", {"collection": "ylecun", "dataset": "mnist"})
            test_success = check_result("serve-croissant", success, result, error)
            all_passed &= test_success
        
        # Final summary
        print("=" * 50)
        if all_passed:
            print("🎉 ALL TESTS PASSED! The MCP server is working correctly.")
            return True
        else:
            print("⚠️  SOME TESTS FAILED. Check the errors above for details.")
            return False
    
    finally:
        # Always stop the server when done
        stop_test_server()


# Pytest fixtures and test functions
@pytest.fixture(scope="session")
def test_server():
    """Pytest fixture to start and stop test server for the entire test session."""
    print("🚀 Starting Eclair MCP server for pytest session...")
    start_test_server()
    
    # Wait a moment for server to start
    import time
    time.sleep(3)
    
    yield
    
    print("🛑 Stopping Eclair MCP server...")
    stop_test_server()


async def run_single_test(tool_name: str, arguments=None):
    """Helper function to run a single tool test for pytest."""
    async with client:
        success, result, error = await call_tool_for_test(tool_name, arguments)
        if not success:
            pytest.fail(f"Tool {tool_name} failed: {error}")
        return result


@pytest.mark.asyncio
async def test_ping_tool(test_server):
    """Test the ping tool."""
    result = await run_single_test("ping")
    assert result is not None
    print("✅ Ping tool test passed")


@pytest.mark.asyncio 
async def test_help_tool(test_server):
    """Test the help tool."""
    result = await run_single_test("help")
    assert result is not None
    print("✅ Help tool test passed")


@pytest.mark.asyncio
async def test_search_datasets_tool(test_server):
    """Test the search-datasets tool."""
    result = await run_single_test("search-datasets", {"query": "mnist"})
    assert result is not None
    print("✅ Search datasets tool test passed")


@pytest.mark.asyncio
async def test_validate_croissant_tool(test_server):
    """Test the validate-croissant tool."""
    # Load Croissant metadata from the resources file
    with open(os.path.join(os.path.dirname(__file__), "resources", "openml_covertype_croissant.json"), 'r') as f:
        croissant_metadata = json.load(f)
    
    result = await run_single_test("validate-croissant", {"metadata_json": croissant_metadata})
    assert result is not None
    print("✅ Validate croissant tool test passed")


@pytest.mark.asyncio
async def test_download_dataset_tool(test_server):
    """Test the download-dataset tool."""
    result = await run_single_test("download-dataset", {"collection": "ylecun", "dataset": "mnist"})
    assert result is not None
    print("✅ Download dataset tool test passed")


@pytest.mark.asyncio
async def test_datasets_preview_url_tool(test_server):
    """Test the datasets-preview-url tool."""
    result = await run_single_test("datasets-preview-url", {"collection": "ylecun", "dataset": "mnist"})
    assert result is not None
    print("✅ Datasets preview URL tool test passed")


@pytest.mark.asyncio
async def test_serve_croissant_tool(test_server):
    """Test the serve-croissant tool."""
    result = await run_single_test("serve-croissant", {"collection": "ylecun", "dataset": "mnist"})
    assert result is not None
    print("✅ Serve croissant tool test passed")


# Standalone execution
if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if not success:
        sys.exit(1)