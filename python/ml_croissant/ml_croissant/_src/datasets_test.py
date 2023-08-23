"""datasets_test module."""

import json

from etils import epath
import pytest

from ml_croissant._src import datasets
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.tests.records import record_to_python


# End-to-end tests on real data. The data is in `tests/graphs/*/metadata.json`.
def get_error_msg(folder):
    with open(f"{folder}/output.txt", "r") as file:
        return file.read().strip()


@pytest.mark.parametrize(
    "folder",
    [
        # Distribution.
        "distribution_bad_contained_in",
        "distribution_bad_type",
        # When the name is missing, the context should still appear without the name.
        "distribution_missing_name",
        "distribution_missing_property_content_url",
        # Metadata.
        "metadata_bad_type",
        "metadata_missing_property_name",
        # ML field.
        "mlfield_bad_source",
        "mlfield_bad_type",
        "mlfield_missing_property_name",
        "mlfield_missing_source",
        # Record set.
        "recordset_bad_type",
        "recordset_missing_context_for_datatype",
        "recordset_missing_property_name",
    ],
)
def test_static_analysis(folder):
    base_path = epath.Path(__file__).parent / "tests/graphs"
    with pytest.raises(ValidationError) as error_info:
        datasets.Dataset(base_path / f"{folder}/metadata.json")
    assert str(error_info.value) == get_error_msg(base_path / folder)


# IF THIS TEST FAILS OR YOU ADD A NEW DATASET:
# You can regenerate .pkl files by launching
# ```bash
# python scripts/load.py \
#   --file ../../datasets/{{dataset_name}}/metadata.json \
#   --record_set {{record_set_name}} \
#   --update_output \
#   --num_records -1
# ```
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name"],
    [
        ["coco2014-mini", "captions"],
        ["coco2014-mini", "images"],
        ["pass-mini", "images"],
        ["simple-join", "publications_by_user"],
        ["simple-parquet", "persons"],
        ["titanic", "passengers"],
    ],
)
def test_loading(dataset_name, record_set_name):
    print(
        "If this test fails, update JSONL with: `python scripts/load.py --file"
        f" ../../datasets/{dataset_name}/metadata.json --record_set"
        f" {record_set_name} --update_output --num_records -1 --debug`"
    )
    dataset_folder = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / dataset_name
    )
    config = dataset_folder / "metadata.json"
    output_file = dataset_folder / "output" / f"{record_set_name}.jsonl"
    with output_file.open("rb") as f:
        lines = f.readlines()
        expected_records = [json.loads(line) for line in lines]
    dataset = datasets.Dataset(config)
    records = dataset.records(record_set_name)
    records = iter(records)
    length = 0
    for i, record in enumerate(records):
        record = record_to_python(record)
        assert record == expected_records[i]
        length += 1
    assert len(expected_records) == length
