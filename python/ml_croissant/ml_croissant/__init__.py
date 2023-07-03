"""Defines the public interface to the `ml_croissant` package."""
from ml_croissant._src.datasets import Dataset
from ml_croissant._src.core.issues import ValidationError

__all__ = [
    "Dataset",
    "ValidationError",
]
