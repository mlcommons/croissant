"""regex_test module."""

import pytest

from mlcroissant._src.core import regex as regex_lib


@pytest.mark.parametrize(
    ["regex", "output"],
    [
        [
            "(?:baz)?xxx(?:foo)?yyy(?:bar)?",
            [
                "bazxxxfooyyybar",
                "bazxxxfooyyy",
                "bazxxxyyybar",
                "bazxxxyyy",
                "xxxfooyyybar",
                "xxxfooyyy",
                "xxxyyybar",
                "xxxyyy",
            ],
        ],
        [
            "^.+/train/.*\.parquet$",  # From a valid regex...
            [
                "*/train/*.parquet",  # ...to a valid glob pattern.
            ],
        ],
        [
            "^.+/my\\-train/.*\.parquet$",  # From a valid regex...
            [
                "*/my-train/*.parquet",  # ...to a valid glob pattern.
            ],
        ],
    ],
)
def test_regex_to_glob(regex: str, output: list[str]):
    assert regex_lib.regex_to_glob(regex) == output


def test_capture_one_capturing_group():
    # The value does not match:
    with pytest.raises(ValueError):
        regex_lib.capture_one_capturing_group(
            "default/(?:partial-)?(train|test)/.+parquet$", "NOT MATCHING"
        )

    # Too many capturing groups:
    with pytest.raises(ValueError):
        regex_lib.capture_one_capturing_group(
            "(default)/(?:partial-)?(train|test)/.+parquet$", "NOT MATCHING"
        )

    assert (
        regex_lib.capture_one_capturing_group(
            "default/(?:partial-)?(train|test)/.+parquet$", "train"
        )
        == "default/(?:partial-)?train/.+parquet$"
    )
