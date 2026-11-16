"""migrate_test module."""

import json

import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.rdf import make_context
from mlcroissant._src.datasets import Dataset


# If this test fails, you probably manually updated a dataset in datasets/.
# Please, use scripts/migrations/migrate.py to migrate datasets.
@pytest.mark.parametrize("version", ["0.8", "1.0", "1.1"])
def test_expand_and_reduce_json_ld(version):
    dataset_folder = constants.DATASETS_FOLDER / version
    paths = [path for path in dataset_folder.glob("*/*.json")]
    assert paths, f"Warning: Checking an empty list of paths: {dataset_folder}"
    for path in paths:
        print(f"Test for {path}")
        with path.open() as f:
            expected = json.load(f)
        dataset = Dataset(path)
        metadata = dataset.metadata
        actual = metadata.to_json()
        assert actual == expected, f"Error in {path}"


def test_make_context():
    assert make_context(foo="bar") == {
        "@language": "en",
        "@vocab": "https://schema.org/",
        "citeAs": "cr:citeAs",
        "column": "cr:column",
        "conformsTo": "dct:conformsTo",
        "cr": "http://mlcommons.org/croissant/",
        "rai": "http://mlcommons.org/croissant/RAI/",
        "data": {"@id": "cr:data", "@type": "@json"},
        "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
        "dct": "http://purl.org/dc/terms/",
        "equivalentProperty": "cr:equivalentProperty",
        "examples": {"@id": "cr:examples", "@type": "@json"},
        "extract": "cr:extract",
        "field": "cr:field",
        "fileProperty": "cr:fileProperty",
        "fileObject": "cr:fileObject",
        "fileSet": "cr:fileSet",
        "format": "cr:format",
        "includes": "cr:includes",
        "isLiveDataset": "cr:isLiveDataset",
        "jsonPath": "cr:jsonPath",
        "key": "cr:key",
        "md5": "cr:md5",
        "parentField": "cr:parentField",
        "path": "cr:path",
        "recordSet": "cr:recordSet",
        "references": "cr:references",
        "regex": "cr:regex",
        "repeated": "cr:repeated",
        "replace": "cr:replace",
        "samplingRate": "cr:samplingRate",
        "sc": "https://schema.org/",
        "separator": "cr:separator",
        "source": "cr:source",
        "subField": "cr:subField",
        "transform": "cr:transform",
        "foo": "bar",
    }


def test_expand_and_reduce_language_tagged():
    ctx = Context(conforms_to=CroissantVersion.V_1_1)
    dataset = Dataset({
        "@context": make_context(ctx),
        "@type": "sc:Dataset",
        "conformsTo": CroissantVersion.V_1_1.value,
        "name": {"en": "a", "fr": "b"},
        "description": [
            {"@language": "en", "@value": "A"},
            {"@language": "de", "@value": "B"},
        ],
    })
    metadata = dataset.metadata
    actual = metadata.to_json()
    assert actual["name"] == {"en": "a", "fr": "b"}
    assert actual["description"] == {"en": "A", "de": "B"}


def test_expand_json_ld_with_a_reference_back_to_a_containing_node():
    # A place whose contained place refers back to it (sc:geoWithin, the inverse of
    # sc:containsPlace): the reference is kept as a reference instead of looping.
    ctx = Context(conforms_to=CroissantVersion.V_1_1)
    dataset = Dataset({
        "@context": make_context(ctx),
        "@type": "sc:Dataset",
        "conformsTo": CroissantVersion.V_1_1.value,
        "name": "a",
        "description": "A",
        "sc:spatialCoverage": {
            "@type": "sc:Place",
            "@id": "bbox",
            "sc:containsPlace": {
                "@type": "sc:Place",
                "@id": "hull",
                "sc:geoWithin": {"@id": "bbox"},
            },
        },
    })
    spatial_coverage = dataset.metadata.to_json()["spatialCoverage"]
    assert spatial_coverage["@id"] == "bbox"
    assert spatial_coverage["containsPlace"]["@id"] == "hull"
    assert spatial_coverage["containsPlace"]["geoWithin"] == {"@id": "bbox"}


def test_expand_json_ld_with_a_node_that_has_the_id_of_the_dataset():
    # A nested node with the @id of the dataset is the dataset itself in JSON-LD: it
    # refers to the dataset from inside it.
    ctx = Context(conforms_to=CroissantVersion.V_1_1)
    dataset = Dataset({
        "@context": make_context(ctx),
        "@type": "sc:Dataset",
        "@id": "https://doi.org/10.1234/a",
        "conformsTo": CroissantVersion.V_1_1.value,
        "name": "a",
        "description": "A",
        "sc:identifier": {"@id": "https://doi.org/10.1234/a", "sc:propertyID": "DOI"},
    })
    assert dataset.metadata.name == "a"
    assert dataset.metadata.to_json()["name"] == "a"
