import dataclasses
import hashlib
import io
import tempfile

from core.state import FileObject
from etils import epath
import pandas as pd
import requests


@dataclasses.dataclass
class FileType:
    name: str
    encoding_format: str
    extensions: list[str]


class FileTypes:
    CSV = FileType(name="CSV", encoding_format="text/csv", extensions=["csv"])
    EXCEL = FileType(
        name="Excel",
        encoding_format="application/vnd.ms-excel",
        extensions=["xls", "xlsx", "xlsm"],
    )
    JSON = FileType(
        name="JSON", encoding_format="application/json", extensions=["json"]
    )
    JSONL = FileType(
        name="JSON-Lines",
        encoding_format="application/jsonl+json",
        extensions=["jsonl"],
    )
    PARQUET = FileType(
        name="Parquet",
        encoding_format="application/vnd.apache.parquet",
        extensions=["parquet"],
    )


FILE_TYPES: dict[str, FileType] = {
    file_type.name: file_type
    for file_type in [
        FileTypes.CSV,
        FileTypes.EXCEL,
        FileTypes.JSON,
        FileTypes.JSONL,
        FileTypes.PARQUET,
    ]
}


def _sha256(content: bytes):
    """Computes the sha256 digest of the byte string."""
    return hashlib.sha256(content).hexdigest()


def hash_file_path(url: str) -> epath.Path:
    """Reproducibly produces the file path."""
    tempdir = epath.Path(tempfile.gettempdir())
    hash = _sha256(url.encode())
    return tempdir / f"croissant-wizard-{hash}"


def download_file(url: str, file_path: epath.Path):
    """Downloads the file locally to `file_path`."""
    with requests.get(url, stream=True) as request:
        request.raise_for_status()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = epath.Path(tmpdir) / "file"
            with tmpdir.open("wb") as file:
                for chunk in request.iter_content(chunk_size=8192):
                    file.write(chunk)
            tmpdir.copy(file_path)


def get_dataframe(file_type: FileType, file: io.BytesIO | epath.Path) -> pd.DataFrame:
    """Gets the df associated to the file."""
    if file_type == FileTypes.CSV:
        return pd.read_csv(file)
    elif file_type == FileTypes.EXCEL:
        return pd.read_excel(file)
    elif file_type == FileTypes.JSON:
        return pd.read_json(file)
    elif file_type == FileTypes.JSONL:
        return pd.read_json(file, lines=True)
    elif file_type == FileTypes.PARQUET:
        return pd.read_parquet(file)
    else:
        raise NotImplementedError()


def file_from_url(file_type: FileType, url: str) -> FileObject:
    """Downloads locally and extracts the file information."""
    file_path = hash_file_path(url)
    if not file_path.exists():
        download_file(url, file_path)
    with file_path.open("rb") as file:
        sha256 = _sha256(file.read())
    df = get_dataframe(file_type, file_path)
    return FileObject(
        name=url.split("/")[-1],
        description="",
        content_url=url,
        encoding_format=file_type.encoding_format,
        sha256=sha256,
        df=df,
    )


def file_from_upload(file_type: FileType, file: io.BytesIO) -> FileObject:
    """Uploads locally and extracts the file information."""
    sha256 = _sha256(file.getvalue())
    df = get_dataframe(file_type, file)
    return FileObject(
        name=file.name,
        description="",
        content_url=f"data/{file.name}",
        encoding_format=file_type.encoding_format,
        sha256=sha256,
        df=df,
    )
