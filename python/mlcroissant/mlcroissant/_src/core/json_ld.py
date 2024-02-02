"""Core utils to manipulate JSON-LD.

The main functions are:
- `expand_json_ld`: human-readable JSON-LD   -> machine-readable JSON-LD.
- `reduce_json_ld`: machine-readable JSON-LD -> human-readable JSON-LD.
"""

import json
from typing import Any

import rdflib
from rdflib import namespace
from rdflib import plugin
from rdflib import term

# This is for compatibility with older versions of rdflib/rdflib-jsonld.
# Indeed, rdflib-jsonld was merged into rdflib from the version 6.0.1.
if rdflib.__version__ < "6.0.1":
    plugin.register(
        "json-ld", plugin.Serializer, "rdflib_jsonld.serializer", "JsonLDSerializer"
    )
    plugin.register("json-ld", plugin.Parser, "rdflib_jsonld.parser", "JsonLDParser")

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.rdf import get_context
from mlcroissant._src.core.rdf import make_context
from mlcroissant._src.core.types import Json

_DCTERMS_PREFIX = constants.DCTERMS
_SCHEMA_ORG_PREFIX = constants.SCHEMA_ORG
_WD_PREFIX = "https://www.wikidata.org/wiki/"
# Mapping for non-trivial conversion:
_DATA = set()
for conforms_to in CroissantVersion:
    ctx = Context(conforms_to=conforms_to)
    _DATA.add(constants.ML_COMMONS_FIELD_TYPE(ctx))
# Mapping for non-trivial conversion:
_PREFIX_MAP = {}
for conforms_to in CroissantVersion:
    ctx = Context(conforms_to=conforms_to)
    _PREFIX_MAP[constants.ML_COMMONS_FIELD_TYPE(ctx)] = "field"
    _PREFIX_MAP[constants.ML_COMMONS_RECORD_SET_TYPE(ctx)] = "recordSet"
    _PREFIX_MAP[constants.ML_COMMONS_SUB_FIELD_TYPE(ctx)] = "subField"
# List of key/type where `key` always outputs lists when used in nodes of type `type`.
_KEYS_WITH_LIST = set()
for conforms_to in CroissantVersion:
    ctx = Context(conforms_to=conforms_to)
    _KEYS_WITH_LIST.add(
        (constants.ML_COMMONS_FIELD(ctx), constants.ML_COMMONS_RECORD_SET_TYPE(ctx))
    )
    _KEYS_WITH_LIST.add(
        (constants.ML_COMMONS_RECORD_SET(ctx), constants.SCHEMA_ORG_DATASET)
    )
    _KEYS_WITH_LIST.add(
        (constants.ML_COMMONS_SUB_FIELD(ctx), constants.ML_COMMONS_FIELD_TYPE(ctx))
    )
    _KEYS_WITH_LIST.add(
        (constants.SCHEMA_ORG_DISTRIBUTION, constants.SCHEMA_ORG_DATASET)
    )


def _is_dataset_node(node: Json) -> bool:
    """Checks if the type of a node is schema.org/Dataset."""
    return node.get("@type") == [constants.SCHEMA_ORG_DATASET]


def _sort_items(jsonld: Json) -> list[tuple[str, Any]]:
    """Sorts items from dict.items().

    For human readability, we want "@type"/"name"/"description/conformsTo" to be
    at the beginning of the JSON, while long lists (""distribution"/"recordSet")
    are at the end.
    """
    items = sorted(jsonld.items())
    start_keys = ["@context", "@type", "name", "description", "conformsTo"]
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


def expand_jsonld(data: Json) -> Json:
    """Expands a Croissant JSON to a nested JSON-LD with expanded.

    For this we use RDFLib. RDFLib expands the CURIE of the form "rdf:type" into their
    full expression, but RDFLib also flattens the JSON-LD in a list of nodes. We then
    need to reconstruct the hierarchy.
    """
    context = get_context(data)
    graph = rdflib.Graph()
    graph.parse(
        data=json.dumps(data),
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
    entry_node["@context"] = make_context(**context)
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
        elif isinstance(json_, str) and constants.ML_COMMONS_V_0_8 in json_:
            return json_.replace(constants.ML_COMMONS_V_0_8, "ml:")
        elif isinstance(json_, str) and constants.ML_COMMONS_V_1_0 in json_:
            return json_.replace(constants.ML_COMMONS_V_1_0, "cr:")
        elif isinstance(json_, str) and _DCTERMS_PREFIX in json_:
            return json_.replace(_DCTERMS_PREFIX, "dct:")
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
                or value.startswith(_DCTERMS_PREFIX)
                or value.startswith(constants.ML_COMMONS_V_0_8)
                or value.startswith(constants.ML_COMMONS_V_1_0)
                or value.startswith(_WD_PREFIX)
            ):
                return new_value
        elif key in _DATA:
            json_["data"] = json.loads(value)
        elif key in _PREFIX_MAP:
            json_[_PREFIX_MAP[key]] = new_value
        elif _SCHEMA_ORG_PREFIX in key:
            new_key = key.replace(_SCHEMA_ORG_PREFIX, "")
            json_[new_key] = new_value
        elif constants.ML_COMMONS_V_0_8 in key:
            new_key = key.replace(constants.ML_COMMONS_V_0_8, "")
            json_[new_key] = new_value
        elif constants.ML_COMMONS_V_1_0 in key:
            new_key = key.replace(constants.ML_COMMONS_V_1_0, "")
            json_[new_key] = new_value
        elif _DCTERMS_PREFIX in key:
            new_key = key.replace(_DCTERMS_PREFIX, "")
            json_[new_key] = value
        else:
            json_[key] = new_value
    return _sort_dict(json_)
