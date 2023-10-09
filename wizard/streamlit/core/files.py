import hashlib
import tempfile

from etils import epath
import pandas as pd
import requests
from state import File


def check_file(encoding_format: str, url: str) -> File:
    """Downloads locally and checks the file."""
    with requests.get(url, stream=True) as request:
        request.raise_for_status()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = epath.Path(tmpdir) / "file"
            with tmpdir.open("wb") as file:
                for chunk in request.iter_content(chunk_size=8192):
                    file.write(chunk)
            with tmpdir.open("rb") as file:
                sha256 = hashlib.sha256(file.read()).hexdigest()
            with tmpdir.open("rb") as file:
                if encoding_format == "text/csv":
                    df = pd.read_csv(file).infer_objects()
                    return File(
                        name=url.split("/")[-1],
                        description="",
                        content_url=url,
                        encoding_format=encoding_format,
                        sha256=sha256,
                        df=df,
                    )
                else:
                    raise NotImplementedError()
