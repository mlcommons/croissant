"""parse_json_test module."""

import pandas as pd

from mlcroissant._src.operation_graph.operations.parse_json import parse_json_content
from mlcroissant._src.structure_graph.nodes.source import Extract
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.tests.nodes import create_test_field


def test_parse_json():
    field1 = create_test_field(
        source=Source(extract=Extract(json_path="$.annotations[*].id")),
        name="record_set_a/field1",
    )
    field2 = create_test_field(
        source=Source(extract=Extract(json_path="$.annotations[*].value")),
        name="record_set_b/field2",
    )
    fields = (field1, field2)
    json = {
        "foo": "bar",
        "annotations": [
            {"id": 1, "value": 3},
            {"id": 2, "value": 4},
        ],
    }

    # Without specifying a record_set name.
    expected_df = pd.DataFrame(
        data={"$.annotations[*].id": [1, 2], "$.annotations[*].value": [3, 4]}
    )
    pd.testing.assert_frame_equal(parse_json_content(json, fields), expected_df)

    # Specifying a record_set name.
    expected_df = pd.DataFrame(data={"$.annotations[*].id": [1, 2]})
    pd.testing.assert_frame_equal(
        parse_json_content(json, fields, record_set="record_set_a"), expected_df
    )
