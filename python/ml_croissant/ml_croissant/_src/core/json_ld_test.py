"""migrate_test module."""

import json

from etils import epath
from ml_croissant._src.core.json_ld import expand_json_ld, reduce_json_ld


# If this test fails, you probably manually updated a dataset in datasets/.
# Please, use scripts/migrations/migrate.py to migrate datasets.
def test_expand_and_reduce_json_ld():
    json_ld_path = (
        epath.Path(__file__).parent.parent.parent.parent.parent.parent
        / "datasets"
        / "titanic"
        / "metadata.json"
    )
    with json_ld_path.open() as f:
        json_ld = json.load(f)
    assert reduce_json_ld(expand_json_ld(json_ld)) == json_ld
