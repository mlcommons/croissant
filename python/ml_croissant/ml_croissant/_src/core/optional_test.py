"""Tests for optional deps."""

import importlib
from unittest import mock

import pytest

from ml_croissant._src.core.optional import _try_import
from ml_croissant._src.core.optional import deps
from ml_croissant._src.core.optional import list_optional_deps


def test_list_optional_deps():
    assert list(list_optional_deps().keys()) == ["dev", "git", "image", "parquet"]


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
        with pytest.raises(ImportError, match="pip install ml_croissant\\[parquet\\]"):
            _try_import("pyarrow")
        with pytest.raises(ImportError, match="pip install foo"):
            _try_import("foo")
        with pytest.raises(ImportError, match="pip install ml_croissant\\[git\\]"):
            _try_import("git", package_name="GitPython")
