import pytest

VERSIONS = ["0.8", "1.0"]

parametrize_version = pytest.mark.parametrize("version", VERSIONS)
