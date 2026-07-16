"""Module for handling CEDA (Centre for Environmental Data Analysis) data conversion and processing.

This module provides utilities for working with CEDA data, including functions for
determining asset types, processing CEDA-specific data formats, and managing CEDA data
resources in the context of the GeoCroissant framework.
"""

import json
from urllib.parse import urlparse

from ceda_datapoint import DataPointClient


def get_asset_type(asset):
    """Determine asset type from asset properties or file extension."""
    # Check if asset has type or media_type attributes
    if hasattr(asset, "type"):
        return asset.type
    if hasattr(asset, "media_type"):
        return asset.media_type

    # For CEDA BasicAsset objects, try to get the URL from different attributes
    url = None
    if hasattr(asset, "hre"):
        url = asset.href
    elif hasattr(asset, "url"):
        url = asset.url
    elif hasattr(asset, "contentUrl"):
        url = asset.contentUrl
    elif hasattr(asset, "content_url"):
        url = asset.content_url

    if url:
        path = urlparse(url).path.lower()
        if path.endswith(".json"):
            return "application/json"
        elif path.endswith((".nc", ".netcd", ".cd")):
            return "application/netcd"
        elif path.endswith(".zarr"):
            return "application/zarr"
        elif path.endswith((".ti", ".tif", ".geotif")):
            return "image/tif"
        else:
            return "application/octet-stream"

    # Default fallback
    return "application/octet-stream"


def stac_to_geocroissant(stac_item, file_hash=None, filename=None):
    """Convert a CEDA STAC item to valid GeoCroissant format, optionally adding hash and filename."""
    if hasattr(stac_item, "stac_attributes"):
        # Get basic STAC metadata
        stac_attrs = stac_item.stac_attributes
        bbox = stac_item.bbox
        geometry = stac_attrs.get("geometry", {})
        item_id = stac_item.id

        # Get rich CMIP6 metadata from attributes
        properties = stac_item.attributes if hasattr(stac_item, "attributes") else {}
        assets = stac_item.get_assets()
    else:
        properties = stac_item.get("properties", {})
        assets = stac_item.get("assets", {})
        bbox = stac_item.get("bbox", [])
        geometry = stac_item.get("geometry", {})
        item_id = stac_item.get("id", "unknown")

    variable_name = properties.get("cmip6:variable_long_name", "Unknown")
    variable_id = properties.get("cmip6:variable_id", "tas")
    variable_units = properties.get("cmip6:variable_units", "K")

    croissant_metadata = {
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
        "name": properties.get("title", item_id),
        "alternateName": [
            "CMIP6-{variable_id}",
            "{properties.get('cmip6:institution_id', 'Unknown')}-{variable_id}",
            "{properties.get('cmip6:experiment_id', 'Unknown')}-{variable_id}",
        ],
        "description": (
            "CMIP6 dataset for {variable_name} ({variable_id}) from"
            " {properties.get('cmip6:institution_id', 'Unknown')} model. This dataset"
            " contains {variable_name} data for the"
            " {properties.get('cmip6:experiment_title', 'Unknown experiment')}"
            " scenario."
        ),
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "version": "1.0.0",
        "creator": {
            "@type": "Organization",
            "name": properties.get("cmip6:institution_id", "Unknown Institution"),
            "url": "https://www.wcrp-climate.org/wgcm-cmip/wgcm-cmip6",
        },
        "url": "https://api.stac.ceda.ac.uk/collections/cmip6/items/{item_id}",
        "keywords": [
            "CMIP6",
            "climate modeling",
            variable_name.lower(),
            variable_id,
            properties.get("cmip6:activity_id", "").lower(),
            properties.get("cmip6:experiment_id", "").lower(),
            properties.get("cmip6:institution_id", "").lower(),
            "netcd",
            "geospatial",
            "climate data",
            "temperature",
            "atmospheric data",
            "model output",
        ],
        "citeAs": properties.get(
            "cmip6:citation_url",
            "https://api.stac.ceda.ac.uk/collections/cmip6/items/{item_id}",
        ),
        "datePublished": properties.get(
            "created", properties.get("updated", "2021-12-31")
        ),
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "geocr:BoundingBox": bbox,
        "geocr:temporalExtent": {
            "startDate": properties.get("start_datetime", ""),
            "endDate": properties.get("end_datetime", ""),
        },
        "distribution": [
            {
                "@type": "cr:FileObject",
                "@id": asset_key,
                "name": filename if filename else asset_key,
                "description": "{asset_key} asset for {item_id}",
                "contentUrl": (
                    download_url
                    if asset_key.startswith("data")
                    else "https://api.stac.ceda.ac.uk/collections/cmip6/items/{item_id}"
                ),
                "encodingFormat": (
                    "application/netcd"
                    if asset_key.startswith("data")
                    else "application/json"
                ),
                "md5": (
                    file_hash
                    if file_hash and asset_key.startswith("data")
                    else "placeholder_hash"
                ),
                "sha256": (
                    file_hash
                    if file_hash and asset_key.startswith("data")
                    else "placeholder_hash"
                ),
            }
            for asset_key, asset in assets.items()
        ] + [
            {
                "@type": "cr:FileSet",
                "@id": "data_files",
                "name": "data_files",
                "description": "NetCDF data files",
                "includes": "*.nc",
                "encodingFormat": "application/netcd",
            }
        ],
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "@id": "geospatial_metadata",
                "name": "geospatial_metadata",
                "description": "Geospatial metadata extracted from STAC",
                "field": [
                    {
                        "@type": "cr:Field",
                        "@id": "geospatial_metadata/bounding_box",
                        "name": "bounding_box",
                        "description": "Dataset bounding box",
                        "dataType": "sc:Text",
                        "data": bbox,
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "geospatial_metadata/geometry",
                        "name": "geometry",
                        "description": "Dataset geometry",
                        "dataType": "sc:Text",
                        "data": geometry,
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "geospatial_metadata/temporal_coverage",
                        "name": "temporal_coverage",
                        "description": "Temporal coverage",
                        "dataType": "sc:Text",
                        "data": (
                            "{properties.get('start_datetime',"
                            " '')}/{properties.get('end_datetime', '')}"
                        ),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                ],
            },
            {
                "@type": "cr:RecordSet",
                "@id": "cmip6_metadata",
                "name": "cmip6_metadata",
                "description": "CMIP6-specific metadata",
                "field": [
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/activity_id",
                        "name": "activity_id",
                        "description": "CMIP6 activity ID",
                        "dataType": "sc:Text",
                        "data": properties.get("cmip6:activity_id", ""),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/experiment_id",
                        "name": "experiment_id",
                        "description": "CMIP6 experiment ID",
                        "dataType": "sc:Text",
                        "data": properties.get("cmip6:experiment_id", ""),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/variable_id",
                        "name": "variable_id",
                        "description": "CMIP6 variable ID",
                        "dataType": "sc:Text",
                        "data": variable_id,
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/variable_long_name",
                        "name": "variable_long_name",
                        "description": "CMIP6 variable long name",
                        "dataType": "sc:Text",
                        "data": variable_name,
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/variable_units",
                        "name": "variable_units",
                        "description": "CMIP6 variable units",
                        "dataType": "sc:Text",
                        "data": variable_units,
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/experiment_title",
                        "name": "experiment_title",
                        "description": "CMIP6 experiment title",
                        "dataType": "sc:Text",
                        "data": properties.get("cmip6:experiment_title", ""),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/frequency",
                        "name": "frequency",
                        "description": "CMIP6 data frequency",
                        "dataType": "sc:Text",
                        "data": properties.get("cmip6:frequency", ""),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/realm",
                        "name": "realm",
                        "description": "CMIP6 realm",
                        "dataType": "sc:Text",
                        "data": properties.get("realm", []),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                    {
                        "@type": "cr:Field",
                        "@id": "cmip6_metadata/cf_standard_name",
                        "name": "cf_standard_name",
                        "description": "CF standard name",
                        "dataType": "sc:Text",
                        "data": properties.get("cmip6:cf_standard_name", ""),
                        "source": {"fileSet": {"@id": "data_files"}},
                    },
                ],
            },
        ],
    }
    return croissant_metadata


# === Step 1: Connect to CEDA and search for CMIP6 tas product (SSP585, KIOST) ===
client = DataPointClient(org="CEDA")
search = client.search(
    collections=["cmip6"],
    query=[
        "cmip6:experiment_id=ssp585",
        "cmip6:activity_id=ScenarioMIP",
        "cmip6:institution_id=KIOST",
        "cmip6:variable_id=tas",
    ],
    max_items=1,
)
_, stac_item = next(iter(search.items.items()))

# === Step 2: Get actual data URLs from CEDA ===
assets = stac_item.get_assets()
print("Available assets:")
for asset_key, asset in assets.items():
    print("  {asset_key}: {type(asset)}")
    print("    Asset ID: {asset.meta.get('asset_id', 'Unknown')}")

# Get the actual data file URLs from CEDA
try:
    data_files = stac_item.get_data_files()
    print("\nData files found: {len(data_files)}")
    for i, data_url in enumerate(data_files):
        print("  [{i}]: {data_url}")

    # Use the first data file URL
    if data_files:
        download_url = data_files[0]
        filename = download_url.split("/")[-1]
        print("\nUsing data file: {filename}")
        print("Download URL: {download_url}")
    else:
        raise RuntimeError("No data files found")

except Exception:
    print("Error getting data files: {e}")
    raise RuntimeError("Could not get data file URLs from CEDA")

# Skip download and use placeholder hash
print("Skipping download - using placeholder hash")
file_hash = "placeholder_hash"
print("Using placeholder hash: {file_hash}")

# === Step 3: (Optional) Open dataset for variable and coordinate names ===
try:
    ds = stac_item.open_dataset()
    data_vars = list(ds.data_vars)
    coord_vars = list(ds.coords)
    print("Variables found:", data_vars + coord_vars)
except Exception:
    print("Warning: Could not open dataset for variable extraction: {e}")
    data_vars, coord_vars = [], []

# === Step 4: Build and save GeoCroissant JSON-LD ===
OUTPUT_PATH = "cmip6_tas_geocroissant.json"
geocroissant_data = stac_to_geocroissant(
    stac_item, file_hash=file_hash, filename=filename
)

# Add variable/coordinate list to recordSet if available
if data_vars or coord_vars:
    variable_fields = []

    # Add data variables with proper metadata
    for var in data_vars:
        var_info = {
            "@type": "cr:Field",
            "@id": "variable_metadata/{var}",
            "name": var,
            "description": "Data variable: {var}",
            "dataType": "sc:Text",
            "data": "Data variable from NetCDF file",
            "source": {"fileSet": {"@id": "data_files"}},
        }
        variable_fields.append(var_info)

    # Add coordinate variables with proper metadata
    for var in coord_vars:
        coord_info = {
            "@type": "cr:Field",
            "@id": "variable_metadata/{var}",
            "name": var,
            "description": "Coordinate variable: {var}",
            "dataType": "sc:Text",
            "data": "Coordinate variable from NetCDF file",
            "source": {"fileSet": {"@id": "data_files"}},
        }
        variable_fields.append(coord_info)

    geocroissant_data["recordSet"].append({
        "@type": "cr:RecordSet",
        "@id": "variable_metadata",
        "name": "variable_metadata",
        "description": "Variables and coordinates found in NetCDF file",
        "field": variable_fields,
    })

with open(OUTPUT_PATH, "w") as f:
    json.dump(geocroissant_data, f, indent=2)

print("\nGeoCroissant metadata written to: {OUTPUT_PATH}")
