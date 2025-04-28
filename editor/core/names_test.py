"""Tests for `names` module."""

from .names import find_unique_name


def test_find_unique_name():
    names = set(["first", "second", "first_0"])
    assert find_unique_name(names, "are there spaces") == "are_there_spaces"
    assert find_unique_name(names, "first") == "first_0_0"
    assert find_unique_name(names, "second") == "second_0"
    assert find_unique_name(names, "third") == "third"
