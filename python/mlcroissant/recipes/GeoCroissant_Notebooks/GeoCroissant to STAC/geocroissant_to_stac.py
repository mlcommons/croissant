"""GeoCroissant to STAC Converter Module.

This module provides functionality for converting GeoCroissant metadata to STAC
(SpatioTemporal Asset Catalog) format. It handles the transformation of GeoCroissant's
structured data into STAC Items and Assets, incorporating relevant extensions like
Table and Scientific metadata.
"""

import json
from datetime import datetime
from typing import Dict, List

from pystac import Asset, Item, MediaType
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.table import TableExtension

# License mapping from URL
KNOWN_LICENSES = {
    "https://creativecommons.org/licenses/by/4.0/": "CC-BY-4.0",
    "https://choosealicense.com/licenses/cc-by-4.0/": "CC-BY-4.0",
    "https://opensource.org/licenses/mit": "MIT",
    "https://www.apache.org/licenses/license-2.0": "Apache-2.0",
    "cc-by-4.0": "CC-BY-4.0",
    "cc-by": "CC-BY-4.0",
}

# CONUS bounding box (approximate)
CONUS_BBOX = [-125.0, 24.0, -66.0, 50.0]
CONUS_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [
        [
            [-125.0, 24.0],  # SW
            [-125.0, 50.0],  # NW
            [-66.0, 50.0],  # NE
            [-66.0, 24.0],  # SE
            [-125.0, 24.0],  # SW (close polygon)
        ]
    ],
}


def extract_band_configuration(metadata: Dict) -> List[Dict]:
    """Extract band configuration from croissant metadata."""
    # Look for bandConfiguration in dataCollection
    data_collection = metadata.get("dataCollection", {})
    band_config = data_collection.get("bandConfiguration", {})

    if not band_config:
        # Look in other locations
        for key, value in metadata.items():
            if isinstance(value, dict) and "bandConfiguration" in value:
                band_config = value["bandConfiguration"]
                break

    bands = []
    if band_config:
        for band_key, band_info in band_config.items():
            if isinstance(band_info, dict) and "name" in band_info:
                bands.append({
                    "name": band_info["name"],
                    "common_name": band_info["name"].lower(),
                    "hls_band": band_info.get("hlsBand", ""),
                    "wavelength": band_info.get("wavelength", ""),
                })

    return bands


def extract_temporal_coverage(metadata: Dict) -> tuple:
    """Extract temporal coverage from croissant metadata."""
    # Check dataCollection first
    data_collection = metadata.get("dataCollection", {})
    temporal_coverage = data_collection.get("temporalCoverage", "")

    if temporal_coverage:
        # Parse "2018-2021" format
        if "-" in temporal_coverage and len(temporal_coverage.split("-")) == 2:
            start_year, end_year = temporal_coverage.split("-")
            try:
                start_datetime = datetime(int(start_year), 1, 1)
                end_datetime = datetime(int(end_year), 12, 31)
                midpoint_datetime = datetime(
                    int(start_year) + (int(end_year) - int(start_year)) // 2, 6, 30
                )
                return start_datetime, end_datetime, midpoint_datetime
            except ValueError:
                pass

    # Fallback to default values
    return datetime(2018, 1, 1), datetime(2021, 12, 31), datetime(2019, 6, 30)


def extract_spatial_coverage(metadata: Dict) -> tuple:
    """Extract spatial coverage from croissant metadata."""
    data_collection = metadata.get("dataCollection", {})
    spatial_coverage = data_collection.get("spatialCoverage", "")

    # For now, assume CONUS for this dataset
    if "United States" in spatial_coverage or "CONUS" in spatial_coverage:
        return CONUS_BBOX, CONUS_GEOMETRY

    # Could be extended to parse other regions
    return CONUS_BBOX, CONUS_GEOMETRY


def normalize_license(license_raw: str) -> str:
    """Normalize license string to standard format."""
    if not license_raw:
        return "proprietary"

    license_key = license_raw.strip().lower()

    # Direct mapping
    if license_key in KNOWN_LICENSES:
        return KNOWN_LICENSES[license_key]

    # Pattern matching
    if "cc-by" in license_key:
        return "CC-BY-4.0"
    elif "mit" in license_key:
        return "MIT"
    elif "apache" in license_key:
        return "Apache-2.0"

    return license_key.upper() if license_key else "proprietary"


def extract_providers(metadata: Dict) -> List[Dict]:
    """Extract provider information from creator metadata."""
    providers = []

    creator = metadata.get("creator", {})
    if isinstance(creator, list):
        creators = creator
    else:
        creators = [creator] if creator else []

    for creator_info in creators:
        if isinstance(creator_info, dict):
            provider = {
                "name": creator_info.get("name", "Unknown"),
                "roles": ["producer"],
            }
            if creator_info.get("url"):
                provider["url"] = creator_info["url"]
            providers.append(provider)

    return providers


def determine_media_type(href: str, asset_id: str, encoding_format: str = None) -> str:
    """Determine media type based on URL and format information."""
    href_lower = href.lower()
    asset_id_lower = asset_id.lower()

    if "parquet" in asset_id_lower or "parquet" in href_lower:
        return MediaType.PARQUET
    elif "git" in href_lower:
        return "application/git"
    elif "tiff" in href_lower or "tif" in href_lower:
        return "image/tiff"
    elif "json" in href_lower:
        return MediaType.JSON
    elif "csv" in href_lower:
        return "text/csv"
    elif "huggingface" in href_lower:
        return MediaType.HTML
    elif encoding_format:
        return encoding_format

    return MediaType.JSON


def croissant_to_stac_item(croissant_json, output_path=None):
    """Convert Croissant metadata to STAC Item."""
    if isinstance(croissant_json, str):
        metadata = json.loads(croissant_json)
    else:
        metadata = croissant_json

    # Extract basic metadata
    item_id = metadata.get("identifier", metadata.get("name", "unknown-id")).replace(
        "/", "_"
    )
    title = metadata.get("name", "")
    description = metadata.get("description", "")
    license_raw = metadata.get("license", "proprietary")
    keywords = metadata.get("keywords", [])
    dataset_url = metadata.get("url", "")
    _ = metadata.get("alternateName", [])

    # Normalize license
    license_normalized = normalize_license(license_raw)

    # Extract provider information
    providers = extract_providers(metadata)

    # Extract temporal and spatial coverage
    start_datetime, end_datetime, midpoint_datetime = extract_temporal_coverage(
        metadata
    )
    bbox, geometry = extract_spatial_coverage(metadata)

    # Extract band configuration
    bands = extract_band_configuration(metadata)

    # Create STAC Item
    item = Item(
        id=item_id,
        geometry=geometry,
        bbox=bbox,
        datetime=midpoint_datetime,
        properties={
            "title": title,
            "description": description,
            "license": license_normalized,
            "start_datetime": start_datetime.isoformat() + "Z",
            "end_datetime": end_datetime.isoformat() + "Z",
            "keywords": keywords,
            "providers": providers,
            "msft:region": "US",
            "msft:short_description": (
                "HLS burn scars imagery and masks for US (2018-2021)"
            ),
            "gsd": 30,  # Ground sample distance in meters (Landsat/Sentinel-2)
            "platform": "Landsat-8, Sentinel-2",
            "instruments": ["OLI", "TIRS", "MSI"],
            "constellation": "HLS",
            "dataset_size": "804 scenes",
            "image_size": "512x512 pixels",
            "hls:bands": (
                bands
                if bands
                else [
                    {
                        "name": "Blue",
                        "common_name": "blue",
                        "hls_band": "B02",
                        "wavelength": "490nm",
                    },
                    {
                        "name": "Green",
                        "common_name": "green",
                        "hls_band": "B03",
                        "wavelength": "560nm",
                    },
                    {
                        "name": "Red",
                        "common_name": "red",
                        "hls_band": "B04",
                        "wavelength": "665nm",
                    },
                    {
                        "name": "NIR",
                        "common_name": "nir",
                        "hls_band": "B8A",
                        "wavelength": "865nm",
                    },
                    {
                        "name": "SW1",
                        "common_name": "swir1",
                        "hls_band": "B11",
                        "wavelength": "1610nm",
                    },
                    {
                        "name": "SW2",
                        "common_name": "swir2",
                        "hls_band": "B12",
                        "wavelength": "2190nm",
                    },
                ]
            ),
            "format": "TIFF",
        },
    )

    # Add extensions
    item.stac_extensions.extend([
        "https://stac-extensions.github.io/table/v1.2.0/schema.json",
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json",
        "https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/item.json",
    ])

    # Add scientific extension
    scientific_ext = ScientificExtension.ext(item, add_if_missing=True)
    doi = metadata.get("doi", "")
    if doi and doi.strip():
        scientific_ext.doi = doi
    scientific_ext.citation = metadata.get("citeAs", "")

    # Add data collection information
    data_collection = metadata.get("dataCollection", {})
    if data_collection and dataset_url and doi and doi.strip():
        from pystac.extensions.scientific import Publication

        # Create citation from data collection info
        citation = (
            f"{data_collection.get('name', '')}."
            f" {data_collection.get('description', '')} Available at: {dataset_url}"
        )
        publication = Publication(doi=doi, citation=citation)
        scientific_ext.publications = [publication]

    # Add additional metadata from dataCollection
    if data_collection:
        # Add collection method and sites
        if data_collection.get("collectionMethod"):
            item.properties["collection_method"] = data_collection["collectionMethod"]

        # Add collection sites
        collection_sites = data_collection.get("collectionSites", [])
        if collection_sites:
            item.properties["collection_sites"] = collection_sites

    # Add assets from Croissant distribution
    for dist in metadata.get("distribution", []):
        href = dist.get("contentUrl")
        if not href:
            continue

        asset_id = dist.get("@id", dist.get("name", "asset")).replace(" ", "_").lower()
        encoding_format = dist.get("encodingFormat")
        desc = dist.get("description", asset_id)

        # Determine media type and roles
        media_type = determine_media_type(href, asset_id, encoding_format)

        # Determine roles based on asset type
        roles = ["data"]
        if "git" in href.lower():
            roles = ["metadata"]
        elif "huggingface" in href.lower():
            roles = ["metadata", "documentation"]
        elif "tiff" in href.lower() or "tif" in href.lower():
            roles = ["data", "visual"]

        # Create asset
        asset = Asset(href=href, media_type=media_type, title=desc, roles=roles)

        # Add additional properties if available
        if dist.get("fileSize"):
            asset.extra_fields["file:size"] = dist["fileSize"]
        if dist.get("md5"):
            asset.extra_fields["file:checksum"] = f"md5:{dist['md5']}"

        item.add_asset(asset_id, asset)

    # Add documentation asset if dataset URL exists
    if dataset_url:
        item.add_asset(
            "documentation",
            Asset(
                href=dataset_url,
                title="Dataset Documentation",
                media_type=MediaType.HTML,
                roles=["metadata", "documentation"],
            ),
        )

    # Process record sets to add table schema and extract actual data
    table_ext = TableExtension.ext(item, add_if_missing=True)
    columns = []
    sample_data = []

    # Extract file listings from geocr:fileListing
    file_listing = metadata.get("geocr:fileListing", {})
    images_data = file_listing.get("images", {})

    for record_set in metadata.get("recordSet", []):
        record_id = record_set.get("@id", "")
        _ = record_set.get("name", "")

        # Add columns for the main record set
        if "hls_burn_scars" in record_id and "splits" not in record_id:
            columns = [
                {
                    "name": "image_path",
                    "type": "string",
                    "description": "Path to the image TIFF file",
                },
                {
                    "name": "annotation_path",
                    "type": "string",
                    "description": "Path to the annotation TIFF file",
                },
                {
                    "name": "split",
                    "type": "string",
                    "description": "Dataset split (train/validation)",
                },
                {
                    "name": "scene_id",
                    "type": "string",
                    "description": "HLS scene identifier",
                },
                {
                    "name": "date",
                    "type": "string",
                    "description": "Acquisition date (YYYYMMDD)",
                },
            ]

            # Extract ALL data records from file listings
            for split_name, file_list in images_data.items():
                for file_path in file_list:  # Include ALL files, not just samples
                    # Extract scene info from filename
                    # Format: training/subsetted_512x512_HLS.S30.T10SDH.2020248.v1.4_merged.tif
                    filename = file_path.split("/")[-1]
                    parts = filename.split(".")
                    if len(parts) >= 4:
                        # Extract the date from the filename (e.g., 2020248 from T10SDH.2020248.v1.4)
                        date_part = parts[3]  # This is the date like "2020248"
                        scene_id = f"{parts[2]}.{date_part}"
                        date = date_part

                        # Create corresponding annotation path
                        annotation_path = file_path.replace("_merged.tif", "_mask.tif")

                        sample_data.append({
                            "image_path": file_path,
                            "annotation_path": annotation_path,
                            "split": split_name,
                            "scene_id": scene_id,
                            "date": date,
                        })

    if columns:
        table_ext.columns = columns

    # Add complete dataset as embedded data in properties
    if sample_data:
        item.properties["dataset_records"] = sample_data
        item.properties["total_records"] = len(sample_data)

    # Add complete file listing information as embedded data
    if images_data:
        file_listings = {}
        total_files = 0
        for split_name, file_list in images_data.items():
            file_listings[split_name] = {
                "count": len(file_list),
                "files": file_list,  # Include ALL files, not just examples
            }
            total_files += len(file_list)

        item.properties["file_listings"] = file_listings
        item.properties["total_files"] = total_files

    # Output or return result
    if output_path:
        item.save_object(dest_href=output_path)
        print(f"STAC item saved to {output_path}")
    else:
        return item.to_dict()


if __name__ == "__main__":
    # Example usage
    with open("croissant.json", "r") as f:
        croissant_data = json.load(f)

    stac_item = croissant_to_stac_item(croissant_data, output_path="stac_item.json")
