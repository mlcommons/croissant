import os

import pytest
from rdflib import Graph

from croissant_rdf.providers import HuggingfaceHarvester

OUTPUT_FILEPATH = "./tests/test_output.ttl"


@pytest.fixture(autouse=True)
def cleanup():
    yield
    if os.path.isfile(OUTPUT_FILEPATH):
        os.remove(OUTPUT_FILEPATH)


def test_convert_to_rdf_mock_data():
    """Test with mock data"""
    data = [
        {
            "@context": {
                "name": "http://schema.org/name",
                "description": "http://schema.org/description",
            },
            "name": "test_dataset",
        },
        {
            "@context": {
                "name": "http://schema.org/name",
                "description": "http://schema.org/description",
            },
            "name": "test_dataset_2",
        },
        {
            "@context": {
                "name": "http://schema.org/name",
                "description": "http://schema.org/description",
            },
            "name": "test_dataset_3",
        },
    ]
    harvester = HuggingfaceHarvester(fname=OUTPUT_FILEPATH)
    file_ttl = harvester.convert_to_rdf(data)
    # assert there is a file named test_output.ttl in the data directory
    assert os.path.isfile(OUTPUT_FILEPATH)
    assert os.path.isfile(file_ttl)
    # assert there are 9 triples in the graph
    g = Graph().parse(OUTPUT_FILEPATH, format="ttl")
    assert len(g) == 3


def test_convert_to_rdf_mock_data_empty():
    """Test with empty data"""
    data = []
    harvester = HuggingfaceHarvester(fname=OUTPUT_FILEPATH)
    harvester.convert_to_rdf(data)
    assert os.path.isfile(OUTPUT_FILEPATH)
    g = Graph().parse(OUTPUT_FILEPATH, format="ttl")
    assert len(g) == 0


def test_convert_to_rdf_real_data():
    """Test data from HuggingFace, does not require API key"""
    harvester = HuggingfaceHarvester(fname=OUTPUT_FILEPATH, limit=5)
    data = harvester.fetch_datasets_croissant()
    harvester.convert_to_rdf(data)
    assert os.path.isfile(OUTPUT_FILEPATH)
    g = Graph().parse(OUTPUT_FILEPATH, format="ttl")
    assert len(g) > 0
