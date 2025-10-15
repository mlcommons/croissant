import json
import re
import pytdml.io

def tdml_to_geocroissant(tdml_path, output_path):
    tdml = pytdml.io.read_from_json(tdml_path)

    # Build variableMeasured from classes and bands
    variable_measured = []
    if hasattr(tdml, "classes") and tdml.classes:
        variable_measured += [
            {"name": c.key, "description": c.value} for c in tdml.classes
        ]
    if hasattr(tdml, "bands") and tdml.bands:
        variable_measured += [
            {"name": b.description, "unitText": getattr(b, "units", None)} for b in tdml.bands
        ]

    # Build distribution from data (include both merged and mask tif)
    distribution = []
    for d in tdml.data:
        # Add merged image
        if d.data_url:
            distribution.append({
                "name": "image",
                "contentUrl": d.data_url[0],
                "encodingFormat": "image/tiff"
            })
        # Add mask image
        if d.labels and hasattr(d.labels[0], "image_url"):
            mask_url = d.labels[0].image_url[0]
            distribution.append({
                "name": "mask",
                "contentUrl": mask_url,
                "encodingFormat": d.labels[0].image_format[0] if hasattr(d.labels[0], "image_format") else "image/tiff"
            })

    # Build spatialCoverage as a Polygon from extent
    extent = tdml.extent
    spatial_coverage = {
        "geo": {
            "type": "Polygon",
            "coordinates": [[
                [extent[0], extent[1]],
                [extent[2], extent[1]],
                [extent[2], extent[3]],
                [extent[0], extent[3]],
                [extent[0], extent[1]]
            ]]
        }
    }

    # Sanitize the name for forbidden characters
    sanitized_name = re.sub(r'[^A-Za-z0-9_-]', '_', tdml.name)

    # Provided BibTeX citation
    citation = """@misc{ibm_nasa_geospatial_2023,
    author       = { IBM NASA Geospatial },
    title        = { hls_burn_scars (Revision f29f6c9) },
    year         = 2023,
    url          = { https://huggingface.co/datasets/ibm-nasa-geospatial/hls_burn_scars },
    doi          = { 10.57967/hf/0956 },
    publisher    = { Hugging Face }
}"""

    geocroissant = {
        "@context": {
            "@vocab": "https://mlcommons.org/croissant/1.0/",
            "geo": "https://mlcommons.org/croissant/geo/1.0/",
            "schema": "https://schema.org/",
            "name": "schema:name",
            "citation": "schema:citation",
            "datePublished": "schema:datePublished",
            "license": "schema:license",
            "version": "schema:version"
        },
        "@type": "schema:Dataset",
        "identifier": tdml.id,
        "name": sanitized_name,
        "description": tdml.description,
        "license": tdml.license,
        "creator": tdml.providers,
        "dateCreated": tdml.created_time,
        "dateModified": tdml.updated_time,
        "datePublished": getattr(tdml, "created_time", ""),
        "citation": citation,
        "version": getattr(tdml, "version", ""),
        "variableMeasured": variable_measured,
        "distribution": distribution,
        "spatialCoverage": spatial_coverage
    }

    with open(output_path, "w") as f:
        json.dump(geocroissant, f, indent=2)
    print(f"GeoCroissant file written to {output_path}")

# Example usage:
tdml_to_geocroissant("hls_burn_scars_tdml.json", "hls_burn_scars_croissant.json")
