"""nodes_test module."""

import dataclasses
import json

from etils import epath
from ml_croissant._src import graphs
from ml_croissant._src import nodes

# Path to a valid JSON to define a valid graph.
path = epath.Path(__file__).parent / "tests/graphs/valid.json"
with path.open() as file:
    rfd_dict = json.load(file)
    operations = graphs.load_rdf_graph(rfd_dict)


def test_there_exists_at_least_one_property():
    @dataclasses.dataclass
    class Node:
        property1: str
        property2: str

    node = Node(property1="property1", property2="property2")
    # pylint:disable=protected-access
    assert nodes._there_exists_at_least_one_property(node, ["property0", "property1"])
    assert not nodes._there_exists_at_least_one_property(node, [])
    assert not nodes._there_exists_at_least_one_property(node, ["property0"])
