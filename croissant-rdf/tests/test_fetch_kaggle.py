import json
import os
from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph

from croissant_rdf.providers import KaggleHarvester

base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "kaggle_croissant.json"), "r") as f:
    test_metadata_kaggle = json.load(f)


@pytest.fixture
def mock_response():
    """Kaggle requires an API key to fetch datasets so we need to mock."""
    mock = MagicMock()
    mock.json.return_value = test_metadata_kaggle
    mock.status_code = 200
    return mock


def test_mock_croissant_dataset(mock_response):
    with patch("requests.get", return_value=mock_response) as mock_get:
        harvester = KaggleHarvester(limit=1)
        result = harvester.fetch_dataset_croissant("test_dataset").json()

        mock_get.assert_called_once_with("https://www.kaggle.com/datasets/test_dataset/croissant/download", timeout=30)
        assert result == test_metadata_kaggle


def test_mock_fetch_datasets(mock_response):
    with patch.object(KaggleHarvester, "fetch_datasets_ids", return_value=["test_dataset"]), patch(
        "requests.get",
        return_value=mock_response,
    ):
        harvester = KaggleHarvester(limit=1)
        result = harvester.fetch_datasets_croissant()
        assert len(result) == 1
        assert result[0] == test_metadata_kaggle


OUTPUT_FILEPATH = "./tests/test_output.ttl"


def test_generate_ttl(mock_response):
    """Test the complete generate_ttl workflow."""
    with patch.object(KaggleHarvester, "fetch_datasets_ids", return_value=["test_dataset"]), patch(
        "requests.get",
        return_value=mock_response,
    ):
        harvester = KaggleHarvester(fname=OUTPUT_FILEPATH, limit=3, use_api_key=False)
        file_ttl = harvester.generate_ttl()
        assert os.path.isfile(OUTPUT_FILEPATH)
        assert os.path.isfile(file_ttl)
        g = Graph().parse(OUTPUT_FILEPATH, format="ttl")
        assert len(g) > 0
        os.remove(OUTPUT_FILEPATH)
