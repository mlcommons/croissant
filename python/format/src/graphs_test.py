import json
from unittest import mock

from etils import epath
from format.src import errors
from format.src import graphs
import networkx as nx
import rdflib

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


def test_check_metadata():
    issues = errors.Issues()
    with mock.patch.object(
            graphs, "_check_node_has_properties"
        ) as check_node_has_properties, mock.patch.object(graphs, "_check_node_has_type"):
        graphs.check_metadata(issues, [], "dataset_name")
        check_node_has_properties.assert_called_once_with(
            issues,
            [],
            mandatory_properties=[
                rdflib.URIRef("https://schema.org/citation"),
                rdflib.URIRef("https://schema.org/license"),
                rdflib.URIRef("https://schema.org/name"),
                rdflib.URIRef("https://schema.org/url"),
            ],
            optional_properties=[rdflib.URIRef("https://schema.org/description")],
        )
        assert not issues.errors
        assert not issues.warnings


def test_check_distribution():
    issues = errors.Issues()
    with mock.patch.object(
        graphs, "_check_node_has_properties"
    ) as check_node_has_properties:
        node = graph.pred[rdflib.URIRef("https://schema.org/FileObject")]
        graphs.check_distribution(issues, graph, node, "dataset_name")
        check_node_has_properties.assert_called_once_with(
            issues,
            mock.ANY,
            mandatory_properties=[
                rdflib.URIRef("https://schema.org/contentSize"),
                rdflib.URIRef("https://schema.org/contentUrl"),
                rdflib.URIRef("https://schema.org/encodingFormat"),
            ],
            exclusive_properties=[
                [
                    rdflib.URIRef("https://schema.org/md5"),
                    rdflib.URIRef("https://schema.org/sha256"),
                ]
            ],
        )
        assert not issues.errors
        assert not issues.warnings


def test_check_record_set():
    issues = errors.Issues()
    node = graph.pred[rdflib.URIRef("http://mlcommons.org/schema/RecordSet")]
    with mock.patch.object(
        graphs, "_check_node_has_properties"
    ) as check_node_has_properties, mock.patch.object(
        graphs, "_find_name"
    ), mock.patch.object(
        graphs, "_check_node_has_type"
    ):
        graphs.check_record_set(issues, graph, node, "dataset_name")
        check_node_has_properties.assert_has_calls([
            # For ML Record Sets.
            mock.call(
                issues,
                mock.ANY,
                mandatory_properties=[
                    rdflib.URIRef("http://mlcommons.org/schema/Field"),
                    rdflib.URIRef("https://schema.org/name"),
                ],
                optional_properties=[
                    rdflib.URIRef("https://schema.org/description"),
                ],
            ),
            # For ML Fields.
            mock.call(
                issues,
                mock.ANY,
                mandatory_properties=[
                    rdflib.URIRef("http://mlcommons.org/schema/dataType"),
                    rdflib.URIRef("https://schema.org/name"),
                ],
                optional_properties=[
                    rdflib.URIRef("https://schema.org/description"),
                ],
            ),
        ])
        assert not issues.errors
        assert not issues.warnings
