"""Core utils to manipulate JSON-LD.

The main functions are:
- `expand_json_ld`: human-readable JSON-LD   -> machine-readable JSON-LD.
- `reduce_json_ld`: machine-readable JSON-LD -> human-readable JSON-LD.
"""

import json
from typing import Any

from ml_croissant._src.core import constants

import rdflib
from rdflib import namespace, term

Json = dict[str, Any]

_ML_COMMONS_PREFIX = str(constants.ML_COMMONS)
_SCHEMA_ORG_PREFIX = str(constants.SCHEMA_ORG)
_WD_PREFIX = "https://www.wikidata.org/wiki/"
# Mapping for non-trivial conversion:
_PREFIX_MAP = {
    "http://mlcommons.org/schema/Field": "field",
    "http://mlcommons.org/schema/RecordSet": "recordSet",
    "http://mlcommons.org/schema/SubField": "subField",
}
# Keys that always output lists:
_KEYS_WITH_LIST = {
    constants.ML_COMMONS_FIELD,
    constants.ML_COMMONS_RECORD_SET,
    constants.ML_COMMONS_SUB_FIELD,
    constants.SCHEMA_ORG_DISTRIBUTION,
}


def _make_context():
    return {
        "@vocab": "https://schema.org/",
        "applyTransform": "ml:applyTransform",
        "data": {"@id": "ml:data", "@nest": "source"},
        "dataType": {"@id": "ml:dataType", "@type": "@vocab"},
        "field": "ml:field",
        "format": "ml:format",
        "includes": "ml:includes",
        "inlineData": {"@id": "ml:data", "@type": "@json"},
        "ml": "http://mlcommons.org/schema/",
        "recordSet": "ml:recordSet",
        "references": "ml:references",
        "regex": "ml:regex",
        "replace": "ml:replace",
        "sc": "https://schema.org/",
        "separator": "ml:separator",
        "source": "ml:source",
        "subField": "ml:subField",
        "wd": "https://www.wikidata.org/wiki/",
    }


def _is_dataset_node(node: Json) -> bool:
    """Checks if the type of a node is schema.org/Dataset."""
    return node.get("@type") == [str(constants.SCHEMA_ORG_DATASET)]


def _sort_items(jsonld: Json) -> list[tuple[str, Any]]:
    """Sorts items from dict.items().

    For human readability, we want "@type"/"name"/"description" to be at the beginning
    of the JSON, while long lists (""distribution"/"recordSet") are at the end.
    """
    items = sorted(jsonld.items())
    start_keys = ["@context", "@type", "name", "description"]
    end_keys = ["distribution", "field", "inlineData", "recordSet", "subField"]
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


def _sort_dict(d: dict[str, Any]):
    """Sorts the keys of a nested dict."""
    return {
        k: _sort_dict(v) if isinstance(v, dict) and k != "@context" else v
        for k, v in _sort_items(d)
    }


def _recursively_populate_fields(entry_node: Json, id_to_node: dict[str, Json]) -> Any:
    """Changes in place `entry_node` with its children."""
    if "@value" in entry_node:
        if entry_node.get("@type") == str(namespace.RDF.JSON):
            # Stringified JSON is loaded as a dict.
            return json.loads(entry_node["@value"])
        else:
            # Other values are loaded as is.
            return entry_node["@value"]
    elif len(entry_node) == 1 and "@id" in entry_node:
        node_id = entry_node["@id"]
        if node_id in id_to_node:
            node = id_to_node[node_id]
            return _recursively_populate_fields(node, id_to_node)
        else:
            return entry_node
    for key, value in entry_node.items():
        if key == "@type":
            entry_node[key] = value[0]
        elif isinstance(value, list):
            value = [_recursively_populate_fields(child, id_to_node) for child in value]
            if term.URIRef(key) in _KEYS_WITH_LIST:
                entry_node[key] = value
            elif len(value) == 1:
                entry_node[key] = value[0]
            else:
                entry_node[key] = value
    return entry_node


def expand_json_ld(data: Json) -> Json:
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
    _recursively_populate_fields(entry_node, id_to_node)
    entry_node["@context"] = _make_context()
    return entry_node


def compact_json_ld(json: Any) -> Any:
    """Recursively compacts the JSON-LD value to human-readable values.

    For example: "http://schema.org/Dataset" -> "sc:Dataset".
    """
    if isinstance(json, list):
        return [compact_json_ld(element) for element in json]
    elif not isinstance(json, dict):
        if isinstance(json, str) and _SCHEMA_ORG_PREFIX in json:
            return json.replace(_SCHEMA_ORG_PREFIX, "sc:")
        elif isinstance(json, str) and _ML_COMMONS_PREFIX in json:
            return json.replace(_ML_COMMONS_PREFIX, "ml:")
        elif isinstance(json, str) and _WD_PREFIX in json:
            return json.replace(_WD_PREFIX, "wd:")
        else:
            return json
    for key, value in json.copy().items():
        if key == "@context":
            # `@context` is left untouched.
            continue
        new_value = compact_json_ld(value)
        if key == "@id":
            if (
                value.startswith(_SCHEMA_ORG_PREFIX)
                or value.startswith(_ML_COMMONS_PREFIX)
                or value.startswith(_WD_PREFIX)
            ):
                return new_value
            else:
                del json[key]
        elif key == str(constants.ML_COMMONS_DATA):
            del json[key]
            # Data can either be inline JSON data...
            if isinstance(value, (dict, list)):
                json["inlineData"] = value
            # ...or "source.data":
            else:
                json["data"] = value
        elif key in _PREFIX_MAP:
            del json[key]
            json[_PREFIX_MAP[key]] = new_value
        elif _SCHEMA_ORG_PREFIX in key:
            new_key = key.replace(_SCHEMA_ORG_PREFIX, "")
            del json[key]
            json[new_key] = new_value
        elif _ML_COMMONS_PREFIX in key:
            new_key = key.replace(_ML_COMMONS_PREFIX, "")
            del json[key]
            json[new_key] = new_value
        else:
            json[key] = new_value
    return _sort_dict(json)
