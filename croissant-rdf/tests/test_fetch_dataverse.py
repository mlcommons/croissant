import os

from rdflib import Graph

from croissant_rdf.providers import DataverseHarvester

OUTPUT_FILEPATH = "./tests/test_output.ttl"


def test_dataverse():
    harvester = DataverseHarvester(
        fname=OUTPUT_FILEPATH,
        limit=3,
        search="Soil",
        api_url="https://demo.dataverse.org",
    )
    harvester.generate_ttl()

    assert os.path.isfile(OUTPUT_FILEPATH)
    g = Graph().parse(OUTPUT_FILEPATH, format="ttl")
    assert len(g) > 0
    os.remove(OUTPUT_FILEPATH)
