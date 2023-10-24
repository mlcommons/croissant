"""Testing utils for `Node`."""

import functools
from typing import Callable, TypeVar

from etils import epath

from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


class _EmptyNode(Node):
    def __post_init__(self):
        pass

    @classmethod
    def from_jsonld(cls):
        pass

    def to_json(self):
        pass


def _node_params(**kwargs):
    params = {
        "issues": Issues(),
        "context": Context(),
        "name": "node_name",
        "folder": epath.Path(),
    }
    for key, value in kwargs.items():
        params[key] = value
    return params


T = TypeVar("T")


def create_test_node(cls: type[T], **kwargs) -> T:
    """Utils to easily create new nodes in tests.

    Usage:

    Instead of writing:
    ```python
    node = FileSet(
        issues=...,
        name=...,
        folder=...,
        description="Description"
    )
    ```

    Use:
    ```python
    node = create_test_file_set(description="Description")
    ```
    """
    return cls(**_node_params(**kwargs))


create_test_field: Callable[..., Field] = functools.partial(  # type: ignore  # Force mypy types.
    create_test_node, Field, name="field_name"
)
create_test_file_object: Callable[..., FileObject] = functools.partial(  # type: ignore  # Force mypy types.
    create_test_node, FileObject, name="file_object_name"
)
create_test_file_set: Callable[..., FileSet] = functools.partial(  # type: ignore  # Force mypy types.
    create_test_node, FileSet, name="file_set_name"
)
create_test_record_set: Callable[..., RecordSet] = functools.partial(  # type: ignore  # Force mypy types.
    create_test_node, RecordSet, name="record_set_name"
)


empty_field: Field = create_test_node(Field, name="field_name")
empty_file_object: FileObject = create_test_node(FileObject, name="file_object_name")
empty_file_set: FileSet = create_test_node(FileSet, name="file_set_name")
empty_node: Node = create_test_node(_EmptyNode)
empty_record_set: RecordSet = create_test_node(RecordSet, name="record_set_name")
