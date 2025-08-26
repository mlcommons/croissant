
# Python Client SDK

The Eclair Python client provides multiple interfaces to interact with the Eclair dataset server, including base MCP clients and AI-powered assistant clients.

## Installation

```bash
pip install eclair
```

For AI assistant functionality:
```bash
# For Gemini integration
pip install google-generativeai

# For Claude integration (coming soon)
pip install anthropic
```

## Client Types

Eclair provides three client types:

1. **EclairClient** - Base MCP client for direct API access
2. **GeminiMCPClient** - AI-powered assistant using Gemini
3. **ClaudeMCPClient** - AI-powered assistant using Claude

## Base MCP Client (EclairClient)

The base client provides direct access to all MCP tools.

### Quick Start

```python
from eclair.client import EclairClient
import asyncio

async def main():
    # Initialize client
    client = EclairClient("http://localhost:8080/mcp")
    
    # Test connectivity
    ping_result = await client.ping()
    print(ping_result.data.result)  # "Pong! Eclair MCP Server is running successfully."
    
    # Search for datasets
    results = await client.search_datasets("fashion mnist")
    print(f"Search completed")
    
    # Get help
    help_info = await client.get_help()
    print("Help information retrieved")

asyncio.run(main())
```

### API Reference - EclairClient

#### Constructor

```python
EclairClient(server_url: str = "http://localhost:8080/mcp")
```

#### Methods

All methods return `CallToolResult` objects with structured data.

##### ping()
Test server connectivity.
```python
result = await client.ping()
print(result.data.result)  # Server status message
```

##### search_datasets(query: str)
Search for datasets.
```python
result = await client.search_datasets("fashion mnist")
datasets = result.structured_content['result']  # List of datasets
```

##### download_dataset(collection: str, dataset: str)
Get download information for a dataset.
```python
result = await client.download_dataset("Han-Xiao", "Fashion-MNIST")
download_info = result.structured_content['result']
```

##### datasets_preview_url(collection: str, dataset: str)
Get preview download URL.
```python
result = await client.datasets_preview_url("Han-Xiao", "Fashion-MNIST")
url = result.structured_content['result']['url']
```

##### serve_croissant(collection: str, dataset: str)
Get Croissant metadata.
```python
result = await client.serve_croissant("Han-Xiao", "Fashion-MNIST")
metadata = result.structured_content['result']
```

##### validate_croissant(metadata_json: dict)
Validate Croissant metadata.
```python
result = await client.validate_croissant(metadata_dict)
validation = result.structured_content['result']
```

##### get_help()
Get help information.
```python
result = await client.get_help()
help_text = result.data.result
```

## Gemini AI Assistant Client

The `GeminiMCPClient` combines MCP tools with Gemini AI for intelligent dataset discovery and analysis.

### Setup

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```env
GEMINI_API_KEY=your-api-key-here
```

### Quick Start

```python
from eclair.client.gemini import GeminiMCPClient
import asyncio

async def main():
    # Initialize with AI capabilities
    client = GeminiMCPClient()
    await client.initialize()
    
    # Ask AI assistant to find and analyze datasets
    response = await client.ask_gemini_with_tools(
        "Find fashion-related datasets and recommend the best one for image classification"
    )
    print(response)
    
    await client.close()

asyncio.run(main())
```

### API Reference - GeminiMCPClient

#### Constructor
```python
GeminiMCPClient(
    mcp_server_url: str = "http://localhost:8080/mcp",
    gemini_api_key: Optional[str] = None
)
```

#### AI Methods

##### ask_gemini_with_tools(prompt: str, temperature: Optional[float] = None)
Use Gemini AI with MCP tools for intelligent responses.
```python
response = await client.ask_gemini_with_tools(
    "Compare MNIST variants and suggest the best for my computer vision project",
    temperature=0.3
)
```

#### Direct MCP Methods

All base MCP methods are also available:
```python
# Direct tool access
datasets = await client.search_datasets("mnist")
metadata = await client.serve_croissant("Han-Xiao", "Fashion-MNIST")
ping = await client.ping()
```

### Configuration

The client loads configuration from `config.json`:

```json
{
  "gemini": {
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.3
  }
}
```

## Claude AI Assistant Client

Similar to Gemini but using Claude AI (implementation in progress).

### Setup

```bash
# Set your Claude API key
export CLAUDE_API_KEY="your-api-key-here"
```

### Usage

```python
from eclair.client.claude import ClaudeMCPClient
import asyncio

async def main():
    try:
        client = ClaudeMCPClient()
        await client.initialize()
        
        # Direct MCP access works
        result = await client.search_datasets("image classification")
        print("Search completed")
        
        # AI features coming soon
        # response = await client.ask_claude_with_tools("Find datasets...")
        
        await client.close()
    except ImportError as e:
        print(f"Claude client requires: pip install anthropic")

asyncio.run(main())
```

## Complete Examples

### 1. Basic Dataset Discovery

```python
from eclair.client import EclairClient
import asyncio
import json

async def basic_discovery():
    client = EclairClient()
    
    # Search for datasets
    result = await client.search_datasets("fashion mnist")
    datasets = result.structured_content['result']
    
    print(f"Found {len(datasets)} datasets")
    for dataset in datasets:
        doc = dataset['document']
        print(f"- {doc['entity_name']} ({doc['collection_name']})")

asyncio.run(basic_discovery())
```

### 2. AI-Powered Dataset Analysis

```python
from eclair.client.gemini import GeminiMCPClient
import asyncio

async def ai_analysis():
    client = GeminiMCPClient()
    await client.initialize()
    
    # Let AI find and analyze datasets
    response = await client.ask_gemini_with_tools("""
    I need datasets for a computer vision project about clothing classification.
    Find relevant datasets and analyze their characteristics.
    Recommend the best option with reasoning.
    """)
    
    print(response)
    await client.close()

asyncio.run(ai_analysis())
```

### 3. Dataset Preview and Download

```python
from eclair.client import EclairClient
import asyncio
import pandas as pd
import requests
import io

async def preview_and_download():
    client = EclairClient()
    
    # Get preview URL
    result = await client.datasets_preview_url("Han-Xiao", "Fashion-MNIST")
    preview_url = result.structured_content['result']['url']
    
    # Download and view preview
    response = requests.get(preview_url)
    if response.status_code == 200:
        df = pd.read_parquet(io.BytesIO(response.content))
        print("Dataset preview:")
        print(df.head())
        print(f"
Dataset shape: {df.shape}")
    
    # Get download information
    download_result = await client.download_dataset("Han-Xiao", "Fashion-MNIST")
    print("
Download information:")
    print(download_result.structured_content['result'])

asyncio.run(preview_and_download())
```

### 4. Metadata Validation

```python
from eclair.client import EclairClient
import asyncio
import json

async def validate_metadata():
    client = EclairClient()
    
    # Get Croissant metadata
    result = await client.serve_croissant("Han-Xiao", "Fashion-MNIST")
    metadata = result.structured_content['result']
    
    # Validate the metadata
    validation_result = await client.validate_croissant(metadata)
    validation = validation_result.structured_content['result']
    
    print("Metadata validation:")
    print(json.dumps(validation, indent=2))

asyncio.run(validate_metadata())
```

## Error Handling

```python
from eclair.client import EclairClient
import asyncio

async def with_error_handling():
    client = EclairClient()
    
    try:
        result = await client.search_datasets("test query")
        if result.is_error:
            print(f"Tool error: {result.content[0].text}")
        else:
            print("Search successful")
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(with_error_handling())
```