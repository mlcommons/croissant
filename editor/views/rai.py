import streamlit as st

from core.state import Metadata
from events.metadata import find_license_index
from events.metadata import LICENSES
from events.metadata import LICENSES_URL
from events.rai import handle_rai_change
from events.rai import RaiEvent


def render_rai_metadata():
    """Renders the `Metadata` view."""
    metadata: Metadata = st.session_state[Metadata]
    col1, col2 = st.columns([1, 1])
    with col1.expander("**Provenance**", expanded=True):
         with st.expander("Data Collection", expanded=False):
            key = "metadata-data-collection"
            st.text_area(
                label=(
                    "Explain the key stages of the data collection process to improves understanding of potential users"
                ),
                key=key,
                value=metadata.data_collection,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION , metadata, key),
            )
            with st.expander("Data Collection Type", expanded=True):
                key = "metadata-data-collection-type"
                st.multiselect(
                    label=('Define the data collection type. Recommended values:'),
                    options=['Surveys', 'Secondary Data analysis', 'Physical data collection', 'Direct measurement', 'Document analysis', 'Manual Human Curator', 'Software Collection', 'Experiments', 'Web Scraping', 'Web API', 'Focus groups', 'Self-reporting', 'Customer feedback data', 'User-generated content data', 'Passive Data Collection', 'Others'],
                    key="metadata-data-collection-type",
                    default=metadata.data_collection_type,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_COLLECTION_TYPE, metadata, key),
                )
                key = "metadata-data-collection-type-others"
                st.text_area(
                    label=(
                        "**Type**. If others, define the data collection type"
                    ),
                    key="metadata-data-collection-type-others",
                    value=metadata.data_collection_type_others,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_COLLECTION_TYPE_OTHERS, metadata, key),
                )
            key = "metadata-data-collection-missing"
            st.text_area(
                label=(
                    "**Missing Data**. Description of missing data in structured/unstructured form"
                ),
                key="metadata-data-collection-missing",
                value=metadata.data_collection_missing,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA, metadata, key),
            )
            key = "metadata-data-collection-rawdata"
            st.text_area(
                label=(
                    "**Raw Data**. Description of the raw data i.e. source of the data "
                ),
                key="metadata-data-collection-rawdata",
                value=metadata.data_collection_raw,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_RAW_DATA, metadata, key),
            )
            with st.expander("Data collection timeframe in terms of start and end the collection process", expanded=True):
                key = "metadata-data-collection-timeframe-start"
                st.date_input(
                    label=(
                        "Start: **range** https://schema.org/DateTime "
                    ),
                    key="metadata-data-collection-timeframe-start",
                    value=metadata.data_collection_timeframe_start,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_COLLECTION_TIMEFRAME_START, metadata, key),
                )
                key = "metadata-data-collection-timeframe-end"
                st.date_input(
                    label=(
                        "End **range**: https://schema.org/DateTime "
                    ),
                    key="metadata-data-collection-timeframe-end",
                    value=metadata.data_collection_timeframe_end,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_COLLECTION_TIMEFRAME_END, metadata, key),
                )
         with st.expander("Data Annotation", expanded=False):
                key = "metadata-data-annotation-protocol"
                st.text_area(
                    label=(
                        "**Protocol**. Description of annotations (labels, ratings) produced, including how these were created or authored -  Annotation Workforce Type, Annotation Characteristic(s), Annotation Description(s), Annotation Task(s), Annotation Distribution(s)  "
                    ),
                    key="metadata-data-annotation-protocol",
                    value=metadata.data_annotation_protocol,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_PROTOCOL, metadata, key),
                )
                key = "metadata-data-annotation-platform"
                st.text_area(
                    label=(
                        "**Platform**. Platform, tool, or library used to collect annotations by human annotators "
                    ),
                    key="metadata-data-annotation-platform",
                    value=metadata.data_annotation_platform,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_PLATFORM, metadata, key),
                )
                key = "metadata-data-annotation-analysis"
                st.text_area(
                    label=(
                        "**Analysis**. Considerations related to the process of converting the “raw” annotations into the labels that are ultimately packaged in a dataset - Uncertainty or disagreement between annotations on each instance as a signal in the dataset, analysis of systematic disagreements between annotators of different socio demographic group,  how the final dataset annotations will relate to individual annotator responses  "
                    ),
                    key="metadata-data-annotation-analysis",
                    value=metadata.data_annotation_analysis,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_ANALYSIS, metadata, key),
                )
                key = "metadata-data-annotation-demographics"
                st.text_area(
                    label=(
                        "**Demographics**. List of demographics specifications about the annotators "
                    ),
                    key="metadata-data-annotation-demographics",
                    value=metadata.data_annotation_demographics,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS, metadata, key),
                )
                key = "metadata-data-annotation-tools"
                st.text_area(
                    label=(
                        "**Tools**. List of software used for data annotation ( e.g. concept extraction, NER, and additional characteristics of the tools used for annotation to allow for replication or extension)  "
                    ),
                    key="metadata-data-annotation-tools",
                    value=metadata.data_annotation_tools,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_TOOLS, metadata, key),
                )
                key = "metadata-data-annotation-peritem"
                st.text_area(
                    label=(
                        "**Annotation per item**. Number of human labels per dataset item  "
                    ),
                    key="metadata-data-annotation-peritem",
                    value=metadata.data_annotation_peritem,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_PERITEM, metadata, key),
                )            
         with st.expander("Data Preprocessing", expanded=False):
                    
                key = "metadata-data-preprocessing-protocol"
                st.text_area(
                    label=(
                        "**Protocol**. Description of data manipulation process if applicable   "
                    ),
                    key="metadata-data-preprocessing-protocol",
                    value=metadata.data_preprocessing_protocol,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL, metadata, key),
                )
                key = "metadata-data-preprocessing-manipulation"
                st.text_area(
                    label=(
                        "**Manipulation**. Description of data manipulation process if applicable    "
                    ),
                    key="metadata-data-preprocessing-manipulation",
                    value=metadata.data_preprocessing_manipulation,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_PREPROCESSING_MANIPULATION, metadata, key),
                )
                key = "metadata-data-preprocessing-imputation"
                st.text_area(
                    label=(
                        "**Imputation**. Description of data imputation process if applicable  "
                    ),
                    key="metadata-data-preprocessing-imputation",
                    value=metadata.data_preprocessing_imputation,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_PREPROCESSING_IMPUTATION, metadata, key),
                )
            
       
    with col2.expander("**Data uses and social impact**", expanded=True):
        key = "metadata-data-usecases"
        st.text_area(
            label=(
                "**Data use cases**. Dataset Use(s) - training, testing, validation, development or production use, fine tuning, others (please specify), usage guidelines, recommended uses, etc."
            ),
            key=key,
            value=metadata.data_usecases,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_USECASES, metadata, key),
        )
        key = "metadata-data-biases"
        st.text_area(
            label=(
                "**Data biases**. Involves understanding the potential risks associated"
                " with data usage and to prevent unintended and potentially harmful"
                " consequences that may arise from using models trained on or evaluated"
                " with the respective data."
            ),
            key=key,
            value=metadata.data_biases,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_BIAS, metadata, key),
        )
        key = "metadata-personal-sensitive-information"
        st.text_area(
            label=(
                "**Personal and sensitive information**. Personal and sensitive information, if"
                " contained within the dataset, can play an important role in the"
                " mitigation of any risks and the responsible use of the datasets."
            ),
            key=key,
            value=metadata.data_sensitive,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_SENSITIVE, metadata, key),
        )
        key = "metadata-social-impact"
        st.text_area(
            label=(
                "**Social impact**. Discussion of social impact, if applicable"
            ),
            key=key,
            value=metadata.data_social_impact,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_SOCIAL_IMPACT, metadata, key),
        )
        key = "metadata-data-limitations"
        st.text_area(
            label=("**Data limitation**. Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses."),
            key=key,
            value=metadata.data_limitation,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_LIMITATION, metadata, key),
        )
        key = "metadata-data-maintenance"
        st.text_area(
            label=("**Data release maintenance**. Versioning information in terms of the updating timeframe, the maintainers, and the deprecation policies. "),
            key=key,
            value=metadata.data_maintenance,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_MAINTENANCE, metadata, key),
        )

        
