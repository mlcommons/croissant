import json
from unittest import mock

from etils import epath
from format.src import graphs

# Path to a valid JSON to define a valid graph.
path = epath.Path(__file__).parent / "tests/graphs/valid.json"
with path.open() as file:
    rfd_dict = json.load(file)
    graph = graphs.load_rdf_graph(rfd_dict)


def test_there_exists_at_least_one_property():
    assert graphs._there_exists_at_least_one_property(
        {"property1", "property2"}, ["property0", "property1"]
    )
    assert not graphs._there_exists_at_least_one_property(
        {"property1", "property2"}, []
    )
    assert not graphs._there_exists_at_least_one_property(
        {"property1", "property2"}, ["property0"]
    )
