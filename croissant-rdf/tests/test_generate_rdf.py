import os.path
import tempfile

from rdflib import Graph

from croissant_rdf import HuggingfaceHarvester

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
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".ttl", delete_on_close=False) as fp:

        harvester = HuggingfaceHarvester(fname=fp.name)
        file_ttl = harvester.convert_to_rdf(data)
        # assert there is a file named test_output.ttl in the data directory
        assert os.path.isfile(fp.name)
        assert os.path.isfile(file_ttl)
        # assert there are 9 triples in the graph
        g = Graph().parse(fp.name, format="ttl")
        assert len(g) == 3


def test_convert_to_rdf_mock_data_empty():
    """Test with empty data"""
    data = []
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".ttl", delete_on_close=False) as fp:
        harvester = HuggingfaceHarvester(fname=fp.name)
        harvester.convert_to_rdf(data)
        assert os.path.isfile(fp.name)
        g = Graph().parse(fp.name, format="ttl")
        assert len(g) == 0


def test_convert_to_rdf_real_data():
    """Test data from HuggingFace, does not require API key"""
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".ttl", delete_on_close=False) as fp:
        harvester = HuggingfaceHarvester(fname=fp.name, limit=5)
        data = harvester.fetch_datasets_croissant()
        harvester.convert_to_rdf(data)
        assert os.path.isfile(fp.name)
        g = Graph().parse(fp.name, format="ttl")
        assert len(g) > 0
