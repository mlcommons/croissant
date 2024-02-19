"""Testing utils for `Operation`."""

from mlcroissant._src.operation_graph.base_operation import Operations


def operations() -> Operations:
    """An empty graph of operations to be used in tests."""
    return Operations()
