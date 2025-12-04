"""GeoCroissant to GeoDCAT Conversion Module.

This module provides functionality for converting GeoCroissant metadata to GeoDCAT
(Geographic Data Catalog Vocabulary) format. It handles the transformation of
GeoCroissant's JSON metadata into RDF-based GeoDCAT representations, enabling
interoperability with geographic data catalog systems.
"""

import json
from urllib.parse import quote

from rdflib import Graph
from rdflib import Literal
from rdflib import Namespace
from rdflib import URIRef
from rdflib.namespace import DCAT
from rdflib.namespace import DCTERMS
from rdflib.namespace import FOAF
from rdflib.namespace import RDF
from rdflib.namespace import SKOS
from rdflib.namespace import XSD


def croissant_to_geodcat_jsonld(
    croissant_json, output_file="geodcat.jsonld", gitattributes_file=".gitattributes"
):
    """Convert GeoCroissant JSON to GeoDCAT JSON-LD format.

    Args:
        croissant_json: GeoCroissant metadata dictionary.
        output_file: Path to output GeoDCAT JSON-LD file.
        gitattributes_file: Path to .gitattributes file for LFS URLs.

    Returns:
        Graph: RDF graph containing the GeoDCAT representation.
    """
    g = Graph()

    # Load real file URLs from .gitattributes
    file_urls = {}
    try:
        with open(gitattributes_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract the relative path from the full URL
                    if "resolve/main/" in line:
                        relative_path = line.split("resolve/main/")[-1]
                        file_urls[relative_path] = line

    except FileNotFoundError:
        print(f"Warning: {gitattributes_file} not found, using example URLs")

    # Namespaces
    GEO = Namespace("http://www.opengis.net/ont/geosparql#")
    SCHEMA = Namespace("https://schema.org/")
    SPDX = Namespace("http://spdx.org/rdf/terms#")
    ADMS = Namespace("http://www.w3.org/ns/adms#")
    PROV = Namespace("http://www.w3.org/ns/prov#")
    GEOCR = Namespace("http://mlcommons.org/croissant/geocr/")
    CR = Namespace("http://mlcommons.org/croissant/")
    RAI = Namespace("http://mlcommons.org/croissant/RAI/")
    GEODCAT = Namespace("http://data.europa.eu/930/")

    g.bind("dct", DCTERMS)
    g.bind("dcat", DCAT)
    g.bind("foaf", FOAF)
    g.bind("geo", GEO)
    g.bind("schema", SCHEMA)
    g.bind("spdx", SPDX)
    g.bind("adms", ADMS)
    g.bind("prov", PROV)
    g.bind("skos", SKOS)
    g.bind("geocr", GEOCR)
    g.bind("cr", CR)
    g.bind("rai", RAI)
    g.bind("geodcat", GEODCAT)

    dataset_id = croissant_json.get("identifier", croissant_json.get("name", "dataset"))
    # Use the real Hugging Face dataset URL if available
    if "huggingface.co/datasets/harshinde/hls_burn_scars" in str(file_urls.values()):
        dataset_uri = URIRef("https://huggingface.co/datasets/harshinde/hls_burn_scars")
    elif not dataset_id.startswith("http"):
        dataset_uri = URIRef(f"https://huggingface.co/datasets/harshinde/{dataset_id}")
    else:
        dataset_uri = URIRef(dataset_id)
    g.add((dataset_uri, RDF.type, DCAT.Dataset))
    g.add((dataset_uri, RDF.type, SCHEMA.Dataset))
    # Add GeoDCAT-AP dataset type
    g.add((dataset_uri, DCTERMS.type, Literal("Dataset")))
    g.add((dataset_uri, DCTERMS.identifier, Literal(dataset_id)))
    g.add((dataset_uri, DCTERMS.title, Literal(croissant_json["name"], lang="en")))
    g.add(
        (
            dataset_uri,
            DCTERMS.description,
            Literal(croissant_json["description"], lang="en"),
        )
    )
    g.add((dataset_uri, DCTERMS.license, URIRef(croissant_json["license"])))

    # Version information
    if "version" in croissant_json:
        g.add((dataset_uri, ADMS.version, Literal(croissant_json["version"])))

    # Publication date
    if "datePublished" in croissant_json:
        date_str = croissant_json["datePublished"]
        # Handle both date and datetime formats
        if "T" in date_str:
            g.add(
                (dataset_uri, DCTERMS.issued, Literal(date_str, datatype=XSD.dateTime))
            )
        else:
            g.add((dataset_uri, DCTERMS.issued, Literal(date_str, datatype=XSD.date)))

    # Citation
    if "citeAs" in croissant_json:
        g.add((dataset_uri, CR.citeAs, Literal(croissant_json["citeAs"])))

    # Live dataset flag
    if "isLiveDataset" in croissant_json:
        g.add(
            (
                dataset_uri,
                CR.isLiveDataset,
                Literal(croissant_json["isLiveDataset"], datatype=XSD.boolean),
            )
        )

    if "conformsTo" in croissant_json:
        g.add((dataset_uri, DCTERMS.conformsTo, URIRef(croissant_json["conformsTo"])))

    for alt in croissant_json.get("alternateName", []):
        g.add((dataset_uri, SCHEMA.alternateName, Literal(alt)))

    if croissant_json.get("sameAs"):
        g.add((dataset_uri, SCHEMA.sameAs, URIRef(croissant_json["sameAs"])))

    creator = croissant_json.get("creator", {})
    if isinstance(creator, dict):
        creator_uri = URIRef(
            creator.get("url", f"https://example.org/agent/{dataset_id}")
        )
        g.add((creator_uri, RDF.type, FOAF.Agent))
        g.add((creator_uri, FOAF.name, Literal(creator["name"])))
        g.add((dataset_uri, DCTERMS.creator, creator_uri))

    for kw in croissant_json.get("keywords", []):
        g.add((dataset_uri, DCAT.keyword, Literal(kw)))

    # Temporal extent from geocr:temporalExtent (GeoDCAT-AP compliant)
    if "geocr:temporalExtent" in croissant_json:
        temporal_extent = croissant_json["geocr:temporalExtent"]
        temporal_uri = URIRef(f"{dataset_uri}/period")
        g.add((dataset_uri, DCTERMS.temporal, temporal_uri))
        g.add((temporal_uri, RDF.type, DCTERMS.PeriodOfTime))
        if "startDate" in temporal_extent:
            g.add(
                (
                    temporal_uri,
                    DCAT.startDate,
                    Literal(temporal_extent["startDate"], datatype=XSD.dateTime),
                )
            )
        if "endDate" in temporal_extent:
            g.add(
                (
                    temporal_uri,
                    DCAT.endDate,
                    Literal(temporal_extent["endDate"], datatype=XSD.dateTime),
                )
            )

        # Add temporal coverage as GeoDCAT-AP property
        if "startDate" in temporal_extent and "endDate" in temporal_extent:
            g.add(
                (
                    dataset_uri,
                    GEODCAT.temporalCoverage,
                    Literal(
                        f"{temporal_extent['startDate']}/{temporal_extent['endDate']}"
                    ),
                )
            )

    # Spatial extent from geocr:BoundingBox (GeoDCAT-AP compliant)
    if "geocr:BoundingBox" in croissant_json:
        bbox = croissant_json["geocr:BoundingBox"]
        if len(bbox) >= 4:
            # Create a spatial coverage node
            spatial_uri = URIRef(f"{dataset_uri}/spatial")
            g.add((dataset_uri, DCTERMS.spatial, spatial_uri))
            g.add((spatial_uri, RDF.type, DCTERMS.Location))

            # Create a geometry node for the bounding box
            geometry_uri = URIRef(f"{dataset_uri}/geometry")
            g.add((spatial_uri, GEO.hasGeometry, geometry_uri))
            g.add((geometry_uri, RDF.type, GEO.Geometry))

            # Create WKT representation of bounding box
            wkt = (
                f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]},"
                f" {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            )
            g.add((geometry_uri, GEO.asWKT, Literal(wkt, datatype=GEO.wktLiteral)))

            # Add bounding box as GeoDCAT-AP property
            g.add(
                (
                    dataset_uri,
                    GEODCAT.bbox,
                    Literal(f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"),
                )
            )

    # Spatial resolution (using GeoDCAT-AP property)
    if "geocr:spatialResolution" in croissant_json:
        g.add(
            (
                dataset_uri,
                GEODCAT.spatialResolutionAsText,
                Literal(croissant_json["geocr:spatialResolution"]),
            )
        )

    # Coordinate Reference System (using GeoDCAT-AP property)
    if "geocr:coordinateReferenceSystem" in croissant_json:
        g.add(
            (
                dataset_uri,
                GEODCAT.referenceSystem,
                Literal(croissant_json["geocr:coordinateReferenceSystem"]),
            )
        )

    # Additional dataset metadata from sensor characteristics
    if "geocr:sensorCharacteristics" in croissant_json:
        for sensor in croissant_json["geocr:sensorCharacteristics"]:
            if "dataVolume" in sensor:
                g.add((dataset_uri, CR.dataVolume, Literal(sensor["dataVolume"])))
            if "fileCounts" in sensor:
                file_counts = sensor["fileCounts"]
                for split, count in file_counts.items():
                    g.add((dataset_uri, CR.fileCount, Literal(f"{split}:{count}")))
            if "classDistribution" in sensor:
                class_dist = sensor["classDistribution"]
                for class_name, percentage in class_dist.items():
                    g.add(
                        (
                            dataset_uri,
                            CR.classDistribution,
                            Literal(f"{class_name}:{percentage}"),
                        )
                    )

    # ML Task information
    if "geocr:mlTask" in croissant_json:
        ml_task = croissant_json["geocr:mlTask"]
        task_uri = URIRef(f"{dataset_uri}/mlTask")
        g.add((dataset_uri, GEOCR.mlTask, task_uri))
        g.add((task_uri, RDF.type, GEOCR.MLTask))

        if "@type" in ml_task:
            g.add((task_uri, RDF.type, URIRef(ml_task["@type"])))
        if "taskType" in ml_task:
            g.add((task_uri, GEOCR.taskType, Literal(ml_task["taskType"])))
        if "evaluationMetric" in ml_task:
            g.add(
                (task_uri, GEOCR.evaluationMetric, Literal(ml_task["evaluationMetric"]))
            )
        if "applicationDomain" in ml_task:
            g.add(
                (
                    task_uri,
                    GEOCR.applicationDomain,
                    Literal(ml_task["applicationDomain"]),
                )
            )
        if "classes" in ml_task:
            for class_name in ml_task["classes"]:
                g.add((task_uri, GEOCR.classes, Literal(class_name)))

    # Sensor characteristics
    if "geocr:sensorCharacteristics" in croissant_json:
        for i, sensor in enumerate(croissant_json["geocr:sensorCharacteristics"]):
            sensor_uri = URIRef(f"{dataset_uri}/sensor/{i}")
            g.add((dataset_uri, GEOCR.sensorCharacteristics, sensor_uri))
            g.add((sensor_uri, RDF.type, GEOCR.SensorCharacteristics))

            if "platform" in sensor:
                g.add((sensor_uri, GEOCR.platform, Literal(sensor["platform"])))
            if "sensorType" in sensor:
                g.add((sensor_uri, GEOCR.sensorType, Literal(sensor["sensorType"])))
            if "bandConfiguration" in sensor:
                band_config = sensor["bandConfiguration"]
                for band_name, band_info in band_config.items():
                    if isinstance(band_info, dict) and "name" in band_info:
                        band_uri = URIRef(f"{sensor_uri}/band/{band_name}")
                        g.add((sensor_uri, GEOCR.bandConfiguration, band_uri))
                        g.add((band_uri, RDF.type, GEOCR.BandConfiguration))
                        g.add((band_uri, GEOCR.bandName, Literal(band_info["name"])))
                        if "wavelength" in band_info:
                            g.add(
                                (
                                    band_uri,
                                    GEOCR.wavelength,
                                    Literal(band_info["wavelength"]),
                                )
                            )

    # File listing information - extract actual file paths
    if "geocr:fileListing" in croissant_json:
        file_listing = croissant_json["geocr:fileListing"]
        file_listing_uri = URIRef(f"{dataset_uri}/fileListing")
        g.add((dataset_uri, GEOCR.fileListing, file_listing_uri))
        g.add((file_listing_uri, RDF.type, GEOCR.FileListing))

        if "basePaths" in file_listing:
            base_paths = file_listing["basePaths"]
            for path_type, path_value in base_paths.items():
                g.add(
                    (
                        file_listing_uri,
                        GEOCR.basePath,
                        Literal(f"{path_type}:{path_value}"),
                    )
                )

        # Handle images and annotations file listings with actual file paths
        for file_type in ["images", "annotations"]:
            if file_type in file_listing:
                file_type_uri = URIRef(f"{file_listing_uri}/{file_type}")
                g.add((file_listing_uri, GEOCR.fileType, file_type_uri))
                g.add((file_type_uri, RDF.type, GEOCR.FileType))
                # Create proper file type titles
                if file_type == "images":
                    file_type_title = "Satellite Images"
                else:  # annotations
                    file_type_title = "Burn Scar Masks"

                g.add((file_type_uri, DCTERMS.title, Literal(file_type_title)))

                file_info = file_listing[file_type]

                # Handle training and validation splits
                for split_type in ["train", "validation"]:
                    if split_type in file_info:
                        split_uri = URIRef(f"{file_type_uri}/{split_type}")
                        g.add((file_type_uri, CR.dataSplit, split_uri))
                        g.add((split_uri, RDF.type, CR.DataSplit))
                        # Create proper split titles
                        if split_type == "train":
                            split_title = "Training"
                        else:  # validation
                            split_title = "Validation"

                        if file_type == "images":
                            file_type_title = "Satellite Images"
                        else:  # annotations
                            file_type_title = "Burn Scar Masks"

                        g.add(
                            (
                                split_uri,
                                DCTERMS.title,
                                Literal(f"{file_type_title} - {split_title}"),
                            )
                        )

                        # Add each file as a distribution with proper naming
                        file_list = file_info[split_type]
                        for i, file_path in enumerate(file_list):
                            # Create proper naming based on file type and split
                            if file_type == "images":
                                if split_type == "train":
                                    title = f"Training Image {i + 1}"
                                    description = (
                                        f"Training satellite image {i + 1} from HLS"
                                        " burn scars dataset"
                                    )
                                else:  # validation
                                    title = f"Validation Image {i + 1}"
                                    description = (
                                        f"Validation satellite image {i + 1} from HLS"
                                        " burn scars dataset"
                                    )
                            else:  # annotations
                                if split_type == "train":
                                    title = f"Training Mask {i + 1}"
                                    description = (
                                        f"Training burn scar mask {i + 1} from HLS burn"
                                        " scars dataset"
                                    )
                                else:  # validation
                                    title = f"Validation Mask {i + 1}"
                                    description = (
                                        f"Validation burn scar mask {i + 1} from HLS"
                                        " burn scars dataset"
                                    )

                            # Use the actual file URL as the distribution URI
                            if file_path.startswith("http"):
                                file_dist_uri = URIRef(file_path)
                            elif file_path in file_urls:
                                file_dist_uri = URIRef(file_urls[file_path])
                            else:
                                file_dist_uri = URIRef(f"file://{file_path}")

                            g.add((dataset_uri, DCAT.distribution, file_dist_uri))
                            g.add((file_dist_uri, RDF.type, DCAT.Distribution))
                            g.add((file_dist_uri, DCTERMS.title, Literal(title)))
                            g.add(
                                (
                                    file_dist_uri,
                                    DCTERMS.description,
                                    Literal(description),
                                )
                            )

                            # The distribution URI is the same as the access URL
                            g.add((file_dist_uri, DCAT.accessURL, file_dist_uri))
                            g.add(
                                (
                                    file_dist_uri,
                                    DCAT.mediaType,
                                    Literal(
                                        "image/tiff"
                                        if file_type == "images"
                                        else "image/tiff"
                                    ),
                                )
                            )
                            g.add((file_dist_uri, CR.dataSplit, Literal(split_type)))
                            g.add((file_dist_uri, CR.fileType, Literal(file_type)))

                            # Link to split
                            g.add((split_uri, CR.file, file_dist_uri))

                # Add file counts
                total_files = 0
                for split_type in ["train", "validation"]:
                    if split_type in file_info:
                        total_files += len(file_info[split_type])
                if total_files > 0:
                    g.add(
                        (
                            file_type_uri,
                            CR.fileCount,
                            Literal(total_files, datatype=XSD.integer),
                        )
                    )

    # Distributions - use actual content URLs as distribution URIs
    for dist in croissant_json.get("distribution", []):
        content_url = dist.get("contentUrl", "https://example.org/data")
        # Handle local file paths by converting to file:// URLs
        if content_url.startswith("/") or "\\" in content_url:
            content_url = f"file://{quote(content_url, safe='/')}"

        # Use the actual content URL as the distribution URI
        dist_uri = URIRef(content_url)
        g.add((dataset_uri, DCAT.distribution, dist_uri))
        g.add((dist_uri, RDF.type, DCAT.Distribution))
        g.add((dist_uri, DCTERMS.title, Literal(dist.get("name", ""))))
        g.add((dist_uri, DCTERMS.description, Literal(dist.get("description", ""))))
        g.add((dist_uri, DCAT.accessURL, dist_uri))
        g.add(
            (
                dist_uri,
                DCAT.mediaType,
                Literal(dist.get("encodingFormat", "application/octet-stream")),
            )
        )

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

    # Record Sets (mapped to DCAT Resources)
    for i, record_set in enumerate(croissant_json.get("recordSet", [])):
        record_set_id = record_set.get("@id", f"recordset_{i}")
        # Ensure valid URI
        safe_id = record_set_id.replace(" ", "_").replace("/", "_")
        record_set_uri = URIRef(f"{dataset_uri}/recordset/{safe_id}")
        g.add((dataset_uri, DCAT.distribution, record_set_uri))
        g.add((record_set_uri, RDF.type, DCAT.Resource))
        g.add((record_set_uri, DCTERMS.title, Literal(record_set.get("name", ""))))
        g.add(
            (
                record_set_uri,
                DCTERMS.description,
                Literal(record_set.get("description", "")),
            )
        )

        # Handle fields within record sets
        for field in record_set.get("field", []):
            field_id = field.get("@id", "field")
            # Ensure valid URI
            safe_field_id = field_id.replace(" ", "_").replace("/", "_")
            field_uri = URIRef(f"{record_set_uri}/field/{safe_field_id}")
            g.add((record_set_uri, CR.field, field_uri))
            g.add((field_uri, RDF.type, CR.Field))
            g.add((field_uri, DCTERMS.title, Literal(field.get("name", ""))))
            g.add(
                (field_uri, DCTERMS.description, Literal(field.get("description", "")))
            )

            if "dataType" in field:
                g.add((field_uri, CR.dataType, Literal(field["dataType"])))
            if "repeated" in field:
                g.add(
                    (
                        field_uri,
                        CR.repeated,
                        Literal(field["repeated"], datatype=XSD.boolean),
                    )
                )

        # Handle data records within record sets
        if "data" in record_set:
            for i, data_record in enumerate(record_set["data"]):
                data_uri = URIRef(f"{record_set_uri}/data/{i}")
                g.add((record_set_uri, CR.data, data_uri))
                g.add((data_uri, RDF.type, CR.DataRecord))

                # Handle each field-value pair in the data record
                for field_name, field_value in data_record.items():
                    _ = field_name.replace(" ", "_").replace("/", "_")
                    g.add(
                        (
                            data_uri,
                            CR.fieldValue,
                            Literal(f"{field_name}:{field_value}"),
                        )
                    )
                    g.add((data_uri, CR.fieldName, Literal(field_name)))
                    g.add((data_uri, CR.fieldValue, Literal(str(field_value))))

    # Data Collection information
    if "dataCollection" in croissant_json:
        data_collection = croissant_json["dataCollection"]
        collection_uri = URIRef(f"{dataset_uri}/dataCollection")
        g.add((dataset_uri, CR.dataCollection, collection_uri))
        g.add((collection_uri, RDF.type, CR.DataCollection))
        g.add((collection_uri, DCTERMS.title, Literal(data_collection.get("name", ""))))
        g.add(
            (
                collection_uri,
                DCTERMS.description,
                Literal(data_collection.get("description", "")),
            )
        )

        # Handle sources
        for source in data_collection.get("source", []):
            source_name = source.get("name", "source")
            safe_source_name = source_name.replace(" ", "_").replace("/", "_")
            source_uri = URIRef(f"{collection_uri}/source/{safe_source_name}")
            g.add((collection_uri, CR.source, source_uri))
            g.add((source_uri, RDF.type, CR.Source))
            g.add((source_uri, FOAF.name, Literal(source.get("name", ""))))
            if "url" in source:
                g.add((source_uri, FOAF.homepage, URIRef(source["url"])))
            if "version" in source:
                g.add((source_uri, ADMS.version, Literal(source["version"])))
            if "description" in source:
                g.add((source_uri, DCTERMS.description, Literal(source["description"])))

    # Data Biases
    if "dataBiases" in croissant_json:
        data_biases = croissant_json["dataBiases"]
        biases_uri = URIRef(f"{dataset_uri}/dataBiases")
        g.add((dataset_uri, CR.dataBiases, biases_uri))
        g.add((biases_uri, RDF.type, CR.DataBiases))
        g.add((biases_uri, DCTERMS.title, Literal(data_biases.get("name", ""))))
        g.add(
            (
                biases_uri,
                DCTERMS.description,
                Literal(data_biases.get("description", "")),
            )
        )

    # Personal/Sensitive Information
    if "personalSensitiveInformation" in croissant_json:
        psi = croissant_json["personalSensitiveInformation"]
        psi_uri = URIRef(f"{dataset_uri}/personalSensitiveInformation")
        g.add((dataset_uri, CR.personalSensitiveInformation, psi_uri))
        g.add((psi_uri, RDF.type, CR.PersonalSensitiveInformation))
        g.add((psi_uri, DCTERMS.description, Literal(psi.get("description", ""))))

    # Examples
    if "examples" in croissant_json:
        examples_uri = URIRef(f"{dataset_uri}/examples")
        g.add((dataset_uri, CR.examples, examples_uri))
        g.add((examples_uri, RDF.type, CR.Examples))

        # Handle examples as JSON data
        examples_data = croissant_json["examples"]
        if isinstance(examples_data, dict):
            for key, value in examples_data.items():
                g.add((examples_uri, CR.exampleKey, Literal(key)))
                if isinstance(value, (str, int, float)):
                    g.add((examples_uri, CR.exampleValue, Literal(str(value))))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        g.add((examples_uri, CR.exampleItem, Literal(str(item))))

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
