"""NASA POWER T2M (2-meter air temperature) Data Converter Module.

This module provides functionality for converting NASA POWER 2-meter air temperature
data to GeoCroissant format. It specializes in handling T2M measurements and their
associated metadata, making the data accessible within the GeoCroissant framework.
"""

import hashlib
import json
from typing import Any, Dict

import xarray as xr


class T2MCroissantConverter:
    """NASA POWER T2M data for the year 2020 to GeoCroissant format."""

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
        self.ds_2020 = None
        self.variable = "T2M"
        self.year = 2020

    def load_dataset(self) -> bool:
        """Load the full dataset from S3 and subset T2M for 2020."""
        try:
            print(f"Loading NASA POWER dataset from {self.zarr_url}...")
            self.ds_full = xr.open_zarr(self.zarr_url, storage_options={"anon": True})
            # Subset for 2020 only
            self.ds_2020 = self.ds_full.sel(
                time=slice("{self.year}-01-01", "{self.year}-12-31")
            )
            print("Dataset loaded successfully!")
            print("  - Dimensions: {self.ds_2020.dims}")
            print("  - T2M shape: {self.ds_2020[self.variable].shape}")
            print(
                "  - Time range: {self.ds_2020.time.values[0]} to"
                " {self.ds_2020.time.values[-1]}"
            )
            return True
        except Exception:
            print("Error loading dataset: {e}")
            return False

    def generate_checksum(self, content: str) -> str:
        """Generate MD5 checksum for content."""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def create_croissant_metadata(
        self, output_file: str = "T2M_2020_croissant.json"
    ) -> Dict[str, Any]:
        """Create GeoCroissant metadata for the T2M 2020 data.

        Args:
            output_file: Output file path.

        Returns:
            dict: GeoCroissant metadata.
        """
        if self.ds_2020 is None:
            print("Error: No 2020 data available. Call load_dataset() first.")
            return {}

        t2m_data = self.ds_2020[self.variable]
        var_metadata = {
            "long_name": t2m_data.attrs.get("long_name", "Temperature at 2 Meters"),
            "units": t2m_data.attrs.get("units", "C"),
            "valid_min": t2m_data.attrs.get("valid_min", -125.0),
            "valid_max": t2m_data.attrs.get("valid_max", 80.0),
            "standard_name": t2m_data.attrs.get(
                "standard_name", "Temperature_at_2_Meters"
            ),
            "definition": t2m_data.attrs.get(
                "definition",
                "The average air (dry bulb) temperature at 2 meters above the surface"
                " of the earth.",
            ),
            "status": t2m_data.attrs.get("status", "official"),
            "significant_digits": t2m_data.attrs.get("significant_digits", 2),
            "cell_methods": t2m_data.attrs.get("cell_methods", "time: mean"),
        }

        # Calculate sizes
        _ = self.ds_2020.nbytes / 1e9
        t2m_size_mb = t2m_data.nbytes / 1e6
        _ = t2m_size_mb / 12

        # Generate checksum
        hash_input = f"{self.zarr_url}{self.year}{self.variable}"
        md5_hash = self.generate_checksum(hash_input)

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
            "name": "NASA-POWER-T2M-Monthly-Time-Series-2020",
            "alternateName": ["nasa-power-t2m-2020", "POWER-T2M-2020"],
            "description": (
                "Monthly time series of Temperature at 2 Meters (T2M) for 2020 from"
                " NASA POWER dataset. This dataset provides global temperature data at"
                " 0.5° latitude and 0.625° longitude resolution with monthly temporal"
                " resolution."
            ),
            "conformsTo": "http://mlcommons.org/croissant/1.0",
            "version": "1.0.0",
            "url": "https://power.larc.nasa.gov",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "creator": {
                "@type": "Organization",
                "name": "NASA Langley Research Center (LaRC)",
                "url": "https://power.larc.nasa.gov",
            },
            "keywords": [
                "Temperature",
                "Climate",
                "NASA",
                "POWER",
                "2020",
                "Monthly",
                "Geospatial",
                "Earth Science",
                "Meteorology",
                "Climate Data",
            ],
            "citeAs": (
                "NASA POWER Project. Prediction Of Worldwide Energy Resource (POWER)"
                " Project. NASA Langley Research Center."
            ),
            "geocr:BoundingBox": [
                self.ds_full.attrs.get("geospatial_lon_min", -180.0),
                self.ds_full.attrs.get("geospatial_lat_min", -90.0),
                self.ds_full.attrs.get("geospatial_lon_max", 180.0),
                self.ds_full.attrs.get("geospatial_lat_max", 90.0),
            ],
            "geocr:temporalExtent": {
                "startDate": "2020-01-01T00:00:00Z",
                "endDate": "2020-12-31T23:59:59Z",
            },
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
                    "@id": "zarr-store-t2m-2020",
                    "name": "zarr-store-t2m-2020",
                    "description": (
                        "Zarr datacube for NASA POWER T2M data for the year 2020"
                    ),
                    "contentUrl": self.zarr_url,
                    "encodingFormat": "application/x-zarr",
                    "md5": md5_hash,
                }
            ],
            "datePublished": "2020-12-31",
            "recordSet": [
                {
                    "@type": "cr:RecordSet",
                    "@id": "nasa_power_t2m_2020",
                    "name": "nasa_power_t2m_2020",
                    "description": "NASA POWER T2M climate data for the year 2020",
                    "field": [],
                }
            ],
        }

        # Add fields
        fields = croissant["recordSet"][0]["field"]

        # Add coordinate fields
        for coord_name, coord in self.ds_2020.coords.items():
            coord_field = {
                "@type": "cr:Field",
                "@id": "nasa_power_t2m_2020/{coord_name}",
                "name": "nasa_power_t2m_2020/{coord_name}",
                "description": "Coordinate: {coord_name}",
                "dataType": "sc:Float" if coord.dtype.kind == "" else "sc:Date",
                "source": {
                    "fileObject": {"@id": "zarr-store-t2m-2020"},
                    "extract": {"jsonPath": "$.{coord_name}"},
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

        # Main T2M field
        main_field = {
            "@type": "cr:Field",
            "@id": "nasa_power_t2m_2020/T2M",
            "name": "nasa_power_t2m_2020/T2M",
            "description": var_metadata["long_name"],
            "dataType": "sc:Float",
            "source": {
                "fileObject": {"@id": "zarr-store-t2m-2020"},
                "extract": {"jsonPath": "$.T2M"},
            },
            "geocr:dataShape": list(t2m_data.shape),
            "geocr:validRange": {
                "min": float(var_metadata["valid_min"]),
                "max": float(var_metadata["valid_max"]),
            },
            "geocr:units": var_metadata["units"],
            "geocr:standardName": var_metadata["standard_name"],
            "geocr:definition": var_metadata["definition"],
            "geocr:cellMethods": var_metadata["cell_methods"],
        }
        fields.append(main_field)

        # Save metadata
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(croissant, f, indent=2, ensure_ascii=False)

        print("GeoCroissant metadata saved to {output_file}")
        print("Total fields: {len(fields)}")

        return croissant

    def convert(self, output_file: str = "T2M_2020_croissant.json") -> Dict[str, Any]:
        """Complete conversion pipeline for T2M 2020.

        Args:
            output_file: Output file path.

        Returns:
            dict: GeoCroissant metadata.
        """
        print(f"Starting conversion for T2M {self.year}...")
        if not self.load_dataset():
            return {}

        metadata = self.create_croissant_metadata(output_file)
        print("Conversion completed successfully!")
        return metadata


# Example usage in notebook:
converter = T2MCroissantConverter()
metadata = converter.convert()
