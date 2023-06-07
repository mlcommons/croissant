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

Here is a high-level roadmap for the library.
If you're interested in developing one of the points, please [create a discussion](https://github.com/mlcommons/datasets_format/discussions).

- [x] First version can verify and load simple datasets like the Titanic dataset.
- [ ] Refactor the code. The structure should make the flow more explicit. See issue [#13](https://github.com/mlcommons/datasets_format/issues/13).
- [ ] [`Good first issue!`] Support Python>=3.8. See issue [#28](https://github.com/mlcommons/datasets_format/issues/28).
- [ ] [`Good first issue!`] Implement more readers. `ReadCsv` becomes `Read` and supports: CSV, Parquet, JSON, JSON-L, text files.
- [ ] [`Good first issue!`] In `Download`, check SHA256 or MD5.
- [ ] [`Good first issue!`] Refactor tests to support golden files. See issue [#14](https://github.com/mlcommons/datasets_format/issues/14).
- [ ] [`Difficult issue!`] Support complex joins (i.e., for the MovieLens dataset).
- [ ] [`Difficult issue!`] Support nested fields (i.e., for the MovieLens dataset).
- [ ] Better handling of issues during dynamic analysis. See issue [#39](https://github.com/mlcommons/datasets_format/issues/39).
- [ ] Remove the usage of `rdflib.Graph` and parse the JSON directly.
- [ ] Distinguish `sources` from `references` in the codebase. See issue [#40](https://github.com/mlcommons/datasets_format/issues/40).
- [ ] Connect the library to [Hugging Face datasets](https://github.com/huggingface/datasets).
- [ ] Connect the library to [TFDS](https://github.com/tensorflow/datasets).
- [ ] [`Difficult issue!`] Smarter operations. Some operations are repeated, so the computation graph could be improved.
- [ ] [`Good first issue!`] Better type checking. Some advanced types (e.g., URLs) can be better type checked (e.g., URL has the right form).
- [ ] [`Difficult issue!`] Use [Dask](https://github.com/dask/dask) to scale DataFrames and the computation graph to bigger datasets (i.e., for the C4 dataset).
