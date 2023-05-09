import textwrap

from format.src import errors


def test_issues():
    issues = errors.Issues()
    assert not issues.errors
    assert not issues.warnings

    # With context
    with issues.context("dataset_abc"):
        issues.add_error("foo")
        issues.add_warning("bar")
    assert issues.errors == ["[dataset_abc] foo"]
    assert issues.warnings == ["[dataset_abc] bar"]

    # Without context
    issues.add_error("foo")
    issues.add_warning("bar")
    assert issues.errors == ["[dataset_abc] foo", "foo"]
    assert issues.warnings == ["[dataset_abc] bar", "bar"]

    # Final report
    assert issues.report() == textwrap.dedent(
        """Found the following 2 error(s) during the validation:
  -  [dataset_abc] foo
  -  foo
Found the following 2 warning(s) during the validation:
  -  [dataset_abc] bar
  -  bar"""
    )
