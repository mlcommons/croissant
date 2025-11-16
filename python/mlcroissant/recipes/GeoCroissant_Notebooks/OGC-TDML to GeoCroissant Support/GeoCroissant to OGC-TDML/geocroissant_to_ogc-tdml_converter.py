"""GeoCroissant to OGC Training Data Markup Language (TDML) converter.

This module provides functionality to convert GeoCroissant format metadata to OGC-TDML format,
using the pytdml library for TDML schema validation and output generation.
"""

import argparse
import json
from datetime import datetime

from pytdml.io import write_to_json

# Import pytdml library with proper structure
from pytdml.type import (
    AI_EOTask,
    AI_EOTrainingData,
    AI_PixelLabel,
    AI_SceneLabel,
    EOTrainingDataset,
    MD_Band,
    MD_Identifier,
    NamedValue,
)


def convert_geocroissant_to_tdml(geocroissant_path, tdml_output_path):
    """Convert GeoCroissant JSON to OGC-TDML JSON format using pytdml library.

    Args:
        geocroissant_path: Path to the input GeoCroissant JSON file.
        tdml_output_path: Path where the converted TDML JSON will be saved.

    Returns:
        None. The converted file is written to tdml_output_path.
    """
    try:
        # Load the GeoCroissant JSON directly
        with open(geocroissant_path, "r") as f:
            croissant_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("GeoCroissant file not found: {geocroissant_path}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in GeoCroissant file: {e}")

    # Extract basic metadata with proper fallbacks
    identifier = (
        croissant_data.get("@id", "")
        or croissant_data.get("id", "")
        or "hls_burn_scars_dataset"
    )
    name = croissant_data.get("name", "HLS_Burn_Scars")
    description = croissant_data.get("description", "")
    if not description:
        description = "No description provided."

    # Extract license with proper handling
    license_ = croissant_data.get("license", "")
    if isinstance(license_, list):
        license_ = license_[0] if license_ else ""
    if not license_:
        license_ = "https://creativecommons.org/licenses/by/4.0/"

    # Extract providers/creators with improved handling
    providers = []
    creators = croissant_data.get("creator", [])
    if isinstance(creators, list):
        for creator in creators:
            if isinstance(creator, dict):
                provider_name = creator.get("name", "")
                if provider_name:
                    providers.append(provider_name)
            elif isinstance(creator, str):
                providers.append(creator)
    elif isinstance(creators, dict):
        provider_name = creators.get("name", "")
        if provider_name:
            providers.append(provider_name)

    # Ensure we have at least one provider
    if not providers:
        providers = ["IBM-NASA Prithvi Models Family"]

    # Set default timestamps - try different formats that pytdml might accept
    created_time_str = croissant_data.get("dateCreated", "") or croissant_data.get(
        "created_time", ""
    )
    updated_time_str = croissant_data.get("dateModified", "") or croissant_data.get(
        "updated_time", ""
    )

    # Use simple date format that should work
    if created_time_str:
        try:
            # Try to parse and use a simple format
            if created_time_str.endswith("Z"):
                created_time_str = created_time_str[:-1]
            dt = datetime.fromisoformat(created_time_str)
            created_time = dt.strftime("%Y-%m-%d")
        except ValueError:
            created_time = "2025-01-17"
    else:
        created_time = "2025-01-17"

    if updated_time_str:
        try:
            # Try to parse and use a simple format
            if updated_time_str.endswith("Z"):
                updated_time_str = updated_time_str[:-1]
            dt = datetime.fromisoformat(updated_time_str)
            updated_time = dt.strftime("%Y-%m-%d")
        except ValueError:
            updated_time = "2025-01-17"
    else:
        updated_time = "2025-01-17"

    version = croissant_data.get("version", "1.0.0")

    # Extract recordSet data with improved error handling
    record_sets = croissant_data.get("recordSet", [])
    main_record_set = None

    # Try to find the main record set by name or use the first one
    for rs in record_sets:
        if rs.get("name") == "hls_burn_scars" or "hls" in rs.get("name", "").lower():
            main_record_set = rs
            break

    if not main_record_set and record_sets:
        main_record_set = record_sets[0]  # Use first record set as fallback
        print(
            "Warning: Using first record set '{main_record_set.get('name', 'unknown')}'"
            " as main record set"
        )

    if not main_record_set:
        raise ValueError("Could not find any recordSet in the GeoCroissant data")

    # Extract fields from the main record set
    _ = main_record_set.get("field", [])

    # Extract band information from geocr:sensorCharacteristics
    bands = []
    classes = []

    # Extract band configuration from geocr:sensorCharacteristics
    sensor_characteristics = croissant_data.get("geocr:sensorCharacteristics", [])
    if sensor_characteristics and len(sensor_characteristics) > 0:
        band_config = sensor_characteristics[0].get("bandConfiguration", {})
        if band_config:
            for band_key, band_info in band_config.items():
                if band_key.startswith("band"):
                    band_name = band_info.get("name", "Band {band_key}")
                    _ = band_info.get("wavelength", "")
                    _ = band_info.get("hlsBand", "")

                    band_dict = MD_Band(name=[MD_Identifier(code=band_name)])
                    bands.append(band_dict)

    # Extract class information from geocr:mlTask
    ml_task = croissant_data.get("geocr:mlTask", {})
    if ml_task and "classes" in ml_task:
        class_list = ml_task["classes"]
        if isinstance(class_list, list):
            # Map class names to their expected keys
            class_mapping = {"NotBurned": "0", "BurnScar": "1", "NoData": "-1"}
            for class_name in class_list:
                class_key = class_mapping.get(class_name, str(len(classes)))
                class_dict = NamedValue(key=class_key, value=class_name)
                classes.append(class_dict)

    # If no classes found, use default burn scar classes
    if not classes:
        classes = [
            NamedValue(key="0", value="NotBurned"),
            NamedValue(key="1", value="BurnScar"),
            NamedValue(key="-1", value="NoData"),
        ]
        print(
            "Warning: No classes found in GeoCroissant data, using default burn scar"
            " classes"
        )

    # If no bands found, use default HLS bands
    if not bands:
        bands = [
            MD_Band(name=[MD_Identifier(code="Blue")]),
            MD_Band(name=[MD_Identifier(code="Green")]),
            MD_Band(name=[MD_Identifier(code="Red")]),
            MD_Band(name=[MD_Identifier(code="NIR")]),
            MD_Band(name=[MD_Identifier(code="SW1")]),
            MD_Band(name=[MD_Identifier(code="SW2")]),
        ]
        print("Warning: No bands found in GeoCroissant data, using default HLS bands")

    # Extract data statistics with improved handling
    data_stats = croissant_data.get("geocr:dataStatistics", {})
    total_samples = data_stats.get("totalSamples", 0)
    _ = data_stats.get("trainingSamples", 0)
    _ = data_stats.get("validationSamples", 0)

    # Build tasks with proper pytdml structure
    tasks = [
        AI_EOTask(
            id="task_0",
            name="Burn Scar Segmentation",
            description=(
                "Semantic segmentation of burn scars in satellite imagery using HLS"
                " data."
            ),
            input_type="image",
            output_type="mask",
            task_type="segmentation",
            type="AI_EOTask",
        )
    ]

    # Extract actual file URLs from geocr:fileListing with improved handling
    data = []
    file_listing = croissant_data.get("geocr:fileListing", {})

    if not file_listing:
        print("Warning: No file listing found in GeoCroissant data")
        # Create empty data structure
        data = []
    else:
        images = file_listing.get("images", {})
        annotations = file_listing.get("annotations", {})

        # Process training images and annotations
        train_images = images.get("train", [])
        train_annotations = annotations.get("train", [])

        # Process validation images and annotations
        val_images = images.get("val", [])
        val_annotations = annotations.get("val", [])

        # Combine training and validation data
        all_images = train_images + val_images
        all_annotations = train_annotations + val_annotations

        # Ensure we have matching image and annotation pairs
        min_pairs = min(len(all_images), len(all_annotations))
        if min_pairs == 0:
            print("Warning: No image-annotation pairs found in file listing")
        else:
            # Create data entries with actual URLs
            max_samples = (
                min(50, total_samples) if total_samples > 0 else min(50, min_pairs)
            )

            for i in range(min(max_samples, min_pairs)):
                img_url = all_images[i]
                mask_url = all_annotations[i]

                # Validate URLs
                if not img_url or not mask_url:
                    print("Warning: Skipping data entry {i} due to missing URL")
                    continue

                data_entry = AI_EOTrainingData(
                    id=f"data_{i}",
                    dataURL=[img_url],
                    labels=[
                        AI_SceneLabel(
                            **{"class": "burn_scar_segmentation"}, type="AI_SceneLabel"
                        ),
                        AI_PixelLabel(
                            imageURL=[mask_url],
                            imageFormat=["image/tif"],
                            class_name="pixel_mask",
                            type="AI_PixelLabel",
                        ),
                    ],
                    type="AI_EOTrainingData",
                )
                data.append(data_entry)

    # Build the complete TDML structure with proper pytdml classes
    tdml_structure = EOTrainingDataset(
        id=identifier,
        name=name,
        description=description,
        license=license_,
        providers=providers,
        created_time=created_time,
        updated_time=updated_time,
        version=version,
        tasks=tasks,
        classes=classes,
        bands=bands,
        data=data,
        amount_of_training_data=len(data),
        number_of_classes=len(classes),
        type="AI_EOTrainingDataset",
    )

    # Write the TDML JSON file using pytdml's write_to_json function
    try:
        write_to_json(tdml_structure, tdml_output_path)

        print("TDML file written to {tdml_output_path}")
        print("Converted dataset: {name}")
        print("Total samples: {total_samples}")
        print("Training samples: {training_samples}")
        print("Validation samples: {validation_samples}")
        print("Classes: {len(classes)}")
        print("Bands: {len(bands)}")
        print("Data entries: {len(data)}")

    except Exception:
        raise IOError("Failed to write TDML file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert GeoCroissant JSON to TDML JSON using pytdml library."
    )
    parser.add_argument("geocroissant_path", help="Path to input GeoCroissant JSON")
    parser.add_argument("tdml_output_path", help="Path to output TDML JSON")
    args = parser.parse_args()
    convert_geocroissant_to_tdml(args.geocroissant_path, args.tdml_output_path)
