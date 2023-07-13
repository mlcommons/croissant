"""migrate_test module."""

import json

from etils import epath
from ml_croissant._src.core.json_ld import expand_json_ld, reduce_json_ld
import pytest

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
    assert reduce_json_ld(expand_json_ld(json_ld)) == json_ld
