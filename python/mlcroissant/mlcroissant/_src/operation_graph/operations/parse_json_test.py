"""parse_json_test module."""

import io
import json

import pandas as pd

from mlcroissant._src.operation_graph.operations.parse_json import JsonlReader
from mlcroissant._src.operation_graph.operations.parse_json import JsonReader
from mlcroissant._src.operation_graph.operations.parse_json import parse_json_content
from mlcroissant._src.structure_graph.nodes.source import Extract
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.tests.nodes import create_test_field


def test_parse_json():
    field1 = create_test_field(
        source=Source(extract=Extract(json_path="$.annotations[*].id"))
    )
    field2 = create_test_field(
        source=Source(extract=Extract(json_path="$.annotations[*].value"))
    )
    fields = (field1, field2)
    json = {
        "foo": "bar",
        "annotations": [
            {"id": 1, "value": 3},
            {"id": 2, "value": 4},
        ],
    }
    expected_df = pd.DataFrame(
        data={"$.annotations[*].id": [1, 2], "$.annotations[*].value": [3, 4]}
    )
    pd.testing.assert_frame_equal(parse_json_content(json, fields), expected_df)


def test_jsonreader_parse():
    # JsonReader.parse should extract values according to JSONPath
    field = create_test_field(
        source=Source(extract=Extract(json_path="$.item[*].value"))
    )
    fields = (field,)
    data = [{"item": [{"value": 10}]}, {"item": [{"value": 20}, {"value": 30}]}]
    raw_str = json.dumps(data)
    fh = io.StringIO(raw_str)
    reader = JsonReader(fields=fields)
    df = reader.parse(fh)
    expected = pd.DataFrame({"$.item[*].value": [10, [20, 30]]})
    pd.testing.assert_frame_equal(df, expected)


def test_jsonreader_parse():
    import orjson

    # Test nested JSONPath ($.level1.level2[*].value)
    field = create_test_field(
        source=Source(extract=Extract(json_path="$.level1.level2[*].value"))
    )
    fields = (field,)
    json_obj = {"level1": {"level2": [{"value": 100}, {"value": 200}]}}
    expected_df = pd.DataFrame({"$.level1.level2[*].value": [100, 200]})
    raw_str = orjson.dumps(json_obj).decode("utf-8")
    fh = io.StringIO(raw_str)
    reader = JsonReader(fields=fields)
    df = reader.parse(fh)
    pd.testing.assert_frame_equal(df, expected_df)


def test_jsonlreader_raw():
    # JsonlReader.raw should read JSON Lines into a DataFrame
    lines = [{"a": 1}, {"a": 2}]
    raw_text = "\n".join(json.dumps(rec) for rec in lines)
    fh = io.StringIO(raw_text)
    reader = JsonlReader(fields=())
    df = reader.raw(fh)
    expected = pd.DataFrame(lines)
    pd.testing.assert_frame_equal(df, expected)


def test_jsonlreader_parse():
    # JsonlReader.parse should extract values across lines
    field = create_test_field(source=Source(extract=Extract(json_path="$.x")))
    fields = (field,)
    lines = [{"x": 5}, {"x": 6}]
    raw_text = "\n".join(json.dumps(rec) for rec in lines)
    fh = io.StringIO(raw_text)
    reader = JsonlReader(fields=fields)
    df = reader.parse(fh)
    expected = pd.DataFrame({"$.x": [5, 6]})
    pd.testing.assert_frame_equal(df, expected)


def test_jsonlreader_deeper_path():
    # JsonlReader.parse should handle nested deeper JSONPath
    field = create_test_field(
        source=Source(extract=Extract(json_path="$.meta.detail[*].info"))
    )
    fields = (field,)
    records = [
        {"meta": {"detail": [{"info": "a"}, {"info": "b"}]}},
        {"meta": {"detail": [{"info": "c"}]}},
    ]
    raw_text = "\n".join(json.dumps(rec) for rec in records)
    fh = io.StringIO(raw_text)
    reader = JsonlReader(fields=fields)
    df = reader.parse(fh)
    expected = pd.DataFrame({"$.meta.detail[*].info": [["a", "b"], "c"]})
    pd.testing.assert_frame_equal(df, expected)
