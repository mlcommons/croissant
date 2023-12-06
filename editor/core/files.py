import dataclasses
import hashlib
import io
import tempfile

from etils import epath
import magic
import pandas as pd
import requests

from .names import find_unique_name
from .path import get_resource_path
from .state import FileObject
from .state import FileSet

FILE_OBJECT = "FileObject"
FILE_SET = "FileSet"
RESOURCE_TYPES = [FILE_OBJECT, FILE_SET]


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
    GZIP = FileType(name="GZIP", encoding_format="application/gzip", extensions=["gz"])
    JPEG = FileType(name="JPEG", encoding_format="image/jpeg", extensions=["json"])
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
    TAR = FileType(
        name="Archive (TAR)",
        encoding_format="application/x-tar",
        extensions=["tar"],
    )
    TXT = FileType(
        name="Text",
        encoding_format="plain/text",
        extensions=["txt"],
    )
    ZIP = FileType(
        name="ZIP",
        encoding_format="application/zip",
        extensions=["zip"],
    )


def _full_name(file_type: FileType):
    return f"{file_type.name} ({file_type.encoding_format})"


FILE_TYPES: dict[str, FileType] = {
    _full_name(file_type): file_type
    for file_type in [
        FileTypes.CSV,
        FileTypes.EXCEL,
        FileTypes.GZIP,
        FileTypes.JPEG,
        FileTypes.JSON,
        FileTypes.JSONL,
        FileTypes.PARQUET,
        FileTypes.TAR,
        FileTypes.TXT,
        FileTypes.ZIP,
    ]
}

ENCODING_FORMATS: dict[str, FileType] = {
    file_type.encoding_format: file_type for file_type in FILE_TYPES.values()
}


def name_to_code(file_type_name: str) -> str | None:
    """Maps names to the encoding format: Text => plain/text."""
    for name, file_type in FILE_TYPES.items():
        if file_type_name == name:
            return file_type.encoding_format
    return None


def code_to_index(encoding_format: str) -> int | None:
    """Maps the encoding format to its index in the list of keys: plain/text => 12."""
    for i, file_type in enumerate(FILE_TYPES.values()):
        if file_type.encoding_format == encoding_format:
            return i
    return None


def _sha256(content: bytes):
    """Computes the sha256 digest of the byte string."""
    return hashlib.sha256(content).hexdigest()


def hash_file_path(url: str) -> epath.Path:
    """Reproducibly produces the file path."""
    tempdir = epath.Path(tempfile.gettempdir())
    hash = _sha256(url.encode())
    return tempdir / f"croissant-editor-{hash}"


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
        df = pd.read_csv(file)
    elif file_type == FileTypes.EXCEL:
        df = pd.read_excel(file)
    elif file_type == FileTypes.JSON:
        df = pd.read_json(file)
    elif file_type == FileTypes.JSONL:
        df = pd.read_json(file, lines=True)
    elif file_type == FileTypes.PARQUET:
        df = pd.read_parquet(file)
    else:
        raise NotImplementedError(
            f"File type {file_type} is not supported. Please, open an issue on GitHub:"
            " https://github.com/mlcommons/croissant/issues/new"
        )
    return df.infer_objects()


def guess_file_type(path: epath.Path) -> FileType | None:
    mime = magic.from_file(path, mime=True)
    return ENCODING_FORMATS.get(mime)


def file_from_url(url: str, names: set[str], folder: epath.Path) -> FileObject:
    """Downloads locally and extracts the file information."""
    file_path = hash_file_path(url)
    if not file_path.exists():
        download_file(url, file_path)
    with file_path.open("rb") as file:
        sha256 = _sha256(file.read())
    file_type = guess_file_type(file_path)
    df = get_dataframe(file_type, file_path)
    return FileObject(
        name=find_unique_name(names, url.split("/")[-1]),
        description="",
        content_url=url,
        encoding_format=file_type.encoding_format,
        sha256=sha256,
        df=df,
        folder=folder,
    )


def file_from_upload(
    file: io.BytesIO, names: set[str], folder: epath.Path
) -> FileObject:
    """Uploads locally and extracts the file information."""
    value = file.getvalue()
    content_url = f"data/{file.name}"
    sha256 = _sha256(value)
    file_path = get_resource_path(content_url)
    with file_path.open("wb") as f:
        f.write(value)
    file_type = guess_file_type(file_path)
    df = get_dataframe(file_type, file)
    return FileObject(
        name=find_unique_name(names, file.name),
        description="",
        content_url=content_url,
        encoding_format=file_type.encoding_format,
        sha256=sha256,
        df=df,
        folder=folder,
    )


def file_from_form(
    type: str, names: set[str], folder: epath.Path
) -> FileObject | FileSet:
    """Creates a file based on manually added fields."""
    if type == FILE_OBJECT:
        return FileObject(name=find_unique_name(names, "file_object"), folder=folder)
    elif type == FILE_SET:
        return FileSet(name=find_unique_name(names, "file_set"))
    else:
        raise ValueError("type has to be one of FILE_OBJECT, FILE_SET")


def is_url(file: FileObject) -> bool:
    return file.content_url and file.content_url.startswith("http")


def trigger_download(file: FileObject):
    if is_url(file):
        file_path = hash_file_path(file.content_url)
        if not file_path.exists():
            download_file(file.content_url, file_path)
    else:
        file_path = get_resource_path(file.content_url)
    file_type = guess_file_type(file_path)
    df = get_dataframe(file_type, file_path)
    file.df = df
