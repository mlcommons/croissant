"""Lazy imports for optional dependencies."""

from __future__ import annotations

import importlib
import types


def _try_import(module_name: str, package_name: str | None = None):
    """Tries importing a module, with an informative error message on failure.

    Args:
        module_name: The name of the module in Python, e.g.: "import git".
        package_name: The name of the package on PyPI, e.g.: "pip install GitPython".
    """
    if package_name is None:
        package_name = module_name
    try:
        return importlib.import_module(module_name)
    except ImportError as exception:
        if package_name is None:
            package_name = module_name
        installs = f"`pip install {package_name}`"
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

    def __get__(self, obj, objtype=None):
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

    Usage:

    - Add a new optional dependency below:

    ```python
    @cached_class_property
    def foo(cls):
        return _try_import("goo")
    ```

    - Use this new dependency:

    ```python
    from mlcroissant._src.core.optional import deps

    foo = deps.foo  # use the `foo` module here in your code
    ```
    """

    @cached_class_property
    def git(cls) -> types.ModuleType:
        """Cached git module."""
        return _try_import("git", package_name="GitPython")

    @cached_class_property
    def PIL_Image(cls) -> types.ModuleType:  # pylint: disable=invalid-name
        """Cached git module."""
        return _try_import("PIL.Image", package_name="Pillow")


deps = OptionalDependencies
