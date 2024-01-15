"""A minimal PyTorch adapter on top of mlcroissant.

The DataPipe abstraction is currently used to enable composing more complex
datasets.
"""

import enum
from typing import Any, Dict, Optional

try:
    import torchdata.datapipes as dp
except ImportError:
    dp = None
    INSTALL_MESSAGE = "torchdata is not installed and is a dependency."

import mlcroissant as mlc


class LoaderSpecificationDataType(enum.Enum):
    """Enum representing data type specification."""

    INFER = "infer"
    UTF8 = "utf8"


# Map from name to DataType
LoaderSpecificationTypes = Dict[str, Optional[LoaderSpecificationDataType]]


def infer_data_type(val: Any) -> Optional[LoaderSpecificationDataType]:
    """Automatically infer LoaderSpecificationDataType from val."""
    if isinstance(val, bytes):
        return LoaderSpecificationDataType.UTF8

    return None


def apply_data_type_transformation(
    val: Any, data_type: Optional[LoaderSpecificationDataType]
) -> Any:
    """Transform val according to data_type."""
    if data_type == LoaderSpecificationDataType.INFER:
        # Infer and Forward
        data_type = infer_data_type(val)
        return apply_data_type_transformation(val, data_type)

    if data_type == LoaderSpecificationDataType.UTF8:
        return val.decode("utf-8")

    return val


if dp is None:
    # Failed to import dependencies. Stub out affected methods.

    def _as_datapipe_helper(
        factory: "LoaderFactory",
        record_set: str,
        specification: Optional[LoaderSpecificationTypes],
    ) -> Any:
        raise NotImplementedError(INSTALL_MESSAGE)

else:
    IterDataPipe = dp.iter.IterDataPipe
    IterableWrapper = dp.iter.IterableWrapper

    def _as_datapipe_helper(
        factory: "LoaderFactory",
        record_set: str,
        specification: Optional[LoaderSpecificationTypes],
    ) -> Any:
        dataset = mlc.Dataset(file=factory.file)
        records = dataset.records(record_set=record_set)
        datapipe = IterableWrapper(records)
        if specification:
            row_processor = factory._get_row_processor(specification)
            datapipe = datapipe.map(row_processor)

        return datapipe


class LoaderFactory:
    """Used to create loaders and get metadata."""

    def __init__(self, file: str):
        """Initialize LoaderFactory with a Croissant file."""
        self.file = file

    def _get_row_processor(self, specification: LoaderSpecificationTypes):
        """Remap columns types to desired type."""

        def row_processor(row):
            for k, v in specification.items():
                row[k] = apply_data_type_transformation(row[k], v)
            return row

        return row_processor

    def as_datapipe(
        self,
        record_set: str,
        specification: Optional[LoaderSpecificationTypes] = None,
    ) -> Any:
        """Load the record set as a DataPipe."""
        datapipe = _as_datapipe_helper(self, record_set, specification)
        # TODO: cast to IterDataPipe
        return datapipe
