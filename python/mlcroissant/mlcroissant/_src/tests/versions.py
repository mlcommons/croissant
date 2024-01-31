import pytest

from mlcroissant._src.structure_graph.nodes.croissant_version import CroissantVersion

VERSIONS = ["0.8", "1.0"]

parametrize_version = pytest.mark.parametrize("version", VERSIONS)
parametrize_conforms_to = pytest.mark.parametrize(
    "conforms_to",
    [
        CroissantVersion(f"http://mlcommons.org/croissant/{version}")
        for version in VERSIONS
    ],
)
