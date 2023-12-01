from typing import Any

import numpy as np

import mlcroissant as mlc


def convert_dtype(dtype: Any):
    """Converts from NumPy/Pandas to Croissant data types."""
    if dtype == np.int64:
        return mlc.DataType.INTEGER
    elif dtype == np.float64:
        return mlc.DataType.FLOAT
    elif dtype == np.bool_:
        return mlc.DataType.BOOL
    elif dtype == np.str_ or dtype == object:
        return mlc.DataType.TEXT
    else:
        raise NotImplementedError(dtype)


MLC_DATA_TYPES = [
    mlc.DataType.TEXT,
    mlc.DataType.FLOAT,
    mlc.DataType.INTEGER,
    mlc.DataType.BOOL,
    mlc.DataType.URL,
]

STR_DATA_TYPES = [
    str(data_type).replace("https://schema.org/", "") for data_type in MLC_DATA_TYPES
]


def str_to_mlc_data_type(data_type: str) -> mlc.DataType | None:
    for str_data_type, mlc_data_type in zip(STR_DATA_TYPES, MLC_DATA_TYPES):
        if data_type == str_data_type:
            return mlc_data_type
    return None


def mlc_to_str_data_type(data_type: str) -> mlc.DataType | None:
    for str_data_type, mlc_data_type in zip(STR_DATA_TYPES, MLC_DATA_TYPES):
        if data_type == mlc_data_type:
            return str_data_type
    return None
