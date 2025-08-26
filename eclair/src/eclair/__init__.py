"""
⚡️ Eclair ⚡️ Data-driven AI assistants

Eclair is an agentic dataset server that helps AI models discover, download, 
and use datasets to answer questions based on factual data.

Key Components:
- server: MCP server implementation for dataset operations  
- client: Client utilities for interacting with Eclair servers
- mlcbakery: Alternative server implementation with FastMCP
"""

__version__ = "0.0.1"
__author__ = "Joaquin Vanschoren, Omar Benjelloun, Jonathan Lebensold"
__email__ = "joaquin@mlcommons.org"
__description__ = "MCP server to help LLMs work with datasets, built on Croissant"

# Components are available as submodules
# Import them explicitly when needed to avoid dependency issues
# e.g., from eclair.server import EclairServer
# e.g., from eclair.client import EclairClient

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__"
]
