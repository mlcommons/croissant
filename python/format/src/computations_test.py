"""computations_test module."""

from etils import epath
from format.src.computations import (
    Download,
    InitOperation,
    ReadCsv,
    ReadField,
    GroupRecordSet,
)
from format.src.errors import Issues
from format.src.nodes import Node
import pytest


@pytest.mark.parametrize(
    ["operation_cls", "kwargs", "expected_str"],
    [
        (Download, {"url": "http://mlcommons.org"}, "Download(node_name)"),
        (InitOperation, {}, "InitOperation(node_name)"),
        (
            ReadCsv,
            {"croissant_folder": epath.Path(), "url": "http://mlcommons.org"},
            "ReadCsv(node_name)",
        ),
        (ReadField, {}, "ReadField(node_name)"),
        (GroupRecordSet, {}, "GroupRecordSet(node_name)"),
    ],
)
def test_str_representation(operation_cls, kwargs, expected_str):
    node = Node(
        issues=Issues(),
        graph=None,
        node=None,
        name="node_name",
        parent_uid="parent_name",
    )
    operation = operation_cls(node=node, **kwargs)
    assert str(operation) == expected_str
