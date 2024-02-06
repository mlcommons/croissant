"""migrate_test module."""

import json

from etils import epath

from mlcroissant._src.core.json_ld import compact_jsonld
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.rdf import make_context


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
        "column": "cr:column",
        "conformsTo": "dct:conformsTo",
        "cr": "http://mlcommons.org/croissant/",
        "data": {"@id": "cr:data", "@type": "@json"},
        "dataAnnotationAnalysis": "cr:dataAnnotationAnalysis",
        "dataAnnotationDemographics": "cr:dataAnnotationDemographics",
        "dataAnnotationPerItem": "cr:dataAnnotationPeritem",
        "dataAnnotationPlatform": "cr:dataAnnotationPlatform",
        "dataAnnotationProtocol": "cr:dataAnnotationProtocol",
        "dataAnnotationTools": "cr:dataAnnotationTools",
        "dataBiases": "cr:dataBiases",
        "dataCollection": "cr:dataCollection",
        "dataCollectionMissing": "cr:dataCollectionMissing",
        "dataCollectionRaw": "cr:dataCollectionRaw",
        "dataCollectionTimeFrameEnd": "cr:dataCollectionTimeframeEnd",
        "dataCollectionTimeFrameStart": "cr:dataCollectionTimeframeStart",
        "dataCollectionType": "cr:dataCollectionType",
        "dataCollectionTypeOthers": "cr:dataCollectionTypeOthers",
        "dataLimitations": "cr:dataLimitation",
        "dataMaitenance": "cr:dataMaintenance",
        "dataPreprocessingImputation": "cr:dataPreprocessingImputation",
        "dataPreprocessingManipulation": "cr:dataPreprocessingManipulation",
        "dataPreprocessingProtocol": "cr:dataPeprocessingProtocol",
        "dataSocialImpact": "cr:dataSocialImpact",
        "dataSensitive": "cr:dataSensitive",
        "dataType": {"@id": "ml:dataType", "@type": "@vocab"},
        "dataUseCases": "cr:dataUsecases",
        "dct": "http://purl.org/dc/terms/",
        "extract": "cr:extract",
        "field": "cr:field",
        "fileProperty": "cr:fileProperty",
        "fileObject": "cr:fileObject",
        "fileSet": "cr:fileSet",
        "format": "cr:format",
        "includes": "cr:includes",
        "isEnumeration": "cr:isEnumeration",
        "jsonPath": "cr:jsonPath",
        "key": "cr:key",
        "md5": "cr:md5",
        "parentField": "cr:parentField",
        "path": "cr:path",
        "personalSensitiveInformation": "cr:personalSensitiveInformation",
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
