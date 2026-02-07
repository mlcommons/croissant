"""STAC to GeoCroissant Conversion Module.

This module provides functionality for converting SpatioTemporal Asset Catalog (STAC)
metadata to GeoCroissant format. It includes utilities for handling name sanitization,
version management, and metadata transformation between STAC and GeoCroissant schemas.
"""

from datetime import datetime
import json
import re


def sanitize_name(name):
    """Sanitize a name to be compatible with GeoCroissant requirements.

    Args:
        name: String to be sanitized.

    Returns:
        Sanitized string containing only alphanumeric characters, underscores and hyphens.
    """
    return re.sub(r"[^a-zA-Z0-9_\-]", "-", name)


def ensure_semver(version):
    """Ensure a version string follows semantic versioning format.

    Args:
        version: Input version string.

    Returns:
        String in semver format (MAJOR.MINOR.PATCH).
    """
    if not version:
        return "1.0.0"
    if version.startswith("v"):
        version = version[1:]
    parts = version.split(".")
    if len(parts) == 2:
        parts.append("0")
    return ".".join(parts[:3])


def stac_to_geocroissant(stac_dict):
    """Convert STAC metadata dictionary to GeoCroissant format.

    Args:
        stac_dict: Dictionary containing STAC metadata.

    Returns:
        Dictionary containing GeoCroissant-formatted metadata.
    """
    dataset_id = stac_dict.get("id")
    name = sanitize_name(stac_dict.get("title", dataset_id or "UnnamedDataset"))
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
        "name": name,
        "description": stac_dict.get("description", ""),
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "version": version,
        "license": stac_dict.get("license", "CC-BY-4.0"),
    }

    # Add @id if available
    if dataset_id:
        croissant["@id"] = dataset_id

    if "sci:citation" in stac_dict:
        croissant["citeAs"] = stac_dict["sci:citation"]

    if stac_dict.get("providers"):
        provider = stac_dict["providers"][0]
        croissant["creator"] = {
            "@type": "Organization",
            "name": provider.get("name", "Unknown"),
            "url": provider.get("url", ""),
        }

    # Add keywords from summaries and other metadata
    keywords = []
    if "summaries" in stac_dict:
        summaries = stac_dict["summaries"]
        for key in ["mission", "platform", "instruments"]:
            if key in summaries:
                if isinstance(summaries[key], list):
                    keywords.extend(summaries[key])
                else:
                    keywords.append(summaries[key])

    # Add some basic geospatial keywords
    keywords.extend(["remote sensing", "geospatial", "satellite data"])

    if keywords:
        croissant["keywords"] = list(set(keywords))  # Remove duplicates

    # Handle 'sel' URL
    for link in stac_dict.get("links", []):
        if link.get("rel") == "sel":
            croissant["url"] = link.get("hre")
            break

    # Handle other STAC references
    references = []
    for link in stac_dict.get("links", []):
        rel = link.get("rel")
        href = link.get("hre")
        if not href or rel == "sel":
            continue

        name_map = {
            "root": "STAC root catalog",
            "parent": "STAC parent catalog",
            "items": "STAC item list",
            "about": "GitHub Repository",
            "predecessor-version": "Previous version",
            "http://www.opengis.net/def/rel/ogc/1.0/queryables": "Queryables",
        }

        references.append({
            "@type": "CreativeWork",
            "url": href,
            "name": name_map.get(rel, rel),
            "encodingFormat": link.get("type", "application/json"),
        })

    if references:
        croissant["references"] = references

    # Spatial and temporal extent
    spatial = stac_dict.get("extent", {}).get("spatial", {}).get("bbox")
    if spatial:
        croissant["geocr:BoundingBox"] = spatial[0]

    temporal = stac_dict.get("extent", {}).get("temporal", {}).get("interval")
    if temporal and temporal[0]:
        start, end = temporal[0][0], temporal[0][1]
        croissant["geocr:temporalExtent"] = {"startDate": start, "endDate": end}
        croissant["datePublished"] = start
    else:
        croissant["datePublished"] = datetime.utcnow().isoformat() + "Z"

    # Add geospatial metadata
    if "summaries" in stac_dict:
        summaries = stac_dict["summaries"]
        if "gsd" in summaries:
            gsd = summaries["gsd"]
            if isinstance(gsd, dict):
                resolution = "{gsd.get('minimum', gsd.get('maximum', 30))}m"
            elif isinstance(gsd, list):
                resolution = "{gsd[0]}m"
            else:
                resolution = "{gsd}m"
            croissant["geocr:spatialResolution"] = resolution

    croissant["geocr:coordinateReferenceSystem"] = "EPSG:4326"

    # Distribution section with FileObjects and FileSets
    croissant["distribution"] = []

    # Add collection-level assets as FileObjects
    for key, asset in stac_dict.get("assets", {}).items():
        file_object = {
            "@type": "cr:FileObject",
            "@id": key,
            "name": key,
            "description": asset.get("description", asset.get("title", "")),
            "contentUrl": asset.get("hre"),
            "encodingFormat": asset.get("type", "application/octet-stream"),
        }

        # Handle checksums
        if "checksum:multihash" in asset:
            file_object["sha256"] = asset["checksum:multihash"]
        elif "file:checksum" in asset:
            file_object["sha256"] = asset["file:checksum"]
        else:
            file_object["sha256"] = "placeholder_hash"

        if "checksum:md5" in asset:
            file_object["md5"] = asset["checksum:md5"]
        else:
            file_object["md5"] = "placeholder_hash"

        croissant["distribution"].append(file_object)

    # Add item_assets as FileSet for data files
    if "item_assets" in stac_dict:
        # Create a FileSet for the item assets
        main_fileset = {
            "@type": "cr:FileSet",
            "@id": "{dataset_id}-files" if dataset_id else "dataset-files",
            "name": "{dataset_id} data files" if dataset_id else "Dataset data files",
            "description": "Collection of data files for this dataset",
            "encodingFormat": "application/octet-stream",
        }

        # If there are multiple item assets, we could include them all
        # For now, we'll create a generic pattern
        if stac_dict["item_assets"]:
            first_asset = list(stac_dict["item_assets"].values())[0]
            main_fileset["encodingFormat"] = first_asset.get(
                "type", "application/octet-stream"
            )
            main_fileset["includes"] = "**/*"  # Generic pattern

        croissant["distribution"].append(main_fileset)

    # Add basic recordSet structure for data access
    if "item_assets" in stac_dict and stac_dict["item_assets"]:
        croissant["recordSet"] = []

        # Create a basic recordSet for data splits/files
        record_set = {
            "@type": "cr:RecordSet",
            "@id": "{dataset_id}_records" if dataset_id else "dataset_records",
            "name": (
                "{dataset_id} data records" if dataset_id else "Dataset data records"
            ),
            "description": "Data records for this dataset",
            "field": [],
        }

        # Add fields for each item asset
        for asset_key, asset_info in stac_dict["item_assets"].items():
            # Determine proper dataType based on asset type
            asset_type = asset_info.get("type", "")
            if "image" in asset_type or "tif" in asset_type:
                data_type = "sc:ImageObject"
            elif "csv" in asset_type or "text" in asset_type:
                data_type = "sc:Text"
            else:
                data_type = "sc:Text"  # Default fallback

            field = {
                "@type": "cr:Field",
                "@id": "data/{asset_key}",
                "name": "data/{asset_key}",
                "description": asset_info.get(
                    "description", asset_info.get("title", "{asset_key} data")
                ),
                "dataType": data_type,
                "source": {
                    "fileSet": {
                        "@id": "{dataset_id}-files" if dataset_id else "dataset-files"
                    },
                    "extract": {"fileProperty": "fullpath"},
                    "transform": {"regex": ".*{asset_key}.*"},
                },
            }

            # Add geospatial information if available
            if "bands" in asset_info:
                bands = asset_info["bands"]
                if isinstance(bands, list) and len(bands) > 0:
                    if isinstance(bands[0], dict) and "data_type" in bands[0]:
                        field["geocr:dataType"] = bands[0]["data_type"]

            record_set["field"].append(field)

        croissant["recordSet"].append(record_set)

    if "renders" in stac_dict:
        croissant["geocr:visualizations"] = stac_dict["renders"]

    if "summaries" in stac_dict:
        croissant["geocr:summaries"] = stac_dict["summaries"]

    if "stac_extensions" in stac_dict:
        croissant["geocr:stac_extensions"] = stac_dict["stac_extensions"]
    if "stac_version" in stac_dict:
        croissant["geocr:stac_version"] = stac_dict["stac_version"]

    if "deprecated" in stac_dict:
        croissant["isLiveDataset"] = not stac_dict["deprecated"]

    # Report unmapped fields
    mapped_keys = {
        "id",
        "type",
        "links",
        "title",
        "assets",
        "extent",
        "license",
        "version",
        "providers",
        "description",
        "sci:citation",
        "renders",
        "summaries",
        "stac_extensions",
        "stac_version",
        "deprecated",
        "item_assets",
    }
    extra_fields = {k: v for k, v in stac_dict.items() if k not in mapped_keys}
    print("\n\033[1mUnmapped STAC Fields:\033[0m")
    if extra_fields:
        for k, v in extra_fields.items():
            print("- {k}: {type(v).__name__}")
    else:
        print("None ")

    return croissant


# === Main Runner ===
if __name__ == "__main__":
    # Load STAC Collection JSON
    with open("stac.json") as f:
        stac_data = json.load(f)

    # Convert to GeoCroissant
    croissant_json = stac_to_geocroissant(stac_data)

    # Save GeoCroissant JSON-LD
    with open("croissant.json", "w") as f:
        json.dump(croissant_json, f, indent=2)

    print("\nGeoCroissant conversion complete. Output saved to 'croissant.json'")
