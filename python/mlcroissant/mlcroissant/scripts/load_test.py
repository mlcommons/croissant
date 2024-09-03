"""Tests for the loading script."""

from etils import epath
import pytest

from mlcroissant._src.tests.versions import parametrize_version
from mlcroissant.scripts import load as load_lib


def test_should_raise_when_no_record_set():
    dataset_name = "huggingface-mnist"
    file = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / "1.0"
        / dataset_name
        / "metadata.json"
    )
    with pytest.raises(
        ValueError,
        match="--record_set flag should have a value in `mnist_splits`, `default`",
    ):
        load_lib.load(jsonld=file, record_set=None)


@parametrize_version()
def test_should_raise_when_invalid_mapping(version):
    file = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / version
        / "huggingface-mnist"
        / "metadata.json"
    )
    with pytest.raises(
        ValueError, match="--mapping should be a valid dict\\[str, str\\]"
    ):
        load_lib.load(jsonld=file, record_set="default", mapping="foobarbaz")
