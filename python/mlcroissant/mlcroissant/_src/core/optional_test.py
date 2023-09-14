"""Tests for optional deps."""

import importlib
from unittest import mock

import pytest

from mlcroissant._src.core.optional import _try_import
from mlcroissant._src.core.optional import deps


@pytest.mark.parametrize(
    "optional_deps",
    [
        "git",
    ],
)
def test_load_optional_deps(optional_deps):
    getattr(deps, optional_deps)


def test_explicit_error_message():
    with mock.patch.object(importlib, "import_module", side_effect=ImportError):
        with pytest.raises(ImportError, match="pip install foo"):
            _try_import("foo")
        with pytest.raises(ImportError, match="pip install bar"):
            _try_import("foo", package_name="bar")
