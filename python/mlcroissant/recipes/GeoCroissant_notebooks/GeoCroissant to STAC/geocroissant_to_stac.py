import json
from datetime import datetime
from pystac import Item, Asset, MediaType
from pystac.extensions.table import TableExtension

# License mapping from URL
KNOWN_LICENSES = {
    "https://choosealicense.com/licenses/cc-by-4.0/": "CC-BY-4.0",
    "https://opensource.org/licenses/mit": "MIT",
    "https://www.apache.org/licenses/license-2.0": "Apache-2.0",
    "cc-by-4.0": "CC-BY-4.0",
}

def croissant_to_stac_item(croissant_json, output_path=None):
    """Convert Croissant metadata to STAC Item."""
    if isinstance(croissant_json, str):
        metadata = json.loads(croissant_json)
    else:
        metadata = croissant_json

    # Extract basic metadata
    item_id = metadata.get("identifier", metadata.get("name", "unknown-id")).replace("/", "_")
    title = metadata.get("name", "")
    description = metadata.get("description", "")
    license_raw = metadata.get("license", "proprietary")
    keywords = metadata.get("keywords", [])
    dataset_url = metadata.get("url", "")
    alternate_names = metadata.get("alternateName", [])

    # Normalize license
    license_key = license_raw.strip().lower()
    license_normalized = KNOWN_LICENSES.get(license_key, 
                                          license_key.upper() if "cc-by" in license_key else "proprietary")

    # Handle creator information
    creator = metadata.get("creator", {})
    if isinstance(creator, list):
        creator = creator[0] if creator else {}
    creator_name = creator.get("name", "Unknown") if isinstance(creator, dict) else str(creator)
    creator_url = creator.get("url", "") if isinstance(creator, dict) else ""

    # Temporal coverage (from description)
    start_datetime = datetime(2018, 1, 1)
    end_datetime = datetime(2021, 12, 31)
    midpoint_datetime = datetime(2019, 6, 30)

    # Create STAC Item
    item = Item(
        id=item_id,
        geometry={
            "type": "Polygon",
            "coordinates": [[
                [-125.0, 24.0],  # SW
                [-125.0, 50.0],   # NW
                [-66.0, 50.0],    # NE
                [-66.0, 24.0],    # SE
                [-125.0, 24.0]    # SW (close polygon)
            ]]
        },
        bbox=[-125.0, 24.0, -66.0, 50.0],  # CONUS bbox
        datetime=midpoint_datetime,
        properties={
            "title": title,
            "description": description,
            "license": license_normalized,
            "start_datetime": start_datetime.isoformat() + "Z",
            "end_datetime": end_datetime.isoformat() + "Z",
            "keywords": keywords,
            "msft:region": "US",
            "msft:short_description": "HLS burn scars imagery and masks for US (2018-2021)",
            "providers": [{
                "name": creator_name,
                "roles": ["producer"],
                "url": creator_url
            }]
        }
    )

    # Add extensions (only those valid for Items)
    item.stac_extensions.extend([
        "https://stac-extensions.github.io/table/v1.2.0/schema.json",
        "https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/item.json"
    ])

    # Add only the actual assets from Croissant distribution
    for dist in metadata.get("distribution", []):
        href = dist.get("contentUrl")
        if not href:
            continue
            
        asset_id = dist.get("@id", dist.get("name", "asset")).replace(" ", "_").lower()
        media_type = dist.get("encodingFormat", MediaType.JSON)
        desc = dist.get("description", asset_id)
        
        # Determine media type
        if "parquet" in asset_id or "parquet" in media_type:
            media_type = MediaType.PARQUET
        elif "git" in href:
            media_type = "application/git"

        item.add_asset(
            asset_id,
            Asset(
                href=href,
                media_type=media_type,
                title=desc,
                roles=["metadata"] if "git" in href else ["data"]
            )
        )

    # Add documentation asset
    item.add_asset(
        "documentation",
        Asset(
            href=dataset_url,
            title="Dataset Documentation",
            media_type=MediaType.HTML,
            roles=["metadata", "documentation"]
        )
    )

    # Process record sets to add table schema
    for record_set in metadata.get("recordSet", []):
        if record_set.get("@id") == "hls_burn_scars":
            TableExtension.ext(item, add_if_missing=True).columns = [
                {
                    "name": "image",
                    "type": "binary",
                    "description": "Harmonized Landsat and Sentinel-2 imagery"
                },
                {
                    "name": "annotation",
                    "type": "binary",
                    "description": "Associated burn scar annotations"
                },
                {
                    "name": "split",
                    "type": "string",
                    "description": "Dataset split (train/validation/test)"
                }
            ]

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
