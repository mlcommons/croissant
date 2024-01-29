"""Module to manipulate URLs."""

from typing import Any


def is_url(url: Any) -> bool:
    """Tests whether a URL is valid.

    The current version is very loose and only supports the HTTP protocol.
    """
    if isinstance(url, str):
        return url.startswith("http://") or url.startswith("https://")
    return False
