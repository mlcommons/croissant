import pytest

from mlcroissant._src.core.context import Context
from mlcroissant._src.operation_graph.graph import OperationGraph
from mlcroissant._src.operation_graph.operations import Extract
from mlcroissant._src.operation_graph.operations import ReadLines
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.structure_graph.nodes.source import Transform


@pytest.mark.parametrize(
    "encoding_format, un_archive_transform, read_lines_transform, expected_extract, expected_read_lines",
    [
        # Case 1: Implicit Unarchive (Existing Behavior)
        ("application/zip", None, None, True, False),
        # Case 2: Explicit Unarchive (New Behavior)
        ("text/plain", True, None, True, False),
        # Case 3: Explicit Skip Unarchive (New Behavior)
        ("application/zip", False, None, False, False),
        # Case 4: ReadLines
        ("text/plain", None, True, False, True),
        # Case 5: Combined Unarchive and ReadLines
        ("application/zip", True, True, True, True),
    ],
)
def test_operation_graph_logic(
    encoding_format,
    un_archive_transform,
    read_lines_transform,
    expected_extract,
    expected_read_lines,
):
    ctx = Context()

    # Setup Metadata (root)
    metadata = Metadata(ctx=ctx, name="metadata")
    ctx.graph.add_node(metadata)

    # Setup FileObject (container)
    file_object = FileObject(
        ctx=ctx,
        name="container",
        id="container",
        encoding_formats=[encoding_format],
        content_url="http://example.com/container",
    )
    ctx.graph.add_node(file_object)
    ctx.graph.add_edge(metadata, file_object)

    # Setup Source with optional transforms
    transforms = []
    if un_archive_transform is not None:
        transforms.append(Transform(un_archive=un_archive_transform))
    if read_lines_transform is not None:
        transforms.append(Transform(read_lines=read_lines_transform))

    source = Source(ctx=ctx, file_object=file_object.name, transforms=transforms)

    # Setup FileSet (contained)
    file_set = FileSet(
        ctx=ctx, name="contained", contained_in=[source], encoding_formats=["text/csv"]
    )
    ctx.graph.add_node(file_set)
    ctx.graph.add_edge(file_object, file_set)

    # Build Graph
    graph = OperationGraph.from_nodes(ctx, metadata)

    # Assertions
    operations = graph.operations.nodes
    has_extract = any(isinstance(op, Extract) for op in operations)
    has_read_lines = any(isinstance(op, ReadLines) for op in operations)
    assert has_extract == expected_extract
    assert has_read_lines == expected_read_lines
