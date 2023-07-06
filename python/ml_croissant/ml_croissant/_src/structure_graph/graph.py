"""Structure graph module."""

from typing import Any, Mapping

from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.nodes import (
    Field,
    FileObject,
    FileSet,
    Metadata,
    RecordSet,
    Source,
)
from ml_croissant._src.structure_graph.nodes.source import parse_reference
import networkx as nx
import rdflib


def _extract_properties(
    issues: Issues, graph: nx.MultiDiGraph, node: rdflib.term.BNode
) -> Mapping[str, Any]:
    """Extracts properties RDF->Python nodes.

    Note: we could find a better way to extract information from the RDF graph.
    """
    properties: Mapping[str, str | tuple[str]] = {}
    # pylint:disable=invalid-name
    for _, _object, _property in graph.edges(node, keys=True):
        if isinstance(_object, rdflib.term.BNode):
            # `source` needs a special treatment when it is a dict.
            if _property == constants.ML_COMMONS_SOURCE:
                source = _extract_properties(issues, graph, _object)
                properties["source"] = source
            if _property == constants.ML_COMMONS_SUB_FIELD:
                properties["has_sub_fields"] = True
            continue

        # Normalize values to strings.
        if isinstance(_object, rdflib.term.Literal):
            _object = str(_object)

        # Normalize properties to Croissant values if it exists.
        _property = constants.TO_CROISSANT.get(_property, _property)

        # Add `property` to existing properties.
        if _property not in properties:
            properties[_property] = _object
        elif isinstance(properties[_property], tuple):
            # Use tuple, because we need immutable types in order
            # for the objects to be hashable and used by NetworkX.
            properties[_property] = properties[_property] + (_object,)
        else:
            # In the loop, we just found out that there are several values for the same
            # property. `self.properties[property]` should be transformed to a tuple.
            properties[_property] = (properties[_property], _object)

    # Normalize `source`.
    if (source := properties.get("source")) is not None:
        properties["source"] = Source.from_json_ld(issues, source)
    # Normalize `references`.
    if (references := properties.get("references")) is not None:
        properties["references"] = Source.from_json_ld(issues, references)
    # Normalize `contained_in`.
    if (contained_in := properties.get("contained_in")) is not None:
        if isinstance(contained_in, str):
            properties["contained_in"] = parse_reference(issues, contained_in)
        else:
            properties["contained_in"] = (
                parse_reference(issues, reference)[0] for reference in contained_in
            )
    return properties


def from_rdf_graph(
    issues: Issues,
    graph: nx.MultiDiGraph,
    node: rdflib.term.BNode,
    parent_uid: str,
):
    """Builds a Node from the provided graph."""
    properties = _extract_properties(issues, graph, node)
    name = properties.get("name")

    # Check @type.
    rdf_type = properties.get(constants.RDF_TYPE)
    expected_types = [
        constants.SCHEMA_ORG_DATASET,
        constants.SCHEMA_ORG_FILE_OBJECT,
        constants.SCHEMA_ORG_FILE_SET,
        constants.ML_COMMONS_RECORD_SET,
        constants.ML_COMMONS_FIELD,
        constants.ML_COMMONS_SUB_FIELD,
    ]
    if rdf_type not in expected_types:
        issues.add_error(
            f'Node should have an attribute `"@type" in "{expected_types}"`.'
        )

    # Return proper node in each case.
    args = [issues, graph, node, name, parent_uid]
    if rdf_type == constants.SCHEMA_ORG_DATASET:
        with issues.context(dataset_name=name):
            return Metadata(
                *args,
                citation=properties.get("citation"),
                description=properties.get("description"),
                license=properties.get("license"),
                url=properties.get("url"),
            )
    elif rdf_type == constants.SCHEMA_ORG_FILE_OBJECT:
        with issues.context(distribution_name=name):
            return FileObject(
                *args,
                contained_in=properties.get("contained_in"),
                content_url=properties.get("content_url"),
                description=properties.get("description"),
                encoding_format=properties.get("encoding_format"),
                md5=properties.get("md5"),
                sha256=properties.get("sha256"),
            )
    elif rdf_type == constants.SCHEMA_ORG_FILE_SET:
        with issues.context(distribution_name=name):
            return FileSet(
                *args,
                contained_in=properties.get("contained_in"),
                description=properties.get("description"),
                includes=properties.get("includes"),
                encoding_format=properties.get("encoding_format"),
            )
    elif rdf_type == constants.ML_COMMONS_RECORD_SET:
        with issues.context(record_set_name=name):
            return RecordSet(
                *args,
                data=properties.get("data"),
                description=properties.get("description"),
                key=properties.get("key"),
            )
    elif rdf_type == constants.ML_COMMONS_FIELD:
        with issues.context(field_name=name):
            return Field(
                *args,
                data_type=properties.get("data_type"),
                description=properties.get("description"),
                has_sub_fields=properties.get("has_sub_fields"),
                references=properties.get("references"),
                source=properties.get("source"),
            )
    raise ValueError(f"Wrong RDF type: {rdf_type}.")


def children_nodes(node: Any, expected_property: str) -> list[Any]:
    """Finds all children objects/nodes."""
    nodes = []
    # pylint:disable=invalid-name
    for _, _object, _property in node._edges_from_node:
        if isinstance(_object, rdflib.term.BNode) and expected_property == _property:
            nodes.append(
                from_rdf_graph(
                    issues=node.issues,
                    graph=node.graph,
                    node=_object,
                    parent_uid=node.uid,
                )
            )
    if not nodes and expected_property in [
        constants.ML_COMMONS_RECORD_SET,
        constants.SCHEMA_ORG_DISTRIBUTION,
    ]:
        node.issues.add_warning(
            "The current dataset doesn't declare any node of type:"
            f' "{expected_property}"'
        )
    return nodes
