import os.path
import tempfile

from rdflib import Graph

from croissant_rdf import OpenmlHarvester

def test_openml():
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".ttl", delete_on_close=False) as fp:

        harvester = OpenmlHarvester(fname=fp.name, limit=5, search="blood")
        harvester.generate_ttl()

        assert os.path.isfile(fp.name)
        g = Graph().parse(fp.name, format="ttl")
        assert len(g) > 0