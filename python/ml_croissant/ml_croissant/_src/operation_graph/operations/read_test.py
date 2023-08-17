"""read_test module."""

from etils import epath
from ml_croissant._src.operation_graph.operations.read import Read
from ml_croissant._src.tests.nodes import empty_file_object


def test_str_representation():
    operation = Read(
        node=empty_file_object,
        folder=epath.Path(),
        url="http://mlcommons.org",
        fields=[],
    )
    assert str(operation) == "Read(file_object_name)"
