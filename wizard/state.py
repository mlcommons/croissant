"""Streamlit session state.

In the future, this could be the serialization format between front and back.
"""

import dataclasses
import streamlit as st
import mlcroissant as mlc
from typing import List


def init_state():

    if Croissant not in st.session_state:
        st.session_state[Croissant] = Croissant()

    if CurrentStep not in st.session_state:
        st.session_state[CurrentStep] = "start"


class CurrentStep:
    pass

@dataclasses.dataclass
class Distribution:
    name: str = ""
    description: str = ""
    contentSize: str = ""
    contentUrl: str = ""
    encodingFormat: str = ""
    sha256: str = ""
    

@dataclasses.dataclass
class RecordSet:
    pass

@dataclass.dataclass
class Field:
    name: str = ""
    description: str = ""
    dataType: str | str[] = ""
    source: Source = Source()

@dataclass.dataclass
class Source:
    distribution: Distribution = Distribution()
    extract: 

@dataclasses.dataclass
class Metadata:
    name: str = ""
    description: str | None = None
    citation: str | None = None
    license: str | None = ""
    url: str = ""

    def __bool__(self):
        return self.name != "" and self.url != ""
    
@dataclasses.dataclass
class Croissant:
    Metadata: Metadata = Metadata()
    Files: List[Distribution] = []
    RecordSets: List[RecordSet] = []

def WizardToCanonical(croi: Croissant):
    pass