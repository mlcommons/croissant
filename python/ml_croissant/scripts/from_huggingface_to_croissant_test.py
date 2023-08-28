"""Tests for the conversion Hugging Face -> Croissant JSON-LD."""

import json

from etils import epath

from .from_huggingface_to_croissant import convert


def test_convert():
    """Tests that huggingface.co/datasets/mnist can be generated using `convert`.

    Warning: this test is an end-to-end test of the script. It is not hermetic as it
    calls Hugging Face API.
    """
    metadata_file = (
        epath.Path(__file__).parent.parent.parent.parent
        / "datasets"
        / "huggingface-mnist"
        / "metadata.json"
    )
    hf_dataset_name = "mnist"
    print(
        "If this test fails, run: `python scripts/from_huggingface_to_croissant.py"
        f" --dataset {hf_dataset_name} --output {metadata_file}`"
    )
    with metadata_file.open("r") as expected_f:
        expected = json.load(expected_f)
        result = convert(hf_dataset_name)
        assert result == expected
