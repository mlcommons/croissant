# Format

## Install

Using Python>=3.8:

```bash
python -m pip install .
```

## Validate a file

```bash
python scripts/validate.py --file ../../datasets/titanic/metadata.json
```

The command:

- Exits with 0, prints `Done` and displays encountered warnings, when no error was found in the file.
- Exits with 1 and displays all encountered errors/warnings, otherwise.

## Run tests

```bash
python -m pip install ".[dev]"
pytest .
```
