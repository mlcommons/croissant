"""datasets_test module."""

import json

from etils import epath
import pytest

from mlcroissant._src import datasets
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.optional import deps
from mlcroissant._src.tests.records import record_to_python
from mlcroissant._src.tests.versions import parametrize_version


# End-to-end tests on real data. The data is in `tests/graphs/*/metadata.json`.
def get_error_msg(folder):
    with open(f"{folder}/output.txt", "r") as file:
        return file.read().strip()


@parametrize_version()
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
        "recordset_wrong_join",
    ],
)
def test_static_analysis(version, folder):
    base_path = epath.Path(__file__).parent / "tests/graphs" / version
    with pytest.raises(ValidationError) as error_info:
        datasets.Dataset(base_path / f"{folder}/metadata.json")
    assert str(error_info.value) == get_error_msg(base_path / folder)


def load_records_and_test_equality(
    version: str, dataset_name: str, record_set_name: str, num_records: int
):
    print(
        "If this test fails, update JSONL with: `mlcroissant load"
        f" --jsonld ../../datasets/{version}/{dataset_name} --record_set"
        f" {record_set_name} --num_records {num_records} --debug --update_output`"
    )
    config = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / version
        / dataset_name
    )
    output_file = config.parent / "output" / f"{record_set_name}.jsonl"
    with output_file.open("rb") as f:
        lines = f.readlines()
        expected_records = [json.loads(line) for line in lines]
    dataset = datasets.Dataset(config)
    records = dataset.records(record_set_name)
    records = iter(records)
    length = 0
    for i, record in enumerate(records):
        if num_records > 0 and i >= num_records:
            break
        record = record_to_python(record)
        assert record == expected_records[i]
        length += 1
    assert len(expected_records) == length


# IF (NON)-HERMETIC TESTS FAIL, OR A NEW DATASET IS ADDED:
# You can regenerate .pkl files by launching
# ```bash
# mlcroissant load \
#   --jsonld ../../datasets/{{version}}/{{dataset_name}}/metadata.json \
#   --record_set {{record_set_name}} \
#   --update_output \
#   --num_records -1
# ```


# Hermetic test cases (data from local folders).
@parametrize_version()
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name", "num_records"],
    [
        ["coco2014-mini/metadata.json", "bounding_boxes", -1],
        ["coco2014-mini/metadata.json", "captions", -1],
        ["coco2014-mini/metadata.json", "images", -1],
        ["pass-mini/metadata.json", "images", -1],
        ["recipes/file_object_in_zip.json", "csv1", -1],
        ["recipes/file_object_in_zip.json", "csv2", -1],
        ["recipes/read_binary_file_by_line.json", "translations_from_directory", -1],
        ["recipes/read_binary_file_by_line.json", "translations_from_zip", -1],
        ["recipes/read_from_directory.json", "read_from_directory_example", -1],
        ["recipes/read_from_tar.json", "images_with_annotations", -1],
        ["simple-join/metadata.json", "publications_by_user", -1],
        ["simple-parquet/metadata.json", "persons", -1],
    ],
)
def test_hermetic_loading(version, dataset_name, record_set_name, num_records):
    load_records_and_test_equality(version, dataset_name, record_set_name, num_records)


# Non-hermetic test cases (data from the internet).
@pytest.mark.nonhermetic
@parametrize_version()
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name", "num_records"],
    [
        [
            "flores-200/metadata.json",
            "language_translations_train_data_with_metadata",
            10,
        ],
        [
            "flores-200/metadata.json",
            "language_translations_test_data_with_metadata",
            10,
        ],
        ["gpt-3/metadata.json", "default", 10],
        ["huggingface-c4/metadata.json", "en", 1],
        ["huggingface-mnist/metadata.json", "default", 10],
        ["titanic/metadata.json", "passengers", -1],
    ],
)
def test_nonhermetic_loading(version, dataset_name, record_set_name, num_records):
    load_records_and_test_equality(version, dataset_name, record_set_name, num_records)


@pytest.mark.nonhermetic
def test_load_from_huggingface():
    url = "https://datasets-server.huggingface.co/croissant?dataset=mnist&full=true"
    dataset = datasets.Dataset(url)
    has_one_record = False
    for record in dataset.records(record_set="record_set_mnist"):
        assert record["label"] == 7
        assert isinstance(record["image"], deps.PIL_Image.Image)
        has_one_record = True
        break
    assert has_one_record, (
        "mlc.Dataset.records() didn't yield any record. Warning: this test is"
        " non-hermetic and makes an API call to Hugging Face, so it's prone to network"
        " failure."
    )


@parametrize_version()
def test_raises_when_the_record_set_does_not_exist(version):
    dataset_folder = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / version
        / "titanic"
    )
    dataset = datasets.Dataset(dataset_folder / "metadata.json")
    with pytest.raises(ValueError, match="did not find"):
        dataset.records("this_record_set_does_not_exist")
