"""Testing utils for `Node`."""

import functools
from typing import Any

from etils import epath
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes import (
    Field,
    FileObject,
    FileSet,
    RecordSet,
)
import networkx as nx
from rdflib import term


class _EmptyNode(Node):
    def check(self):
        pass


def _node_params(**kwargs):
    params = {
        "issues": Issues(),
        "bnode": term.BNode("rdf_id"),
        "graph": nx.MultiDiGraph(),
        "name": "node_name",
        "folder": epath.Path(),
        "parents": (),
    }
    for key, value in kwargs.items():
        params[key] = value
    return params


def create_test_node(cls: type[Any], **kwargs):
    """Utils to easily create new nodes in tests.

    Usage:

    Instead of writing:
    ```python
    node = FileSet(
        issues=...,
        bnode=...,
        graph=...,
        name=...,
        folder=...,
        parents=...,
        description="Description"
    )
    ```

    Use:
    ```python
    node = test_node(FileSet, description="Description")
    ```
    """
    return cls(**_node_params(**kwargs))


create_test_field = functools.partial(create_test_node, Field, name="field_name")
create_test_file_object = functools.partial(
    create_test_node, FileObject, name="file_object_name"
)
create_test_file_set = functools.partial(
    create_test_node, FileSet, name="file_set_name"
)
create_test_record_set = functools.partial(
    create_test_node, RecordSet, name="record_set_name"
)


empty_field = create_test_node(Field, name="field_name")
empty_file_object = create_test_node(FileObject, name="file_object_name")
empty_file_set = create_test_node(FileSet, name="file_set_name")
empty_node = create_test_node(_EmptyNode)
empty_record_set = create_test_node(RecordSet, name="record_set_name")
