from collections.abc import Iterable
import itertools
import re
from typing import Any


def regex_to_glob(regexes: str | list[str]) -> list[str]:
    """Converts a regular expression to several glob patterns.

    The function applies several transformations to achieve this:

    - Expand all non-capturing groups to possibly several expression. For example,
    for Hugging Face croissants, "default/(?:partial-)?train/.+parquet$" would become
    ["default/train/.+parquet$", "default/partial-train/.+parquet$"] to match both with
    and without the `partial-` prefix.

    - Convert to a glob pattern using some heuristics.
    """
    if isinstance(regexes, str):
        regexes = [regexes]
    for fn in [_expand_non_capturing_groups, _regex_to_glob_for_str]:
        regexes = list(itertools.chain.from_iterable(fn(regex) for regex in regexes))
    return regexes


def _expand_non_capturing_groups(regex: str) -> Iterable[str]:
    if "(?:" not in regex:
        # There is no non-capturing group:
        return [regex]

    # Find all capturing groups:
    pattern = r"\(\?:.*?\)\?|[^()]+"
    strings = re.findall(pattern, regex)
    if not strings:
        raise ValueError("the string should not be empty")
    subregex = "".join(strings[1:])
    # Recursively construct the results for the sub-regex:
    results = _expand_non_capturing_groups(subregex)
    string = strings[0]
    if string.startswith("(?:") and string.endswith(")?"):
        # Append the inside of the non-capturing group:
        string = string[len("(?:") : -len(")?")]
        return itertools.chain(
            [f"{string}{result}" for result in results],
            results,
        )
    else:
        # Append the string itself to each result:
        return [f"{string}{result}" for result in results]


def _regex_to_glob_for_str(regex: str) -> Iterable[str]:
    """Converts a regular expression to a glob pattern by unescaping regex syntax.

    Warning: this is based on manual heuristics to convert a regular expression to a
    glob expression.
    """
    # Remove starting ^
    regex = re.sub(r"^\^", "", regex)
    # Remove trailing $
    regex = re.sub(r"\$$", "", regex)
    # Interpret \. as .
    regex = re.sub(r"\\\.", ".", regex)
    # Interpret .* as *
    regex = re.sub(r"\.\*", "*", regex)
    # Interpret .+ as *
    regex = re.sub(r"\.\+", "*", regex)
    # Interpret \\- as -
    regex = re.sub(r"\\-", "-", regex)
    return [regex]


def capture_one_capturing_group(str_regex: str, value: Any) -> str:
    """Captures the one and only capturing group, but ignoring non-capturing gorups."""
    # Non-capturing groups have the form (?:a_non_capturing_group)
    capturing_groups = re.compile(r"\((?!\?\:).*?\)")
    groups = capturing_groups.findall(str_regex)
    if len(groups) == 1:
        matches = re.match(groups[0], value)
        if not matches:
            raise ValueError(
                "The replace value doesn't respect the expected capturing group."
                f" Expected: {groups[0]}. Got: {value}"
            )
    else:
        raise ValueError(
            "A transform regex should have exactly 1 capturing group in"
            f" the transform regex. Got: '{str_regex}'"
        )
    return capturing_groups.sub(re.escape(value), str_regex)
