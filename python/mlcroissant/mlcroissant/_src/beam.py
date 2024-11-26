"""Beam module."""

from __future__ import annotations

from collections.abc import Mapping
import functools
import typing
from typing import Any, Callable

from etils import epath

from mlcroissant._src.datasets import Dataset
from mlcroissant._src.datasets import Filters

if typing.TYPE_CHECKING:
    import apache_beam as beam


def _beam_ptransform_fn(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Lazy version of `@beam.ptransform_fn` in case Beam is not installed."""
    lazy_decorated_fn = None

    @functools.wraps(fn)
    def decorated(*args, **kwargs):
        nonlocal lazy_decorated_fn
        # Actually decorate the function only the first time it is called
        if lazy_decorated_fn is None:
            import apache_beam as beam

            lazy_decorated_fn = beam.ptransform_fn(fn)
        return lazy_decorated_fn(*args, **kwargs)

    return decorated


@_beam_ptransform_fn
def ReadFromCroissant(
    pipeline: beam.Pipeline,
    *,
    jsonld: epath.PathLike | Mapping[str, Any],
    record_set: str,
    mapping: Mapping[str, epath.PathLike] | None = None,
    filters: Filters | None = None,
):
    """Returns an Apache Beam reader to generate the dataset using e.g. Spark.

    Example of usage:

    ```python
    import apache_beam as beam
    from apache_beam.options import pipeline_options
    import mlcroissant as mlc

    jsonld = "https://huggingface.co/api/datasets/ylecun/mnist/croissant"

    options = pipeline_options.PipelineOptions()
    with beam.Pipeline(options=options) as pipeline:
        _ = pipeline | mlc.ReadFromCroissant(
            jsonld=jsonld,
            record_set="mnist",
        )
    ```

    The sharding is done on the filtered files. This is currently optimized for Hugging
    Face datasets, so it raises an error if the dataset is not a Hugging Face dataset.

    Args:
        pipeline: A Beam pipeline (automatically set).
        jsonld: A JSON object or a path to a Croissant file (URL, str or pathlib.Path).
        record_set: The name of the record set to generate.
        mapping: Mapping filename->filepath as a Python dict[str, str] to handle manual
            downloads. If `document.csv` is the FileObject and you downloaded it to
            `~/Downloads/document.csv`, you can specify `mapping={"document.csv":
            "~/Downloads/document.csv"}`.
        filters: A dictionary mapping a field ID to the value we want to filter in. For
            example, when writing {'data/split': 'train'}, we want to keep all records
            whose field `data/split` takes the value `train`.

    Returns:
        A Beam PCollection with all the records where each element contains a tuple with
            a) a global index, and
            b) the content of the record.

    Raises:
        A ValueError if the dataset is not streamable.
    """
    dataset = Dataset(jsonld=jsonld, mapping=mapping)
    return dataset.records(record_set, filters=filters).beam_reader(
        pipeline,
        filters=filters,
    )
