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
from textwrap import dedent
import re

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


# Context/guidance for builders (LLM/agent)
async def get_builder_context() -> str:
    """Return guidance for LLM/agent on building datasets with Croissant/TFDS/PyTorch.

    Loads a curated context file if available; otherwise returns a minimal fallback.
    """
    context_path = os.path.join(os.path.dirname(__file__), "context", "builder_context.md")
    try:
        with open(context_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("builder_context.md not found; returning fallback guidance")
        return dedent(
            """
            Croissant Builder Context
            - Use mlcroissant.Dataset(jsonld=<croissant_url>) to access records
            - Wrap it with torch.utils.data.Dataset to integrate with PyTorch
            - See TFDS builder notebook for reference: https://github.com/mlcommons/croissant/blob/main/python/mlcroissant/recipes/tfds_croissant_builder.ipynb
            """
        ).strip()


# PyTorch scaffold generator
async def generate_pytorch_scaffold(croissant_url: str, record_set: str | None = None, x_fields: List[str] | None = None, y_field: str | None = None) -> Dict[str, Any]:
    """Generate a PyTorch Dataset scaffold for a given Croissant URL.

    Args:
        croissant_url: URL to a Croissant JSON-LD metadata file.
        record_set: Optional record set ID to read. If omitted, instruct user to pick one.
        x_fields: Optional list of field IDs to treat as inputs.
        y_field: Optional field ID to treat as label.

    Returns:
        A dictionary with keys: instructions (str), code (str), notes (list[str]).
    """
    # Normalize Hugging Face dataset page URLs to direct Croissant JSON-LD endpoint.
    normalized_url = croissant_url
    try:
        m = re.match(r"^https?://huggingface\.co/datasets/([^/]+)/([^/?#]+)", croissant_url)
        if m and "/api/" not in croissant_url:
            org, name = m.group(1), m.group(2)
            normalized_url = f"https://huggingface.co/api/datasets/{org}/{name}/croissant"
    except Exception:
        # Best-effort normalization; keep original on failure
        normalized_url = croissant_url

    # Build a minimal, robust scaffold that works even if metadata can't be fetched now.
    scaffold_code = f"""
import torch
from torch.utils.data import Dataset
from typing import Any, Dict, List, Optional, Tuple

from mlcroissant import Dataset as CroissantDataset


class CroissantTorchDataset(Dataset):
    '''PyTorch Dataset backed by a Croissant metadata description.

    - jsonld: Croissant JSON-LD URL or dict
    - record_set: ID of the RecordSet to iterate over (matches @id in metadata)
    - split: optional split value to filter (e.g., "train", "validation", "test")
    - x_fields: list of field IDs to form the input tensor or structure
    - y_field: field ID for the label/target
    '''

    def __init__(
        self,
        jsonld: str,
        record_set: str,
        *,
        split: Optional[str] = None,
        x_fields: Optional[List[str]] = None,
        y_field: Optional[str] = None,
        transform=None,
        target_transform=None,
    ) -> None:
        self.jsonld = jsonld
        self.record_set = record_set
        self.split = split
        self.x_fields = x_fields or []
        self.y_field = y_field
        self.transform = transform
        self.target_transform = target_transform

        # Initialize Croissant dataset
        self._ds = CroissantDataset(jsonld=self.jsonld)

        # Materialize examples as a list for deterministic __len__.
        filters = {{}}
        if self.split:
            # Common split field IDs include "data/split" or "split"; update if needed
            # Adjust the key here to match your metadata field ID
            filters = {{"split": self.split}}

        self._examples: List[Dict[str, Any]] = list(self._ds.records(self.record_set, filters=filters))

    def __len__(self) -> int:
        return len(self._examples)

    def __getitem__(self, idx: int) -> Tuple[Any, Any] | Any:
        example = self._examples[idx]

        # Extract inputs
        if self.x_fields:
            x = [example.get(fid) for fid in self.x_fields]
            # Simplify single-input case
            if len(x) == 1:
                x = x[0]
        else:
            x = example

        # Extract target
        y = example.get(self.y_field) if self.y_field else None

        if self.transform:
            x = self.transform(x)
        if self.target_transform and y is not None:
            y = self.target_transform(y)

        return (x, y) if self.y_field is not None else x


def build_dataset() -> CroissantTorchDataset:
    return CroissantTorchDataset(
        jsonld={normalized_url!r},
        record_set={record_set!r},
        split=None,  # e.g., "train"
        x_fields={x_fields or []!r},
        y_field={y_field!r},
    )


if __name__ == "__main__":
    ds = build_dataset()
    print(len(ds))
    first = ds[0]
    print(type(first), (first[0].__class__ if isinstance(first, tuple) else None))
"""

    instructions = dedent(
        f"""
        Quickstart (PyTorch + Croissant)
        1) Install: pip install mlcroissant torch
        2) Pick the correct record set ID and field IDs from your metadata
           - If unsure, open the JSON-LD at: {croissant_url}
           - Look under "@graph" for RecordSet (@type: sc:RecordSet) and Field nodes
        3) Save the scaffold to croissant_torch_dataset.py and run it
        4) Replace the split/key names to match your metadata (e.g., data/split)

        Reference: TFDS Croissant builder recipe
        - https://github.com/mlcommons/croissant/blob/main/python/mlcroissant/recipes/tfds_croissant_builder.ipynb
        Note: For Hugging Face datasets, prefer the Croissant JSON-LD endpoint
        https://huggingface.co/api/datasets/<org-or-user>/<dataset>/croissant
        """
    ).strip()

    notes = [
        "Adjust filters to your split field ID (often 'data/split' or 'split').",
        "Some fields may contain URIs to files; apply transforms to load them (e.g., PIL.Image).",
        "For streaming large datasets, iterate over CroissantDataset.records directly instead of materializing.",
    ]

    return {"instructions": instructions, "code": scaffold_code.strip(), "notes": notes}
