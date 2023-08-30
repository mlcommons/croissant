"""Core utils to manipulate JSON-LD.

The main functions are:
- `expand_json_ld`: human-readable JSON-LD   -> machine-readable JSON-LD.
- `reduce_json_ld`: machine-readable JSON-LD -> human-readable JSON-LD.
"""

import json
from typing import Any

import rdflib
from rdflib import namespace
from rdflib import term

from ml_croissant._src.core import constants
from ml_croissant._src.core.types import Json

_ML_COMMONS_PREFIX = constants.ML_COMMONS
_SCHEMA_ORG_PREFIX = constants.SCHEMA_ORG
_WD_PREFIX = "https://www.wikidata.org/wiki/"
# Mapping for non-trivial conversion:
_PREFIX_MAP = {
    constants.ML_COMMONS_FIELD_TYPE: "field",
    constants.ML_COMMONS_RECORD_SET_TYPE: "recordSet",
    constants.ML_COMMONS_SUB_FIELD_TYPE: "subField",
}
# List of key/type where `key` always outputs lists when used in nodes of type `type`.
_KEYS_WITH_LIST = {
    (constants.ML_COMMONS_FIELD, constants.ML_COMMONS_RECORD_SET_TYPE),
    (constants.ML_COMMONS_RECORD_SET, constants.SCHEMA_ORG_DATASET),
    (constants.ML_COMMONS_SUB_FIELD, constants.ML_COMMONS_FIELD_TYPE),
    (constants.SCHEMA_ORG_DISTRIBUTION, constants.SCHEMA_ORG_DATASET),
}


def _make_context():
    return {
        "@language": "en",
        "@vocab": "https://schema.org/",
        "applyTransform": "ml:applyTransform",
        "csvColumn": "ml:csvColumn",
        "data": {"@id": "ml:data", "@type": "@json"},
        "dataExtraction": "ml:dataExtraction",
        "dataType": {"@id": "ml:dataType", "@type": "@vocab"},
        "field": "ml:field",
        "fileProperty": "ml:fileProperty",
        "format": "ml:format",
        "includes": "ml:includes",
        "isEnumeration": "ml:isEnumeration",
        "jsonPath": "ml:jsonPath",
        "ml": "http://mlcommons.org/schema/",
        "parentField": "ml:parentField",
        "path": "ml:path",
        "recordSet": "ml:recordSet",
        "references": "ml:references",
        "regex": "ml:regex",
        "repeated": "ml:repeated",
        "replace": "ml:replace",
        "sc": "https://schema.org/",
        "separator": "ml:separator",
        "source": "ml:source",
        "subField": "ml:subField",
        "wd": "https://www.wikidata.org/wiki/",
    }


def _is_dataset_node(node: Json) -> bool:
    """Checks if the type of a node is schema.org/Dataset."""
    return node.get("@type") == [constants.SCHEMA_ORG_DATASET]


def _sort_items(jsonld: Json) -> list[tuple[str, Any]]:
    """Sorts items from dict.items().

    For human readability, we want "@type"/"name"/"description" to be at the beginning
    of the JSON, while long lists (""distribution"/"recordSet") are at the end.
    """
    items = sorted(jsonld.items())
    start_keys = ["@context", "@type", "name", "description"]
    end_keys = ["distribution", "field", "data", "recordSet", "subField"]
    sorted_items = []
    for key in start_keys:
        if key in jsonld:
            sorted_items.append((key, jsonld[key]))
    for item in items:
        if item[0] not in start_keys and item[0] not in end_keys:
            sorted_items.append(item)
    for key in end_keys:
        if key in jsonld:
            sorted_items.append((key, jsonld[key]))
    return sorted_items


def _sort_dict(d: Json):
    """Sorts the keys of a nested dict."""
    return {
        k: _sort_dict(v) if isinstance(v, dict) and k != "@context" else v
        for k, v in _sort_items(d)
    }


def remove_empty_values(d: Json) -> Json:
    """Removes empty values in a JSON."""
    return {k: v for k, v in d.items() if v}


def recursively_populate_jsonld(entry_node: Json, id_to_node: dict[str, Json]) -> Any:
    """Changes in place `entry_node` with its children."""
    if "@value" in entry_node:
        if entry_node.get("@type") == namespace.RDF.JSON:
            # Stringified JSON is loaded as a dict.
            return json.loads(entry_node["@value"])
        else:
            # Other values are loaded as is.
            return entry_node["@value"]
    elif len(entry_node) == 1 and "@id" in entry_node:
        node_id = entry_node["@id"]
        if node_id in id_to_node:
            entry_node = id_to_node[node_id]
            return recursively_populate_jsonld(entry_node, id_to_node)
        else:
            return entry_node
    for key, value in entry_node.copy().items():
        if key == "@type":
            entry_node[key] = term.URIRef(value[0])
        elif isinstance(value, list):
            del entry_node[key]
            value = [recursively_populate_jsonld(child, id_to_node) for child in value]
            node_type = entry_node.get("@type", "")
            key, node_type = term.URIRef(key), term.URIRef(node_type)
            if (key, node_type) in _KEYS_WITH_LIST:
                entry_node[key] = value
            elif len(value) == 1:
                entry_node[key] = value[0]
            else:
                entry_node[key] = value
    return entry_node


def from_jsonld_to_json(jsonld: list[Json]) -> Json:
    """Converts an RDFLib JSON-LD representation to Croissant JSON.

    RDFLib JSON-LD is a list of nodes. So to output a JSON, we have to recursively
    populate the output JSON.
    """
    # Check jsonld is not empty
    id_to_node: dict[str, Json] = {}
    for node in jsonld:
        node_id = str(node.get("@id"))
        id_to_node[node_id] = node
    # Find the entry node (schema.org/Dataset).
    entry_node = next(
        (record for record in jsonld if _is_dataset_node(record)), jsonld[0]
    )
    recursively_populate_jsonld(entry_node, id_to_node)
    return entry_node


def expand_jsonld(data: Json) -> Json:
    """Expands a Croissant JSON to a nested JSON-LD with expanded.

    For this we use RDFLib. RDFLib expands the CURIE of the form "rdf:type" into their
    full expression, but RDFLib also flattens the JSON-LD in a list of nodes. We then
    need to reconstruct the hierarchy.
    """
    graph = rdflib.Graph()
    # Parse with the new context if it has been changed.
    data["@context"] = _make_context()
    graph.parse(
        data=data,
        format="json-ld",
    )
    # `graph.serialize` outputs a stringified list of JSON-LD nodes.
    nodes = graph.serialize(format="json-ld")
    nodes = json.loads(nodes)
    assert nodes, "Found no node in graph"
    # Find the entry node (schema.org/Dataset).
    entry_node = next(
        (record for record in nodes if _is_dataset_node(record)), nodes[0]
    )
    id_to_node: dict[str, Json] = {}
    for node in nodes:
        node_id = node.get("@id")
        id_to_node[node_id] = node
    recursively_populate_jsonld(entry_node, id_to_node)
    entry_node["@context"] = _make_context()
    return entry_node


def compact_jsonld(json_: Any) -> Any:
    """Recursively compacts the JSON-LD value to human-readable values.

    For example: "http://schema.org/Dataset" -> "sc:Dataset".
    """
    if isinstance(json_, list):
        return [compact_jsonld(element) for element in json_]
    elif not isinstance(json_, dict):
        if isinstance(json_, str) and _SCHEMA_ORG_PREFIX in json_:
            return json_.replace(_SCHEMA_ORG_PREFIX, "sc:")
        elif isinstance(json_, str) and _ML_COMMONS_PREFIX in json_:
            return json_.replace(_ML_COMMONS_PREFIX, "ml:")
        elif isinstance(json_, str) and _WD_PREFIX in json_:
            return json_.replace(_WD_PREFIX, "wd:")
        else:
            return json_
    for key, value in json_.copy().items():
        if key == "@context":
            # `@context` is left untouched.
            continue
        new_value = compact_jsonld(value)
        del json_[key]
        if key == "@id":
            if (
                value.startswith(_SCHEMA_ORG_PREFIX)
                or value.startswith(_ML_COMMONS_PREFIX)
                or value.startswith(_WD_PREFIX)
            ):
                return new_value
        elif key == constants.ML_COMMONS_DATA:
            json_["data"] = json.loads(value)
        elif key in _PREFIX_MAP:
            json_[_PREFIX_MAP[key]] = new_value
        elif _SCHEMA_ORG_PREFIX in key:
            new_key = key.replace(_SCHEMA_ORG_PREFIX, "")
            json_[new_key] = new_value
        elif _ML_COMMONS_PREFIX in key:
            new_key = key.replace(_ML_COMMONS_PREFIX, "")
            json_[new_key] = new_value
        else:
            json_[key] = new_value
    return _sort_dict(json_)
