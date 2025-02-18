"""migrate_test module."""

import json

from etils import epath

from mlcroissant._src.core.rdf import make_context
from mlcroissant._src.datasets import Dataset
from mlcroissant._src.tests.versions import parametrize_version


# If this test fails, you probably manually updated a dataset in datasets/.
# Please, use scripts/migrations/migrate.py to migrate datasets.
@parametrize_version()
def test_expand_and_reduce_json_ld(version):
    dataset_folder = (
        epath.Path(__file__).parent.parent.parent.parent.parent.parent
        / "datasets"
        / version
    )
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
        "sc": "https://schema.org/",
        "separator": "cr:separator",
        "source": "cr:source",
        "subField": "cr:subField",
        "transform": "cr:transform",
        "foo": "bar",
    }
