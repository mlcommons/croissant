from .metadata import find_license_index


def test_find_license_index():
    assert find_license_index("unknown") == 0
    assert find_license_index("llama2") == 66
    assert find_license_index("fooo") is None
