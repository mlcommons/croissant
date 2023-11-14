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
