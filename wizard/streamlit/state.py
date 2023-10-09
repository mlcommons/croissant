import dataclasses

import pandas as pd


class CurrentStep:
    pass


class Files:
    pass


@dataclasses.dataclass
class File:
    name: str = ""
    description: str | None = None
    content_url: str = ""
    encoding_format: str | None = None
    sha256: str | None = None
    df: pd.DataFrame | None = None


class RecordSets:
    pass


class RecordSet:
    pass


@dataclasses.dataclass
class Metadata:
    """In the future, this could be the serialization format between front and back."""

    name: str = ""
    description: str | None = None
    citation: str | None = None
    license: str | None = ""
    url: str = ""

    def __bool__(self):
        return self.name != "" and self.url != ""
