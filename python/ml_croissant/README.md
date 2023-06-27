# 🥐 ML Croissant

## Install

Using Python>=3.8:

```bash
python -m pip install .
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
python scripts/generate.py \
    --file ../../datasets/titanic/metadata.json \
    --record_set passengers \
    --num_records 10
```

## Run tests

```bash
python -m pip install ".[dev]"
pytest .
```

## Roadmap

Refer to the [design doc](https://docs.google.com/document/d/1zYQIUX9ae1sZOOBq9OCsJ8JW8-Ejy3NLSeqaI5LtOEM/edit?resourcekey=0-CK78DfFvF7fnufyZqF3h3Q) for an overview of the implementation.

Refer to the [GitHub project](https://github.com/orgs/mlcommons/projects/26) for more detailed user stories.

All contributions are welcome! We even have [good first issues](https://github.com/mlcommons/croissant/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to start in the project.
