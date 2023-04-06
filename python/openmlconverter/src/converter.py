import datetime
from functools import partial

import dateutil.parser
import langcodes


def bake(openml_dataset: dict, openml_features: dict) -> dict:
    _ds = partial(_get_field, json_dict=openml_dataset)  # get field from openml_dataset

    distributions = [
        _distribution(name=_ds(field="name"), url=url)
        for url in sorted({_ds(field="minio_url"), _ds(field="url"), _ds(field="parquet_url")})
    ]
    distribution_source = distributions[0]["name"]
    croissant = {
        "@context": {"@vocab": "https://schema.org/", "ml": "http://mlcommons.org/schema/"},
        "@type": "Dataset",
        "@language": "en",
        "name": _ds(field="name", required=True),
        "description": _ds(field="description", required=True),
        "version": _ds(field="version"),
        "creator": _ds(
            field="creator",
            transform=lambda v: [_person(p) for p in v] if isinstance(v, list) else _person(v),
        ),
        "contributor": _ds(field="contributor", transform=_person),
        "dateCreated": _ds(field="upload_date", transform=dateutil.parser.parse),
        "dateModified": _ds(field="processing_date", transform=dateutil.parser.parse),
        "datePublished": _ds(field="collection_date", transform=_lenient_date_parser),
        "inLanguage": _ds(field="language", transform=lambda v: langcodes.find(v).language),
        "isAccessibleForFree": True,
        "license": _ds(field="license"),
        "creativeWorkStatus": _ds(field="status"),
        "keywords": _ds(field="tag"),
        "citation": _ds(field="citation"),
        "sameAs": _ds(field="original_data_url"),
        "url": f"https://www.openml.org/api/v1/json/data/{_ds(field='id')}",
        "distribution": distributions,
        "recordSet": [
            {
                "name": _ds(field="name"),
                "@type": "ml:RecordSet",
                "source": f"#{{{distribution_source}}}",
                "key": _row_identifier(openml_features),
                "field": [
                    {
                        "name": feat["name"],
                        "@type": "ml:Field",
                        "dataType": _datatype(feat["data_type"], feat.get("nominal_value", None)),
                        "source": f"#{{{distribution_source}/{feat['name']}}}",
                    }
                    for feat in openml_features
                ],
            }
        ],
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


def _distribution(name: str, url: str) -> dict | None:
    if url is None:
        return None

    if url.endswith(".arff"):
        type_ = "arff"
        mimetype = "text/plain"  # No official arff mimetype exists
    elif url.endswith(".pq"):
        type_ = "parquet"
        mimetype = "application/vnd.apache.parquet"  # Not an official mimetype yet
        # see https://issues.apache.org/jira/browse/PARQUET-1889
    else:
        raise ValueError(f"Unrecognized file extension in url: {url}")
    return {
        "name": f"{name} ({type_})",
        "@type": "FileObject",
        "contentUrl": url,
        "encodingFormat": mimetype
        # TODO: add the md5 hash? But where? 'sha256' is in the Google Docs file, but not official?
        # TODO: add sameAs (other distribution)?
    }


def _datatype(value: str, nominal_value: list[str] | None) -> str:
    if nominal_value is not None:
        if set(nominal_value) == {"TRUE", "FALSE"} or set(nominal_value) == {"0", "1"}:
            return "Boolean"
    d_type = {
        "numeric": "Number",
        "string": "Text",
        "nominal": "Text",  # TODO: where to add the possible values?
    }.get(value, None)
    if d_type is None:
        raise ValueError(f"Unknown datatype: {value}")
    return d_type


def _row_identifier(openml_features):
    row_identifiers = [
        f"#{{{f['name']}}}" for f in openml_features if f["is_row_identifier"] == "true"
    ]
    if len(row_identifiers) > 2:
        return row_identifiers
    elif len(row_identifiers) == 1:
        return row_identifiers[0]
    return None


def _lenient_date_parser(value: str) -> datetime.date | datetime.datetime:
    try:
        dateutil.parser.parse(value)
    except dateutil.parser.ParserError:
        pass
    if len(value) == 4 and (value.startswith("19") or value.startswith("20")):
        year = int(value)
        return datetime.date(year, 1, 1)
    raise ValueError(f"Unknown date/datetime format: {value}")


def _remove_none_values(dct_: dict):
    for key, value in list(dct_.items()):
        if isinstance(value, dict):
            _remove_none_values(value)
        elif value is None:
            del dct_[key]
        elif isinstance(value, list) and len(value) == 0:
            del dct_[key]
