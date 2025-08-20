import json
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import DCTERMS, DCAT, FOAF, XSD, RDF


def croissant_to_geodcat_jsonld(croissant_json, output_file="geodcat.jsonld"):
    g = Graph()

    # Namespaces
    GEO = Namespace("http://www.opengis.net/ont/geosparql#")
    SCHEMA = Namespace("https://schema.org/")
    SPDX = Namespace("http://spdx.org/rdf/terms#")
    ADMS = Namespace("http://www.w3.org/ns/adms#")
    PROV = Namespace("http://www.w3.org/ns/prov#")

    g.bind("dct", DCTERMS)
    g.bind("dcat", DCAT)
    g.bind("foaf", FOAF)
    g.bind("geo", GEO)
    g.bind("schema", SCHEMA)
    g.bind("spdx", SPDX)
    g.bind("adms", ADMS)
    g.bind("prov", PROV)

    dataset_id = croissant_json.get("identifier", "dataset")
    dataset_uri = URIRef(f"https://{dataset_id}")
    g.add((dataset_uri, RDF.type, DCAT.Dataset))
    g.add((dataset_uri, RDF.type, SCHEMA.Dataset))
    g.add((dataset_uri, DCTERMS.identifier, Literal(dataset_id)))
    g.add((dataset_uri, DCTERMS.title, Literal(croissant_json["name"])))
    g.add((dataset_uri, DCTERMS.description, Literal(croissant_json["description"])))
    g.add((dataset_uri, DCTERMS.license, URIRef(croissant_json["license"])))
    if "conformsTo" in croissant_json:
        g.add((dataset_uri, DCTERMS.conformsTo, URIRef(croissant_json["conformsTo"])))

    for alt in croissant_json.get("alternateName", []):
        g.add((dataset_uri, SCHEMA.alternateName, Literal(alt)))

    if croissant_json.get("sameAs"):
        g.add((dataset_uri, SCHEMA.sameAs, URIRef(croissant_json["sameAs"])))

    creator = croissant_json.get("creator", {})
    if isinstance(creator, dict):
        creator_uri = URIRef(creator.get("url", f"https://example.org/agent/{dataset_id}"))
        g.add((creator_uri, RDF.type, FOAF.Agent))
        g.add((creator_uri, FOAF.name, Literal(creator["name"])))
        g.add((dataset_uri, DCTERMS.creator, creator_uri))

    for kw in croissant_json.get("keywords", []):
        g.add((dataset_uri, DCAT.keyword, Literal(kw)))

    # Temporal extent (hardcoded or extracted if available)
    temporal_uri = URIRef(f"{dataset_uri}/period")
    g.add((dataset_uri, DCTERMS.temporal, temporal_uri))
    g.add((temporal_uri, RDF.type, DCAT.PeriodOfTime))
    g.add((temporal_uri, DCAT.startDate, Literal("2018-01-01", datatype=XSD.date)))
    g.add((temporal_uri, DCAT.endDate, Literal("2021-12-31", datatype=XSD.date)))

    # Spatial extent (optional example)
    spatial_uri = URIRef("http://sws.geonames.org/6252001/")  # USA
    g.add((dataset_uri, DCTERMS.spatial, spatial_uri))

    # Distributions
    for dist in croissant_json.get("distribution", []):
        dist_id = dist.get("@id", "dist")
        dist_uri = URIRef(f"{dataset_uri}/distribution/{dist_id}")
        g.add((dataset_uri, DCAT.distribution, dist_uri))
        g.add((dist_uri, RDF.type, DCAT.Distribution))
        g.add((dist_uri, DCTERMS.title, Literal(dist.get("name", ""))))
        g.add((dist_uri, DCTERMS.description, Literal(dist.get("description", ""))))
        g.add((dist_uri, DCAT.accessURL, URIRef(dist.get("contentUrl", "https://example.org/data"))))
        g.add((dist_uri, DCAT.mediaType, Literal(dist.get("encodingFormat", "application/octet-stream"))))

        if "sha256" in dist:
            checksum_node = URIRef(f"{dist_uri}/checksum")
            g.add((dist_uri, SPDX.checksum, checksum_node))
            g.add((checksum_node, RDF.type, SPDX.Checksum))
            g.add((checksum_node, SPDX.algorithm, Literal("SHA256")))
            g.add((checksum_node, SPDX.checksumValue, Literal(dist["sha256"])))

        if "containedIn" in dist:
            parent_id = dist["containedIn"].get("@id")
            if parent_id:
                parent_uri = URIRef(f"{dataset_uri}/distribution/{parent_id}")
                g.add((dist_uri, DCTERMS.isPartOf, parent_uri))

        if "includes" in dist:
            g.add((dist_uri, SCHEMA.hasPart, Literal(dist["includes"])))

    if croissant_json.get("url"):
        g.add((dataset_uri, DCAT.landingPage, URIRef(croissant_json["url"])))

    g.serialize(destination=output_file, format="json-ld", indent=2)
    print(f"GeoDCAT JSON-LD metadata written to {output_file}")

    g.serialize(destination="geodcat.ttl", format="turtle")
    print("GeoDCAT Turtle metadata written to geodcat.ttl")


if __name__ == "__main__":
    with open("croissant.json", "r") as f:
        croissant = json.load(f)

    croissant_to_geodcat_jsonld(croissant, output_file="geodcat.jsonld")
