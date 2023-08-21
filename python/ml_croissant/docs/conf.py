"""Generate documentation.

Usage (from the root directory):

```sh
pip install -e .[docs]

sphinx-build -b html docs/ docs/_build
```
"""

import apitree

modules = [
    apitree.ModuleInfo(
        api="ml_croissant",
        module_name="ml_croissant",
        alias="ml_croissant",
        github_url="https://github.com/mlcommons/croissant",
    ),
]

apitree.make_project(
    modules=modules,
    globals=globals(),
)
