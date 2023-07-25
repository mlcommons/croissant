# 🥐 ML Croissant

## Python requirements

Python version >= 3.10.

If you do not have a Python environment:

```bash
python3 -m venv ~/py3
source ~/py3/bin/activate
```

## Install

```bash
python -m pip install ".[dev]"
```

## Verify/load a Croissant dataset

```bash
python scripts/validate.py --file ../../datasets/titanic/metadata.json
```

The command:

- Exits with 0, prints `Done` and displays encountered warnings, when no error was found in the file.
- Exits with 1 and displays all encountered errors/warnings, otherwise.

Similarly, you can generate a dataset by launching:

```bash
python scripts/load.py \
    --file ../../datasets/titanic/metadata.json \
    --record_set passengers \
    --num_records 10
```

## Run tests

```bash
pytest .
```

## Design

The most important modules in the library are:

- [`ml_croissant/_src/structure_graph`](./ml_croissant/_src/structure_graph/graph.py) is responsible for the **static analysis** of the Croissant files. We convert Croissant files to a Python representation called "**structure graph**" (using [NetworkX](https://networkx.org/)). In the process, we catch any static analysis issues (e.g., a missing mandatory field or a logic problem in the file).
- [`ml_croissant/_src/operation_graph`](./ml_croissant/_src/operation_graph/graph.py) is responsible for the **dynamic analysis** of the Croissant files (i.e., actually loading the dataset by yielding examples). We convert the structure graph into an "**operation graph**". Operations are the unit transformations that allow to build the dataset (like [`Download`](./ml_croissant/_src/operation_graph/operations/download.py), [`Extract`](./ml_croissant/_src/operation_graph/operations/extract.py), etc).

Other important modules are:

- [`ml_croissant/_src/core`](./ml_croissant/_src/core) defines all needed core internals. For instance, [`Issues`](./ml_croissant/_src/core/issues.py) are a way to track errors and warning during the analysis of Croissant files.
- [`ml_croissant/__init__.py`](./ml_croissant/__init__.py) declares the public API with [`ml_croissant.Dataset`](./ml_croissant/_src/datasets.py).

For the full design, refer to the [design doc](https://docs.google.com/document/d/1zYQIUX9ae1sZOOBq9OCsJ8JW8-Ejy3NLSeqaI5LtOEM/edit?resourcekey=0-CK78DfFvF7fnufyZqF3h3Q) for an overview of the implementation.

## Contribute

All contributions are welcome! We even have [good first issues](https://github.com/mlcommons/croissant/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to start in the project. Refer to the [GitHub project](https://github.com/orgs/mlcommons/projects/26) for more detailed user stories.

The development workflow goes as follow:

- Read above how the repo is [designed](#design).
- [Fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) the repository: https://github.com/mlcommons/croissant.
- Clone the newly forked repository:
  ```bash
  git clone git@github.com:<YOUR_GITHUB_LDAP>/croissant.git
  ```
- Create a new branch:
  ```bash
  cd croissant/
  git checkout -b feature/my-awesome-new-feature
  ```
- Install the repository and dev tools:
  ```bash
  cd python/ml_croissant
  pip install -e .[dev]
  ```
- Code the feature. We support [VS Code](https://code.visualstudio.com) with pre-set settings.
- Push to GitHub:
  ```bash
  git add .
  git push --set-upstream origin feature/my-awesome-new-feature
  ```
- Update your code until all tests are green:
  - `pytest` runs unit tests.
  - `pytype -j auto` runs pytype.
- Open a pull request (PR) with the main branch of https://github.com/mlcommons/croissant, and ask for feedback!

## Debug

You can debug the validation of the file using the `--debug` flag:

```bash
python scripts/validate.py --file ../../datasets/titanic/metadata.json --debug
```

This will:
1. print extra information, like the generated nodes;
2. save the generated structure graph to a folder indicated in the logs.
