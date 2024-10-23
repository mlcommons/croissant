"""datasets_test module."""

import json
from typing import Any

from apache_beam.testing import test_pipeline
from apache_beam.testing.util import assert_that
from etils import epath
import pytest

from mlcroissant._src import datasets
from mlcroissant._src.beam import ReadFromCroissant
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.optional import deps
from mlcroissant._src.tests.records import record_to_python
from mlcroissant._src.tests.versions import parametrize_version

_REPOSITORY_FOLDER = epath.Path(__file__).parent.parent.parent.parent.parent


# End-to-end tests on real data. The data is in `tests/graphs/*/metadata.json`.
def get_error_msg(folder: epath.Path):
    path = folder / "output.txt"
    with path.open("r") as file:
        return file.read().strip()


@parametrize_version()
@pytest.mark.parametrize(
    "folder",
    [
        # Distribution.
        "distribution_bad_contained_in",
        "distribution_bad_type",
        "distribution_missing_encoding_format",
        "distribution_missing_property_content_url",
        # Metadata.
        "metadata_bad_type",
        # ML field.
        "mlfield_bad_source",
        "mlfield_bad_type",
        "mlfield_missing_source",
        # Record set.
        "recordset_bad_type",
        "recordset_missing_context_for_datatype",
        "recordset_wrong_join",
    ],
)
def test_static_analysis(version, folder):
    base_path = epath.Path(__file__).parent / "tests/graphs" / version
    with pytest.raises(ValidationError) as error_info:
        datasets.Dataset(base_path / f"{folder}/metadata.json")
    assert str(error_info.value) == get_error_msg(base_path / folder)


# These tests refer to properties which were mandatory for Croissant 0.8, but not 1.0.
@pytest.mark.parametrize(
    "folder",
    [
        "distribution_missing_name",
        "metadata_missing_property_name",
        "mlfield_missing_property_name",
        "recordset_missing_property_name",
    ],
)
def test_static_analysis_0_8(folder):
    base_path = epath.Path(__file__).parent / "tests/graphs" / "0.8"
    with pytest.raises(ValidationError) as error_info:
        datasets.Dataset(base_path / f"{folder}/metadata.json")
    assert str(error_info.value) == get_error_msg(base_path / folder)


# Tests for 1.0-datasets only.
@pytest.mark.parametrize(
    "folder",
    [
        "distribution_bad_id",
    ],
)
def test_static_analysis_1_0(folder):
    base_path = epath.Path(__file__).parent / "tests/graphs/1.0"
    with pytest.raises(ValidationError) as error_info:
        datasets.Dataset(base_path / f"{folder}/metadata.json")
    assert str(error_info.value) == get_error_msg(base_path / folder)


def load_records_and_test_equality(
    version: str,
    dataset_name: str,
    record_set_name: str,
    num_records: int,
    filters: dict[str, Any] | None = None,
    mapping: dict[str, epath.PathLike] | None = None,
):
    filters_command = ""
    if filters:
        filters_command = str(filters).replace("'", '"')
        filters_command = f" --filters '{filters_command}'"
    print(
        "If this test fails, update JSONL with: `mlcroissant load --jsonld"
        f" ../../datasets/{version}/{dataset_name} --record_set"
        f" {record_set_name} --num_records {num_records} --debug --update_output"
        f" {filters_command}`"
    )
    config = _REPOSITORY_FOLDER / "datasets" / version / dataset_name
    output_file = config.parent / "output" / f"{record_set_name}.jsonl"
    with output_file.open("rb") as f:
        lines = f.readlines()
        expected_records = [json.loads(line) for line in lines]
    dataset = datasets.Dataset(config, mapping=mapping)
    records = dataset.records(record_set_name, filters=filters)
    records = iter(records)
    length = 0
    for i, record in enumerate(records):
        if num_records > 0 and i >= num_records:
            break
        record = record_to_python(record)
        assert record == expected_records[i]
        length += 1
    assert len(expected_records) == length


def _equal_to_set(expected):
    """Checks whether 2 beam.PCollections are equal as sets."""

    def matcher_fn(actual):
        # Sort by index, then remove the index from the PCollection returned by Beam:
        actual = [element for _, element in sorted(list(actual))]
        expected_set = set([
            json.dumps(record_to_python(element)) for element in list(expected)
        ])
        actual_set = set([
            json.dumps(record_to_python(element)) for element in list(actual)
        ])
        assert expected_set == actual_set

    return matcher_fn


def load_records_with_beam_and_test_equality(
    version: str,
    dataset_name: str,
    record_set_name: str,
):
    jsonld = _REPOSITORY_FOLDER / "datasets" / version / dataset_name
    output_file = jsonld.parent / "output" / f"{record_set_name}.jsonl"
    with output_file.open("rb") as f:
        lines = f.readlines()
        expected_records = [json.loads(line) for line in lines]

    with test_pipeline.TestPipeline() as pipeline:
        result = pipeline | ReadFromCroissant(jsonld=jsonld, record_set=record_set_name)
        assert_that(result, _equal_to_set(expected_records))


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
        ["audio_test/metadata.json", "records", 2],
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


@parametrize_version()
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name"],
    [
        ["simple-parquet/metadata.json", "persons"],
        ["simple-join/metadata.json", "publications_by_user"],
    ],
)
def test_beam_hermetic_loading(version, dataset_name, record_set_name):
    load_records_with_beam_and_test_equality(version, dataset_name, record_set_name)


# Hermetic test cases for croissant >=1.0 only.
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name", "num_records", "filters"],
    [
        ["coco2014-mini/metadata.json", "bounding_boxes", -1, None],
        ["coco2014-mini/metadata.json", "captions", -1, None],
        ["coco2014-mini/metadata.json", "images", -1, None],
        ["coco2014-mini/metadata.json", "split_enums", -1, None],
        ["simple-split/metadata.json", "data", -1, {"data/split": "train"}],
    ],
)
def test_hermetic_loading_1_0(dataset_name, record_set_name, num_records, filters):
    load_records_and_test_equality(
        "1.0", dataset_name, record_set_name, num_records, filters
    )


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
        ["huggingface-mnist/metadata.json", "default", 10],
        ["titanic/metadata.json", "passengers", -1],
    ],
)
def test_nonhermetic_loading(version, dataset_name, record_set_name, num_records):
    load_records_and_test_equality(version, dataset_name, record_set_name, num_records)


# Non-hermetic test cases for croissant >=1.0 only (data from the internet).
@pytest.mark.nonhermetic
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name", "num_records", "filters"],
    [
        ["huggingface-anthropic-hh-rlhf/metadata.json", "red-team-attempts", 10, None],
        ["huggingface-c4/metadata.json", "data", 1, {"data/variant": "en"}],
        ["huggingface-levanti/metadata.json", "levanti_train", 10, None],
        ["huggingface-open-hermes/metadata.json", "default", 3, None],
    ],
)
def test_nonhermetic_loading_1_0(dataset_name, record_set_name, num_records, filters):
    load_records_and_test_equality(
        "1.0", dataset_name, record_set_name, num_records, filters
    )


@pytest.mark.nonhermetic
def test_load_from_huggingface():
    url = "https://huggingface.co/api/datasets/mnist/croissant"
    dataset = datasets.Dataset(url)
    has_one_record = False
    for record in dataset.records(record_set="mnist"):
        assert record["mnist/label"] == 7
        assert isinstance(record["mnist/image"], deps.PIL_Image.Image)
        has_one_record = True
        break
    assert has_one_record, (
        "mlc.Dataset.records() didn't yield any record. Warning: this test is"
        " non-hermetic and makes an API call to Hugging Face, so it's prone to network"
        " failure."
    )


@parametrize_version()
def test_raises_when_the_record_set_does_not_exist(version):
    dataset_folder = _REPOSITORY_FOLDER / "datasets" / version / "titanic"
    dataset = datasets.Dataset(dataset_folder / "metadata.json")
    with pytest.raises(ValueError, match="did not find"):
        dataset.records("this_record_set_does_not_exist")


@parametrize_version()
def test_cypress_fixtures(version):
    # Cypress cannot read files outside of its direct scope, so we have to copy them
    # as fixtures. This test tests that the copies are equal to the original.
    fixture_folder: epath.Path = (
        _REPOSITORY_FOLDER / "editor" / "cypress" / "fixtures" / version
    )
    datasets_folder: epath.Path = _REPOSITORY_FOLDER / "datasets" / version
    for fixture in fixture_folder.glob("*.json"):
        dataset = datasets_folder / f"{fixture.stem}" / "metadata.json"
        assert json.load(fixture.open()) == json.load(dataset.open()), (
            f"If this test fails, you probably have to copy the content of {dataset} to"
            f" {fixture}. Launch the command `cp {dataset} {fixture}`"
        )


@pytest.mark.parametrize(
    ["filters", "raises"],
    [
        [{}, False],
        [{"split": "test"}, False],
        [{"split": "test", "other_filter": "foo"}, True],
        [{"split": ["train", "test"]}, True],
        [{"split": 1}, True],
    ],
)
def test_validate_filters(filters, raises):
    if raises:
        with pytest.raises(ValueError):
            datasets._validate_filters(filters)
    else:
        datasets._validate_filters(filters)


@parametrize_version()
def test_check_mapping_when_the_key_does_not_exist(version):
    dataset_name = "simple-parquet/metadata.json"
    record_set_name = "persons"
    with pytest.raises(ValueError, match="doesn't exist in the JSON-LD"):
        load_records_and_test_equality(
            version,
            dataset_name,
            record_set_name,
            -1,
            mapping={"this_UUID_does_not_exist": "/this/path/does/not/exist"},
        )


@parametrize_version()
def test_check_mapping_when_the_path_does_not_exist(version):
    dataset_name = "simple-parquet/metadata.json"
    record_set_name = "persons"
    with pytest.raises(ValueError, match="doesn't exist on disk"):
        load_records_and_test_equality(
            version,
            dataset_name,
            record_set_name,
            -1,
            mapping={"dataframe": "/this/path/does/not/exist"},
        )


@parametrize_version()
def test_check_mapping_when_the_mapping_is_correct(version, tmp_path):
    dataset_name = "simple-parquet/metadata.json"
    record_set_name = "persons"
    old_path = (
        _REPOSITORY_FOLDER
        / "datasets"
        / version
        / "simple-parquet/data/dataframe.parquet"
    )
    assert old_path.exists()
    # Copy the dataframe to a temporary file:
    new_path = tmp_path / "dataframe.parquet"
    old_path.copy(new_path)
    load_records_and_test_equality(
        version,
        dataset_name,
        record_set_name,
        -1,
        mapping={"dataframe": new_path},
    )
