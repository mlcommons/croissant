"""errors_test module."""

import textwrap

from format.src import errors


def test_issues():
    issues = errors.Issues()
    assert not issues.errors
    assert not issues.warnings

    # With context
    with issues.context(dataset_name="abc"):
        issues.add_error("foo")
        issues.add_warning("bar")
    assert issues.errors == {"[dataset(abc)] foo"}
    assert issues.warnings == {"[dataset(abc)] bar"}

    # With nested context
    with issues.context(dataset_name="abc", distribution_name="xyz"):
        issues.add_error("foo")
        issues.add_warning("bar")
    assert issues.errors == {
        "[dataset(abc)] foo",
        "[dataset(abc) > distribution(xyz)] foo",
    }
    assert issues.warnings == {
        "[dataset(abc)] bar",
        "[dataset(abc) > distribution(xyz)] bar",
    }

    # Without context
    issues.add_error("foo")
    issues.add_warning("bar")
    assert issues.errors == {
        "[dataset(abc)] foo",
        "[dataset(abc) > distribution(xyz)] foo",
        "foo",
    }
    assert issues.warnings == {
        "[dataset(abc)] bar",
        "[dataset(abc) > distribution(xyz)] bar",
        "bar",
    }

    # Final report
    assert issues.report() == textwrap.dedent(
        """Found the following 3 error(s) during the validation:
  -  [dataset(abc) > distribution(xyz)] foo
  -  [dataset(abc)] foo
  -  foo
Found the following 3 warning(s) during the validation:
  -  [dataset(abc) > distribution(xyz)] bar
  -  [dataset(abc)] bar
  -  bar"""
    )
