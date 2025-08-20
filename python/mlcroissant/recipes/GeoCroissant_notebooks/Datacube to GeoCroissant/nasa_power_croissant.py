import json
from datetime import datetime
import xarray as xr
import numpy as np
import hashlib


def _infer_data_type(dtype) -> str:
    """Infer GeoCroissant data type from numpy dtype."""
    if dtype.kind in ['f']:
        return "float"
    elif dtype.kind in ['i']:
        return "integer"
    elif dtype.kind in ['U', 'S']:
        return "string"
    elif dtype.kind in ['M']:
        return "datetime"
    else:
        return "number"


def _validate_coordinates(ds: xr.Dataset) -> dict:
    """Validate and extract coordinate information."""
    coord_info = {}
    for coord_name, coord in ds.coords.items():
        coord_info[coord_name] = {
            "name": coord_name,
            "size": coord.size,
            "dtype": str(coord.dtype),
            "values_sample": coord.values[:5].tolist() if coord.size > 5 else coord.values.tolist()
        }
    return coord_info


def clean_name(name: str) -> str:
    """Clean name to follow GeoCroissant naming conventions."""
    if not name:
        return "unnamed"
    
    # Replace spaces and special characters with hyphens
    cleaned = name.lower()
    cleaned = cleaned.replace(" ", "-")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = cleaned.replace(":", "-")
    cleaned = cleaned.replace("_", "-")
    cleaned = cleaned.replace(".", "-")
    
    # Remove multiple consecutive hyphens
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    
    # Remove leading/trailing hyphens
    cleaned = cleaned.strip("-")
    
    return cleaned if cleaned else "unnamed"


def clean_dataset_attributes(ds: xr.Dataset) -> xr.Dataset:
    """Clean and validate dataset attributes for GeoCroissant compatibility."""
    attrs = ds.attrs.copy()
    
    # Clean title/name - remove forbidden characters
    if "title" in attrs:
        attrs["title"] = clean_name(attrs["title"])
    
    # Ensure version follows semantic versioning (MAJOR.MINOR.PATCH)
    if "version" in attrs:
        version = attrs["version"]
        # Check if version follows semantic versioning
        if not version or not version.replace(".", "").replace("-", "").isdigit():
            attrs["version"] = "1.0.0"
    
    # Add citation if missing
    if "citation" not in attrs:
        attrs["citation"] = "Please provide citation information"
    
    ds.attrs = attrs
    return ds


def generate_checksum(content: str) -> str:
    """Generate SHA256 checksum for content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def datacube_to_geocroissant(ds: xr.Dataset, zarr_url: str) -> dict:
    """
    Convert xarray.Dataset metadata + variables into GeoCroissant JSON-LD.
    
    Args:
        ds: xarray.Dataset to convert
        zarr_url: URL to the zarr store
        
    Returns:
        dict: GeoCroissant JSON-LD metadata
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not isinstance(ds, xr.Dataset):
        raise ValueError("Input must be an xarray.Dataset")
    
    if not zarr_url:
        raise ValueError("Zarr URL is required")
    
    # Clean dataset attributes
    ds = clean_dataset_attributes(ds)
    
    # Validate required attributes
    required_attrs = ["id", "title", "summary"]
    missing_attrs = [attr for attr in required_attrs if attr not in ds.attrs]
    if missing_attrs:
        print(f"Warning: Missing attributes: {missing_attrs}")
    
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    # Calculate dataset size in GB
    total_size_gb = ds.nbytes / 1e9

    # Generate checksum for the zarr URL (you might want to generate this from actual data)
    zarr_checksum = generate_checksum(zarr_url)

    croissant = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "geocr": "http://mlcommons.org/geocroissant/",
            "dct": "http://purl.org/dc/terms/"
        },
        "@type": "Dataset",
        "@id": ds.attrs.get("id", "unknown-dataset"),
        "name": ds.attrs.get("title", ds.attrs.get("id", "unnamed-dataset")),
        "description": ds.attrs.get("summary", ""),
        "version": ds.attrs.get("version", "1.0.0"),
        "license": ds.attrs.get("license", "CC-BY-4.0"),
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "citation": ds.attrs.get("citation", ""),
        "creator": {
            "@type": "Person",
            "name": ds.attrs.get("creator_name", "Unknown"),
            "email": ds.attrs.get("creator_email", "")
        },
        "publisher": {
            "@type": "Person",
            "name": ds.attrs.get("publisher_name", ""),
            "email": ds.attrs.get("publisher_email", "")
        },
        "institution": ds.attrs.get("institution", ""),
        "project": ds.attrs.get("project", ""),
        "keywords": ds.attrs.get("keywords", "").split(",") if ds.attrs.get("keywords") else [],
        "category": "Climate Data",
        "domain": "Earth Science",
        "geocr:BoundingBox": [
            ds.attrs.get("geospatial_lon_min", -180.0),
            ds.attrs.get("geospatial_lat_min", -90.0),
            ds.attrs.get("geospatial_lon_max", 180.0),
            ds.attrs.get("geospatial_lat_max", 90.0),
        ],
        "coordinateSystem": {
            "type": "geographic",
            "crs": "EPSG:4326",  # WGS84
            "spatialResolution": {
                "lat": ds.attrs.get("geospatial_lat_resolution", 0.5),
                "lon": ds.attrs.get("geospatial_lon_resolution", 0.625)
            }
        },
        "dct:temporal": {
            "startDate": ds.attrs.get("time_coverage_start", now_iso),
            "endDate": ds.attrs.get("time_coverage_end", now_iso),
            "resolution": ds.attrs.get("time_coverage_resolution", "P1ME"),
            "duration": ds.attrs.get("time_coverage_duration", "P1ME")
        },
        "dataQuality": {
            "processingLevel": ds.attrs.get("processing_level", "4"),
            "qualityFlags": ds.attrs.get("quality_flags", []),
            "uncertainty": ds.attrs.get("uncertainty", ""),
            "significantDigits": ds.attrs.get("significant_digits", 2)
        },
        "distribution": [
            {
                "@type": "https://schema.org/FileObject",
                "@id": "zarr-store",
                "name": "zarr-store",  # Fixed: Use clean name
                "description": "Zarr datacube dataset",
                "contentUrl": zarr_url,
                "encodingFormat": "application/x-zarr",
                "size": f"{total_size_gb:.2f} GB",
                "sha256": zarr_checksum,  # Added: SHA256 checksum
                "accessMethod": "HTTP/HTTPS"
            }
        ],
        "references": [
            ds.attrs.get("references", "")
        ],
        "additionalProperty": [
            {
                "name": "source",
                "value": ds.attrs.get("source", "")
            },
            {
                "name": "derived_from",
                "value": ds.attrs.get("derived_from", "")
            },
            {
                "name": "history",
                "value": ds.attrs.get("history", "")
            },
            {
                "name": "conventions",
                "value": ds.attrs.get("conventions", "")
            },
            {
                "name": "naming_authority",
                "value": ds.attrs.get("naming_authority", "")
            }
        ],
        "dateModified": now_iso,
        "datePublished": ds.attrs.get("date_created", now_iso),
        "coordinates": _validate_coordinates(ds),
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "name": "variables",
                "field": []
            }
        ]
    }

    # Add variables with enhanced metadata
    fields = croissant["recordSet"][0]["field"]
    for var_name, da in ds.data_vars.items():
        # Handle numpy types for JSON serialization
        valid_min = float(da.attrs.get("valid_min", np.nan)) if da.attrs.get("valid_min") is not None else None
        valid_max = float(da.attrs.get("valid_max", np.nan)) if da.attrs.get("valid_max") is not None else None
        
        field = {
            "name": var_name,
            "description": da.attrs.get("long_name", ""),
            "dataType": _infer_data_type(da.dtype),
            "units": da.attrs.get("units", ""),
            "shape": [str(s) for s in da.shape],
            "dimensions": list(da.dims),
            "valid_min": valid_min,
            "valid_max": valid_max,
            "standard_name": da.attrs.get("standard_name", ""),
            "definition": da.attrs.get("definition", ""),
            "status": da.attrs.get("status", ""),
            "significant_digits": da.attrs.get("significant_digits"),
            "cell_methods": da.attrs.get("cell_methods", ""),
            "missing_value": da.attrs.get("missing_value", None),
            "fill_value": da.attrs.get("_FillValue", None),
            "scale_factor": da.attrs.get("scale_factor", 1.0),
            "add_offset": da.attrs.get("add_offset", 0.0),
            "base": str(da.attrs.get("base", da.dtype)),
            "size_mb": f"{da.nbytes / 1e6:.2f} MB"
        }
        
        # Remove None values for cleaner JSON
        field = {k: v for k, v in field.items() if v is not None}
        fields.append(field)

    return croissant


def save_geocroissant_metadata(croissant: dict, output_file: str = "croissant.json"):
    """
    Save GeoCroissant metadata to JSON file with proper formatting.
    
    Args:
        croissant: GeoCroissant metadata dictionary
        output_file: Output file path
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(croissant, f, indent=2, ensure_ascii=False)
        print(f" GeoCroissant metadata saved to {output_file}")
    except Exception as e:
        print(f" Error saving metadata: {e}")


if __name__ == "__main__":
    # Example usage
    zarr_url = "s3://nasa-power/merra2/temporal/power_merra2_monthly_temporal_utc.zarr/"

    try:
        print(" Loading Dataset...")
        ds = xr.open_zarr(zarr_url, storage_options={"anon": True})
        
        print(f" Dataset loaded: {ds.dims}")
        print(f" Variables: {len(ds.data_vars)}")
        print(f" Size: {ds.nbytes / 1e9:.2f} GB")

        print(" Converting to GeoCroissant...")
        croissant = datacube_to_geocroissant(ds, zarr_url)

        output_file = "nasa_power_croissant.json"
        save_geocroissant_metadata(croissant, output_file)
        
        # Print summary
        print(f"\n Summary:")
        print(f"   - Dataset: {croissant['name']}")
        print(f"   - Variables: {len(croissant['recordSet'][0]['field'])}")
        print(f"   - Time range: {croissant['dct:temporal']['startDate']} to {croissant['dct:temporal']['endDate']}")
        print(f"   - Spatial extent: {croissant['geocr:BoundingBox']}")
        
    except Exception as e:
        print(f" Error: {e}")
