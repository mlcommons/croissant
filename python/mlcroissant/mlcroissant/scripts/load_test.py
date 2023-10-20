"""Tests for the loading script."""

from etils import epath
import pytest

from mlcroissant.scripts import load as load_lib


def test_should_raise_when_no_record_set():
    dataset_name = "huggingface-mnist"
    file = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / dataset_name
        / "metadata.json"
    )
    with pytest.raises(
        ValueError, match="--record_set flag should have a value in `default`"
    ):
        load_lib.load(file=file, record_set=None)
