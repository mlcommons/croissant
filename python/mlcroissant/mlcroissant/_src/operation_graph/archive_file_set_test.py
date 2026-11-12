"""Regression tests for content extraction from archive-contained FileSets."""

import hashlib
import json
import zipfile

import pytest

from mlcroissant import Dataset
from mlcroissant._src.core.rdf import make_context


def _metadata(root, encoding_format, extension, extract, *, archived):
    distribution = []
    file_set = {
        "@type": "cr:FileSet",
        "@id": "files",
        "name": "files",
        "includes": f"part*.{extension}",
        "encodingFormat": encoding_format,
    }
    if archived:
        archive = root / "records.zip"
        distribution.append({
            "@type": "cr:FileObject",
            "@id": "archive",
            "name": "archive",
            "contentUrl": str(archive),
            "encodingFormat": "application/zip",
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        })
        file_set["containedIn"] = {"@id": "archive"}
    distribution.append(file_set)
    metadata = {
        "@context": make_context(),
        "@type": "sc:Dataset",
        "name": "synthetic-archive-fields",
        "description": "Synthetic local archive extraction regression.",
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "version": "1.0.0",
        "datePublished": "2024-01-01",
        "citeAs": "Synthetic regression fixture",
        "distribution": distribution,
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "@id": "records",
                "name": "records",
                "field": [
                    {
                        "@type": "cr:Field",
                        "@id": "records/value",
                        "name": "records/value",
                        "dataType": "sc:Text",
                        "source": {"fileSet": {"@id": "files"}, "extract": extract},
                    }
                ],
            }
        ],
    }
    path = root / ("archived.json" if archived else "plain.json")
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "encoding_format, extension, extract",
    [
        ("application/json", "json", {"jsonPath": "$.*"}),
        ("text/csv", "csv", {"column": "value"}),
    ],
)
@pytest.mark.parametrize("count", [1, 2])
def test_archive_fields_match_plain_files(
    tmp_path, encoding_format, extension, extract, count
):
    values = ["alpha", "한글"][:count]
    paths = []
    for index, value in enumerate(values):
        path = tmp_path / f"part-{index}.{extension}"
        content = (
            json.dumps({"value": value}) if extension == "json" else f"value\n{value}\n"
        )
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    archive = tmp_path / "records.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for path in paths:
            bundle.write(path, path.name)
        bundle.writestr("ignored.txt", "This file must be filtered out.")
    original = archive.read_bytes()
    expected = sorted(value.encode("utf-8") for value in values)
    for archived in (False, True):
        path = _metadata(
            tmp_path, encoding_format, extension, extract, archived=archived
        )
        records = list(Dataset(str(path)).records("records"))
        assert sorted(record["records/value"] for record in records) == expected
    assert archive.read_bytes() == original


@pytest.mark.parametrize("file_property", ["filename", "content", "lines"])
def test_archive_file_properties_keep_existing_behavior(tmp_path, file_property):
    archive = tmp_path / "records.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("part.txt", "alpha,beta\ngamma\n")
    path = _metadata(
        tmp_path, "text/plain", "txt", {"fileProperty": file_property}, archived=True
    )
    records = list(Dataset(str(path)).records("records"))
    expected = {
        "filename": [b"part.txt"],
        "content": [b"alpha,beta\ngamma\n"],
        "lines": [b"alpha,beta", b"gamma"],
    }
    assert [record["records/value"] for record in records] == expected[file_property]
