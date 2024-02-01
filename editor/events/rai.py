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
    RAI_DATA_COLLECTION_MISSING_DATA = "RAI_DATA_COLLECTION_MISSING_DATA"
    RAI_DATA_COLLECTION_RAW_DATA = "RAI_DATA_COLLECTION_RAW_DATA"
    RAI_DATA_COLLECTION_TIMEFRAME = "RAI_DATA_COLLECTION_TIMEFRAME"
    RAI_DATA_PREPROCESSING_IMPUTATION = "RAI_DATA_PREPROCESSING_IMPUTATION"
    RAI_DATA_PREPROCESSING_PROTOCOL = " RAI_DATA_PREPROCESSING_PROTOCOL"
    RAI_DATA_PREPROCESSING_MANIPULATION = "RAI_DATA_PREPROCESSING_MANIPULATIO"
    RAI_DATA_ANNOTATION_PROTOCOL = "RAI_DATA_ANNOTATION_PROTOCOL"
    RAI_DATA_ANNOTATION_PLATFORM = "RAI_DATA_ANNOTATION_PLATFORM"
    RAI_DATA_ANNOTATION_ANALYSIS = "RAI_DATA_ANNOTATION_ANALYSIS"
    RAI_DATA_ANNOTATION_PERITEM = "RAI_DATA_ANNOTATION_PERITEM"
    RAI_DATA_ANNOTATION_DEMOGRAPHICS = "RAI_DATA_ANNOTATION_DEMOGRAPHICS"
    RAI_DATA_ANNOTATION_TOOLS = "RAI_DATA_ANNOTATION_TOOLS"
    RAI_DATA_USECASES = "RAI_DATA_USECASES"
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
    if event == RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA:
        Metadata.data_collection_missing = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_RAW_DATA:
        Metadata.data_collection_raw = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_TIMEFRAME:
        Metadata.data_collection_timeframe = st.session_state[key]
    if event == RaiEvent.RAI_DATA_PREPROCESSING_IMPUTATION:
        Metadata.data_preprocessing_imputation = st.session_state[key]
    if event == RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL:
        Metadata.data_preprocessing_protocol = st.session_state[key]
    if event == RaiEvent.RAI_DATA_PREPROCESSING_MANIPULATION:
        Metadata.data_preprocessing_manipulation = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PROTOCOL:
        Metadata.data_annotation_protocol = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PLATFORM:
        Metadata.data_annotation_platform = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_ANALYSIS:
        Metadata.data_annotation_analysis = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PERITEM:
        Metadata.data_annotation_peritem = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS:
        Metadata.data_annotation_demographics = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_TOOLS:
        Metadata.data_annotation_tools = st.session_state[key]
    if event == RaiEvent.RAI_DATA_USECASES:
        Metadata.data_usecases = st.session_state[key]
    if event == RaiEvent.RAI_DATA_BIAS:
        Metadata.data_biases = st.session_state[key]
    if event == RaiEvent.RAI_DATA_LIMITATION:
        Metadata.data_limitation = st.session_state[key]
    if event == RaiEvent.RAI_DATA_SOCIAL_IMPACT:
        Metadata.data_social_impact = st.session_state[key]
    if event == RaiEvent.RAI_SENSITIVE:
        Metadata.data_sensitive = st.session_state[key]
    if event == RaiEvent.RAI_MAINTENANCE:
        Metadata.data_maintenance = st.session_state[key]
   
  
