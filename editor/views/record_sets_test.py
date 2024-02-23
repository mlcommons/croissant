from core.state import Field
import mlcroissant as mlc
from views.record_sets import _find_joins


def test_find_joins():
    fields = [
        Field(
            uuid="field1",
            name="field1",
            source=mlc.Source(
                uuid="some_csv", extract=mlc.Extract(column="some_column")
            ),
            references=mlc.Source(uuid="some_record_set/some_field"),
        ),
        Field(uuid="field2", name="field2", source=mlc.Source(uuid="foo/bar")),
        Field(
            uuid="field3",
            name="field3",
            source=mlc.Source(uuid="some_record_set/some_field"),
            references=mlc.Source(uuid="some_other_record_set/some_other_field"),
        ),
    ]
    assert _find_joins(fields) == set([
        (("some_csv", "some_column"), ("some_record_set", "some_field")),
        (
            ("some_record_set", "some_field"),
            ("some_other_record_set", "some_other_field"),
        ),
    ])
