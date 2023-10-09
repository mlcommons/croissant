import dataclasses
import hashlib
import tempfile

from etils import epath
import pandas as pd
import requests


@dataclasses.dataclass
class File:
    name: str = ""
    description: str | None = None
    content_url: str = ""
    encoding_format: str | None = None
    sha256: str | None = None
    df: pd.DataFrame | None = None


class FileTypes:
    CSV = "text/csv"


def hash_file_path(url: str) -> epath.Path:
    """Reproducibly produces the file path."""
    tempdir = epath.Path(tempfile.gettempdir())
    hash = hashlib.sha256(url.encode()).hexdigest()
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


def get_dataframe(encoding_format: str, file_path: epath.Path) -> pd.DataFrame:
    """Gets the df associated to the file."""
    if encoding_format == FileTypes.CSV:
        return pd.read_csv(file_path)
    else:
        raise NotImplementedError()


def check_file(encoding_format: str, url: str) -> File:
    """Downloads locally and checks the file."""
    file_path = hash_file_path(url)
    if not file_path.exists():
        download_file(url, file_path)
    with file_path.open("rb") as file:
        sha256 = hashlib.sha256(file.read()).hexdigest()
    df = get_dataframe(encoding_format, file_path)
    return File(
        name=url.split("/")[-1],
        description="",
        content_url=url,
        encoding_format=encoding_format,
        sha256=sha256,
        df=df.infer_objects(),
    )
