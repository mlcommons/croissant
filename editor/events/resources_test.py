from core.state import FileObject
from core.state import FileSet

from .resources import _create_instance1_from_instance2


def test_create_instance1_from_instance2():
    file_object = FileObject(
        name="name",
        description="description",
        contained_in=["foo", "bar"],
        content_url="mlcommons.com",
    )
    file_set = _create_instance1_from_instance2(file_object, FileSet)
    assert isinstance(file_set, FileSet)
    assert file_set.name == "name"
    assert file_set.description == "description"
    assert file_set.contained_in == ["foo", "bar"]
    assert file_set.encoding_format == None
