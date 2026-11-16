"""join_test module."""

import hashlib
import json

from mlcroissant._src import datasets
from mlcroissant._src.operation_graph.operations import join
from mlcroissant._src.tests.nodes import empty_record_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = join.Join(operations=operations(), node=empty_record_set)
    assert str(operation) == "Join(record_set_name)"


def test_join_on_text_identifiers_with_leading_zeros(tmp_path):
    # A CSV column declared sc:Text joins with an inline record set holding the same
    # identifiers as strings. If the CSV column were read as integers ("06073" ->
    # 6073), the join would silently find no match.
    (tmp_path / "population.csv").write_text("fips,population\n06073,3343364\n")

    def text_field(record_set, name, source=None, references=None):
        field = {
            "@type": "cr:Field",
            "@id": f"{record_set}/{name}",
            "name": f"{record_set}/{name}",
            "dataType": "sc:Text",
        }
        if source:
            field["source"] = source
        if references:
            field["references"] = {"field": {"@id": references}}
        return field

    def csv_column(column):
        return {"fileObject": {"@id": "population"}, "extract": {"column": column}}

    metadata = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "sc": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "dct": "http://purl.org/dc/terms/",
            "conformsTo": "dct:conformsTo",
            "column": "cr:column",
            "data": {"@id": "cr:data", "@type": "@json"},
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "extract": "cr:extract",
            "field": "cr:field",
            "fileObject": "cr:fileObject",
            "recordSet": "cr:recordSet",
            "references": "cr:references",
            "source": "cr:source",
        },
        "@type": "sc:Dataset",
        "name": "leading-zeros-join",
        "description": "Joins on identifiers with leading zeros.",
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "url": "https://mlcommons.org",
        "distribution": [
            {
                "@type": "cr:FileObject",
                "@id": "population",
                "name": "population",
                "contentUrl": "population.csv",
                "encodingFormat": "text/csv",
                "sha256": hashlib.sha256(
                    (tmp_path / "population.csv").read_bytes()
                ).hexdigest(),
            }
        ],
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "@id": "counties",
                "name": "counties",
                "field": [
                    text_field("counties", "fips"),
                    text_field("counties", "name"),
                ],
                "data": [{"counties/fips": "06073", "counties/name": "San Diego"}],
            },
            {
                "@type": "cr:RecordSet",
                "@id": "county_population",
                "name": "county_population",
                "field": [
                    text_field(
                        "county_population",
                        "fips",
                        source=csv_column("fips"),
                        references="counties/fips",
                    ),
                    text_field(
                        "county_population",
                        "name",
                        source={"field": {"@id": "counties/name"}},
                    ),
                ],
            },
        ],
    }
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))
    dataset = datasets.Dataset(tmp_path / "metadata.json")
    records = list(dataset.records("county_population"))
    assert [record["county_population/fips"] for record in records] == [b"06073"]
    assert [record["county_population/name"] for record in records] == [b"San Diego"]
