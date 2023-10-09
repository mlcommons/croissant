"""Streamlit session state.

In the future, this could be the serialization format between front and back.
"""

import dataclasses


class CurrentStep:
    pass


class Files:
    pass


class RecordSets:
    pass


class RecordSet:
    pass


@dataclasses.dataclass
class Metadata:
    name: str = ""
    description: str | None = None
    citation: str | None = None
    license: str | None = ""
    url: str = ""

    def __bool__(self):
        return self.name != "" and self.url != ""
