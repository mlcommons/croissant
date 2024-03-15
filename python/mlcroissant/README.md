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

The command can fail, for example, due to missing dependencies, e.g.:

```bash
Failed to build pygraphviz
ERROR: Could not build wheels for pygraphviz, which is required to install pyproject.toml-based projects
```

This can be fixed by running

```bash
sudo apt-get install python3-dev graphviz libgraphviz-dev pkg-config
```

### Conda installation
Conda can help create a consistent environment.
It can also be useful to install packages without root access.
To use Conda, run:

```bash
conda create --name croissant python=3.10 -y
conda activate croissant
conda install graphviz
python3 -m pip install ".[dev]"
```

## Verify/load a Croissant dataset

```bash
mlcroissant validate --jsonld ../../datasets/titanic/metadata.json
```

The command:

- Exits with 0, prints `Done` and displays encountered warnings, when no error was found in the file.
- Exits with 1 and displays all encountered errors/warnings, otherwise.

Similarly, you can generate a dataset by launching:

```bash
mlcroissant load \
    --jsonld ../../datasets/titanic/metadata.json \
    --record_set passengers \
    --num_records 10
```

### Loading a `distribution` via `git+https`

If the `encodingFormat` of a `distribution` is `git+https`, please provide the username and password by setting the `CROISSANT_GIT_USERNAME` and `CROISSANT_GIT_PASSWORD` environment variables. These will be used to construct the authentication necessary to load the distribution.

Note that, for datasets hosted on HuggingFace, `CROISSANT_GIT_USERNAME` and `CROISSANT_GIT_PASSWORD` should correspond respectively to your HuggingFace's username and User Access Token. User Access Tokens can be generated following [this guide](https://huggingface.co/docs/hub/security-tokens#user-access-tokens).

### Loading a `distribution` via HTTP with Basic Auth

If the `contentUrl` of a `distribution` requires authentication via Basic Auth, please provide the username and password by setting the `CROISSANT_BASIC_AUTH_USERNAME` and `CROISSANT_BASIC_AUTH_PASSWORD` environment variables. These will be used to construct the authentication necessary to load the distribution.

## Programmatically build JSON-LD files

You can programmatically build Croissant JSON-LD files using the Python API.

```python
import mlcroissant as mlc
metadata=mlc.nodes.Metadata(
  name="...",
)
metadata.to_json()  # this returns the JSON-LD file.
```

## Add new properties to the standard

Nodes (Metadata, RecordSets, etc) implement [PEP 681](https://peps.python.org/pep-0681/). So you can declare RDF triplets using the [dataclass](https://docs.python.org/3/library/dataclasses.html) syntax.

**Example 1**: implement [CreativeWork](https://schema.org/CreativeWork):

```python
@mlc_dataclasses.dataclass
class CreativeWork(Node):

    JSONLD_TYPE = SDO.CreativeWork           # https://schema.org/CreativeWork

    name: str | None = mlc_dataclasses.jsonld_field(
        cardinality="ONE",                   # Cardinality can be ONE or MANY
        default=None,                        # Specify the default value in Python
        description="The name of the item.", # The full description
        input_types=[SDO.Text],              # The schema.org type
        url=SDO.name,                        # The URL of the property
    )
```

**Example 2**: implement [RecordSet](https://mlcommons.github.io/croissant/docs/croissant-spec.html#recordset):

```python
@mlc_dataclasses.dataclass
class RecordSet(Node):
    JSONLD_TYPE = constants.ML_COMMONS_RECORD_SET_TYPE

    fields: list[Field] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",                  # Example with cardinality=="MANY"
        default_factory=list,
        description=(
            "A data element that appears in the records of the RecordSet (e.g., one"
            " column of a table)."
        ),
        input_types=[Field],                 # Types can also be other nodes (here `Field`)
        url=constants.ML_COMMONS_FIELD,
    )
```

**Example 3**: specify a version (by default all versions):

```python
@mlc_dataclasses.dataclass
class Field(Node):
    is_enumeration: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_IS_ENUMERATION,
        versions=[CroissantVersion.V_0_8],   # `is_enumeration` is only valid for v0.8, not v1.0
    )
```

## Run tests

All tests can be run from the Makefile:

```bash
make tests
```

Note that `git lfs` should be installed to successfully pass all tests:

```bash
git lfs install
```

## Design

The most important modules in the library are:

- [`mlcroissant/_src/structure_graph`](./mlcroissant/_src/structure_graph/graph.py) is responsible for the **static analysis** of the Croissant files. We convert Croissant files to a Python representation called "**structure graph**" (using [NetworkX](https://networkx.org/)). In the process, we catch any static analysis issues (e.g., a missing mandatory field or a logic problem in the file).
- [`mlcroissant/_src/operation_graph`](./mlcroissant/_src/operation_graph/graph.py) is responsible for the **dynamic analysis** of the Croissant files (i.e., actually loading the dataset by yielding examples). We convert the structure graph into an "**operation graph**". Operations are the unit transformations that allow to build the dataset (like [`Download`](./mlcroissant/_src/operation_graph/operations/download.py), [`Extract`](./mlcroissant/_src/operation_graph/operations/extract.py), etc).

Other important modules are:

- [`mlcroissant/_src/core`](./mlcroissant/_src/core) defines all needed core internals. For instance, [`Issues`](./mlcroissant/_src/core/issues.py) are a way to track errors and warning during the analysis of Croissant files.
- [`mlcroissant/__init__.py`](./mlcroissant/__init__.py) declares the public API with [`mlcroissant.Dataset`](./mlcroissant/_src/datasets.py).

For the full design, refer to the [design doc](https://docs.google.com/document/d/1zYQIUX9ae1sZOOBq9OCsJ8JW8-Ejy3NLSeqaI5LtOEM/edit?resourcekey=0-CK78DfFvF7fnufyZqF3h3Q) for an overview of the implementation.

**Caching**. By default, all downloaded/extracted files are cached in `~/.cache/croissant`, but you can overwrite this by setting the environment variable `$CROISSANT_CACHE`.

## Contribute

All contributions are welcome! We even have [good first issues](https://github.com/mlcommons/croissant/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to start in the project. Refer to the [GitHub project](https://github.com/orgs/mlcommons/projects/26) for more detailed user stories and read above how the repo is [designed](#design).

An easy way to contribute to `mlcroissant` is using Croissant's configured [codespaces](https://docs.github.com/en/codespaces/overview).
To start a codespace:

- On Croissant's main [repo page](https://github.com/mlcommons/croissant), click on the `<Code>` button and select the `Codespaces` tab. You can start a new codespace by clicking on the `+` sign on the left side of the tab. By default, the codespace will start on Croissant's `main` branch, unless you select otherwise from the branches drop-down menu on the left side.
- While building the environment, your codespaces will install all `mlcroissant`'s required dependencies - so that you can start coding right away! Of course, you can [further personalize](https://docs.github.com/en/codespaces/customizing-your-codespace/personalizing-github-codespaces-for-your-account) your codespace.
- To start contributing to Croissant:
  - Create a new branch from the `Terminal` tab in the bottom panel of your codespace with `git checkout -b feature/my-awesome-new-feature`
  - You can create new commits, and run most git commands from the `Source Control` tab in the left panel of your codespace. Alternatively, use the `Terminal` in the bottom panel of your codespace.
  - Iterate on your code until all tests are green (you can run tests with `make pytest` or form the `Tests` tab in the left panel of your codespace).
  - Open a pull request (PR) with the main branch of https://github.com/mlcommons/croissant, and ask for feedback!

Alternatively, you can contribute to `mlcroissant` using the "classic" GitHub workflow:

## Debug

You can debug the validation of the file using the `--debug` flag:

```bash
mlcroissant validate --jsonld ../../datasets/titanic/metadata.json --debug
```

This will:
1. print extra information, like the generated nodes;
2. save the generated structure graph to a folder indicated in the logs.

## Publishing packages

To publish a package,

1. Bump the version in `croissant/python/mlcroissant/pyproject.toml`.
2. Publish a release in GitHub. The workflow script `python-publish.yml` will trigger and publish the package to PyPI.

