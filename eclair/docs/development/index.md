# Development

This section covers everything you need to know to contribute to Eclair, set up a development environment, and extend the platform with new features.

## Quick Start for Contributors

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setup Development Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/mlcommons/croissant.git
   cd croissant/eclair
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Run Tests (Optional)**
Running the tests will also startup an Eclair server. Hence you don't need to start it beforehand.
   ```bash
   pytest
   ```

5. **Start Eclair Server**
   ```bash
   eclair-server
   ```

## Project Structure

```
eclair/
├── src/eclair/                 # Main package
│   ├── client/                # Client libraries
│   │   ├── cli.py            # Command line interface
│   │   ├── client.py         # Python client
│   │   └── gemini/           # Gemini integration
│   └── server/               # Server implementation
│       ├── server.py         # Main server
│       ├── tools.py          # MCP tools
│       └── validation.py     # Data validation
├── tests/                    # Test suite
├── docs/                     # Documentation
├── config.json               # Configuration
├── mkdocs.yml                # Documentation building
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
└── pyproject.toml            # Package configuration
```

### Testing

We use pytest with comprehensive test coverage:

```python
# tests/test_client.py
import pytest
from eclair.client import EclairClient

@pytest.fixture
def client():
    return EclairClient("http://localhost:8080")

def test_search_datasets(client):
    """Test dataset search functionality."""
    results = client.search_datasets("test query")
    assert isinstance(results, list)
    
def test_download_dataset(client):
    """Test dataset download."""
    path = client.download_dataset("test_collection", "test_dataset")
    assert isinstance(path, str)
    assert path.endswith("test_dataset")
```

Run tests with coverage:

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=src/eclair --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest -v
```

### Documentation

Documentation is built with MkDocs and Material theme:

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material

# Serve docs locally
mkdocs serve

# Build docs
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

## Adding New Features

### Adding a New MCP Tool

1. **Define Tool Schema**
   ```python
   # src/eclair/server/tools.py
   def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
       schemas = {
           "my-new-tool": {
               "name": "my-new-tool",
               "description": "Description of what this tool does",
               "inputSchema": {
                   "type": "object",
                   "properties": {
                       "param1": {
                           "type": "string",
                           "description": "Description of parameter"
                       }
                   },
                   "required": ["param1"]
               }
           }
       }
       return schemas.get(tool_name)
   ```

2. **Implement Tool Function**
   ```python
   async def my_new_tool(self, param1: str) -> Dict[str, Any]:
       """Implementation of the new tool."""
       try:
           # Tool logic here
           result = await self._process_data(param1)
           
           return {
               "success": True,
               "result": result
           }
       except Exception as e:
           return {
               "success": False,
               "error": str(e)
           }
   ```

3. **Register Tool**
   ```python
   def __init__(self):
       self.tools = {
           "search-datasets": self.search_datasets,
           "download-dataset": self.download_dataset,
           "my-new-tool": self.my_new_tool,  # Add here
       }
   ```

4. **Add Client Method**
   ```python
   # src/eclair/client/client.py
   def my_new_tool(self, param1: str) -> Dict[str, Any]:
       """Client method for new tool."""
       return self._call_tool("my-new-tool", {"param1": param1})
   ```

5. **Write Tests**
   ```python
   # tests/test_new_tool.py
   def test_my_new_tool(client):
       """Test the new tool."""
       result = client.my_new_tool("test_value")
       assert result["success"] is True
       assert "result" in result
   ```

6. **Update Documentation**
   ```markdown
   <!-- docs/api/tools.md -->
   ### my-new-tool
   
   Description of the new tool.
   
   **Parameters:**
   - `param1` (string): Description
   
   **Example:**
   ```python
   result = client.my_new_tool("example")
   ```

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_tools.py
import pytest
from unittest.mock import AsyncMock, patch
from eclair.server.tools import EclairTools

@pytest.fixture
def tools():
    return EclairTools()

@pytest.mark.asyncio
async def test_search_datasets_unit(tools):
    """Unit test for search functionality."""
    with patch('eclair.server.tools.search_engine') as mock_search:
        mock_search.search.return_value = [{"name": "test", "collection": "test"}]
        
        result = await tools.search_datasets("test query")
        
        assert len(result) == 1
        assert result[0]["name"] == "test"
        mock_search.search.assert_called_once_with("test query")
```

### Integration Tests

Test component interactions:

```python
# tests/integration/test_server.py
import pytest
import httpx
from eclair.server.server import app

@pytest.fixture
def client():
    return httpx.AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_search_endpoint_integration(client):
    """Integration test for search endpoint."""
    response = await client.post("/mcp", json={
        "method": "tools/call",
        "params": {
            "name": "search-datasets",
            "arguments": {"query": "test"}
        }
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
```

### End-to-End Tests

Test complete workflows:

```python
# tests/e2e/test_workflow.py
import pytest
from eclair.client import EclairClient

@pytest.mark.e2e
def test_complete_workflow():
    """End-to-end test of search, download, analyze workflow."""
    client = EclairClient()
    
    # Search for datasets
    results = client.search_datasets("test datasets")
    assert len(results) > 0
    
    # Download first dataset
    first_dataset = results[0]
    path = client.download_dataset(
        first_dataset["collection"],
        first_dataset["name"]
    )
    assert path is not None
    
    # Get metadata
    metadata = client.get_dataset_metadata(
        first_dataset["collection"],
        first_dataset["name"]
    )
    assert "name" in metadata
```

### Performance Tests

Test performance characteristics:

```python
# tests/performance/test_load.py
import pytest
import asyncio
import time
from eclair.client import AsyncEclairClient

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_searches():
    """Test performance under concurrent load."""
    client = AsyncEclairClient()
    
    start_time = time.time()
    
    # Run 10 concurrent searches
    tasks = [
        client.search_datasets(f"query {i}")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Should complete within reasonable time
    assert total_time < 5.0
    assert all(len(result) >= 0 for result in results)
```

