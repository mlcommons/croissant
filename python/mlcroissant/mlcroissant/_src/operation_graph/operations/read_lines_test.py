import os

from etils import epath
import pytest

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.operations.read_lines import ReadLines


def test_read_lines(tmp_path):
    # Setup temporary file
    file_path = tmp_path / "test.txt"
    file_path.write_text("line1\nline2 \n line3\n")

    # Setup operation
    from mlcroissant._src.core.context import Context
    from mlcroissant._src.operation_graph.base_operation import Operations
    from mlcroissant._src.structure_graph.nodes.file_set import FileSet

    ctx = Context()
    node = FileSet(ctx=ctx, name="test_fileset")
    operations = Operations()
    operation = ReadLines(operations=operations, node=node)
    path = Path(filepath=epath.Path(file_path), fullpath=epath.Path(file_path))

    # Execute operation
    lines = list(operation.call(path))

    # Assertions
    assert lines == ["line1", "line2", "line3"]
