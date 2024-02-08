"""graph_test module."""

import json

from etils import epath
from rdflib import term

from mlcroissant._src.core.context import Context
from mlcroissant._src.structure_graph.nodes.metadata import Metadata

Literal = term.Literal


# If this test fails, you probably manually updated a dataset in datasets/.
# Please, use scripts/migrations/migrate.py to migrate datasets.
def jsonld_to_python_to_jsonld(path):
    with path.open() as f:
        json_ld = json.load(f)
    ctx = Context()
    metadata = Metadata.from_file(ctx, {})
    result = metadata.to_json()
    # `distribution` may not be in the right order:
    if "distribution" in result:
        distribution = result.pop("distribution")
        distribution = {file["name"]: file for file in distribution}
        expected_distribution = json_ld.pop("distribution")
        expected_distribution = {file["name"]: file for file in expected_distribution}
        assert distribution == expected_distribution
    # Check the expected JSON-LD:
    assert result == json_ld
    assert not ctx.issues.errors


def test_jsonld_to_python_to_jsonld():
    dataset_folder = (
        epath.Path(__file__).parent.parent.parent.parent.parent.parent / "datasets"
    )
    json_ld_paths = [path for path in dataset_folder.glob("*/*.json")]
    for path in json_ld_paths:
        jsonld_to_python_to_jsonld(path)
