"""migrate_test module."""

import json

from etils import epath
import pytest

from ml_croissant._src.core.json_ld import compact_jsonld
from ml_croissant._src.core.json_ld import expand_jsonld

_DATASETS_FOLDER = (
    epath.Path(__file__).parent.parent.parent.parent.parent.parent / "datasets"
)
_JSON_LD_PATHS = [path for path in _DATASETS_FOLDER.glob("*/*.json")]


# If this test fails, you probably manually updated a dataset in datasets/.
# Please, use scripts/migrations/migrate.py to migrate datasets.
@pytest.mark.parametrize(
    ["path"],
    [[path] for path in _JSON_LD_PATHS],
)
def test_expand_and_reduce_json_ld(path):
    with path.open() as f:
        json_ld = json.load(f)
    assert compact_jsonld(expand_jsonld(json_ld)) == json_ld
