"""
Claude AI Client Package

Claude integration for Eclair MCP dataset discovery and analysis.
"""

try:
    from .client import ClaudeMCPClient, CLAUDE_AVAILABLE
except ImportError:
    ClaudeMCPClient = None
    CLAUDE_AVAILABLE = False

__all__ = ['ClaudeMCPClient', 'CLAUDE_AVAILABLE']
