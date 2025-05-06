import os

from rdflib import Graph

from croissant_rdf.providers import OpenmlHarvester

OUTPUT_FILEPATH = "./tests/test_output.ttl"


def test_openml():
    harvester = OpenmlHarvester(fname=OUTPUT_FILEPATH, limit=5, search="blood")
    harvester.generate_ttl()

    assert os.path.isfile(OUTPUT_FILEPATH)
    g = Graph().parse(OUTPUT_FILEPATH, format="ttl")
    assert len(g) > 0
    os.remove(OUTPUT_FILEPATH)
