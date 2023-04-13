import pathlib


def path_test_resources() -> pathlib.Path:
    """Return the absolute path of src/tests/resources"""
    return pathlib.Path(__file__).parent / "resources"
