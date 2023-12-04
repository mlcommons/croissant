import enum

import streamlit as st

from core.names import find_unique_name
from core.state import Metadata

# List from:
LICENSES_URL = "https://huggingface.co/docs/hub/repositories-licenses"
LICENSES = {
    "Unknown": "unknown",
    "Other": "other",
    "Apache license 2.0": "apache-2.0",
    "MIT": "mit",
    "OpenRAIL license family": "openrail",
    "BigScience OpenRAIL-M": "bigscience-openrail-m",
    "CreativeML OpenRAIL-M": "creativeml-openrail-m",
    "BigScience BLOOM RAIL 1.0": "bigscience-bloom-rail-1.0",
    "BigCode Open RAIL-M v1": "bigcode-openrail-m",
    "Academic Free License v3.0": "afl-3.0",
    "Artistic license 2.0": "artistic-2.0",
    "Boost Software License 1.0": "bsl-1.0",
    "BSD license family": "bsd",
    "BSD 2-clause “Simplified” license": "bsd-2-clause",
    "BSD 3-clause “New” or “Revised” license": "bsd-3-clause",
    "BSD 3-clause Clear license": "bsd-3-clause-clear",
    "Computational Use of Data Agreement": "c-uda",
    "Creative Commons license family": "cc",
    "Creative Commons Zero v1.0 Universal": "cc0-1.0",
    "Creative Commons Attribution 2.0": "cc-by-2.0",
    "Creative Commons Attribution 2.5": "cc-by-2.5",
    "Creative Commons Attribution 3.0": "cc-by-3.0",
    "Creative Commons Attribution 4.0": "cc-by-4.0",
    "Creative Commons Attribution Share Alike 3.0": "cc-by-sa-3.0",
    "Creative Commons Attribution Share Alike 4.0": "cc-by-sa-4.0",
    "Creative Commons Attribution Non Commercial 2.0": "cc-by-nc-2.0",
    "Creative Commons Attribution Non Commercial 3.0": "cc-by-nc-3.0",
    "Creative Commons Attribution Non Commercial 4.0": "cc-by-nc-4.0",
    "Creative Commons Attribution No Derivatives 4.0": "cc-by-nd-4.0",
    "Creative Commons Attribution Non Commercial No Derivatives 3.0": "cc-by-nc-nd-3.0",
    "Creative Commons Attribution Non Commercial No Derivatives 4.0": "cc-by-nc-nd-4.0",
    "Creative Commons Attribution Non Commercial Share Alike 2.0": "cc-by-nc-sa-2.0",
    "Creative Commons Attribution Non Commercial Share Alike 3.0": "cc-by-nc-sa-3.0",
    "Creative Commons Attribution Non Commercial Share Alike 4.0": "cc-by-nc-sa-4.0",
    "Community Data License Agreement – Sharing, Version 1.0": "cdla-sharing-1.0",
    "Community Data License Agreement – Permissive, Version 1.0": "cdla-permissive-1.0",
    "Community Data License Agreement – Permissive, Version 2.0": "cdla-permissive-2.0",
    "Do What The F*ck You Want To Public License": "wtfpl",
    "Educational Community License v2.0": "ecl-2.0",
    "Eclipse Public License 1.0": "epl-1.0",
    "Eclipse Public License 2.0": "epl-2.0",
    "European Union Public License 1.1": "eupl-1.1",
    "GNU Affero General Public License v3.0": "agpl-3.0",
    "GNU Free Documentation License family": "gfdl",
    "GNU General Public License family": "gpl",
    "GNU General Public License v2.0": "gpl-2.0",
    "GNU General Public License v3.0": "gpl-3.0",
    "GNU Lesser General Public License family": "lgpl",
    "GNU Lesser General Public License v2.1": "lgpl-2.1",
    "GNU Lesser General Public License v3.0": "lgpl-3.0",
    "ISC": "isc",
    "LaTeX Project Public License v1.3c": "lppl-1.3c",
    "Microsoft Public License": "ms-pl",
    "Mozilla Public License 2.0": "mpl-2.0",
    "Open Data Commons License Attribution family": "odc-by",
    "Open Database License family": "odbl",
    "Open Rail++-M License": "openrail++",
    "Open Software License 3.0": "osl-3.0",
    "PostgreSQL License": "postgresql",
    "SIL Open Font License 1.1": "ofl-1.1",
    "University of Illinois/NCSA Open Source License": "ncsa",
    "The Unlicense": "unlicense",
    "zLib License": "zlib",
    "Open Data Commons Public Domain Dedication and License": "pddl",
    "Lesser General Public License For Linguistic Resources": "lgpl-lr",
    "DeepFloyd IF Research License Agreement": "deepfloyd-if-license",
    "Llama 2 Community License Agreement": "llama2",
}


def find_license_index(code: str) -> int | None:
    """Finds the index in the list of LICENSES."""
    for index, license_code in enumerate(LICENSES.values()):
        if license_code == code:
            return index
    return None


class MetadataEvent(enum.Enum):
    """Event that triggers a metadata change."""

    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    URL = "URL"
    LICENSE = "LICENSE"
    CITATION = "CITATION"


def handle_metadata_change(event: MetadataEvent, metadata: Metadata, key: str):
    if event == MetadataEvent.NAME:
        metadata.name = find_unique_name(set(), st.session_state[key])
    elif event == MetadataEvent.DESCRIPTION:
        metadata.description = st.session_state[key]
    elif event == MetadataEvent.LICENSE:
        metadata.license = LICENSES.get(st.session_state[key])
    elif event == MetadataEvent.CITATION:
        metadata.citation = st.session_state[key]
    elif event == MetadataEvent.URL:
        metadata.url = st.session_state[key]
