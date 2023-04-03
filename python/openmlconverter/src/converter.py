from functools import partial

import dateutil.parser
import langcodes


TABLE_NAME = "table"


def bake(openml_dataset: dict, openml_features: dict) -> dict:
    _ds = partial(_get_field, json_dict=openml_dataset)  # get field from openml_dataset

    croissant = {
        "@context": {"@vocab": "https://schema.org/", "ml": "http://mlcommons.org/schema/"},
        "@type": "Dataset",
        "@language": "en",
        "name": _ds(field="name", required=True),
        "description": _ds(field="description", required=True),
        "version": _ds(field="version"),
        # TODO: discuss. Multiple creators not supported  by schema.org, so joining them with "and"
        "creator": _ds(field="creator", transform=lambda v: _person(" and ".join(v) if isinstance(
            v, list) else v)),
        "contributor": _ds(field="contributor", transform=_person),
        "dateCreated": _ds(field="upload_date", transform=dateutil.parser.parse),
        "dateModified": _ds(field="processing_date", transform=dateutil.parser.parse),
        "inLanguage": _ds(field="language", transform=lambda v: langcodes.find(v).language),
        "isAccessibleForFree": True,
        "license": _ds(field="license"),
        "creativeWorkStatus": _ds(field="status"),
        "keywords": _ds(field="tag"),
        "citation": _ds(field="citation"),
        "sameAs": _ds(field="original_data_url"),
        "url": f"https://www.openml.org/api/v1/json/data/{_ds(field='id')}",
        "distribution": [
            _distribution(url) for url in sorted({_ds(field="minio_url"), _ds(field="url"), _ds(field="parquet_url")})
        ],
        "recordSet": [
            {
                "name": TABLE_NAME,
                "@type": "ml:RecordSet",
                "source": f"#{{{TABLE_NAME}}}",
                "key": _row_identifier(openml_features),
                "field": [
                    {
                        "name": feat["name"],
                        "@type": "ml:Field",
                        "dataType": _datatype(feat["data_type"], feat.get("nominal_value", None)),
                        "source": f"#{{{feat['name']}}}"
                    }
                    for feat in openml_features
                ]
            }
        ]
    }
    _remove_none_values(croissant)
    for recordSet in croissant["recordSet"]:
        _remove_none_values(recordSet)
    return croissant


def _get_field(json_dict, field: str, transform=None, required=False):
    """
    Convenience function. Get field and optionally perform the transformation. If field does not
    exist, throw an error if the field is  required, otherwise return None.
    """
    if field not in json_dict:
        if required:
            raise ValueError(f"Required field {field} missing.")
        return None
    val = json_dict[field]
    if transform is not None:
        return transform(val)
    return val


def _person(name: str) -> dict | None:
    if name is None or name == "":
        return None
    return {"@context": "https://schema.org", "@type": "Person", "name": name}


def _distribution(url: str) -> dict | None:
    if url is None:
        return None

    if url.endswith(".arff"):
        mimetype = "text/plain"  # No official arff mimetype exists
    elif url.endswith(".pq"):
        mimetype = "application/vnd.apache.parquet"  # TODO: Not an official mimetype yet
        # see https://issues.apache.org/jira/browse/PARQUET-1889
    else:
        raise ValueError(f"Unrecognized file extension in url: {url}")
    return {
        "name": TABLE_NAME,
        "@type": "FileObject",
        "contentUrl": url,
        "encodingFormat": mimetype
        # TODO: add the md5 hash? But where? 'sha256' is in the Google Docs file, but not official?
    }


def _datatype(value: str, nominal_value: list[str] | None) -> str:
    if nominal_value is not None:
        if set(nominal_value) == {"TRUE", "FALSE"} or set(nominal_value) == {"0", "1"}:
            return "boolean"
    d_type = {
        "numeric": "number",
        "string": "string",
        "nominal": "string",  # TODO: where to add the possible values?
        # see https://www.w3.org/TR/tabular-data-primer/datatypes.png
    }.get(value, None)
    if d_type is None:
        raise ValueError(f"Unknown datatype: {value}")
    return d_type


def _row_identifier(openml_features):
    row_identifiers = [f"#{{{f['name']}}}" for f in openml_features
                       if f["is_row_identifier"] == "true"]
    if len(row_identifiers) > 2:
        return row_identifiers
    elif len(row_identifiers) == 1:
        return row_identifiers[0]
    return None


def _remove_none_values(dct_: dict):
    for key, value in list(dct_.items()):
        if isinstance(value, dict):
            _remove_none_values(value)
        elif value is None:
            del dct_[key]
        elif isinstance(value, list) and len(value) == 0:
            del dct_[key]
