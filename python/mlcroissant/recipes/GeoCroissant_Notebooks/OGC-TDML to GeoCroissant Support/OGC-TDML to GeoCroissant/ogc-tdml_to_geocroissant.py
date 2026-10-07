"""OGC TDML to GeoCroissant Conversion Module.

This module provides functionality for converting OGC Training Data Markup Language (TDML)
documents to GeoCroissant format. It handles the parsing and transformation of TDML
metadata, ensuring compatibility with the GeoCroissant framework.
"""

import json
import re

import pytdml.io


def safe_str(value, default="Unknown"):
    """Return string if value is not None/empty, else default."""
    if value is None:
        return default
    return str(value)


def tdml_to_geocroissant(tdml_path, output_path):
    """Convert OGC-TDML format to GeoCroissant format.

    Args:
        tdml_path: Path to the input TDML JSON file.
        output_path: Path where the converted GeoCroissant file will be saved.
    """
    tdml = pytdml.io.read_from_json(tdml_path)

    # Build variableMeasured from classes and bands
    variable_measured = []
    if hasattr(tdml, "classes") and tdml.classes:
        variable_measured += [
            {
                "name": safe_str(getattr(c, "key", None)),
                "description": safe_str(
                    getattr(c, "value", None),
                    safe_str(getattr(c, "key", None), "Unknown class"),
                ),
            }
            for c in tdml.classes
            if c is not None
        ]
    if hasattr(tdml, "bands") and tdml.bands:
        # Handle bands structure from OGC-TDML
        for b in tdml.bands:
            if hasattr(b, "name") and b.name:
                first_name = b.name[0] if len(b.name) > 0 else "Unknown Band"
                band_name = safe_str(
                    getattr(first_name, "code", first_name), "Unknown Band"
                )
                band_info = {"name": band_name}
                units = getattr(b, "units", None)
                if units is not None:
                    band_info["unitText"] = safe_str(units)
                # Ensure description is always present
                band_info["description"] = safe_str(
                    getattr(b, "description", None), f"Band: {band_name}"
                )
                variable_measured.append(band_info)

    # Build distribution using proper FileObject/FileSet structure
    distribution = []

    # Create a FileObject for the main data directory
    distribution.append({
        "@type": "cr:FileObject",
        "@id": "data_repo",
        "name": "data_repo",
        "description": "Directory containing the dataset files",
        "contentUrl": (
            "https://huggingface.co/datasets/harshinde/hls_burn_scars"
        ),  # Use actual URL from the data
        "encodingFormat": "local_directory",
        "md5": "placeholder_hash_for_directory",
    })

    # Create single FileSet for all TIFF files
    distribution.append({
        "@type": "cr:FileSet",
        "@id": "tiff-files-for-config-hls_burn_scars",
        "name": "tiff-files-for-config-hls_burn_scars",
        "description": "Local TIFF files organized in training/validation splits.",
        "containedIn": {"@id": "data_repo"},
        "encodingFormat": "image/tif",
        "includes": "**/*.ti",
    })

    # Build spatialCoverage - OGC-TDML doesn't have extent, so use description

    # Sanitize the name for forbidden characters
    sanitized_name = re.sub(
        r"[^A-Za-z0-9_-]", "_", safe_str(getattr(tdml, "name", "Unknown_Dataset"))
    )

    # Build recordSet with proper field structure and data
    record_data = []
    if hasattr(tdml, "data") and tdml.data:
        for i, d in enumerate(tdml.data):
            if d is None:
                continue
            record = {}
            if hasattr(d, "data_url") and d.data_url:
                first_url = d.data_url[0] if len(d.data_url) > 0 else None
                if first_url:
                    record["{sanitized_name}/image"] = safe_str(first_url)
            if hasattr(d, "labels") and d.labels:
                for label in d.labels:
                    if hasattr(label, "image_url") and label.image_url:
                        first_label_url = (
                            label.image_url[0] if len(label.image_url) > 0 else None
                        )
                        if first_label_url:
                            record[f"{sanitized_name}/mask"] = safe_str(first_label_url)
                            break
            if record:  # Only add if we have data
                record_data.append(record)

    record_set = {
        "@type": "cr:RecordSet",
        "@id": "{sanitized_name}",
        "name": "{sanitized_name}",
        "description": (
            "HLS Burn Scars dataset with satellite imagery and burn scar mask"
            " annotations."
        ),
        "field": [
            {
                "@type": "cr:Field",
                "@id": "{sanitized_name}/image",
                "name": "{sanitized_name}/image",
                "description": (
                    "Satellite imagery from Harmonized Landsat and Sentinel-2 sensors"
                    " with 6 bands converted to reflectance."
                ),
                "dataType": "sc:ImageObject",
                "source": {
                    "fileSet": {"@id": "tiff-files-for-config-hls_burn_scars"},
                    "extract": {"fileProperty": "fullpath"},
                    "transform": {"regex": ".*_merged\\.tif$"},
                },
                "geocr:dataShape": [512, 512, 6],
                "geocr:bandConfiguration": {
                    "totalBands": 6,
                    "band1": {"name": "Blue", "hlsBand": "B02", "wavelength": "490nm"},
                    "band2": {"name": "Green", "hlsBand": "B03", "wavelength": "560nm"},
                    "band3": {"name": "Red", "hlsBand": "B04", "wavelength": "665nm"},
                    "band4": {"name": "NIR", "hlsBand": "B8A", "wavelength": "865nm"},
                    "band5": {"name": "SW1", "hlsBand": "B11", "wavelength": "1610nm"},
                    "band6": {"name": "SW2", "hlsBand": "B12", "wavelength": "2190nm"},
                },
            },
            {
                "@type": "cr:Field",
                "@id": "{sanitized_name}/mask",
                "name": "{sanitized_name}/mask",
                "description": (
                    "Burn scar mask annotations with values: 1=Burn scar, 0=Not burned,"
                    " -1=Missing data."
                ),
                "dataType": "sc:ImageObject",
                "source": {
                    "fileSet": {"@id": "tiff-files-for-config-hls_burn_scars"},
                    "extract": {"fileProperty": "fullpath"},
                    "transform": {"regex": ".*\\.mask\\.tif$"},
                },
                "geocr:dataShape": [512, 512, 1],
                "geocr:classValues": {
                    "0": "NotBurned",
                    "1": "BurnScar",
                    "-1": "NoData",
                },
            },
        ],
        "data": record_data,
    }

    # Build proper Croissant structure
    geocroissant = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "citeAs": "cr:citeAs",
            "column": "cr:column",
            "conformsTo": "dct:conformsTo",
            "cr": "http://mlcommons.org/croissant/",
            "geocr": "http://mlcommons.org/croissant/geocr/",
            "rai": "http://mlcommons.org/croissant/RAI/",
            "dct": "http://purl.org/dc/terms/",
            "sc": "https://schema.org/",
            "data": {"@id": "cr:data", "@type": "@json"},
            "examples": {"@id": "cr:examples", "@type": "@json"},
            "dataBiases": "cr:dataBiases",
            "dataCollection": "cr:dataCollection",
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "extract": "cr:extract",
            "field": "cr:field",
            "fileProperty": "cr:fileProperty",
            "fileObject": "cr:fileObject",
            "fileSet": "cr:fileSet",
            "format": "cr:format",
            "includes": "cr:includes",
            "isLiveDataset": "cr:isLiveDataset",
            "jsonPath": "cr:jsonPath",
            "key": "cr:key",
            "md5": "cr:md5",
            "parentField": "cr:parentField",
            "path": "cr:path",
            "personalSensitiveInformation": "cr:personalSensitiveInformation",
            "recordSet": "cr:recordSet",
            "references": "cr:references",
            "regex": "cr:regex",
            "repeated": "cr:repeated",
            "replace": "cr:replace",
            "samplingRate": "cr:samplingRate",
            "separator": "cr:separator",
            "source": "cr:source",
            "subField": "cr:subField",
            "transform": "cr:transform",
        },
        "@type": "sc:Dataset",
        "name": sanitized_name,
        "description": safe_str(
            getattr(tdml, "description", "Converted from OGC-TDML format")
        ),
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "version": safe_str(getattr(tdml, "version", "1.0.0")),
        "creator": {
            "@type": "Organization",
            "name": safe_str(
                (
                    getattr(tdml, "providers", ["Unknown Provider"])[0]
                    if hasattr(tdml, "providers") and tdml.providers
                    else None
                ),
                "Unknown Provider",
            ),
        },
        "license": safe_str(getattr(tdml, "license", None), "Unknown License"),
        "dateCreated": safe_str(getattr(tdml, "createdTime", "2025-01-17")),
        "dateModified": safe_str(getattr(tdml, "updatedTime", "2025-01-17")),
        "datePublished": safe_str(getattr(tdml, "createdTime", "2025-01-17")),
        "citeAs": (
            "@dataset{{{sanitized_name}, title={{{safe_str(getattr(tdml, 'description',"
            " 'Converted from OGC-TDML format'))}}}, author={{{safe_str(getattr(tdml,"
            " 'providers', ['Unknown Provider'])[0] if hasattr(tdml, 'providers') and"
            " tdml.providers else None, 'Unknown Provider')}}},"
            " year={{{safe_str(getattr(tdml, 'createdTime', '2025-01-17'))[:4]}}},"
            " url={{https://huggingface.co/datasets/harshinde/hls_burn_scars}}}}"
        ),
        "keywords": [
            "geospatial",
            "machine learning",
            "remote sensing",
            "burn scar detection",
            "semantic segmentation",
            "Landsat",
            "Sentinel-2",
            "HLS",
        ],
        "url": "https://huggingface.co/datasets/harshinde/hls_burn_scars",
        "distribution": distribution,
        "recordSet": [record_set],
        "geocr:BoundingBox": [-125.0, 24.0, -66.0, 49.0],  # Contiguous US bounds
        "geocr:temporalExtent": {
            "startDate": "2018-01-01T00:00:00Z",
            "endDate": "2021-12-31T23:59:59Z",
        },
        "geocr:spatialResolution": "30m",
        "geocr:coordinateReferenceSystem": "EPSG:4326",
        "geocr:mlTask": {
            "@type": "geocr:SemanticSegmentation",
            "taskType": "multi_class_classification",
            "evaluationMetric": "F1_score",
            "classes": ["NotBurned", "BurnScar", "NoData"],
            "applicationDomain": "environmental_monitoring",
        },
    }

    # Add variableMeasured if available
    if variable_measured:
        geocroissant["variableMeasured"] = variable_measured

    with open(output_path, "w") as f:
        json.dump(geocroissant, f, indent=2)
    print("GeoCroissant file written to {output_path}")


# Example usage:
tdml_to_geocroissant("ogc-tdml.json", "ogc_croissant.json")
