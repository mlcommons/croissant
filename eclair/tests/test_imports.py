"""
Test basic package imports
"""
import pytest
import sys
import os

# Add src to path so we can import from eclair
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_package_import():
    """Test that the main package can be imported."""
    import eclair
    assert eclair.__version__ == "0.0.1"


def test_server_import():
    """Test that server module can be imported."""
    try:
        from eclair.server import EclairServer
        assert EclairServer is not None
    except ImportError:
        pytest.skip("Server dependencies not available")


def test_client_import():
    """Test that client module can be imported."""
    try:
        from eclair.client import EclairClient
        assert EclairClient is not None
    except ImportError:
        pytest.skip("Client dependencies not available")