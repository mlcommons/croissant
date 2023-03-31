import dateutil.parser
import langcodes


def bake(openml_dataset: dict) -> dict:
    def _ds(field: str, transform=None, required=False):
        return _g(openml_dataset, field, transform, required)

    def _g(json_dict, field: str, transform=None, required=False):
        if field not in json_dict:
            if required:
                raise ValueError(f"Required field {field} missing.")
            return None
        val = json_dict[field]
        if transform is not None:
            return transform(val)
        return val

    # TODO: add record_set
    return {
        "@context": {"@vocab": "https://schema.org/", "ml": "http://mlcommons.org/schema/"},
        "@type": "Dataset",
        "@language": "en",
        "name": _ds("name", required=True),
        "description": _ds("description", required=True),
        "version": _ds("version"),
        # Multiple creators not supported  by schema.org, so joining them with " and "
        "creator": _ds("creator", transform=lambda v: person(" and ".join(v))),
        "contributor": _ds("contributor", transform=person),
        "dateCreated": _ds("upload_date", transform=dateutil.parser.parse),
        "dateModified": _ds("processing_date", transform=dateutil.parser.parse),
        "inLanguage": _ds("language", lambda v: langcodes.find(v).language),
        "isAccessibleForFree": True,
        "license": _ds("license"),
        "creativeWorkStatus": _ds("status"),
        "keywords": _ds("tag"),
        "citation": _ds("citation"),
        "sameAs": _ds("original_data_url"),
        "url": f"https://www.openml.org/api/v1/json/data/{_ds('id')}",
        "distribution": [
            distribution(url) for url in sorted({_ds("minio_url"), _ds("url"), _ds("parquet_url")})
        ],
    }


def person(name: str) -> dict | None:
    if name is None or name == "":
        return None
    return {"@context": "https://schema.org", "@type": "Person", "name": name}


def distribution(url: str) -> dict | None:
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
        "name": url.split("/")[-1],
        "@type": "FileObject",
        "contentUrl": url,
        "encodingFormat": mimetype
        # TODO: add the md5 hash? But where? 'sha256' is in the Google Docs file, but not official?
    }
