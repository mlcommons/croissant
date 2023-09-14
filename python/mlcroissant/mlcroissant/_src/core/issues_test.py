"""issues_test module."""

import textwrap

from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues


def test_issues():
    issues = Issues()
    assert not issues.errors
    assert not issues.warnings

    # With context
    issues.add_error("foo", Context(dataset_name="abc"))
    issues.add_warning("bar", Context(dataset_name="abc", distribution_name="xyz"))
    assert issues.errors == {"[dataset(abc)] foo"}
    assert issues.warnings == {"[dataset(abc) > distribution(xyz)] bar"}

    # Without context
    issues.add_error("foo")
    issues.add_warning("bar")
    assert issues.errors == {
        "[dataset(abc)] foo",
        "foo",
    }
    assert issues.warnings == {
        "[dataset(abc) > distribution(xyz)] bar",
        "bar",
    }

    # Final report
    assert issues.report() == textwrap.dedent(
        """Found the following 2 error(s) during the validation:
  -  [dataset(abc)] foo
  -  foo
Found the following 2 warning(s) during the validation:
  -  [dataset(abc) > distribution(xyz)] bar
  -  bar"""
    )
