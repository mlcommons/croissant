"""filter_test module."""

import pytest

from mlcroissant._src.operation_graph.operations.filter import FilterFiles
from mlcroissant._src.operation_graph.operations.filter import match_path
from mlcroissant._src.tests.nodes import empty_file_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = FilterFiles(operations=operations(), node=empty_file_set)
    assert str(operation) == "FilterFiles(file_set_name)"


@pytest.mark.parametrize(
    ["patterns", "path", "expected"],
    [
        [["**/*.csv"], "/path/to/this.csv", True],
        [["**/*.csv", "**/*.json"], "/path/to/this.csv", True],
        [["**/*.csv", "**/*.json"], "/path/to/this.parquet", False],
        [None, "/path/to/this.csv", True],
        [[], "/path/to/this.csv", True],
    ],
)
def test_match_path(patterns, path, expected):
    assert match_path(patterns, path) == expected
