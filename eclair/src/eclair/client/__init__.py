"""
Eclair Client Package

Contains client utilities for interacting with Eclair servers.
"""

try:
    from .client import EclairClient
except ImportError:
    EclairClient = None

try:
    from .gemini import GeminiMCPClient
except ImportError:
    GeminiMCPClient = None

try:
    from .claude import ClaudeMCPClient
except ImportError:
    ClaudeMCPClient = None

__all__ = ["EclairClient", "GeminiMCPClient", "ClaudeMCPClient"]
