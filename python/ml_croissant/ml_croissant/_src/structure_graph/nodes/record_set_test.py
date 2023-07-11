"""record_set module."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.nodes import Field, RecordSet
import networkx as nx
import pytest
from rdflib import term


@pytest.mark.parametrize(
    ["data", "error"],
    [
        [
            '{"foo": "bar"}',
            (
                "[record_set(record_set_name)] http://mlcommons.org/schema/data should"
                " declare a list. Got: <class 'dict'>."
            ),
        ],
        [
            "[]",
            (
                "[record_set(record_set_name)] http://mlcommons.org/schema/data should"
                " declare a non empty list."
            ),
        ],
        [
            '[[{"foo": "bar"}]]',
            (
                "[record_set(record_set_name)] http://mlcommons.org/schema/data should"
                " declare a list of dict. Got: a list of <class 'list'>."
            ),
        ],
        [
            '[{"foo": "bar"}]',
            (
                "[record_set(record_set_name)] Line #0 doesn't have the expected"
                " columns. Expected: {'field_name'}. Got: {'foo'}."
            ),
        ],
    ],
)
def test_invalid_data(data, error):
    issues = Issues()
    graph = nx.MultiDiGraph()
    record_set = RecordSet(
        issues=issues,
        bnode=term.BNode("rdf_id"),
        graph=graph,
        name="record_set_name",
        parents=(),
        data=data,
    )
    field = Field(
        issues=issues,
        bnode=term.BNode("rdf_id"),
        graph=graph,
        name="field_name",
        parents=(record_set,),
    )
    graph.add_node(record_set)
    graph.add_node(field)
    record_set.check()
    assert error in issues.errors
