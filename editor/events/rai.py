import datetime
import enum

import streamlit as st

from core.names import find_unique_name
from core.state import Metadata
import mlcroissant as mlc


class RaiEvent(enum.Enum):
    """Event that triggers a Rai change."""

    RAI_DATA_COLLECTION = "RAI_DATA_COLLECTION"
    RAI_DATA_COLLECTION_TYPE = "RAI_DATA_COLLECTION_TYPE"
    RAI_DATA_COLLECTION_TYPE_OTHERS = "RAI_DATA_COLLECTION_TYPE_OTHERS"
    RAI_DATA_COLLECTION_MISSING_DATA = "RAI_DATA_COLLECTION_MISSING_DATA"
    RAI_DATA_COLLECTION_RAW = "RAI_DATA_COLLECTION_RAW"
    RAI_DATA_COLLECTION_TIMEFRAME = "RAI_DATA_COLLECTION_TIMEFRAME"
    RAI_DATA_PREPROCESSING_IMPUTATION = "RAI_DATA_PREPROCESSING_IMPUTATION"
    RAI_DATA_PREPROCESSING_PROTOCOL = " RAI_DATA_PREPROCESSING_PROTOCOL"
    RAI_DATA_PREPROCESSING_MANIPULATION = "RAI_DATA_PREPROCESSING_MANIPULATIO"
    RAI_DATA_ANNOTATION_PROTOCOL = "RAI_DATA_ANNOTATION_PROTOCOL"
    RAI_DATA_ANNOTATION_PLATFORM = "RAI_DATA_ANNOTATION_PLATFORM"
    RAI_DATA_ANNOTATION_ANALYSIS = "RAI_DATA_ANNOTATION_ANALYSIS"
    RAI_DATA_ANNOTATION_PER_ITEM = "RAI_DATA_ANNOTATION_PERI_TEM"
    RAI_DATA_ANNOTATION_DEMOGRAPHICS = "RAI_DATA_ANNOTATION_DEMOGRAPHICS"
    RAI_DATA_ANNOTATION_TOOLS = "RAI_DATA_ANNOTATION_TOOLS"
    RAI_DATA_USE_CASES = "RAI_DATA_USECASES"
    RAI_DATA_BIAS = "RAI_DATA_BIAS"
    RAI_DATA_LIMITATION = "RAI_DATA_LIMITATION"
    RAI_DATA_SOCIAL_IMPACT = "RAI_DATA_SOCIAL_IMPACT"
    RAI_SENSITIVE = "RAI_SENSITIVE"
    RAI_MAINTENANCE = "RAI_MAINTENANCE"


def handle_rai_change(event: RaiEvent, Metadata: Metadata, key: str):
    if event == RaiEvent.RAI_DATA_COLLECTION:
        Metadata.data_collection = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_TYPE:
        Metadata.data_collection_type = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_TYPE_OTHERS:
        ## To implement
        pass
    if event == RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA:
        Metadata.data_collection_missing_data = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_RAW:
        Metadata.data_collection_raw_data = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_TIMEFRAME:
        date = st.session_state[key]
        Metadata.data_collection_timeframe = datetime.datetime(
            date.year, date.month, date.day
        )
    if event == RaiEvent.RAI_DATA_PREPROCESSING_IMPUTATION:
        Metadata.data_preprocessing_imputation = st.session_state[key]
    if event == RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL:
        if Metadata.data_preprocessing_protocol:
            index = key.split("_")[-1]
            Metadata.data_preprocessing_protocol[int(index)] = st.session_state[key]
        else:
            Metadata.data_preprocessing_protocol = []
            Metadata.data_preprocessing_protocol.append(st.session_state[key])
    if event == RaiEvent.RAI_DATA_PREPROCESSING_MANIPULATION:
        Metadata.data_preprocessing_manipulation = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PROTOCOL:

        Metadata.data_annotation_protocol = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PLATFORM:
        Metadata.data_annotation_platform = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_ANALYSIS:
        Metadata.data_annotation_analysis = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PER_ITEM:
        Metadata.annotation_per_item = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS:
        Metadata.annotator_demographics = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_TOOLS:
        Metadata.machine_annotation_tools = st.session_state[key]
    if event == RaiEvent.RAI_DATA_USE_CASES:

        if Metadata.data_use_cases:
            index = key.split("_")[-1]
            Metadata.data_use_cases[int(index)] = st.session_state[key]
        else:
            Metadata.data_use_cases = []
            Metadata.data_use_cases.append(st.session_state[key])

    if event == RaiEvent.RAI_DATA_BIAS:

        if Metadata.data_biases:
            index = key.split("_")[-1]
            Metadata.data_biases[int(index)] = st.session_state[key]
        else:
            Metadata.data_biases = []
            Metadata.data_biases.append(st.session_state[key])

    if event == RaiEvent.RAI_DATA_LIMITATION:
        if Metadata.data_limitations:
            index = key.split("_")[-1]
            Metadata.data_limitations[int(index)] = st.session_state[key]
        else:
            Metadata.data_limitations = []
            Metadata.data_limitations.append(st.session_state[key])
    if event == RaiEvent.RAI_DATA_SOCIAL_IMPACT:
        Metadata.data_social_impact = st.session_state[key]
    if event == RaiEvent.RAI_SENSITIVE:

        if Metadata.personal_sensitive_information:
            index = key.split("_")[-1]
            Metadata.personal_sensitive_information[int(index)] = st.session_state[key]
        else:
            Metadata.personal_sensitive_information = []
            Metadata.personal_sensitive_information.append(st.session_state[key])
    if event == RaiEvent.RAI_MAINTENANCE:
        Metadata.data_release_maintenance_plan = st.session_state[key]
