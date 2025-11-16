"""GeoCroissant Time-Series Data Conversion Utilities.

This module provides utility functions for handling time-series data in GeoCroissant format.
It includes tools for name sanitization, version management, and other conversion operations
necessary for working with time-series data within the GeoCroissant framework.
"""

import json
import re
from datetime import datetime


def sanitize_name(name):
    """Sanitize a name to be valid for use in GeoCroissant.

    Args:
        name: Input string to sanitize.

    Returns:
        str: Sanitized name containing only alphanumeric chars, underscores and hyphens.
    """
    return re.sub(r"[^a-zA-Z0-9_\-]", "-", name)


def ensure_semver(version):
    """Ensure a version string follows semantic versioning format.

    Args:
        version: Input version string to process.

    Returns:
        str: Valid semantic version with major.minor.patch format.
            Returns "1.0.0" if input is empty.
            Strips leading 'v' if present.
            Adds ".0" if only major.minor is provided.
    """
    if not version:
        return "1.0.0"
    if version.startswith("v"):
        version = version[1:]
    parts = version.split(".")
    if len(parts) == 2:
        parts.append("0")
    return ".".join(parts[:3])


def get_bbox_union(bboxes):
    """Calculate the union of multiple bounding boxes.

    Args:
        bboxes: List of bounding boxes where each box is [minx, miny, maxx, maxy].

    Returns:
        list: Combined bounding box [minx, miny, maxx, maxy] that encompasses all input boxes.
    """
    # Union of all bounding boxes
    minx = min(b[0] for b in bboxes)
    miny = min(b[1] for b in bboxes)
    maxx = max(b[2] for b in bboxes)
    maxy = max(b[3] for b in bboxes)
    return [minx, miny, maxx, maxy]


def get_time_range(times):
    """Get the earliest and latest times from a list of ISO8601 timestamps.

    Args:
        times: List of ISO8601 timestamp strings.

    Returns:
        tuple: (earliest, latest) timestamps, or (None, None) if no valid times.
    """
    # Get min/max ISO8601 times
    times = [t for t in times if t]
    if not times:
        return None, None
    times = sorted(times)
    return times[0], times[-1]


def stac_itemcollection_to_geocroissant(stac_dict):
    """Convert a STAC ItemCollection to GeoCroissant metadata format.

    Args:
        stac_dict: Dictionary containing a STAC ItemCollection.

    Returns:
        dict: GeoCroissant metadata dictionary.

    Raises:
        ValueError: If no features are found in the STAC ItemCollection.
    """
    features = stac_dict.get("features", [])
    if not features:
        raise ValueError("No features found in STAC ItemCollection.")

    # Aggregate spatial and temporal extents
    bboxes = []
    start_times = []
    end_times = []
    for feat in features:
        bbox = feat.get("bbox")
        if bbox:
            bboxes.append(bbox)
        props = feat.get("properties", {})
        # Try both 'datetime' and 'start_datetime'/'end_datetime'
        if "start_datetime" in props and "end_datetime" in props:
            start_times.append(props["start_datetime"])
            end_times.append(props["end_datetime"])
        elif "datetime" in props:
            start_times.append(props["datetime"])
            end_times.append(props["datetime"])

    # Use the first feature for some metadata
    first = features[0]
    dataset_id = stac_dict.get("id", first.get("collection", "UnnamedDataset"))
    name = sanitize_name(stac_dict.get("title", dataset_id))
    version = ensure_semver(stac_dict.get("version", "1.0.0"))

    croissant = {
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
        "@id": dataset_id,
        "name": name,
        "description": stac_dict.get("description", ""),
        "version": version,
        "license": stac_dict.get("license", "CC-BY-4.0"),
        "conformsTo": "http://mlcommons.org/croissant/1.0",
    }

    # Add numberReturned if present
    if "numberReturned" in stac_dict:
        croissant["numberReturned"] = stac_dict["numberReturned"]

    # Links and references
    references = []
    for link in stac_dict.get("links", []):
        rel = link.get("rel")
        href = link.get("href")
        if not href or rel == "self":
            continue
        references.append({
            "@type": "CreativeWork",
            "url": href,
            "name": rel,
            "encodingFormat": link.get("type", "application/json"),
        })
    if references:
        croissant["references"] = references

    # Spatial and temporal extent
    if bboxes:
        croissant["geocr:BoundingBox"] = get_bbox_union(bboxes)
    if start_times and end_times:
        start, end = get_time_range(start_times + end_times)
        croissant["geocr:temporalExtent"] = {"startDate": start, "endDate": end}
        croissant["datePublished"] = start
    else:
        croissant["datePublished"] = datetime.utcnow().isoformat() + "Z"

    # Add geospatial metadata
    croissant["geocr:spatialResolution"] = "Unknown"
    croissant["geocr:coordinateReferenceSystem"] = "EPSG:4326"

    # Distribution: all assets from all features
    croissant["distribution"] = []
    for feat in features:
        assets = feat.get("assets", {})
        for key, asset in assets.items():
            file_object = {
                "@type": "cr:FileObject",
                "@id": f"{feat['id']}/{key}",
                "name": f"{feat['id']}/{key}",
                "description": asset.get("description", asset.get("title", "")),
                "contentUrl": asset.get("href"),
                "encodingFormat": asset.get("type", "application/octet-stream"),
                "md5": "placeholder_hash",
            }
            croissant["distribution"].append(file_object)

    # Create recordSet with proper structure
    croissant["recordSet"] = [
        {
            "@type": "cr:RecordSet",
            "@id": f"{dataset_id}_items",
            "name": f"{dataset_id}_items",
            "description": f"STAC items from {dataset_id} collection",
            "field": [
                {
                    "@type": "cr:Field",
                    "@id": f"{dataset_id}_items/id",
                    "name": "id",
                    "description": "STAC item identifier",
                    "dataType": "sc:Text",
                },
                {
                    "@type": "cr:Field",
                    "@id": f"{dataset_id}_items/datetime",
                    "name": "datetime",
                    "description": "Item datetime",
                    "dataType": "sc:DateTime",
                },
                {
                    "@type": "cr:Field",
                    "@id": f"{dataset_id}_items/bbox",
                    "name": "bbox",
                    "description": "Bounding box coordinates",
                    "dataType": "sc:Text",
                },
                {
                    "@type": "cr:Field",
                    "@id": f"{dataset_id}_items/assets",
                    "name": "assets",
                    "description": "Available assets",
                    "dataType": "sc:Text",
                },
            ],
            "data": [],
        }
    ]

    # Populate recordSet data
    for feat in features:
        props = feat.get("properties", {})
        record_data = {
            f"{dataset_id}_items/id": feat.get("id"),
            f"{dataset_id}_items/datetime": props.get("datetime"),
            f"{dataset_id}_items/bbox": feat.get("bbox"),
            f"{dataset_id}_items/assets": list(feat.get("assets", {}).keys()),
        }
        croissant["recordSet"][0]["data"].append(record_data)

    # Optionally, add stac_extensions, stac_version, etc. at top level
    if "stac_extensions" in stac_dict:
        croissant["geocr:stac_extensions"] = stac_dict["stac_extensions"]
    if "stac_version" in stac_dict:
        croissant["geocr:stac_version"] = stac_dict["stac_version"]

    # Add citeAs if not present (recommended by Croissant)
    if "citeAs" not in croissant:
        croissant["citeAs"] = "Citation information not provided."

    # Report unmapped fields
    mapped_keys = {
        "type",
        "links",
        "features",
        "id",
        "title",
        "description",
        "license",
        "version",
        "stac_extensions",
        "stac_version",
        "numberReturned",
    }
    extra_fields = {k: v for k, v in stac_dict.items() if k not in mapped_keys}
    print("\n\033[1mUnmapped STAC Fields:\033[0m")
    if extra_fields:
        for k, v in extra_fields.items():
            print(f"- {k}: {type(v).__name__}")
    else:
        print("None ")

    return croissant


# === Main Runner ===
if __name__ == "__main__":
    # Load STAC ItemCollection JSON
    with open("stac.json") as f:
        stac_data = json.load(f)

    # Convert to GeoCroissant
    croissant_json = stac_itemcollection_to_geocroissant(stac_data)

    # Save GeoCroissant JSON-LD
    with open("croissant.json", "w") as f:
        json.dump(croissant_json, f, indent=2)

    print("\nGeoCroissant conversion complete. Output saved to 'croissant.json'")
