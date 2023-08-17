"""Defines the public interface to the `ml_croissant` package."""
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.datasets import Dataset

__all__ = [
    "Dataset",
    "ValidationError",
]
