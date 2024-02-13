from core.state import Field
import mlcroissant as mlc
from views.record_sets import _find_joins


def test_find_joins():
    fields = [
        Field(
            name="field1",
            source=mlc.Source(
                uid="some_csv", extract=mlc.Extract(column="some_column")
            ),
            references=mlc.Source(uid="some_record_set/some_field"),
        ),
        Field(name="field2", source=mlc.Source(uid="foo/bar")),
        Field(
            name="field3",
            source=mlc.Source(uid="some_record_set/some_field"),
            references=mlc.Source(uid="some_other_record_set/some_other_field"),
        ),
    ]
    assert _find_joins(fields) == set(
        [
            (("some_csv", "some_column"), ("some_record_set", "some_field")),
            (
                ("some_record_set", "some_field"),
                ("some_other_record_set", "some_other_field"),
            ),
        ]
    )
