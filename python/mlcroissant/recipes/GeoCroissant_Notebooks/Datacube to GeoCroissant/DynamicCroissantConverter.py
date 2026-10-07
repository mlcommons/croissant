"""Dynamic Converter for NASA POWER Data.

This module provides functionality for converting NASA POWER (Prediction of Worldwide Energy
Resources) data to GeoCroissant format. It allows users to specify year and month to
generate metadata for specific time periods, and handles temporal data from the MERRA2
dataset stored in Zarr format.
"""

import calendar
import hashlib
import json
from typing import Any, Dict, Optional

import xarray as xr


class DynamicCroissantConverter:
    """Dynamic converter for NASA POWER data to GeoCroissant format."""

    def __init__(
        self,
        zarr_url: str = "s3://nasa-power/merra2/temporal/power_merra2_monthly_temporal_utc.zarr/",
    ):
        """Initialize the converter with the Zarr URL.

        Args:
            zarr_url: URL to the NASA POWER Zarr dataset.
        """
        self.zarr_url = zarr_url
        self.ds_full = None
        self.ds_subset = None

    def load_dataset(self) -> bool:
        """Load the full dataset from S3."""
        try:
            print(f"Loading NASA POWER dataset from {self.zarr_url}...")
            self.ds_full = xr.open_zarr(self.zarr_url, storage_options={"anon": True})
            print("Dataset loaded successfully!")
            print(f"  - Dimensions: {self.ds_full.dims}")
            print(f"  - Total size: {self.ds_full.nbytes / 1e9:.2f} GB")
            print(f"  - Variables: {len(self.ds_full.data_vars)}")
            print(
                f"  - Time range: {self.ds_full.time.values[0]} to"
                f" {self.ds_full.time.values[-1]}"
            )
            return True
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return False

    def get_available_variables(self) -> Dict[str, Any]:
        """Get list of available variables with their metadata."""
        if not self.ds_full:
            return {}

        variables = {}
        for var_name, var in self.ds_full.data_vars.items():
            variables[var_name] = {
                "shape": list(var.shape),
                "dimensions": list(var.dims),
                "dtype": str(var.dtype),
                "size_mb": float(var.nbytes / 1e6),
                "attributes": (
                    dict(var.attrs) if hasattr(var, "attrs") and var.attrs else {}
                ),
            }
        return variables

    def subset_data(
        self, year: int, month: Optional[int] = None, variables: Optional[list] = None
    ) -> bool:
        """Subset the data for specific year/month and variables.

        Args:
            year: Year to extract (e.g., 2020).
            month: Month to extract (1-12), if None extracts entire year.
            variables: List of variable names to include, if None includes all.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.ds_full:
            print("Error: Dataset not loaded. Call load_dataset() first.")
            return False

        try:
            # Create time slice
            if month:
                # Single month
                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
                time_slice = slice(start_date, end_date)
                print(f"Extracting data for {calendar.month_name[month]} {year}...")
            else:
                # Entire year
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                time_slice = slice(start_date, end_date)
                print(f"Extracting data for entire year {year}...")

            # Subset by time
            self.ds_subset = self.ds_full.sel(time=time_slice)

            # Subset by variables if specified
            if variables:
                available_vars = [
                    var for var in variables if var in self.ds_subset.data_vars
                ]
                if available_vars:
                    self.ds_subset = self.ds_subset[available_vars]
                    print(f"  - Selected variables: {available_vars}")
                else:
                    print(
                        "  - Warning: None of the specified variables found. Using all"
                        " variables."
                    )

            print(f"  - Subset dimensions: {self.ds_subset.dims}")
            print(f"  - Subset size: {self.ds_subset.nbytes / 1e9:.2f} GB")
            print(f"  - Variables in subset: {len(self.ds_subset.data_vars)}")

            return True

        except Exception as e:
            print(f"Error subsetting data: {e}")
            return False

    def generate_checksum(self, content: str) -> str:
        """Generate MD5 checksum for content."""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def create_croissant_metadata(
        self, year: int, month: Optional[int] = None, output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create GeoCroissant metadata for the subset data.

        Args:
            year: Year of the data.
            month: Month of the data (if None, entire year).
            output_file: Output file path (if None, auto-generated).

        Returns:
            dict: GeoCroissant metadata.
        """
        if not self.ds_subset:
            print("Error: No subset data available. Call subset_data() first.")
            return {}

        # Generate output filename if not provided
        if not output_file:
            if month:
                output_file = f"NASA_POWER_{year}_{month:02d}_croissant.json"
            else:
                output_file = f"NASA_POWER_{year}_croissant.json"

        # Generate checksum
        hash_input = f"{self.zarr_url}{year}{month if month else 'year'}"
        md5_hash = self.generate_checksum(hash_input)

        # Create time extent
        if month:
            start_date = f"{year}-{month:02d}-01T00:00:00Z"
            end_date = (
                f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}T23:59:59Z"
            )
            _ = "P1M"
            _ = "P1M"
            description_suffix = f"for {calendar.month_name[month]} {year}"
        else:
            start_date = f"{year}-01-01T00:00:00Z"
            end_date = f"{year}-12-31T23:59:59Z"
            _ = "P1M"
            _ = "P1Y"
            description_suffix = f"for the year {year}"

        # Create GeoCroissant metadata
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
            "name": f"NASA-POWER-Climate-Data-{description_suffix.replace(' ', '-')}",
            "alternateName": [
                f"nasa-power-{year}-{month:02d}" if month else f"nasa-power-{year}",
                f"POWER-{year}-{month:02d}" if month else f"POWER-{year}",
            ],
            "description": (
                f"NASA POWER climate dataset {description_suffix}. This dataset"
                " provides global climate data at 0.5° latitude and 0.625° longitude"
                " resolution with monthly temporal resolution."
            ),
            "conformsTo": "http://mlcommons.org/croissant/1.0",
            "version": "1.0.0",
            "creator": {
                "@type": "Organization",
                "name": "NASA Langley Research Center (LaRC)",
                "url": "https://power.larc.nasa.gov",
            },
            "url": "https://power.larc.nasa.gov",
            "keywords": [
                "Climate",
                "NASA",
                "POWER",
                str(year),
                "Monthly" if month else "Annual",
                "Geospatial",
                "Earth Science",
                "Meteorology",
                "Climate Data",
            ],
            "citeAs": (
                "NASA POWER Project. Prediction Of Worldwide Energy Resource (POWER)"
                " Project. NASA Langley Research Center."
            ),
            "datePublished": (
                f"{year}-12-31"
                if not month
                else f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
            ),
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "geocr:BoundingBox": [
                self.ds_full.attrs.get("geospatial_lon_min", -180.0),
                self.ds_full.attrs.get("geospatial_lat_min", -90.0),
                self.ds_full.attrs.get("geospatial_lon_max", 180.0),
                self.ds_full.attrs.get("geospatial_lat_max", 90.0),
            ],
            "geocr:temporalExtent": {"startDate": start_date, "endDate": end_date},
            "geocr:spatialResolution": "0.5° lat × 0.625° lon",
            "geocr:coordinateReferenceSystem": "EPSG:4326",
            "geocr:mlTask": {
                "@type": "geocr:Regression",
                "taskType": "climate_prediction",
                "evaluationMetric": "RMSE",
                "applicationDomain": "climate_monitoring",
            },
            "distribution": [
                {
                    "@type": "cr:FileObject",
                    "@id": (
                        f"zarr-store-{year}-{month:02d}"
                        if month
                        else f"zarr-store-{year}"
                    ),
                    "name": (
                        f"zarr-store-{year}-{month:02d}"
                        if month
                        else f"zarr-store-{year}"
                    ),
                    "description": (
                        f"Zarr datacube for NASA POWER data {description_suffix}"
                    ),
                    "contentUrl": self.zarr_url,
                    "encodingFormat": "application/x-zarr",
                    "md5": md5_hash,
                }
            ],
            "recordSet": [
                {
                    "@type": "cr:RecordSet",
                    "@id": (
                        f"nasa_power_data_{year}_{month:02d}"
                        if month
                        else f"nasa_power_data_{year}"
                    ),
                    "name": (
                        f"nasa_power_data_{year}_{month:02d}"
                        if month
                        else f"nasa_power_data_{year}"
                    ),
                    "description": f"NASA POWER climate data {description_suffix}",
                    "field": [],
                }
            ],
        }

        # Add fields for each variable
        fields = croissant["recordSet"][0]["field"]

        # Add coordinate fields
        for coord_name, coord in self.ds_subset.coords.items():
            coord_field = {
                "@type": "cr:Field",
                "@id": (
                    f"nasa_power_data_{year}_{month:02d}/{coord_name}"
                    if month
                    else f"nasa_power_data_{year}/{coord_name}"
                ),
                "name": (
                    f"nasa_power_data_{year}_{month:02d}/{coord_name}"
                    if month
                    else f"nasa_power_data_{year}/{coord_name}"
                ),
                "description": f"Coordinate: {coord_name}",
                "dataType": "sc:Float" if coord.dtype.kind == "f" else "sc:Date",
                "source": {
                    "fileObject": {
                        "@id": (
                            f"zarr-store-{year}-{month:02d}"
                            if month
                            else f"zarr-store-{year}"
                        )
                    },
                    "extract": {"jsonPath": f"$.{coord_name}"},
                },
                "geocr:dataShape": list(coord.shape),
                "geocr:validRange": (
                    {
                        "min": (
                            -90.0
                            if coord_name == "lat"
                            else -180.0 if coord_name == "lon" else None
                        ),
                        "max": (
                            90.0
                            if coord_name == "lat"
                            else 180.0 if coord_name == "lon" else None
                        ),
                    }
                    if coord_name in ["lat", "lon"]
                    else None
                ),
                "geocr:units": (
                    "degrees_north"
                    if coord_name == "lat"
                    else "degrees_east" if coord_name == "lon" else None
                ),
            }
            # Remove None values
            coord_field = {k: v for k, v in coord_field.items() if v is not None}
            fields.append(coord_field)

        # Add data variable fields
        for var_name, var in self.ds_subset.data_vars.items():
            var_field = {
                "@type": "cr:Field",
                "@id": (
                    f"nasa_power_data_{year}_{month:02d}/{var_name}"
                    if month
                    else f"nasa_power_data_{year}/{var_name}"
                ),
                "name": (
                    f"nasa_power_data_{year}_{month:02d}/{var_name}"
                    if month
                    else f"nasa_power_data_{year}/{var_name}"
                ),
                "description": var.attrs.get("long_name", var_name),
                "dataType": "sc:Float",
                "source": {
                    "fileObject": {
                        "@id": (
                            f"zarr-store-{year}-{month:02d}"
                            if month
                            else f"zarr-store-{year}"
                        )
                    },
                    "extract": {"jsonPath": f"$.{var_name}"},
                },
                "geocr:dataShape": list(var.shape),
                "geocr:validRange": (
                    {
                        "min": float(var.attrs.get("valid_min", 0.0)),
                        "max": float(var.attrs.get("valid_max", 100.0)),
                    }
                    if var.attrs.get("valid_min") is not None
                    and var.attrs.get("valid_max") is not None
                    else None
                ),
                "geocr:units": var.attrs.get("units", ""),
                "geocr:standardName": var.attrs.get("standard_name", ""),
                "geocr:definition": var.attrs.get("definition", ""),
                "geocr:cellMethods": var.attrs.get("cell_methods", ""),
            }
            # Remove None values
            var_field = {k: v for k, v in var_field.items() if v is not None}
            fields.append(var_field)

        # Save metadata
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(croissant, f, indent=2, ensure_ascii=False)

        print(f"GeoCroissant metadata saved to {output_file}")
        print(f"Total fields: {len(fields)}")

        return croissant

    def convert(
        self,
        year: int,
        month: Optional[int] = None,
        variables: Optional[list] = None,
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Complete conversion pipeline.

        Args:
            year: Year to convert.
            month: Month to convert (1-12), if None converts entire year.
            variables: List of variables to include, if None includes all.
            output_file: Output file path, if None auto-generated.

        Returns:
            dict: GeoCroissant metadata.
        """
        print(
            "Starting conversion for"
            f" {calendar.month_name[month] if month else 'year'} {year}..."
        )

        # Load dataset
        if not self.load_dataset():
            return {}

        # Subset data
        if not self.subset_data(year, month, variables):
            return {}

        # Generate metadata
        metadata = self.create_croissant_metadata(year, month, output_file)

        print("Conversion completed successfully!")
        return metadata
