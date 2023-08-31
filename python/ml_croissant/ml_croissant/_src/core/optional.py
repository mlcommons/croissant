"""Lazy imports for optional dependencies."""

from __future__ import annotations

import importlib
import types

from etils import epath
import toml


def list_optional_deps() -> dict[str, str]:
    """Lists all optional dependencies from the pyproject.toml."""
    toml_file = epath.Path(__file__).parent.parent.parent.parent / "pyproject.toml"
    return toml.load(toml_file).get("project", {}).get("optional-dependencies", {})


def _try_import(module_name):
    """Tries importing a module, with an informative error message on failure."""
    try:
        return importlib.import_module(module_name)
    except ImportError as exception:
        optional_deps = list_optional_deps()
        installs = f"`pip install {module_name}`"
        for sub_module, deps in optional_deps.items():
            if module_name in deps:
                installs = f"`pip install ml_croissant[{sub_module}]`"
        error = (
            f"Failed importing {module_name}. This likely means that the dataset"
            " requires additional dependencies that have to be manually installed"
            f" (usually with {installs}). See the optional dependencies listed in"
            " pyproject.toml."
        ).format(name=module_name)
        raise ModuleNotFoundError(error) from exception


class cached_class_property(classmethod):
    """Cached class property decorator.

    Equivalent of @classmethod + @functools.cached_property.
    """

    def __init__(self, func):
        """Constructor with cache."""
        self._func = func
        self._cache = {}

    def __get__(self, obj, objtype):
        """Cached getter."""
        if objtype not in self._cache:
            self._cache[objtype] = self._func(objtype)
        return self._cache[objtype]


class OptionalDependencies(object):
    """Optional dependencies can be heavy and need not be loaded by all clients.

    Some datasets require optional dependencies for data generation. To allow for
    the default installation to remain lean, those heavy dependencies are
    lazily imported here.

    Warning: we haven't found a way to properly type the return of each property.
    """

    @cached_class_property
    def git(cls) -> types.ModuleType:
        """Cached git module."""
        return _try_import("git")


deps = OptionalDependencies
