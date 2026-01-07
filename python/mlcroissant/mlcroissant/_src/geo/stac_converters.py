"""STAC to GeoCroissant Conversion Module.

This module provides functionality for converting SpatioTemporal Asset Catalog (STAC)
metadata to GeoCroissant format. It includes utilities for handling name sanitization,
version management, and metadata transformation between STAC and GeoCroissant schemas.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def _check_dependencies() -> None:
    """Check if required dependencies are installed."""
    if not REQUESTS_AVAILABLE:
        raise ImportError(
            "Requests dependency not found. Install with: pip install requests"
        )


def sanitize_name(name: str) -> str:
    """Sanitize a name to be compatible with GeoCroissant requirements.

    Args:
        name: String to be sanitized.

    Returns:
        Sanitized string containing only alphanumeric characters, underscores and hyphens.
    """
    if not name:
        return "UnnamedDataset"

    # Replace special characters with dash
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "-", str(name))
    # Collapse multiple dashes into one
    sanitized = re.sub(r"-+", "-", sanitized)
    # Strip leading/trailing dashes and spaces
    sanitized = sanitized.strip("- ")

    # If sanitization resulted in empty string, return default
    if not sanitized:
        return "UnnamedDataset"

    return sanitized


def ensure_semver(version: Optional[Union[str, int, float]]) -> str:
    """Ensure a version string follows semantic versioning format.

    Args:
        version: Input version string, number, or None.

    Returns:
        String in semver format (MAJOR.MINOR.PATCH).
    """
    if version is None or version == "":
        return "1.0.0"

    # Convert to string if it's a number
    version_str = str(version)

    if version_str.startswith("v"):
        version_str = version_str[1:]
    parts = version_str.split(".")

    # Ensure we have at least 3 parts
    while len(parts) < 3:
        parts.append("0")

    return ".".join(parts[:3])


def extract_spatial_extent(stac_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract spatial extent information from STAC metadata."""
    spatial = stac_dict.get("extent", {}).get("spatial", {}).get("bbox")
    if spatial and spatial[0]:
        return {"bbox": spatial[0]}
    return None


def extract_temporal_extent(stac_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract temporal extent information from STAC metadata."""
    temporal = stac_dict.get("extent", {}).get("temporal", {}).get("interval")
    if temporal and temporal[0]:
        start, end = temporal[0][0], temporal[0][1]
        return {"start": start, "end": end}
    return None


def extract_provider_info(stac_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract provider information from STAC metadata."""
    providers = stac_dict.get("providers", [])
    if providers:
        provider = providers[0]
        return {
            "@type": "Organization",
            "name": provider.get("name", "Unknown"),
            "url": provider.get("url", ""),
        }
    return None


def extract_keywords(stac_dict: Dict[str, Any]) -> List[str]:
    """Extract keywords from STAC metadata."""
    keywords = ["remote sensing", "geospatial", "satellite data"]

    # Add keywords from summaries
    if "summaries" in stac_dict:
        summaries = stac_dict["summaries"]
        for key in ["mission", "platform", "instruments"]:
            if key in summaries:
                if isinstance(summaries[key], list):
                    keywords.extend(summaries[key])
                else:
                    keywords.append(summaries[key])

    return list(set(keywords))  # Remove duplicates


def extract_references(stac_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract references from STAC links."""
    references = []
    for link in stac_dict.get("links", []):
        rel = link.get("rel")
        href = link.get("href")
        if not href or rel == "self":
            continue

        name_map = {
            "root": "STAC root catalog",
            "parent": "STAC parent catalog",
            "items": "STAC item list",
            "about": "GitHub Repository",
            "predecessor-version": "Previous version",
            "http://www.opengis.net/def/rel/ogc/1.0/queryables": "Queryables",
        }

        references.append(
            {
                "@type": "CreativeWork",
                "url": href,
                "name": name_map.get(rel, rel),
                "encodingFormat": link.get("type", "application/json"),
            }
        )

    return references


def extract_citation(stac_dict: Dict[str, Any]) -> Optional[str]:
    """Extract citation information from STAC metadata."""
    if "sci:citation" in stac_dict:
        return stac_dict["sci:citation"]

    # Fallback to generating a citation
    title = stac_dict.get("title", stac_dict.get("id", "STAC Dataset"))
    providers = stac_dict.get("providers", [])
    provider_name = (
        providers[0].get("name", "Unknown Provider")
        if providers
        else "Unknown Provider"
    )

    return f"{title}, {provider_name}"


def determine_encoding_format(url: str, asset_type: str) -> str:
    """Determine the encoding format based on URL and asset type."""
    if url.endswith(".tif") or url.endswith(".tiff"):
        return "image/tiff"
    elif url.endswith(".jpg") or url.endswith(".jpeg"):
        return "image/jpeg"
    elif url.endswith(".json"):
        return "application/json"
    elif url.endswith(".xml"):
        return "application/xml"
    elif url.endswith(".hdf") or url.endswith(".h5"):
        return "application/x-hdf"
    elif url.endswith(".nc"):
        return "application/x-netcdf"
    elif url.endswith(".zip"):
        return "application/zip"
    elif "image" in asset_type:
        return "image/tiff"  # Default for image assets
    elif "json" in asset_type:
        return "application/json"
    else:
        return "application/octet-stream"


def detect_stac_type(stac_dict: Dict[str, Any]) -> str:
    """Detect the type of STAC object."""
    stac_type = stac_dict.get("type", "").lower()

    if stac_type == "collection":
        return "collection"
    elif stac_type == "feature":
        return "item"
    elif stac_type == "featurecollection":
        return "featurecollection"
    elif stac_type == "catalog":
        return "catalog"
    else:
        # Try to infer from structure
        if "item_assets" in stac_dict or "extent" in stac_dict:
            return "collection"
        elif "features" in stac_dict:
            return "featurecollection"
        elif "assets" in stac_dict and "geometry" in stac_dict:
            return "item"
        else:
            return "unknown"


def extract_item_spatial_extent(item_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract spatial extent from a STAC Item."""
    bbox = item_dict.get("bbox")
    if bbox:
        return {"bbox": bbox}
    return None


def extract_item_temporal_extent(item_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract temporal extent from a STAC Item."""
    properties = item_dict.get("properties", {})
    start_time = properties.get("datetime") or properties.get("start_datetime")
    end_time = properties.get("end_datetime", start_time)

    if start_time:
        return {"start": start_time, "end": end_time}
    return None


def extract_featurecollection_extent(fc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract combined extent from a FeatureCollection."""
    features = fc_dict.get("features", [])

    if not features:
        return {"spatial": None, "temporal": None}

    # Calculate combined bounding box
    bboxes = [f.get("bbox", []) for f in features if f.get("bbox")]
    combined_bbox = None
    if bboxes:
        min_x = min(bbox[0] for bbox in bboxes)
        min_y = min(bbox[1] for bbox in bboxes)
        max_x = max(bbox[2] for bbox in bboxes)
        max_y = max(bbox[3] for bbox in bboxes)
        combined_bbox = [min_x, min_y, max_x, max_y]

    # Calculate combined temporal extent
    datetimes = []
    for f in features:
        props = f.get("properties", {})
        if props.get("datetime"):
            datetimes.append(props["datetime"])
        if props.get("start_datetime"):
            datetimes.append(props["start_datetime"])
        if props.get("end_datetime"):
            datetimes.append(props["end_datetime"])

    combined_temporal = None
    if datetimes:
        combined_temporal = {"start": min(datetimes), "end": max(datetimes)}

    return {
        "spatial": {"bbox": combined_bbox} if combined_bbox else None,
        "temporal": combined_temporal,
    }


def extract_catalog_links(stac_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and categorize links from a STAC Catalog."""
    links = stac_dict.get("links", [])

    categorized_links: Dict[str, List[Dict[str, str]]] = {
        "collections": [],
        "items": [],
        "catalogs": [],
        "other": [],
    }

    for link in links:
        rel = link.get("rel", "")
        href = link.get("href", "")
        title = link.get("title", "")

        if rel == "child" and (
            "collection" in href.lower() or "collection" in title.lower()
        ):
            categorized_links["collections"].append(
                {
                    "href": href,
                    "title": title,
                    "type": link.get("type", "application/json"),
                }
            )
        elif rel == "item":
            categorized_links["items"].append(
                {
                    "href": href,
                    "title": title,
                    "type": link.get("type", "application/geo+json"),
                }
            )
        elif rel == "child":
            categorized_links["catalogs"].append(
                {
                    "href": href,
                    "title": title,
                    "type": link.get("type", "application/json"),
                }
            )
        elif rel not in ["self", "root", "parent"]:
            categorized_links["other"].append(
                {
                    "href": href,
                    "title": title,
                    "rel": rel,
                    "type": link.get("type", "application/json"),
                }
            )

    return categorized_links


def extract_catalog_extent(stac_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract or estimate extent from a STAC Catalog based on its structure."""
    # Catalogs don't always have explicit extents, but we can try to infer
    extent_info: Dict[str, Optional[Dict[str, Any]]] = {
        "spatial": None,
        "temporal": None,
    }

    # Check if catalog has explicit extent (some do)
    if "extent" in stac_dict:
        spatial_extent = extract_spatial_extent(stac_dict)
        temporal_extent = extract_temporal_extent(stac_dict)
        extent_info["spatial"] = spatial_extent
        extent_info["temporal"] = temporal_extent

    # If no explicit extent, we could potentially fetch from child collections
    # but for now, we'll leave it as None to avoid making additional HTTP requests

    return extent_info


def extract_band_info(stac_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract band information from STAC item_assets or direct assets."""
    bands = []
    band_config = {}

    # Check item_assets (Collection) or assets (Item)
    assets_to_check = stac_dict.get("item_assets", {}) or stac_dict.get("assets", {})

    # For FeatureCollection, check assets from all features
    if stac_dict.get("type", "").lower() == "featurecollection":
        features = stac_dict.get("features", [])
        for feature in features:
            feature_assets = feature.get("assets", {})
            assets_to_check.update(feature_assets)

    for asset_key, asset_info in assets_to_check.items():
        if "bands" in asset_info:
            bands_data = asset_info["bands"]
            if isinstance(bands_data, list):
                for i, band in enumerate(bands_data, 1):
                    band_id = f"band{i}"
                    bands.append(band_id)
                    band_config[band_id] = {
                        "identifier": band.get("name", f"B{i}"),
                        "description": band.get("description", f"Band {i}"),
                        "wavelength": band.get("center_wavelength"),
                    }

    return {"count": len(bands), "bands": bands, "configuration": band_config}


def stac_to_geocroissant(
    stac_input: Union[str, Path, Dict[str, Any]],
    output_path: Optional[Union[str, Path]] = None,
    enable_custom_properties: bool = True,
) -> Dict[str, Any]:
    """Convert STAC metadata to GeoCroissant format.

    Args:
        stac_input: STAC dictionary, path to STAC file, or URL to STAC endpoint
        output_path: Optional output file path (if provided, saves to file)
        enable_custom_properties: Whether to include geocr:CustomProperty1 and geocr:CustomProperty2.
                                 Enabled by default. Uses flat structures to prevent JSON-LD circular reference issues.

    Returns:
        Dictionary containing GeoCroissant-formatted metadata.

    Raises:
        ImportError: If required dependencies are not installed
        ValueError: If STAC data is invalid or URL fetch fails
        FileNotFoundError: If stac_input file path does not exist
    """
    _check_dependencies()

    # Input validation
    if not isinstance(stac_input, (str, Path, dict)):
        raise TypeError(f"Expected string, Path, or dict input, got {type(stac_input)}")

    # Handle file input or URL
    if isinstance(stac_input, (str, Path)):
        stac_input_str = str(stac_input)

        # Check if input is a URL
        if stac_input_str.startswith(("http://", "https://")):
            try:
                logger.info(f"Fetching STAC data from URL: {stac_input_str}")
                response = requests.get(stac_input_str, timeout=30)
                response.raise_for_status()
                stac_dict = response.json()
                logger.info("Successfully fetched STAC data from URL")
            except requests.RequestException as e:
                raise ValueError(
                    f"Failed to fetch STAC data from URL {stac_input_str}: {e}"
                )
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON response from URL {stac_input_str}: {e}"
                )
        else:
            # Handle local file path
            stac_path = Path(stac_input)
            if not stac_path.exists():
                raise FileNotFoundError(f"STAC file not found: {stac_path}")

            logger.info(f"Loading STAC file: {stac_path}")
            with open(stac_path, "r") as f:
                stac_dict = json.load(f)
    else:
        stac_dict = stac_input

    # Extract basic information
    dataset_id = stac_dict.get("id")
    title = stac_dict.get("title", dataset_id or "UnnamedDataset")
    name = sanitize_name(title)
    version = ensure_semver(stac_dict.get("version", "1.0.0"))

    # Detect STAC type and extract information accordingly
    stac_type = detect_stac_type(stac_dict)
    logger.info(f"Detected STAC type: {stac_type}")

    # Extract spatial and temporal information based on STAC type
    if stac_type == "collection":
        spatial_info = extract_spatial_extent(stac_dict)
        temporal_info = extract_temporal_extent(stac_dict)
    elif stac_type == "item":
        spatial_info = extract_item_spatial_extent(stac_dict)
        temporal_info = extract_item_temporal_extent(stac_dict)
    elif stac_type == "featurecollection":
        extent_info = extract_featurecollection_extent(stac_dict)
        spatial_info = extent_info["spatial"]
        temporal_info = extent_info["temporal"]
    elif stac_type == "catalog":
        extent_info = extract_catalog_extent(stac_dict)
        spatial_info = extent_info["spatial"]
        temporal_info = extent_info["temporal"]
    else:
        # Fallback to collection methods for unknown types
        spatial_info = extract_spatial_extent(stac_dict)
        temporal_info = extract_temporal_extent(stac_dict)
    provider_info = extract_provider_info(stac_dict)
    keywords = extract_keywords(stac_dict)
    references = extract_references(stac_dict)
    citation = extract_citation(stac_dict)
    band_info = extract_band_info(stac_dict)

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
        "alternateName": (
            [dataset_id, f"{name}-satellite-imagery"]
            if dataset_id
            else [f"{name}-satellite-imagery"]
        ),
        "description": stac_dict.get("description", "STAC satellite imagery dataset"),
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "version": version,
        "license": stac_dict.get("license", "CC-BY-4.0"),
        "keywords": keywords,
        "citeAs": citation,
    }

    # Add @id if available
    if dataset_id:
        croissant["@id"] = dataset_id

    # Add creator/provider information
    if provider_info:
        croissant["creator"] = provider_info

    # Add references
    if references:
        croissant["references"] = references

    # Handle 'self' URL
    for link in stac_dict.get("links", []):
        if link.get("rel") == "self":
            croissant["url"] = link.get("href")
            break

    # Add mandatory GeoCroissant core properties ONLY
    if spatial_info and spatial_info.get("bbox"):
        croissant["geocr:BoundingBox"] = spatial_info["bbox"]

    if temporal_info:
        croissant["geocr:temporalExtent"] = {
            "startDate": temporal_info.get("start"),
            "endDate": temporal_info.get("end"),
        }
        croissant["datePublished"] = temporal_info.get("start")
    else:
        croissant["datePublished"] = datetime.utcnow().isoformat() + "Z"

    # Add mandatory spatial resolution (core property)
    resolution_found = False
    if "summaries" in stac_dict:
        summaries = stac_dict["summaries"]
        if "gsd" in summaries:
            gsd = summaries["gsd"]
            if isinstance(gsd, dict):
                resolution = f"{gsd.get('minimum', gsd.get('maximum', 30))}m"
            elif isinstance(gsd, list):
                resolution = f"{gsd[0]}m"
            else:
                resolution = f"{gsd}m"
            croissant["geocr:spatialResolution"] = resolution
            resolution_found = True

    # For FeatureCollections, check individual feature assets for gsd
    if not resolution_found and stac_type == "featurecollection":
        features = stac_dict.get("features", [])
        for feature in features:
            for asset_key, asset_info in feature.get("assets", {}).items():
                if "gsd" in asset_info:
                    gsd = asset_info["gsd"]
                    croissant["geocr:spatialResolution"] = f"{gsd}m"
                    resolution_found = True
                    break
            if resolution_found:
                break

    # Default spatial resolution if not found
    if not resolution_found:
        croissant["geocr:spatialResolution"] = "30m"  # Default for satellite imagery

    # Add comprehensive GeoCroissant extensions via Custom Properties following NASA UMM pattern
    # All STAC-specific properties that are not core GeoCroissant properties are mapped here

    # STAC Custom Properties - Group 1: Spectral & Sensor Data (non-core properties from STAC)

    # Only add custom properties if enabled (disabled by default to prevent circular references)
    if enable_custom_properties:
        # CustomProperty1: Completely flat structure with only simple data types
        croissant["geocr:CustomProperty1"] = {
            "geocr:totalBands": band_info["count"],
            "geocr:coordinateReferenceSystem": "EPSG:4326",
            "geocr:resolutionValue": croissant.get("geocr:spatialResolution", "30m"),
            "geocr:hasBands": (
                len(band_info["bands"]) > 0 if band_info["bands"] else False
            ),
            "geocr:bandCount": len(band_info["bands"]) if band_info["bands"] else 0,
            "geocr:spectralBands": (
                ", ".join(band_info["bands"]) if band_info["bands"] else ""
            ),
            "geocr:bands": str(band_info["bands"]) if band_info["bands"] else "[]",
            "geocr:bandInfo": (
                str(band_info["configuration"]) if band_info["configuration"] else "{}"
            ),
            "geocr:visualizations": (
                str(stac_dict.get("renders", [])) if stac_dict.get("renders") else "[]"
            ),
        }

    # Distribution section with FileObjects and FileSets
    distributions = []

    # Handle assets based on STAC type
    if stac_type == "catalog":
        # For Catalogs, create distributions based on links to child resources
        catalog_links = extract_catalog_links(stac_dict)

        # Create file objects for collections
        for i, collection_link in enumerate(catalog_links["collections"]):
            file_object = {
                "@type": "cr:FileObject",
                "@id": f"collection_{i}",
                "name": collection_link.get("title", f"Collection {i}"),
                "description": f"STAC Collection: {collection_link.get('title', 'Unnamed Collection')}",
                "contentUrl": collection_link.get("href"),
                "encodingFormat": collection_link.get("type", "application/json"),
                "sha256": "d41d8cd98f00b204e9800998ecf8427e",  # Placeholder for remote resources
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
            }
            distributions.append(file_object)

        # Create file objects for sub-catalogs
        for i, catalog_link in enumerate(catalog_links["catalogs"]):
            file_object = {
                "@type": "cr:FileObject",
                "@id": f"subcatalog_{i}",
                "name": catalog_link.get("title", f"Sub-catalog {i}"),
                "description": f"STAC Sub-catalog: {catalog_link.get('title', 'Unnamed Catalog')}",
                "contentUrl": catalog_link.get("href"),
                "encodingFormat": catalog_link.get("type", "application/json"),
                "sha256": "d41d8cd98f00b204e9800998ecf8427e",
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
            }
            distributions.append(file_object)

    elif stac_type == "featurecollection":
        # For FeatureCollections, process individual feature assets
        features = stac_dict.get("features", [])
        for i, feature in enumerate(features):
            for key, asset in feature.get("assets", {}).items():
                # Determine proper encoding format
                encoding_format = determine_encoding_format(
                    asset.get("href", ""), asset.get("type", "")
                )

                file_object = {
                    "@type": "cr:FileObject",
                    "@id": f"feature_{i}_{key}",
                    "name": f"feature_{i}_{key}",
                    "description": asset.get(
                        "description", asset.get("title", f"Feature {i} {key} asset")
                    ),
                    "contentUrl": asset.get("href"),
                    "encodingFormat": encoding_format,
                    "sha256": asset.get(
                        "checksum:multihash",
                        asset.get("file:checksum", "d41d8cd98f00b204e9800998ecf8427e"),
                    ),
                    "md5": asset.get(
                        "checksum:md5", "d41d8cd98f00b204e9800998ecf8427e"
                    ),
                }
                distributions.append(file_object)
    else:
        # For Collections and Items, process direct assets
        for key, asset in stac_dict.get("assets", {}).items():
            # Determine proper encoding format
            encoding_format = determine_encoding_format(
                asset.get("href", ""), asset.get("type", "")
            )

            file_object = {
                "@type": "cr:FileObject",
                "@id": key,
                "name": key,
                "description": asset.get(
                    "description", asset.get("title", f"{key} asset")
                ),
                "contentUrl": asset.get("href"),
                "encodingFormat": encoding_format,
            }

            # Handle checksums
            if "checksum:multihash" in asset:
                file_object["sha256"] = asset["checksum:multihash"]
            elif "file:checksum" in asset:
                file_object["sha256"] = asset["file:checksum"]
            else:
                file_object[
                    "sha256"
                ] = "d41d8cd98f00b204e9800998ecf8427e"  # Standard placeholder

            if "checksum:md5" in asset:
                file_object["md5"] = asset["checksum:md5"]
            else:
                file_object[
                    "md5"
                ] = "d41d8cd98f00b204e9800998ecf8427e"  # Standard placeholder

            distributions.append(file_object)

    # Add item_assets as FileSet for data files
    if "item_assets" in stac_dict and stac_dict["item_assets"]:
        # Create a FileSet for the item assets
        main_fileset = {
            "@type": "cr:FileSet",
            "@id": f"{dataset_id}-files" if dataset_id else "dataset-files",
            "name": f"{dataset_id} data files" if dataset_id else "Dataset data files",
            "description": "Collection of data files for this dataset",
            "encodingFormat": "application/octet-stream",
        }

        # Set encoding format based on first asset
        first_asset = list(stac_dict["item_assets"].values())[0]
        main_fileset["encodingFormat"] = determine_encoding_format(
            "", first_asset.get("type", "")
        )
        main_fileset["includes"] = "**/*"  # Generic pattern

        distributions.append(main_fileset)

    # Add distributions to the main croissant object
    if distributions:
        croissant["distribution"] = distributions

    # Add recordSet structure based on STAC type
    record_sets: List[Dict[str, Any]] = []

    if (
        stac_type == "collection"
        and "item_assets" in stac_dict
        and stac_dict["item_assets"]
    ):
        # Create recordSet for Collection item_assets
        record_set = {
            "@type": "cr:RecordSet",
            "@id": f"{dataset_id}_records" if dataset_id else "dataset_records",
            "name": (
                f"{dataset_id} data records" if dataset_id else "Dataset data records"
            ),
            "description": "Data records for this dataset",
            "field": [],
        }

        # Add fields for each item asset
        for asset_key, asset_info in stac_dict["item_assets"].items():
            asset_type = asset_info.get("type", "")
            if "image" in asset_type or "tif" in asset_type:
                data_type = "sc:ImageObject"
            elif "csv" in asset_type or "text" in asset_type:
                data_type = "sc:Text"
            else:
                data_type = "sc:Text"

            field = {
                "@type": "cr:Field",
                "@id": f"data/{asset_key}",
                "name": f"data/{asset_key}",
                "description": asset_info.get(
                    "description", asset_info.get("title", f"{asset_key} data")
                ),
                "dataType": data_type,
                "source": {
                    "fileSet": {
                        "@id": f"{dataset_id}-files" if dataset_id else "dataset-files"
                    },
                    "extract": {"fileProperty": "fullpath"},
                    "transform": {"regex": f".*{asset_key}.*"},
                },
            }

            if "bands" in asset_info:
                bands = asset_info["bands"]
                if isinstance(bands, list) and len(bands) > 0:
                    if isinstance(bands[0], dict) and "data_type" in bands[0]:
                        field["geocr:dataType"] = bands[0]["data_type"]

            record_set["field"].append(field)
        record_sets.append(record_set)

    elif stac_type == "item" and distributions:
        # For STAC Items, create separate recordSets for each asset to avoid join requirements
        for dist in distributions:
            if dist.get("@type") == "cr:FileObject":
                asset_id = dist.get("@id", dist.get("name", "unknown"))
                asset_record_set = {
                    "@type": "cr:RecordSet",
                    "@id": f"{asset_id}_records",
                    "name": f"{asset_id} records",
                    "description": f"Records for {asset_id} asset",
                    "field": [
                        {
                            "@type": "cr:Field",
                            "@id": f"asset/{asset_id}",
                            "name": f"asset/{asset_id}",
                            "description": dist.get("description", f"{asset_id} asset"),
                            "dataType": (
                                "sc:ImageObject"
                                if "image" in dist.get("encodingFormat", "")
                                else "sc:Text"
                            ),
                            "source": {
                                "fileObject": {"@id": asset_id},
                                "extract": {"fileProperty": "content"},
                            },
                        }
                    ],
                }
                record_sets.append(asset_record_set)

    elif stac_type == "catalog":
        # For Catalogs, create recordSets describing the organizational structure
        catalog_links = extract_catalog_links(stac_dict)

        # Create separate recordSets for each collection to avoid join requirements
        for i, collection_link in enumerate(catalog_links["collections"]):
            collection_record_set = {
                "@type": "cr:RecordSet",
                "@id": f"collection_{i}_records",
                "name": f"Collection {i} Records",
                "description": f"Records for {collection_link.get('title', f'Collection {i}')}",
                "field": [
                    {
                        "@type": "cr:Field",
                        "@id": f"collection/collection_{i}",
                        "name": f"collection/collection_{i}",
                        "description": collection_link.get("title", f"Collection {i}"),
                        "dataType": "sc:Text",
                        "source": {
                            "fileObject": {"@id": f"collection_{i}"},
                            "extract": {"fileProperty": "content"},
                        },
                    }
                ],
            }
            record_sets.append(collection_record_set)

        # Create separate recordSets for each sub-catalog to avoid join requirements
        for i, catalog_link in enumerate(catalog_links["catalogs"]):
            subcatalog_record_set = {
                "@type": "cr:RecordSet",
                "@id": f"subcatalog_{i}_records",
                "name": f"Sub-catalog {i} Records",
                "description": f"Records for {catalog_link.get('title', f'Sub-catalog {i}')}",
                "field": [
                    {
                        "@type": "cr:Field",
                        "@id": f"subcatalog/subcatalog_{i}",
                        "name": f"subcatalog/subcatalog_{i}",
                        "description": catalog_link.get("title", f"Sub-catalog {i}"),
                        "dataType": "sc:Text",
                        "source": {
                            "fileObject": {"@id": f"subcatalog_{i}"},
                            "extract": {"fileProperty": "content"},
                        },
                    }
                ],
            }
            record_sets.append(subcatalog_record_set)

    elif stac_type == "featurecollection":
        # For FeatureCollections, create minimal recordSet structure pointing to first asset to avoid validation issues
        if distributions:
            # Use the first distribution as a source for a simple field
            first_dist = distributions[0]
            simple_record_set = {
                "@type": "cr:RecordSet",
                "@id": "features_collection",
                "name": "Features Collection",
                "description": "Collection of STAC features with their associated assets",
                "field": [
                    {
                        "@type": "cr:Field",
                        "@id": "features/data",
                        "name": "features/data",
                        "description": "Feature data files",
                        "dataType": (
                            "sc:ImageObject"
                            if "image" in first_dist.get("encodingFormat", "")
                            else "sc:Text"
                        ),
                        "source": {
                            "fileObject": {"@id": first_dist.get("@id")},
                            "extract": {"fileProperty": "content"},
                        },
                    }
                ],
            }
            record_sets.append(simple_record_set)

    # Add record sets if any exist
    if record_sets:
        croissant["recordSet"] = record_sets

    # STAC Custom Properties - Group 2: Metadata & Extensions (non-core properties from STAC)
    # These are STAC-specific properties mapped to GeoCroissant custom properties
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

    # Only add custom properties if enabled (disabled by default to prevent circular references)
    if enable_custom_properties:
        # Extract STAC version and extensions from FeatureCollection features if needed
        stac_version = stac_dict.get("stac_version", "1.0.0")
        stac_extensions = stac_dict.get("stac_extensions", [])
        total_assets = len(stac_dict.get("assets", {}))

        if stac_type == "featurecollection":
            features = stac_dict.get("features", [])
            if features:
                # Get stac_version from first feature that has it
                for feature in features:
                    if "stac_version" in feature:
                        stac_version = feature["stac_version"]
                        break
                # Collect unique stac_extensions from all features
                extensions_set = set()
                for feature in features:
                    feature_extensions = feature.get("stac_extensions", [])
                    extensions_set.update(feature_extensions)
                stac_extensions = list(extensions_set)
                # Count total assets across all features
                total_assets = sum(
                    len(feature.get("assets", {})) for feature in features
                )

        # CustomProperty2: Completely flat structure with only simple data types
        croissant["geocr:CustomProperty2"] = {
            "geocr:stac_version": stac_version,
            "geocr:totalAttributes": len(extra_fields),
            "geocr:deprecated": stac_dict.get("deprecated", False),
            "geocr:stacType": stac_type,
            "geocr:assetCount": total_assets,
            "geocr:linkCount": len(stac_dict.get("links", [])),
            "geocr:hasCollection": "collection" in stac_dict,
            "geocr:hasGeometry": "geometry" in stac_dict,
            "geocr:hasBbox": "bbox" in stac_dict,
            "geocr:hasProperties": "properties" in stac_dict
            and len(stac_dict.get("properties", {})) > 0,
            "geocr:stac_extensions": str(stac_extensions),
            "geocr:summaries": str(stac_dict.get("summaries", {})),
            "geocr:stacSpecificAttributes": str(extra_fields),
            "geocr:customProperties": "CustomProperty1,CustomProperty2",
        }

    if "deprecated" in stac_dict:
        croissant["isLiveDataset"] = not stac_dict["deprecated"]

    # Log unmapped fields for debugging
    logger.info("Unmapped STAC Fields:")
    if extra_fields:
        for k, v in extra_fields.items():
            logger.info(f"- {k}: {type(v).__name__}")
    else:
        logger.info("None")

    # Save to file if output_path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(croissant, f, indent=2)
        logger.info(f"GeoCroissant saved to: {output_path}")

    return croissant
