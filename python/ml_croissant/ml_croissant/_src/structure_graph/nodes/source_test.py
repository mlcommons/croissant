"""source_test module."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.nodes.source import (
    apply_transforms_fn,
    Source,
    Transform,
)
import pytest


def test_source_bool():
    empty_source = Source()
    assert not empty_source

    whole_source = Source(reference=("one", "two"))
    assert whole_source


@pytest.mark.parametrize(
    ["json_ld", "expected_source"],
    [
        [
            "#{one/two}",
            Source(reference=("one", "two")),
        ],
        [
            {
                "data": "#{token-files/content}",
                "apply_transform": [{"replace": "\\n/<eos>"}, {"separator": " "}],
            },
            Source(
                reference=("token-files", "content"),
                apply_transform=(
                    Transform(replace="\\n/<eos>"),
                    Transform(separator=" "),
                ),
            ),
        ],
        [
            [
                {
                    "data": "#{token-files/content}",
                    "apply_transform": [{"replace": "\\n/<eos>"}, {"separator": " "}],
                }
            ],
            Source(
                reference=("token-files", "content"),
                apply_transform=(
                    Transform(replace="\\n/<eos>"),
                    Transform(separator=" "),
                ),
            ),
        ],
        [
            {
                "data": "#{token-files/content}",
                "apply_transform": [{"replace": "\\n/<eos>", "separator": " "}],
            },
            Source(
                reference=("token-files", "content"),
                apply_transform=(Transform(replace="\\n/<eos>", separator=" "),),
            ),
        ],
    ],
)
def test_source_parses_list(json_ld, expected_source):
    issues = Issues()
    assert Source.from_json_ld(issues, json_ld) == expected_source
    assert not issues.errors
    assert not issues.warnings


@pytest.mark.parametrize(
    ["value", "source", "expected_value"],
    [
        # No source
        ["this is a value", None, "this is a value"],
        # Capturing group
        [
            "train1234",
            Source(apply_transform=(Transform(regex="(train|val)\\d\\d\\d\\d"),)),
            "train",
        ],
        # Non working capturing group
        [
            "foo1234",
            Source(apply_transform=(Transform(regex="(train|val)\\d\\d\\d\\d"),)),
            "foo1234",
        ],
    ],
)
def test_apply_transforms_fn(value, source, expected_value):
    assert apply_transforms_fn(value, source) == expected_value
