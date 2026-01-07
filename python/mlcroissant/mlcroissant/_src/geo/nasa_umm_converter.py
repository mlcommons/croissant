"""Convert NASA UMM-G datasets to GeoCroissant format.

This module provides functions to convert NASA UMM-G (Unified Metadata Model
Granule) format to the GeoCroissant JSON-LD format.
"""

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
            "Requests dependency not found. " "Install with: pip install requests"
        )


def _extract_cite_as(umm: Dict[str, Any]) -> str:
    """Extract citation information from UMM-G data."""
    # First, look for direct DOI field (some UMM-G may have this)
    doi = umm.get("DOI", {})
    if doi.get("DOI"):
        return f"https://doi.org/{doi['DOI']}"

    # For UMM-G: Look for DOI in AdditionalAttributes
    additional_attrs = umm.get("AdditionalAttributes", [])
    for attr in additional_attrs:
        if attr.get("Name") == "IDENTIFIER_PRODUCT_DOI":
            values = attr.get("Values", [])
            if values and values[0]:
                return f"https://doi.org/{values[0]}"

    # Look for DOI in CollectionReference (UMM-G)
    collection_ref = umm.get("CollectionReference", {})
    if collection_ref.get("DOI"):
        return f"https://doi.org/{collection_ref['DOI']}"

    # Generic fallback based on collection name
    collection_name = (
        collection_ref.get("ShortName")
        or umm.get("ShortName")  # UMM-G collection reference
        or "NASA_Dataset"  # Direct granule name
    )
    return f"NASA {collection_name} Dataset, NASA Earthdata"


def sanitize_name(name: str) -> str:
    """Sanitize name for use in Croissant format.

    Args:
        name: Input string to sanitize

    Returns:
        Sanitized string with special characters replaced by single dashes
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
    """Ensure version follows semver format."""
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


def extract_spatial_extent(umm: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract spatial extent information from UMM-G."""
    spatial_extent = umm.get("SpatialExtent", {})
    if not spatial_extent:
        return None

    horizontal_domain = spatial_extent.get("HorizontalSpatialDomain", {})
    geometry = horizontal_domain.get("Geometry", {})

    # Extract bounding box
    bbox = None
    if "BoundingRectangle" in horizontal_domain:
        rect = horizontal_domain["BoundingRectangle"]
        bbox = [
            rect.get("WestBoundingCoordinate", -180),
            rect.get("SouthBoundingCoordinate", -90),
            rect.get("EastBoundingCoordinate", 180),
            rect.get("NorthBoundingCoordinate", 90),
        ]

    # Extract polygon geometry
    geometry_wkt = None
    if "GPolygons" in geometry:
        polygons = geometry["GPolygons"]
        if polygons:
            points = polygons[0].get("Boundary", {}).get("Points", [])
            if points:
                geometry_wkt = convert_polygon_to_wkt(points)

    # Only return if we have either bbox or geometry
    if bbox or geometry_wkt:
        return {"bbox": bbox, "geometry": geometry_wkt}
    return None


def extract_temporal_extent(umm: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract temporal extent information from UMM-G."""
    temporal_extent = umm.get("TemporalExtent", {})
    if not temporal_extent:
        return None

    range_datetime = temporal_extent.get("RangeDateTime", {})
    if not range_datetime:
        return None

    return {
        "start": range_datetime.get("BeginningDateTime"),
        "end": range_datetime.get("EndingDateTime"),
    }


def convert_polygon_to_wkt(points: List[Dict[str, float]]) -> str:
    """Convert polygon points to WKT format."""
    if not points:
        return ""

    coords = []
    for point in points:
        lon = point.get("Longitude", 0)
        lat = point.get("Latitude", 0)
        coords.append(f"{lon} {lat}")

    # Ensure polygon is closed (first and last points are the same)
    if coords and (len(coords) == 1 or coords[0] != coords[-1]):
        coords.append(coords[0])

    return f"POLYGON(({', '.join(coords)}))"


def extract_platform_information(umm: Dict[str, Any]) -> Dict[str, Any]:
    """Extract platform and instrument information from UMM-G."""
    platforms = umm.get("Platforms", [])
    if not platforms:
        return {}

    platform = platforms[0]
    instruments = platform.get("Instruments", [])

    return {
        "platform": platform.get("ShortName", "Unknown"),
        "instrument": (
            instruments[0].get("ShortName", "Unknown") if instruments else "Unknown"
        ),
        "platform_long_name": platform.get("LongName", ""),
        "instrument_long_name": (
            instruments[0].get("LongName", "") if instruments else ""
        ),
    }


def extract_distribution_info(umm: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract distribution information from UMM-G."""
    distributions: List[Dict[str, Any]] = []
    related_urls = umm.get("RelatedUrls", [])
    used_ids = set()

    for url_info in related_urls:
        url = url_info.get("URL", "")
        url_type = url_info.get("Type", "")
        subtype = url_info.get("Subtype", "")
        description = url_info.get("Description", "")

        # Determine encoding format
        encoding_format = determine_encoding_format(url, url_type, subtype)

        # Create proper file ID based on filename with unique suffix if needed
        filename = url.split("/")[-1] or "data_file"
        base_id = f"file_{filename.replace('.', '_').replace('-', '_')}"

        if (
            url_type == "VIEW RELATED INFORMATION"
            or url_type == "GET RELATED VISUALIZATION"
        ):
            base_id = f"other_{len(distributions)}"

        # Ensure unique ID
        file_id = base_id
        counter = 1
        while file_id in used_ids:
            file_id = f"{base_id}_{counter}"
            counter += 1
        used_ids.add(file_id)

        distribution = {
            "@type": "cr:FileObject",
            "@id": file_id,
            "name": (
                filename
                if url_type.startswith(("GET DATA", "EXTENDED METADATA"))
                else url_type
            ),
            "description": description or f"Download {filename}",
            "contentUrl": url,
            "encodingFormat": encoding_format,
            "md5": "d41d8cd98f00b204e9800998ecf8427e",  # Standard placeholder
        }

        distributions.append(distribution)

    return distributions


def determine_encoding_format(url: str, url_type: str, subtype: str) -> str:
    """Determine the encoding format based on URL and type."""
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
    else:
        return "application/octet-stream"


def extract_keywords(umm: Dict[str, Any], platform_info: Dict[str, Any]) -> List[str]:
    """Extract keywords for the dataset based on UMM data."""
    keywords = [
        "satellite imagery",
        "remote sensing",
        "geospatial",
        "Earth observation",
        "NASA",
    ]

    # Add platform-specific keywords
    if platform_info.get("platform"):
        keywords.append(platform_info["platform"])
    if platform_info.get("instrument"):
        keywords.append(platform_info["instrument"])

    # Add collection-specific keywords
    collection_ref = umm.get("CollectionReference", {})
    if collection_ref.get("ShortName"):
        keywords.append(collection_ref["ShortName"])

    return keywords


def find_additional_attribute(
    additional_attrs: List[Dict[str, Any]], name: str
) -> Optional[str]:
    """Find a specific additional attribute by name."""
    for attr in additional_attrs:
        if attr.get("Name") == name:
            values = attr.get("Values", [])
            if values:
                return values[0]
    return None


def extract_sensor_characteristics(umm: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract detailed sensor characteristics from UMM data universally."""
    platforms = umm.get("Platforms", [])
    if not platforms:
        return []

    platform = platforms[0]

    # Extract actual band information from the data
    band_info = extract_actual_bands_from_umm(umm)

    # Determine sensor type from collection or platform info
    sensor_type = determine_sensor_type(umm)
    acquisition_mode = "spaceborne"  # Most NASA datasets are satellite-based

    # Extract spatial resolution from additional attributes or default
    additional_attrs = umm.get("AdditionalAttributes", [])
    spatial_res = (
        find_additional_attribute(additional_attrs, "SPATIAL_RESOLUTION") or "unknown"
    )
    if spatial_res != "unknown" and not spatial_res.endswith("m"):
        spatial_res = f"{spatial_res}m"

    characteristics = [
        {
            "platform": platform.get("ShortName", "Unknown"),
            "sensorType": sensor_type,
            "acquisitionMode": acquisition_mode,
            "spectralBands": band_info.get("count", 0),
            "spatialResolution": spatial_res,
            "temporalResolution": extract_temporal_resolution(umm),
        }
    ]

    return characteristics


def extract_actual_bands_from_umm(umm: Dict[str, Any]) -> Dict[str, Any]:
    """Extract actual band information from UMM-G data universally."""
    bands = []
    band_config = {}

    # Check RelatedUrls for band files (common pattern: .B01.tif, .B02.tif, etc.)
    related_urls = umm.get("RelatedUrls", [])
    detected_bands = set()

    for url_info in related_urls:
        url = url_info.get("URL", "")
        # Extract band identifiers from filenames
        # Pattern to match band files: .B01.tif, .B02.tif, .B8A.tif, etc.
        band_matches = re.findall(r"\.B([0-9A-Z]+)\.", url)
        for band in band_matches:
            detected_bands.add(f"B{band}")

    # If no bands detected from URLs, check AdditionalAttributes
    if not detected_bands:
        additional_attrs = umm.get("AdditionalAttributes", [])
        for attr in additional_attrs:
            name = attr.get("Name", "")
            if "BAND" in name.upper() or "SPECTRAL" in name.upper():
                # Try to extract band information from attribute names/values
                values = attr.get("Values", [])
                if values and values[0]:
                    # Parse band information if available
                    band_info = values[0]
                    if isinstance(band_info, str) and "B" in band_info:
                        # Extract band identifiers
                        band_matches = re.findall(r"B[0-9A-Z]+", band_info)
                        detected_bands.update(band_matches)

    # Convert to sorted list
    bands = sorted(list(detected_bands))

    # Create basic configuration for detected bands
    for i, band in enumerate(bands, 1):
        band_config[f"band{i}"] = {
            "identifier": band,
            "name": f"Band {band}",
            "description": f"Spectral band {band}",
        }

    return {"count": len(bands), "bands": bands, "configuration": band_config}


def determine_sensor_type(umm: Dict[str, Any]) -> str:
    """Determine sensor type from UMM data."""
    platforms = umm.get("Platforms", [])
    if not platforms:
        return "unknown"

    platform_name = platforms[0].get("ShortName", "").lower()
    instruments = platforms[0].get("Instruments", [])
    instrument_name = instruments[0].get("ShortName", "").lower() if instruments else ""

    # Determine sensor type based on platform/instrument
    if any(term in platform_name for term in ["sentinel", "landsat", "modis"]):
        return "optical_multispectral"
    elif any(term in instrument_name for term in ["radar", "sar"]):
        return "radar"
    elif any(term in instrument_name for term in ["lidar"]):
        return "lidar"
    elif any(term in instrument_name for term in ["hyperspectral"]):
        return "optical_hyperspectral"
    else:
        return "optical_multispectral"  # Default for most Earth observation


def extract_temporal_resolution(umm: Dict[str, Any]) -> str:
    """Extract temporal resolution from UMM data."""
    # Check for temporal resolution in additional attributes
    additional_attrs = umm.get("AdditionalAttributes", [])
    temporal_res = find_additional_attribute(additional_attrs, "TEMPORAL_RESOLUTION")
    if temporal_res:
        return temporal_res

    # Default based on platform type
    platforms = umm.get("Platforms", [])
    if platforms:
        platform_name = platforms[0].get("ShortName", "").lower()
        if "sentinel-2" in platform_name:
            return "5 days"
        elif "landsat" in platform_name:
            return "16 days"
        elif "modis" in platform_name:
            return "daily"

    return "unknown"


def extract_spatial_resolution(additional_attrs: List[Dict[str, Any]]) -> str:
    """Extract spatial resolution from additional attributes."""
    spatial_res = (
        find_additional_attribute(additional_attrs, "SPATIAL_RESOLUTION")
        or find_additional_attribute(additional_attrs, "HORIZONTAL_RESOLUTION")
        or find_additional_attribute(additional_attrs, "RESOLUTION")
        or "unknown"
    )
    if spatial_res != "unknown" and not spatial_res.endswith("m"):
        spatial_res = f"{spatial_res}m"
    return spatial_res


def extract_access_methods(umm: Dict[str, Any]) -> Dict[str, int]:
    """Extract access methods from related URLs."""
    related_urls = umm.get("RelatedUrls", [])
    access_methods = {"https": 0, "s3": 0, "other": 0}
    for url_info in related_urls:
        url = url_info.get("URL", "")
        if url.startswith("https"):
            access_methods["https"] += 1
        elif "s3://" in url:
            access_methods["s3"] += 1
        else:
            access_methods["other"] += 1
    return access_methods


def extract_add_offset(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract ADD_OFFSET value."""
    add_offset = find_additional_attribute(additional_attrs, "ADD_OFFSET")
    return float(add_offset) if add_offset is not None else None


def extract_ang_scale_factor(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract ANG_SCALE_FACTOR value."""
    ang_scale = find_additional_attribute(additional_attrs, "ANG_SCALE_FACTOR")
    return float(ang_scale) if ang_scale is not None else None


def extract_byte_order(umm: Dict[str, Any], distributions: List[Dict[str, Any]]) -> str:
    """Extract byte order information."""
    raster_info = extract_raster_data_info(umm, distributions)
    return raster_info.get("byteOrder", "unknown")


def extract_cloud_coverage(
    additional_attrs: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Extract cloud coverage information."""
    cloud_coverage = find_additional_attribute(additional_attrs, "CLOUD_COVERAGE")
    if cloud_coverage is not None:
        return {
            "geocr:value": float(cloud_coverage),
            "geocr:unit": "percentage",
        }
    return None


def extract_compression(
    umm: Dict[str, Any], distributions: List[Dict[str, Any]]
) -> str:
    """Extract compression information."""
    raster_info = extract_raster_data_info(umm, distributions)
    return raster_info.get("compression", "unknown")


def extract_coordinate_reference_system(additional_attrs: List[Dict[str, Any]]) -> str:
    """Extract coordinate reference system."""
    return (
        find_additional_attribute(additional_attrs, "HORIZONTAL_CS_NAME")
        or find_additional_attribute(additional_attrs, "PROJECTION")
        or find_additional_attribute(additional_attrs, "CRS")
        or find_additional_attribute(additional_attrs, "SPATIAL_REFERENCE")
        or "EPSG:4326"  # Default to WGS84
    )


def extract_data_scaling_info(additional_attrs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract data scaling information."""
    scaling_info: Dict[str, Any] = {"@type": "geocr:DataScaling"}

    add_offset = find_additional_attribute(additional_attrs, "ADD_OFFSET")
    if add_offset is not None:
        scaling_info["geocr:addOffset"] = str(float(add_offset))

    ref_scale = find_additional_attribute(additional_attrs, "REF_SCALE_FACTOR")
    if ref_scale is not None:
        scaling_info["geocr:refScaleFactor"] = str(float(ref_scale))

    ang_scale = find_additional_attribute(additional_attrs, "ANG_SCALE_FACTOR")
    if ang_scale is not None:
        scaling_info["geocr:angScaleFactor"] = str(float(ang_scale))

    fill_value = find_additional_attribute(additional_attrs, "FILLVALUE")
    if fill_value is not None:
        scaling_info["geocr:fillValue"] = str(float(fill_value))

    qa_fill = find_additional_attribute(additional_attrs, "QA_FILLVALUE")
    if qa_fill is not None:
        scaling_info["geocr:qaFillValue"] = str(float(qa_fill))

    return scaling_info


def extract_fill_value(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract fill value."""
    fill_value = find_additional_attribute(additional_attrs, "FILLVALUE")
    return float(fill_value) if fill_value is not None else None


def extract_format(umm: Dict[str, Any], distributions: List[Dict[str, Any]]) -> str:
    """Extract format information."""
    raster_info = extract_raster_data_info(umm, distributions)
    return raster_info.get("format", "unknown")


def extract_geometric_accuracy(
    additional_attrs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Extract geometric accuracy information."""
    geometric_accuracy = {}
    for attr_pattern in ["XSHIFT", "YSHIFT", "RMSE", "ACCURACY", "AROP"]:
        for attr in additional_attrs:
            attr_name = attr.get("Name", "")
            if attr_pattern in attr_name and attr.get("Values"):
                try:
                    value = float(attr["Values"][0])
                    if "XSHIFT" in attr_name or "X_SHIFT" in attr_name:
                        geometric_accuracy["geocr:xShift"] = value
                    elif "YSHIFT" in attr_name or "Y_SHIFT" in attr_name:
                        geometric_accuracy["geocr:yShift"] = value
                    elif "RMSE" in attr_name:
                        geometric_accuracy["geocr:rmse"] = value
                except (ValueError, TypeError):
                    continue
    return geometric_accuracy


def extract_calibration_offset(
    additional_attrs: List[Dict[str, Any]],
) -> Optional[float]:
    """Extract calibration offset value."""
    for attr in additional_attrs:
        name = attr.get("Name", "")
        if "OFFSET" in name and attr.get("Values"):
            try:
                return float(attr["Values"][0])
            except (ValueError, TypeError):
                continue
    return None


def extract_qa_fill_value(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract QA fill value."""
    qa_fill = find_additional_attribute(additional_attrs, "QA_FILLVALUE")
    return float(qa_fill) if qa_fill is not None else None


def extract_quality_assessment_full(
    additional_attrs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Extract full quality assessment information."""
    quality_info: Dict[str, Any] = {"@type": "geocr:QualityAssessment"}

    geometric_accuracy = extract_geometric_accuracy(additional_attrs)
    if geometric_accuracy:
        quality_info["geocr:geometricAccuracy"] = str(geometric_accuracy)

    cloud_coverage = extract_cloud_coverage(additional_attrs)
    if cloud_coverage:
        quality_info["geocr:cloudCoverage"] = str(cloud_coverage)

    return quality_info


def extract_ref_scale_factor(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract REF_SCALE_FACTOR value."""
    ref_scale = find_additional_attribute(additional_attrs, "REF_SCALE_FACTOR")
    return float(ref_scale) if ref_scale is not None else None


def extract_rmse_value(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract RMSE value from geometric accuracy."""
    for attr in additional_attrs:
        attr_name = attr.get("Name", "")
        if "RMSE" in attr_name and attr.get("Values"):
            try:
                return float(attr["Values"][0])
            except (ValueError, TypeError):
                continue
    return None


def extract_calibration_slope(
    additional_attrs: List[Dict[str, Any]],
) -> Optional[float]:
    """Extract calibration slope value."""
    for attr in additional_attrs:
        name = attr.get("Name", "")
        if ("SCALE" in name or "SLOPE" in name) and attr.get("Values"):
            try:
                return float(attr["Values"][0])
            except (ValueError, TypeError):
                continue
    return None


def extract_spectral_bands_info(umm: Dict[str, Any]) -> Dict[str, Any]:
    """Extract spectral bands information."""
    band_info = extract_actual_bands_from_umm(umm)
    if band_info["bands"]:
        return {
            "@type": "geocr:SpectralBands",
            "geocr:totalBands": band_info["count"],
            "geocr:bandInfo": band_info["configuration"],
        }
    else:
        return {
            "@type": "geocr:SpectralBands",
            "geocr:totalBands": 0,
            "geocr:bandInfo": {},
        }


# NOTE: URL categories should only be in distribution section, not in custom properties
# This function is removed to prevent duplication in GeoCroissant output


def extract_generic_value(additional_attrs: List[Dict[str, Any]]) -> Optional[str]:
    """Extract a generic value from attributes."""
    # Return the first non-empty value found
    for attr in additional_attrs:
        values = attr.get("Values", [])
        if values and values[0]:
            return str(values[0])
    return None


def extract_x_shift(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract X shift value."""
    for attr in additional_attrs:
        attr_name = attr.get("Name", "")
        if ("XSHIFT" in attr_name or "X_SHIFT" in attr_name) and attr.get("Values"):
            try:
                return float(attr["Values"][0])
            except (ValueError, TypeError):
                continue
    return None


def extract_y_shift(additional_attrs: List[Dict[str, Any]]) -> Optional[float]:
    """Extract Y shift value."""
    for attr in additional_attrs:
        attr_name = attr.get("Name", "")
        if ("YSHIFT" in attr_name or "Y_SHIFT" in attr_name) and attr.get("Values"):
            try:
                return float(attr["Values"][0])
            except (ValueError, TypeError):
                continue
    return None


def umm_to_geocroissant(
    umm_g_input: Union[str, Path, Dict[str, Any]],
    output_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Convert NASA UMM-G to GeoCroissant JSON-LD format.

    Args:
        umm_g_input: UMM-G dictionary, path to UMM-G file, or URL to UMM-G endpoint
        output_path: Optional output file path (if provided, saves to file)

    Returns:
        GeoCroissant JSON-LD dictionary

    Raises:
        ImportError: If required dependencies are not installed
        ValueError: If UMM-G data is invalid or URL fetch fails
        FileNotFoundError: If umm_g_input file path does not exist
    """
    _check_dependencies()

    # Input validation
    if not isinstance(umm_g_input, (str, Path, dict)):
        raise TypeError(
            f"Expected string, Path, or dict input, got {type(umm_g_input)}"
        )

    # Handle file input or URL
    if isinstance(umm_g_input, (str, Path)):
        umm_g_input_str = str(umm_g_input)

        # Check if input is a URL
        if umm_g_input_str.startswith(("http://", "https://")):
            try:
                logger.info(f"Fetching UMM-G data from URL: {umm_g_input_str}")
                response = requests.get(umm_g_input_str, timeout=30)
                response.raise_for_status()
                umm_g_dict = response.json()
                logger.info("Successfully fetched UMM-G data from URL")
            except requests.RequestException as e:
                raise ValueError(
                    f"Failed to fetch UMM-G data from URL {umm_g_input_str}: {e}"
                )
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON response from URL {umm_g_input_str}: {e}"
                )
        else:
            # Handle local file path
            umm_g_path = Path(umm_g_input)
            if not umm_g_path.exists():
                raise FileNotFoundError(f"UMM-G file not found: {umm_g_path}")

            logger.info(f"Loading UMM-G file: {umm_g_path}")
            with open(umm_g_path, "r") as f:
                umm_g_dict = json.load(f)
    else:
        umm_g_dict = umm_g_input

    # Extract main sections - handle both direct UMM-G and CMR response formats
    if "items" in umm_g_dict:
        # This is a CMR response - extract the first item
        if umm_g_dict.get("items"):
            umm_g_dict = umm_g_dict["items"][0]
            logger.info("Detected CMR response format, extracted first granule")
        else:
            raise ValueError("CMR response contains no granules")

    meta = umm_g_dict.get("meta", {})
    umm = umm_g_dict.get("umm", umm_g_dict)  # Handle both formats

    # Extract basic information
    dataset_id = umm.get("GranuleUR") or meta.get("concept-id") or "unnamed_dataset"
    title = (
        umm.get("CollectionReference", {}).get("EntryTitle")
        or umm.get("EntryTitle")
        or "Unnamed Dataset"
    )
    name = sanitize_name(title)
    version = ensure_semver(umm.get("Version") or meta.get("revision-id") or "1.0.0")

    # Extract spatial and temporal information
    spatial_info = extract_spatial_extent(umm)
    temporal_info = extract_temporal_extent(umm)
    platform_info = extract_platform_information(umm)
    distributions = extract_distribution_info(umm)

    # Create GeoCroissant structure
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
        "alternateName": [dataset_id, f"{name}-satellite-imagery"],
        "description": umm.get("Abstract")
        or umm.get("CollectionReference", {}).get("Abstract")
        or "NASA satellite imagery dataset",
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "version": version,
        "creator": {
            "@type": "Organization",
            "name": "NASA Earthdata",
            "url": "https://earthdata.nasa.gov/",
        },
        "url": "https://data.lpdaac.earthdatacloud.nasa.gov/",
        "keywords": extract_keywords(umm, platform_info),
        "citeAs": _extract_cite_as(umm),
        "datePublished": (
            temporal_info.get("start") if temporal_info else meta.get("revision-date")
        ),
        "license": "https://creativecommons.org/licenses/by/4.0/",
    }

    # Add GeoCroissant spatial and temporal extensions
    if spatial_info:
        if spatial_info.get("bbox"):
            croissant["geocr:BoundingBox"] = spatial_info["bbox"]
        if spatial_info.get("geometry"):
            croissant["geocr:Geometry"] = spatial_info["geometry"]

    if temporal_info:
        croissant["geocr:temporalExtent"] = {
            "startDate": temporal_info.get("start"),
            "endDate": temporal_info.get("end"),
        }

    # Get additional attributes for processing
    additional_attrs = umm.get("AdditionalAttributes", [])

    # Add core GeoCroissant properties (mandatory)
    croissant["geocr:spatialResolution"] = extract_spatial_resolution(additional_attrs)

    # Add comprehensive GeoCroissant extensions via Custom Properties

    # NASA UMM Custom Properties - Group 1: Administrative & Metadata
    croissant["geocr:CustomProperty1"] = {
        "@type": "geocr:AdministrativeMetadata",
        "geocr:accessMethods": extract_access_methods(umm),
        "geocr:addOffset": extract_add_offset(additional_attrs),
        "geocr:administrativeMetadata": {
            "geocr:conceptType": meta.get("concept-type"),
            "geocr:revisionId": meta.get("revision-id"),
            "geocr:nativeId": meta.get("native-id"),
            "geocr:collectionConceptId": meta.get("collection-concept-id"),
            "geocr:providerId": meta.get("provider-id"),
            "geocr:metadataFormat": meta.get("format"),
        },
        "geocr:angScaleFactor": extract_ang_scale_factor(additional_attrs),
        "geocr:attributeCategories": categorize_attributes(additional_attrs),
        "geocr:byteOrder": extract_byte_order(umm, distributions),
        "geocr:cloudCoverage": extract_cloud_coverage(additional_attrs),
        "geocr:collectionConceptId": meta.get("collection-concept-id"),
        "geocr:compression": extract_compression(umm, distributions),
        "geocr:conceptType": meta.get("concept-type"),
        "geocr:coordinateReferenceSystem": extract_coordinate_reference_system(
            additional_attrs
        ),
        "geocr:dataScaling": extract_data_scaling_info(additional_attrs),
        "geocr:fillValue": extract_fill_value(additional_attrs),
        "geocr:format": extract_format(umm, distributions),
        "geocr:geometricAccuracy": extract_geometric_accuracy(additional_attrs),
        "geocr:metadataFormat": meta.get("format"),
        "geocr:mgrsTileId": find_additional_attribute(additional_attrs, "MGRS_TILE_ID"),
        "geocr:nasaSpecificAttributes": extract_nasa_attributes(additional_attrs),
        "geocr:nativeId": meta.get("native-id"),
    }

    # NASA UMM Custom Properties - Group 2: Product & Quality
    croissant["geocr:CustomProperty2"] = {
        "@type": "geocr:ProductInformation",
        "geocr:offset": extract_calibration_offset(additional_attrs),
        "geocr:productInformation": {
            "geocr:productUri": find_additional_attribute(
                additional_attrs, "PRODUCT_URI"
            ),
            "geocr:mgrsTileId": find_additional_attribute(
                additional_attrs, "MGRS_TILE_ID"
            ),
            "geocr:spatialCoverage": float(
                find_additional_attribute(additional_attrs, "SPATIAL_COVERAGE") or 99.0
            ),
        },
        "geocr:providerId": meta.get("provider-id"),
        "geocr:qaFillValue": extract_qa_fill_value(additional_attrs),
        "geocr:qualityAssessment": extract_quality_assessment_full(additional_attrs),
        "geocr:rasterData": extract_raster_data_info(umm, distributions),
        "geocr:refScaleFactor": extract_ref_scale_factor(additional_attrs),
        "geocr:revisionId": meta.get("revision-id"),
        "geocr:rmse": extract_rmse_value(additional_attrs),
        "geocr:sensorCharacteristics": extract_sensor_characteristics(umm),
        "geocr:slope": extract_calibration_slope(additional_attrs),
        "geocr:spatialCoverage": float(
            find_additional_attribute(additional_attrs, "SPATIAL_COVERAGE") or 99.0
        ),
        "geocr:spectralBands": extract_spectral_bands_info(umm),
        "geocr:totalAttributes": len(additional_attrs),
        "geocr:unit": "percentage",  # Default unit for most measurements
        "geocr:value": extract_generic_value(additional_attrs),
        "geocr:xShift": extract_x_shift(additional_attrs),
        "geocr:yShift": extract_y_shift(additional_attrs),
    }

    # Add distribution
    if distributions:
        croissant["distribution"] = distributions
        # Add FileSet for TIFF files
        tiff_files: List[Dict[str, Any]] = [
            d for d in distributions if d.get("encodingFormat") == "image/tiff"
        ]
        if tiff_files:
            distributions.append(
                {
                    "@type": "cr:FileSet",
                    "@id": "tiff_files",
                    "name": "TIFF Files",
                    "description": f"Collection of {len(tiff_files)} TIFF files containing satellite imagery bands",
                    "encodingFormat": "image/tiff",
                    "includes": "**/*.tif",
                }
            )

    # Add record set for granule data
    croissant["recordSet"] = [
        create_granule_record_set(meta, umm, spatial_info, temporal_info)
    ]

    # Save to file if output_path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(croissant, f, indent=2)
        logger.info(f"GeoCroissant saved to: {output_path}")

    return croissant


def extract_spectral_band_info(umm: Dict[str, Any]) -> Dict[str, Any]:
    """Extract spectral band information universally from UMM data."""
    band_info_dict = {}

    # Get detected bands
    band_info = extract_actual_bands_from_umm(umm)
    detected_bands = band_info.get("bands", [])

    # Extract resolution from additional attributes or files
    additional_attrs = umm.get("AdditionalAttributes", [])
    default_resolution = (
        find_additional_attribute(additional_attrs, "SPATIAL_RESOLUTION") or "unknown"
    )
    if default_resolution != "unknown" and not default_resolution.endswith("m"):
        default_resolution = f"{default_resolution}m"

    # Create band info for each detected band
    for band in detected_bands:
        band_info_dict[band] = {
            "name": f"Band {band}",
            "identifier": band,
            "resolution": default_resolution,
        }

        # Look for wavelength information in additional attributes
        wavelength = find_additional_attribute(additional_attrs, f"{band}_WAVELENGTH")
        if wavelength:
            band_info_dict[band]["wavelength"] = wavelength

    return band_info_dict


def extract_nasa_attributes(additional_attrs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract NASA-specific attributes."""
    nasa_attrs: Dict[str, Any] = {}
    for attr in additional_attrs:
        name: Optional[str] = attr.get("Name")
        values = attr.get("Values", [])
        if name and values:
            value = values[0]
            # Convert to appropriate type
            if name in ["ULX", "ULY", "NCOLS", "NROWS"]:
                nasa_attrs[name] = float(value) if "." in str(value) else int(value)
            elif "ANGLE" in name or "SHIFT" in name or "RMSE" in name:
                nasa_attrs[name] = float(value)
            elif name in ["ADD_OFFSET", "REF_SCALE_FACTOR", "ANG_SCALE_FACTOR"]:
                nasa_attrs[name] = float(value)
            elif name in ["FILLVALUE", "QA_FILLVALUE", "AROP_NCP"]:
                nasa_attrs[name] = int(float(value))
            else:
                nasa_attrs[name] = value
    return nasa_attrs


def categorize_attributes(
    additional_attrs: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Categorize NASA attributes by type."""
    categories: Dict[str, List[str]] = {
        "processing": [],
        "geometry": [],
        "quality": [],
        "raster": [],
        "scaling": [],
    }

    for attr in additional_attrs:
        name = attr.get("Name", "")
        if "PROCESSING" in name or "SENSING" in name or "BASELINE" in name:
            categories["processing"].append(name)
        elif "ANGLE" in name:
            categories["geometry"].append(name)
        elif "AROP" in name or "SHIFT" in name or "RMSE" in name:
            categories["quality"].append(name)
        elif name in ["NCOLS", "NROWS", "ULX", "ULY"]:
            categories["raster"].append(name)
        elif "SCALE" in name or "OFFSET" in name:
            categories["scaling"].append(name)

    return categories


def extract_raster_data_info(
    umm: Dict[str, Any], distributions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Extract raster data format information from UMM data and distributions."""
    raster_info = {}

    # Determine format from file extensions in distributions
    formats = set()
    for dist in distributions:
        encoding_format = dist.get("encodingFormat", "")
        if encoding_format == "image/tiff":
            formats.add("GeoTIFF")
        elif encoding_format == "application/x-hdf":
            formats.add("HDF")
        elif encoding_format == "application/x-netcdf":
            formats.add("NetCDF")
        elif encoding_format == "image/jpeg":
            formats.add("JPEG")

    # Use most common format or default
    if "GeoTIFF" in formats:
        raster_info["format"] = "GeoTIFF"
        raster_info["compression"] = "LZW"  # Common for GeoTIFF
        raster_info["byteOrder"] = "little-endian"
    elif "HDF" in formats:
        raster_info["format"] = "HDF"
        raster_info["compression"] = "unknown"
        raster_info["byteOrder"] = "unknown"
    elif "NetCDF" in formats:
        raster_info["format"] = "NetCDF"
        raster_info["compression"] = "unknown"
        raster_info["byteOrder"] = "unknown"
    else:
        raster_info["format"] = "unknown"
        raster_info["compression"] = "unknown"
        raster_info["byteOrder"] = "unknown"

    # Determine data type from additional attributes or platform
    additional_attrs = umm.get("AdditionalAttributes", [])
    data_type = find_additional_attribute(additional_attrs, "DATA_TYPE")

    if not data_type:
        # Infer from platform/instrument
        platforms = umm.get("Platforms", [])
        if platforms:
            platform_name = platforms[0].get("ShortName", "").lower()
            if "sentinel" in platform_name or "landsat" in platform_name:
                data_type = "surface reflectance"
            elif "modis" in platform_name:
                data_type = "radiance"
            elif "radar" in platform_name or "sar" in platform_name:
                data_type = "backscatter"
            else:
                data_type = "unknown"

    raster_info["dataType"] = data_type or "unknown"

    return raster_info


# NOTE: URL information should only be in distribution section, not in custom properties
# This function is removed to prevent duplication in GeoCroissant output


def determine_access_method(url: str) -> str:
    """Determine access method from URL."""
    if ".xml" in url:
        return "CMR_METADATA"
    elif ".json" in url:
        return "STAC_METADATA"
    elif ".jpg" in url or ".png" in url:
        return "PREVIEW_IMAGE"
    else:
        return "DIRECT_ACCESS"


def create_granule_record_set(
    meta: Dict[str, Any],
    umm: Dict[str, Any],
    spatial_info: Optional[Dict[str, Any]],
    temporal_info: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a record set for the granule data."""
    additional_attrs = umm.get("AdditionalAttributes", [])

    # Extract spatial coverage as WKT
    spatial_coverage = ""
    if spatial_info and spatial_info.get("bbox"):
        bbox = spatial_info["bbox"]
        spatial_coverage = f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"

    # Create universal record set names
    collection_ref = umm.get("CollectionReference", {})
    collection_name = collection_ref.get("ShortName", "nasa_dataset")
    platform_name = (
        umm.get("Platforms", [{}])[0].get("ShortName", "satellite")
        if umm.get("Platforms")
        else "dataset"
    )

    record_id = f"{collection_name.lower()}_{platform_name.lower()}_granule".replace(
        "-", "_"
    )

    return {
        "@type": "cr:RecordSet",
        "@id": record_id,
        "name": record_id,
        "description": f"{collection_name} granule: {umm.get('GranuleUR', 'Unknown')}",
        "field": [
            {
                "@type": "cr:Field",
                "@id": f"{record_id}/granule_id",
                "name": f"{record_id}/granule_id",
                "description": "Unique granule identifier",
                "dataType": "sc:Text",
            },
            {
                "@type": "cr:Field",
                "@id": f"{record_id}/cloud_coverage",
                "name": f"{record_id}/cloud_coverage",
                "description": "Cloud coverage percentage",
                "dataType": "sc:Text",
            },
            {
                "@type": "cr:Field",
                "@id": f"{record_id}/temporal_extent",
                "name": f"{record_id}/temporal_extent",
                "description": "Temporal extent of the granule",
                "dataType": "sc:Text",
            },
            {
                "@type": "cr:Field",
                "@id": f"{record_id}/spatial_coverage",
                "name": f"{record_id}/spatial_coverage",
                "description": "Spatial coverage polygon",
                "dataType": "sc:Text",
            },
            {
                "@type": "cr:Field",
                "@id": f"{record_id}/spectral_bands",
                "name": f"{record_id}/spectral_bands",
                "description": "Available spectral bands",
                "dataType": "sc:Text",
            },
        ],
        "data": [
            {
                f"{record_id}/granule_id": umm.get("GranuleUR", ""),
                f"{record_id}/cloud_coverage": float(
                    find_additional_attribute(additional_attrs, "CLOUD_COVERAGE") or 0.0
                ),
                f"{record_id}/temporal_extent": (
                    temporal_info.get("start") if temporal_info else ""
                ),
                f"{record_id}/spatial_coverage": spatial_coverage,
                f"{record_id}/spectral_bands": ",".join(
                    extract_actual_bands_from_umm(umm).get("bands", [])
                ),
            }
        ],
    }
