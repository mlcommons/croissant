"""migrate_test module."""

import json

from etils import epath

from mlcroissant._src.core.json_ld import compact_jsonld
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.json_ld import make_context


# If this test fails, you probably manually updated a dataset in datasets/.
# Please, use scripts/migrations/migrate.py to migrate datasets.
def test_expand_and_reduce_json_ld():
    dataset_folder = (
        epath.Path(__file__).parent.parent.parent.parent.parent.parent / "datasets"
    )
    json_ld_paths = [path for path in dataset_folder.glob("*/*.json")]
    for path in json_ld_paths:
        with path.open() as f:
            json_ld = json.load(f)
        assert compact_jsonld(expand_jsonld(json_ld)) == json_ld


def test_make_context():
    assert make_context(foo="bar") == {
        "@language": "en",
        "@vocab": "https://schema.org/",
        "column": "ml:column",
        "data": {"@id": "ml:data", "@type": "@json"},
        "dataType": {"@id": "ml:dataType", "@type": "@vocab"},
        "extract": "ml:extract",
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
        "transform": "ml:transform",
        "foo": "bar",
    }
