"""graph_test module."""

from etils import epath
from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.graph import (
    from_rdf_to_nodes,
)
from ml_croissant._src.structure_graph.nodes import (
    FileObject,
    Metadata,
)
import rdflib
from rdflib import term

Literal = term.Literal


def test_from_rdf_to_nodes():
    issues = Issues()
    graph = rdflib.Graph()
    bnode1 = term.BNode("ID_DATASET")
    bnode2 = term.BNode("ID_FILE_OBJECT")

    # Metadata
    graph.add((bnode1, constants.RDF_TYPE, constants.SCHEMA_ORG_DATASET))
    graph.add((bnode1, constants.SCHEMA_ORG_CITATION, Literal("Citation.")))
    graph.add((bnode1, constants.SCHEMA_ORG_DESCRIPTION, Literal("Description.")))
    graph.add((bnode1, constants.SCHEMA_ORG_LICENSE, Literal("License.")))
    graph.add((bnode1, constants.SCHEMA_ORG_NAME, Literal("mydataset")))
    graph.add((bnode1, constants.SCHEMA_ORG_URL, Literal("google.com/dataset")))
    graph.add((bnode1, constants.SCHEMA_ORG_DISTRIBUTION, bnode2))

    # FileObject
    graph.add((bnode2, constants.RDF_TYPE, constants.SCHEMA_ORG_FILE_OBJECT))
    graph.add((bnode2, constants.SCHEMA_ORG_NAME, Literal("a-csv-table")))
    graph.add((bnode2, constants.SCHEMA_ORG_CONTENT_URL, Literal("ratings.csv")))
    graph.add((bnode2, constants.SCHEMA_ORG_ENCODING_FORMAT, Literal("text/csv")))
    graph.add((bnode2, constants.SCHEMA_ORG_SHA256, Literal("xxx")))

    graph = from_rdf_to_nodes(issues, graph, epath.Path())
    nodes = list(graph.nodes)
    metadata = Metadata(
        issues=issues,
        bnode=bnode1,
        folder=epath.Path(),
        graph=graph,
        parents=(),
        name="mydataset",
        citation="Citation.",
        description="Description.",
        license="License.",
        url="google.com/dataset",
    )
    expected_nodes = [
        metadata,
        FileObject(
            issues=issues,
            bnode=bnode2,
            folder=epath.Path(),
            graph=graph,
            parents=(metadata,),
            name="a-csv-table",
            content_url="ratings.csv",
            encoding_format="text/csv",
            sha256="xxx",
        ),
    ]
    assert not issues.errors
    assert not issues.warnings
    assert nodes == expected_nodes
