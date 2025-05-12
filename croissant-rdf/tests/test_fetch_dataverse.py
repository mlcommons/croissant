from rdflib import Graph

from croissant_rdf import DataverseHarvester

import tempfile



def test_dataverse():
    
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".ttl", delete_on_close=False) as fp:

        harvester = DataverseHarvester(
            fname=fp.name,
            limit=3,
            search="Soil",
            api_url="https://demo.dataverse.org",
        )
        harvester.generate_ttl()

        g = Graph().parse(fp.name, format="ttl")
        assert len(g) > 0