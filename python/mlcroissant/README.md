# mlcroissant 🥐

Discover `mlcroissant 🥐` with this
[introduction tutorial in Google Colab](https://colab.sandbox.google.com/github/mlcommons/croissant/blob/main/python/mlcroissant/recipes/introduction.ipynb).

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

## Programmatically build JSON-LD files

You can programmatically build Croissant JSON-LD files using the Python API.

```python
import mlcroissant as mlc
metadata=mlc.nodes.Metadata(
  name="...",
)
metadata.to_json()  # this returns the JSON-LD file.
```

For a full working example, refer to
[the script to convert Hugging Face datasets to Croissant files](./scripts/from_huggingface_to_croissant.py).
This script uses the Python API to programmatically build JSON-LD files.

## Run tests

All tests can be run from the Makefile:

```bash
make tests
```

## Design

The most important modules in the library are:

- [`mlcroissant/_src/structure_graph`](./mlcroissant/_src/structure_graph/graph.py) is responsible for the **static analysis** of the Croissant files. We convert Croissant files to a Python representation called "**structure graph**" (using [NetworkX](https://networkx.org/)). In the process, we catch any static analysis issues (e.g., a missing mandatory field or a logic problem in the file).
- [`mlcroissant/_src/operation_graph`](./mlcroissant/_src/operation_graph/graph.py) is responsible for the **dynamic analysis** of the Croissant files (i.e., actually loading the dataset by yielding examples). We convert the structure graph into an "**operation graph**". Operations are the unit transformations that allow to build the dataset (like [`Download`](./mlcroissant/_src/operation_graph/operations/download.py), [`Extract`](./mlcroissant/_src/operation_graph/operations/extract.py), etc).

Other important modules are:

- [`mlcroissant/_src/core`](./mlcroissant/_src/core) defines all needed core internals. For instance, [`Issues`](./mlcroissant/_src/core/issues.py) are a way to track errors and warning during the analysis of Croissant files.
- [`mlcroissant/__init__.py`](./mlcroissant/__init__.py) declares the public API with [`mlcroissant.Dataset`](./mlcroissant/_src/datasets.py).

For the full design, refer to the [design doc](https://docs.google.com/document/d/1zYQIUX9ae1sZOOBq9OCsJ8JW8-Ejy3NLSeqaI5LtOEM/edit?resourcekey=0-CK78DfFvF7fnufyZqF3h3Q) for an overview of the implementation.

## Contribute

All contributions are welcome! We even have [good first issues](https://github.com/mlcommons/croissant/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to start in the project. Refer to the [GitHub project](https://github.com/orgs/mlcommons/projects/26) for more detailed user stories.

The development workflow goes as follow:

- Read above how the repo is [designed](#design).

### Contribute on Codespaces.
An easy way to contribute to `mlcroissant` is using Croissant's configured [codespaces](https://docs.github.com/en/codespaces/overview).
To start a codespace:

- On Croissant's main [repo page](https://github.com/mlcommons/croissant), click on the `<Code>` button and select the `Codespaces` tab. You can start a new codespace by clicking on the `+` sign on the left side of the tab. By default, the codespace will start on Croissant's `main` branch, unless you select otherwise from the branches drop-down menu on the left side.
- While building the environment, your codespaces will install all `mlcroissant`'s required dependencies - so that you can start coding right away! Of course, you can [further personalize](https://docs.github.com/en/codespaces/customizing-your-codespace/personalizing-github-codespaces-for-your-account) your codespace.
- To start contributing to Croissant:
  - Create a new branch from the `Terminal` tab in the bottom panel of your codespace with `git checkout -b feature/my-awesome-new-feature`
  - You can create new commits, and run most git commands from the `Source Control` tab in the left panel of your codespace. Alternatively, use the `Terminal` in the bottom panel of your codespace.
  - Iterate on your code until all tests are green (you can run tests with `make pytest` or form the `Tests` tab in the left panel of your codespace).
  - Open a pull request (PR) with the main branch of https://github.com/mlcommons/croissant, and ask for feedback!

### Contribute via GitHub clone.
Alternatively, you can contribute to `mlcroissant` using the "classic" GitHub workflow:

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
  cd python/mlcroissant
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
