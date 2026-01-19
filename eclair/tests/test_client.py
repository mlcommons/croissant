import asyncio
import sys
import os
import json
import time
import subprocess
from typing import Optional

# Add src to path so we can import from eclair
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import from the eclair package
from eclair.client.gemini import GeminiMCPClient

# Server management for testing
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

class EclairMCPTester:
    """Comprehensive test suite for the Eclair MCP server."""
    
    def __init__(self, server_url: str = "http://localhost:8080/mcp"):
        self.server_url = server_url
        self.client = None
        
    async def setup(self):
        """Initialize the test client."""
        self.client = GeminiMCPClient(self.server_url)
        await self.client.initialize()
        
    async def test_ping(self):
        """Test the ping tool to verify server is working."""
        print("🏓 Testing server ping...")
        try:
            result = await self.client.call_mcp_tool("ping")
            if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                print(f"✅ {result.structured_content['result']}")
                return True
            else:
                print(f"✅ {result}")
                return True
        except Exception as e:
            print(f"❌ Error pinging server: {e}")
            return False
    
    async def test_search_datasets(self, query: str = "mnist"):
        """Test the search-datasets tool."""
        print(f"🔍 Testing search-datasets with query: '{query}'")
        try:
            result = await self.client.call_mcp_tool("search-datasets", {"query": query})
            
            # Handle CallToolResult properly
            if hasattr(result, 'content'):
                # Extract the actual data from the structured result
                actual_result = result.content
                if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                    actual_result = result.structured_content['result']
                
                if isinstance(actual_result, list):
                    print(f"✅ Found {len(actual_result)} datasets:")
                    for i, dataset in enumerate(actual_result[:3], 1):  # Show first 3 results
                        if isinstance(dataset, dict) and "name" in dataset:
                            print(f"   {i}. {dataset.get('name', 'Unknown')} - {dataset.get('description', 'No description')[:100]}")
                        else:
                            print(f"   {i}. {dataset}")
                    return True  # Return True for success instead of the actual result
                else:
                    print(f"⚠️ Unexpected result format: {actual_result}")
                    return False
            else:
                print(f"⚠️ Result has no content: {result}")
                return None
        except Exception as e:
            print(f"❌ Error calling search-datasets: {e}")
            return None
    
    async def test_help(self):
        """Test the help tool."""
        print("❓ Testing help tool...")
        try:
            result = await self.client.call_mcp_tool("help")
            print("✅ Help retrieved successfully")
            if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                help_text = result.structured_content['result']
                print(f"📄 Help preview: {str(help_text)[:200]}...")
            else:
                print(f"📄 Help preview: {str(result)[:200]}...")
            return True
        except Exception as e:
            print(f"❌ Error getting help: {e}")
            return False
    
    async def test_validate_croissant(self):
        """Test the validate-croissant tool with actual Croissant metadata."""
        print("🧪 Testing validate-croissant tool...")
        
        # Load the actual Croissant metadata from resources
        resources_path = os.path.join(os.path.dirname(__file__), "resources", "openml_covertype_croissant.json")
        try:
            with open(resources_path, 'r') as f:
                croissant_metadata = json.load(f)
        except Exception as e:
            print(f"❌ Error loading Croissant metadata: {e}")
            return False
        
        try:
            result = await self.client.call_mcp_tool("validate-croissant", {"metadata_json": croissant_metadata})
            print("✅ Croissant validation completed")
            if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                validation_result = result.structured_content['result']
                print(f"📄 Validation result: {validation_result}")
            else:
                print(f"📄 Validation result: {result}")
            return True
        except Exception as e:
            print(f"❌ Error validating croissant: {e}")
            return False
    
    async def test_dataset_metadata(self, collection: str = "ylecun", dataset: str = "mnist"):
        """Test getting dataset metadata."""
        print(f"📊 Testing dataset metadata for {collection}/{dataset}...")
        try:
            result = await self.client.call_mcp_tool("serve-croissant", {"collection": collection, "dataset": dataset})
            print("✅ Dataset metadata retrieved")
            if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                metadata = result.structured_content['result']
                print(f"📄 Metadata type: {type(metadata)}")
            else:
                print(f"📄 Metadata type: {type(result)}")
            return True
        except Exception as e:
            print(f"❌ Error getting dataset metadata: {e}")
            return False
    
    async def test_preview_url(self, collection: str = "ylecun", dataset: str = "mnist"):
        """Test getting dataset preview URL."""
        print(f"🔗 Testing preview URL for {collection}/{dataset}...")
        try:
            result = await self.client.call_mcp_tool("datasets-preview-url", {"collection": collection, "dataset": dataset})
            print("✅ Preview URL retrieved")
            if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                url = result.structured_content['result']
                print(f"📄 Preview URL: {url}")
            else:
                print(f"📄 Preview URL: {result}")
            return True
        except Exception as e:
            print(f"❌ Error getting preview URL: {e}")
            return False
    
    async def test_download_dataset(self, collection: str = "ylecun", dataset: str = "mnist"):
        """Test downloading dataset info."""
        print(f"📦 Testing download dataset for {collection}/{dataset}...")
        try:
            result = await self.client.call_mcp_tool("download-dataset", {"collection": collection, "dataset": dataset})
            print("✅ Download dataset info retrieved")
            if hasattr(result, 'structured_content') and 'result' in result.structured_content:
                download_info = result.structured_content['result']
                print(f"📄 Download info type: {type(download_info)}")
            else:
                print(f"📄 Download info type: {type(result)}")
            return True
        except Exception as e:
            print(f"❌ Error getting download info: {e}")
            return False
    
    async def test_gemini_integration(self):
        """Test Gemini integration if API key is available."""
        if not self.client.gemini_client:
            print("⚠️ Skipping Gemini test - no API key available")
            return None
            
        print("🤖 Testing Gemini integration...")
        try:
            response = await self.client.ask_gemini_with_tools(
                "Search for datasets about image classification, and tell me about the top 3 results"
            )
            print(f"✅ Gemini response received")
            print(f"📄 Response preview: {response[:200]}...")
            return True
        except Exception as e:
            print(f"❌ Error with Gemini integration: {e}")
            return False
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 Starting Eclair MCP Server Test Suite")
        print("=" * 60)
        
        # Start the server
        if not start_test_server():
            print("❌ Failed to start test server")
            return False
        
        try:
            await self.setup()
            
            tests = [
                ("Server Ping", self.test_ping()),
                ("Search Datasets", self.test_search_datasets("mnist")),
                ("Help Tool", self.test_help()),
                ("Validate Croissant", self.test_validate_croissant()),
                ("Dataset Metadata", self.test_dataset_metadata()),
                ("Preview URL", self.test_preview_url()),
                ("Download Dataset", self.test_download_dataset()),
                ("Gemini Integration", self.test_gemini_integration()),
            ]
            
            results = {}
            for test_name, test_coro in tests:
                print(f"\n{'=' * 20} {test_name} {'=' * 20}")
                try:
                    result = await test_coro
                    results[test_name] = result
                except Exception as e:
                    print(f"❌ Test {test_name} failed with exception: {e}")
                    results[test_name] = False
        
        finally:
            # Always stop the server
            stop_test_server()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        passed = sum(1 for r in results.values() if r is True)
        failed = sum(1 for r in results.values() if r is False)
        skipped = sum(1 for r in results.values() if r is None)
        
        for test_name, result in results.items():
            if result is True:
                print(f"✅ {test_name}: PASSED")
            elif result is False:
                print(f"❌ {test_name}: FAILED")
            else:
                print(f"⚠️ {test_name}: SKIPPED")
        
        print(f"\nTotal: {len(results)} tests")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Skipped: {skipped}")
        
        if failed == 0:
            print("\n🎉 All available tests passed!")
        else:
            print(f"\n⚠️ {failed} test(s) failed")
        
        return results


async def main():
    """Main test runner."""
    tester = EclairMCPTester()
    await tester.run_all_tests()


# Pytest compatibility additions
import pytest

@pytest.fixture(scope="session")
def test_server():
    """Pytest fixture to start and stop test server for the entire test session."""
    print("🚀 Starting Eclair MCP server for pytest session...")
    start_test_server()
    
    # Wait a moment for server to start
    time.sleep(3)
    
    yield
    
    print("🛑 Stopping Eclair MCP server...")
    stop_test_server()

@pytest.fixture(scope="session")
def client_tester():
    """Pytest fixture to provide EclairMCPTester instance."""
    return EclairMCPTester()


async def setup_client_for_test(client_tester):
    """Helper to setup client for individual tests."""
    await client_tester.setup()
    return client_tester


@pytest.mark.asyncio
async def test_client_ping(test_server, client_tester):
    """Test server ping functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_ping()
    assert result is True, "Ping test should pass"


@pytest.mark.asyncio
async def test_client_search_datasets(test_server, client_tester):
    """Test search datasets functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_search_datasets("mnist")
    assert result is True, "Search datasets test should pass"


@pytest.mark.asyncio
async def test_client_help(test_server, client_tester):
    """Test help tool functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_help()
    assert result is True, "Help test should pass"


@pytest.mark.asyncio
async def test_client_validate_croissant(test_server, client_tester):
    """Test croissant validation functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_validate_croissant()
    assert result is True, "Validate croissant test should pass"


@pytest.mark.asyncio
async def test_client_dataset_metadata(test_server, client_tester):
    """Test dataset metadata functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_dataset_metadata()
    assert result is True, "Dataset metadata test should pass"


@pytest.mark.asyncio
async def test_client_preview_url(test_server, client_tester):
    """Test preview URL functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_preview_url()
    assert result is True, "Preview URL test should pass"


@pytest.mark.asyncio
async def test_client_download_dataset(test_server, client_tester):
    """Test download dataset functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_download_dataset()
    assert result is True, "Download dataset test should pass"


@pytest.mark.asyncio
async def test_client_gemini_integration(test_server, client_tester):
    """Test Gemini integration functionality."""
    tester = await setup_client_for_test(client_tester)
    result = await tester.test_gemini_integration()
    # Gemini test can return None if no API key, so we check for None or True
    assert result is None or result is True, "Gemini integration test should pass or be skipped"


if __name__ == "__main__":
    asyncio.run(main())
