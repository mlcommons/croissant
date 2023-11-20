"""Tests for the conversion Hugging Face -> Croissant JSON-LD."""

import json

from etils import epath
import pytest

from mlcroissant.scripts.from_huggingface_to_croissant import convert


# Hugging Face's code emits warning concerning NumPy versions.
@pytest.mark.filterwarnings("ignore:A NumPy version")
@pytest.mark.parametrize(
    ["croissant_dataset_name", "hf_dataset_name"],
    [["huggingface-mnist", "mnist"], ["huggingface-c4", "c4"]],
)
def test_convert(croissant_dataset_name, hf_dataset_name):
    """Tests that huggingface.co/datasets/mnist can be generated using `convert`.

    Warning: this test is an end-to-end test of the script. It is not hermetic as it
    calls Hugging Face API.
    """
    metadata_file = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / croissant_dataset_name
        / "metadata.json"
    )
    print(
        "If this test fails, run: `mlcroissant from_huggingface_to_croissant"
        f" --dataset {hf_dataset_name} --output {metadata_file}`"
    )
    with metadata_file.open("r") as expected_f:
        expected = json.load(expected_f)
        result = convert(hf_dataset_name)
        assert result == expected
