from typing import Any

import numpy as np


def convert_dtype(dtype: Any):
    """Converts from NumPy/Pandas to Croissant data types."""
    if dtype == np.int64:
        return "https://schema.org/Integer"
    elif dtype == np.float64:
        return "https://schema.org/Float"
    elif dtype == np.bool_:
        return "https://schema.org/Boolean"
    elif dtype == np.str_ or dtype == object:
        return "https://schema.org/Text"
    else:
        raise NotImplementedError(dtype)
