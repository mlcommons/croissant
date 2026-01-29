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
    assert lines == [
        Path(
            filepath=path.filepath / "line1",
            fullpath=epath.Path("line1"),
        ),
        Path(
            filepath=path.filepath / "line2",
            fullpath=epath.Path("line2"),
        ),
        Path(
            filepath=path.filepath / "line3",
            fullpath=epath.Path("line3"),
        ),
    ]


def test_read_lines_with_multiple_files_error(tmp_path):
    # Setup temporary directory with multiple files
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.txt").touch()

    # Setup operation
    from mlcroissant._src.core.context import Context
    from mlcroissant._src.operation_graph.base_operation import Operations
    from mlcroissant._src.structure_graph.nodes.file_set import FileSet

    ctx = Context()
    node = FileSet(ctx=ctx, name="test_fileset")
    operations = Operations()
    operation = ReadLines(operations=operations, node=node)
    path = Path(filepath=epath.Path(tmp_path), fullpath=epath.Path(tmp_path))

    # Assertions
    with pytest.raises(ValueError, match="ReadLines expects a single file"):
        list(operation.call(path))
