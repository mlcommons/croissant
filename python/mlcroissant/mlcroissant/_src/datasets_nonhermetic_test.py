"""datasets_nonhermetic_test module with data from the internet."""

import json

from etils import epath
import pytest

from mlcroissant._src import datasets
from mlcroissant._src.core import constants
from mlcroissant._src.core.optional import deps
from mlcroissant._src.datasets_test import load_records_and_test_equality
from mlcroissant._src.tests.versions import parametrize_version


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


# Non-hermetic test cases for croissant 1.0 only (data from the internet).
@pytest.mark.nonhermetic
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name", "num_records", "filters"],
    [
        ["huggingface-anthropic-hh-rlhf/metadata.json", "red-team-attempts", 10, None],
        ["huggingface-c4/metadata.json", "data", 1, {"data/variant": "en"}],
        ["huggingface-levanti/metadata.json", "levanti_train", 10, None],
        ["huggingface-open-hermes/metadata.json", "default", 3, None],
        # This dataset will timeout if the following feature is broken: mlcroissant
        # yields examples by downloading parquet files one by one. mlcroissant should
        # not download all parquet files upfront.
        # TODO(ccl-core): re-enable this test once HF regression in fixed.
        # [
        #     "https://huggingface.co/api/datasets/bigcode/the-stack-metadata/croissant",
        #     "default",
        #     1,
        #     {"default/split": "train"},
        # ],
    ],
)
def test_nonhermetic_loading_1_0(dataset_name, record_set_name, num_records, filters):
    load_records_and_test_equality(
        "1.0", dataset_name, record_set_name, num_records, filters
    )


# Non-hermetic test cases for croissant >=1.1 only.
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name", "num_records", "filters"],
    [
        ["huggingface-pollen-robotics-apple-storage/metadata.json", "default", 2, None],
        [
            "huggingface-manud-dfl_video_classification/metadata.json",
            "default",
            2,
            None,
        ],
    ],
)
def test_nonhermetic_loading_1_1(dataset_name, record_set_name, num_records, filters):
    load_records_and_test_equality(
        "1.1", dataset_name, record_set_name, num_records, filters
    )


@pytest.mark.nonhermetic
def test_load_from_huggingface():
    url = "https://huggingface.co/api/datasets/ylecun/mnist/croissant"
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
def test_cypress_fixtures(version):
    # Cypress cannot read files outside of its direct scope, so we have to copy them
    # as fixtures. This test tests that the copies are equal to the original.
    fixture_folder: epath.Path = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "editor"
        / "cypress"
        / "fixtures"
        / version
    )
    datasets_folder: epath.Path = constants.DATASETS_FOLDER / version
    for fixture in fixture_folder.glob("*.json"):
        dataset = datasets_folder / f"{fixture.stem}" / "metadata.json"
        assert json.load(fixture.open()) == json.load(dataset.open()), (
            f"If this test fails, you probably have to copy the content of {dataset} to"
            f" {fixture}. Launch the command `cp {dataset} {fixture}`"
        )
