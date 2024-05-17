"""issues_test module."""

import textwrap

from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.metadata import Metadata


def test_issues():
    issues = Issues()
    assert not issues.errors
    assert not issues.warnings

    # With context
    metadata = Metadata(id="abc", name="abc")
    file_object = FileObject(id="xyz", name="xyz")
    file_object.parents = [metadata]
    issues.add_error("foo", metadata)
    issues.add_warning("bar", file_object)
    assert issues.errors == {"[Metadata(abc)] foo"}
    assert issues.warnings == {"[Metadata(abc) > FileObject(xyz)] bar"}

    # Without context
    issues.add_error("foo")
    issues.add_warning("bar")
    assert issues.errors == {
        "[Metadata(abc)] foo",
        "foo",
    }
    assert issues.warnings == {
        "[Metadata(abc) > FileObject(xyz)] bar",
        "bar",
    }

    # Final report
    assert issues.report() == textwrap.dedent(
        """Found the following 2 error(s) during the validation:
  -  [Metadata(abc)] foo
  -  foo
Found the following 2 warning(s) during the validation:
  -  [Metadata(abc) > FileObject(xyz)] bar
  -  bar"""
    )


def test_issues_ignore_warnings():
    issues = Issues(ignore_warnings=True)
    assert not issues.errors
    assert not issues.warnings

    metadata = Metadata(id="abc", name="abc")
    file_object = FileObject(id="xyz", name="xyz")
    file_object.parents = [metadata]
    issues.add_error("foo", metadata)
    issues.add_warning("bar", file_object)

    print(issues.report())

    assert issues.report() == textwrap.dedent(
        """Found the following 1 error(s) during the validation:
  -  [Metadata(abc)] foo"""
    )
