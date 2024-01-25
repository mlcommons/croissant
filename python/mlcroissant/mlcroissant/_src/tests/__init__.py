import pytest

VERSIONS = ["0.8"]

parametrize_version = pytest.mark.parametrize("version", VERSIONS)
