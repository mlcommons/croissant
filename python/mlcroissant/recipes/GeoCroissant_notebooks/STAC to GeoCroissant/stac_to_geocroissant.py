#stac_to_geocroissant-DATASET_LEVEL.py
import json
from datetime import datetime
import re

def sanitize_name(name):
    return re.sub(r"[^a-zA-Z0-9_\-]", "-", name)

def ensure_semver(version):
    if not version:
        return "1.0.0"
    if version.startswith("v"):
        version = version[1:]
    parts = version.split(".")
    if len(parts) == 2:
        parts.append("0")
    return ".".join(parts[:3])

def stac_to_geocroissant(stac_dict):
    dataset_id = stac_dict.get("id")
    name = sanitize_name(stac_dict.get("title", dataset_id or "UnnamedDataset"))
    version = ensure_semver(stac_dict.get("version", "1.0.0"))

    croissant = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "geocr": "http://mlcommons.org/geocroissant/",
            "dct": "http://purl.org/dc/terms/",
            "sc": "https://schema.org/",
            "citeAs": "cr:citeAs",
            "column": "cr:column",
            "conformsTo": "dct:conformsTo",
            "data": {"@id": "cr:data", "@type": "@json"},
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
            "md5": {"@id": "cr:md5", "@type": "sc:Text"},
            "sha256": {"@id": "cr:sha256", "@type": "sc:Text"},
            "parentField": "cr:parentField",
            "path": "cr:path",
            "personalSensitiveInformation": "cr:personalSensitiveInformation",
            "recordSet": "cr:recordSet",
            "references": "cr:references",
            "regex": "cr:regex",
            "repeated": "cr:repeated",
            "replace": "cr:replace",
            "separator": "cr:separator",
            "source": "cr:source",
            "subField": "cr:subField",
            "transform": "cr:transform"
        },
        "@type": "Dataset",
        "@id": dataset_id,
        "name": name,
        "description": stac_dict.get("description", ""),
        "version": version,
        "license": stac_dict.get("license", "CC-BY-4.0"),
        "conformsTo": "http://mlcommons.org/croissant/1.0"
    }

    if "sci:citation" in stac_dict:
        croissant["citeAs"] = stac_dict["sci:citation"]
        croissant["citation"] = stac_dict["sci:citation"]

    if stac_dict.get("providers"):
        provider = stac_dict["providers"][0]
        croissant["creator"] = {
            "@type": "Organization",
            "name": provider.get("name", "Unknown"),
            "url": provider.get("url", "")
        }

    # Handle 'self' URL
    for link in stac_dict.get("links", []):
        if link.get("rel") == "self":
            croissant["url"] = link.get("href")
            break

    # Handle other STAC references
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
            "http://www.opengis.net/def/rel/ogc/1.0/queryables": "Queryables"
        }

        references.append({
            "@type": "CreativeWork",
            "url": href,
            "name": name_map.get(rel, rel),
            "encodingFormat": link.get("type", "application/json")
        })

    if references:
        croissant["references"] = references

    # Spatial and temporal extent
    spatial = stac_dict.get("extent", {}).get("spatial", {}).get("bbox")
    if spatial:
        croissant["geocr:BoundingBox"] = spatial[0]

    temporal = stac_dict.get("extent", {}).get("temporal", {}).get("interval")
    if temporal and temporal[0]:
        start, end = temporal[0][0], temporal[0][1]
        croissant["dct:temporal"] = {"startDate": start, "endDate": end}
        croissant["datePublished"] = start
    else:
        croissant["datePublished"] = datetime.utcnow().isoformat() + "Z"

    # Asset-level distribution
    croissant["distribution"] = []
    for key, asset in stac_dict.get("assets", {}).items():
        file_object = {
            "@type": "cr:FileObject",
            "@id": key,
            "name": key,
            "description": asset.get("description", asset.get("title", "")),
            "contentUrl": asset.get("href"),
            "encodingFormat": asset.get("type", "application/octet-stream"),
            "sha256": "https://github.com/mlcommons/croissant/issues/80",
            "md5": "https://github.com/mlcommons/croissant/issues/80"
        }

        if "checksum:multihash" in asset:
            file_object["sha256"] = asset["checksum:multihash"]
        elif "file:checksum" in asset:
            file_object["sha256"] = asset["file:checksum"]
        if "checksum:md5" in asset:
            file_object["md5"] = asset["checksum:md5"]

        croissant["distribution"].append(file_object)

    # item_assets as fileSet templates
    if "item_assets" in stac_dict:
        croissant["fileSet"] = []
        for key, asset in stac_dict["item_assets"].items():
            file_obj = {
                "@type": "cr:FileObject",
                "@id": key,
                "name": key,
                "description": asset.get("description", asset.get("title", "")),
                "encodingFormat": asset.get("type", "application/octet-stream"),
                "sha256": "https://github.com/mlcommons/croissant/issues/80",
                "md5": "https://github.com/mlcommons/croissant/issues/80"
            }
            file_set = {
                "@type": "cr:FileSet",
                "name": f"Template for {key}",
                "includes": [file_obj]
            }
            croissant["fileSet"].append(file_set)

    if "renders" in stac_dict:
        croissant["geocr:visualizations"] = stac_dict["renders"]

    if "summaries" in stac_dict:
        croissant["geocr:summaries"] = stac_dict["summaries"]

    if "stac_extensions" in stac_dict:
        croissant["geocr:stac_extensions"] = stac_dict["stac_extensions"]
    if "stac_version" in stac_dict:
        croissant["geocr:stac_version"] = stac_dict["stac_version"]

    if "deprecated" in stac_dict:
        croissant["isLiveDataset"] = not stac_dict["deprecated"]

    # Report unmapped fields
    mapped_keys = {
        "id", "type", "links", "title", "assets", "extent",
        "license", "version", "providers", "description", "sci:citation",
        "renders", "summaries", "stac_extensions", "stac_version", "deprecated", "item_assets"
    }
    extra_fields = {k: v for k, v in stac_dict.items() if k not in mapped_keys}
    print("\n\033[1mUnmapped STAC Fields:\033[0m")
    if extra_fields:
        for k, v in extra_fields.items():
            print(f"- {k}: {type(v).__name__}")
    else:
        print("None ")

    return croissant

# === Main Runner ===
if __name__ == "__main__":
    # Load STAC Collection JSON
    with open("stac.json") as f:
        stac_data = json.load(f)

    # Convert to GeoCroissant
    croissant_json = stac_to_geocroissant(stac_data)

    # Save GeoCroissant JSON-LD
    with open("croissant.json", "w") as f:
        json.dump(croissant_json, f, indent=2)

    print("\nGeoCroissant conversion complete. Output saved to 'croissant.json'")
