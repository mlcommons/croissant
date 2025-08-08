import argparse
import json
from mlcroissant import Dataset as CroissantDataset
import pytdml
import pytdml.io
from pytdml.type.extended_types import EOTrainingDataset, AI_EOTrainingData, AI_PixelLabel, MD_Band, AI_EOTask

def get_distribution_from_json(json_path):
    with open(json_path) as f:
        croissant = json.load(f)
    return croissant.get("distribution", [])

def get_variable_measured_from_json(json_path):
    with open(json_path) as f:
        croissant = json.load(f)
    return croissant.get("variableMeasured", [])

def convert_geocroissant_to_tdml_objectmodel(geocroissant_path, tdml_output_path):
    # Use mlcroissant to parse and validate the GeoCroissant JSON
    croissant = CroissantDataset(geocroissant_path)
    meta = croissant.metadata

    # Use direct JSON for distribution and variableMeasured
    distribution = get_distribution_from_json(geocroissant_path)
    variable_measured = get_variable_measured_from_json(geocroissant_path)

    # Extract fields from mlcroissant object
    identifier = getattr(meta, 'id', None) or getattr(meta, 'uuid', None) or ''
    name = getattr(meta, 'name', '') or ''
    description = getattr(meta, 'description', '')
    if not description:
        description = "No description provided."
    license_ = getattr(meta, 'license', '')
    if isinstance(license_, list):
        license_ = license_[0] if license_ else ''
    providers = getattr(meta, 'creators', [])
    # Fix created_time and updated_time to always be valid date strings
    created_time = getattr(meta, 'created_time', '') or getattr(meta, 'date_created', '') or ''
    updated_time = getattr(meta, 'updated_time', '') or getattr(meta, 'date_modified', '') or ''
    if not created_time:
        created_time = "2025-07-17"
    if not updated_time:
        updated_time = "2025-07-17"
    version = getattr(meta, 'version', '') or ''
    spatial_coverage = getattr(meta, 'spatial_coverage', None)

    # Debug print for variable_measured
    print("variable_measured raw:", variable_measured)
    print("variable_measured types:", [type(v) for v in variable_measured])

    # Build classes (as dicts) and bands (as MD_Band) with robust field access
    classes = []
    bands = []
    for v in variable_measured:
        print("Entry:", v)
        if hasattr(v, "__dict__"):
            print("Entry __dict__:", v.__dict__)
        # Robustly get name, description, and unitText/unit_text
        name_v = v.get('name', '') if isinstance(v, dict) else ''
        description_v = v.get('description', '') if isinstance(v, dict) else ''
        unit_text = v.get('unitText', None) if isinstance(v, dict) else None
        if unit_text:
            bands.append(MD_Band(description=name_v, units=unit_text))
        else:
            classes.append({"key": name_v, "value": description_v})

    # Debug print for classes
    print("Extracted classes:", classes)
    print("Number of classes:", len(classes))

    # Build data and labels
    data = []
    for i in range(0, len(distribution), 2):
        img_entry = distribution[i]
        mask_entry = distribution[i+1] if i+1 < len(distribution) else None
        img_url = img_entry.get('contentUrl', '') if isinstance(img_entry, dict) else ''
        data_id = f"data_{i//2}"
        labels = []
        if mask_entry:
            mask_url = mask_entry.get('contentUrl', '') if isinstance(mask_entry, dict) else ''
            mask_format = mask_entry.get('encodingFormat', 'image/tiff') if isinstance(mask_entry, dict) else 'image/tiff'
            labels = [AI_PixelLabel(
                type="AI_PixelLabel",
                image_url=[mask_url],
                image_format=[mask_format],
                class_=""
            )]
        data.append(AI_EOTrainingData(
            type="AI_EOTrainingData",
            id=data_id,
            data_url=[img_url],
            labels=labels
        ))

    # Ensure data is not empty
    if not data:
        raise ValueError("No data entries found. The distribution field may be empty or not parsed correctly.")

    # Build tasks
    tasks = [AI_EOTask(
        type="AI_EOTask",
        id="task_0",
        name="Burn Scar Segmentation",
        description="Semantic segmentation of burn scars in satellite imagery.",
        input_type="image",
        output_type="mask",
        taskType="segmentation"
    )]

    # Build extent
    extent = None
    if spatial_coverage and hasattr(spatial_coverage, 'geo'):
        geo = spatial_coverage.geo
        coords = geo.get('coordinates', [[]])[0] if isinstance(geo, dict) else getattr(geo, 'coordinates', [[]])[0]
        if coords:
            min_x = min(c[0] for c in coords)
            min_y = min(c[1] for c in coords)
            max_x = max(c[0] for c in coords)
            max_y = max(c[1] for c in coords)
            extent = [min_x, min_y, max_x, max_y]

    # Debug print of TDML object arguments
    print("TDML object args:", {
        "type": "AI_EOTrainingDataset",
        "id": identifier,
        "name": name,
        "description": description,
        "license": license_,
        "providers": providers,
        "created_time": created_time,
        "updated_time": updated_time,
        "version": version,
        "tasks": tasks,
        "classes": classes,
        "bands": bands,
        "data": data,
        "extent": extent,
        "amount_of_training_data": len(data),
        "number_of_classes": len(classes)
    })

    # Create EOTrainingDataset object
    tdml_obj = EOTrainingDataset(
        type="AI_EOTrainingDataset",
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
        extent=extent,
        amount_of_training_data=len(data),
        number_of_classes=len(classes)
    )

    # Write TDML JSON using pytdml
    pytdml.io.write_to_json(tdml_obj, tdml_output_path)
    print(f"TDML file written to {tdml_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert GeoCroissant JSON to TDML JSON using mlcroissant and pytdml object model.")
    parser.add_argument("geocroissant_path", help="Path to input GeoCroissant JSON")
    parser.add_argument("tdml_output_path", help="Path to output TDML JSON")
    args = parser.parse_args()
    convert_geocroissant_to_tdml_objectmodel(args.geocroissant_path, args.tdml_output_path) 
