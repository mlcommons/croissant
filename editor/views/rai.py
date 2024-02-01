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
                    "**Data collection**. Key stages of the data collection process encourage"
                    " its creators to reflect on the process and improves understanding for"
                    " users."
                ),
                key=key,
                value=metadata.data_collection,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION , metadata, key),
            )
            key = "metadata-data-collection-type"
            st.text_area(
                label=(
                    "**Data collection Type**. Define the data collection type. Recommended values:"
                    "Surveys, Secondary Data analysis, Physical data collection, Direct measurement, Document analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus groups, Self-reporting, Customer feedback data, User-generated content data, Passive Data Collection, Others"
                ),
                key="metadata-data-collection-type",
                value=metadata.data_collection_type,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_TYPE, metadata, key),
            )
            key = "metadata-data-collection-missing"
            st.text_area(
                label=(
                    "**Data Collection - Missing Data**. Description of missing data in structured/unstructured form"
                ),
                key="metadata-data-collection-missing",
                value=metadata.data_collection_missing,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA, metadata, key),
            )
            key = "metadata-data-collection-rawdata"
            st.text_area(
                label=(
                    "**Data Collection - RawData**. Description of the raw data i.e. source of the data "
                ),
                key="metadata-data-collection-rawdata",
                value=metadata.data_collection_raw,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_RAW_DATA, metadata, key),
            )
            key = "metadata-data-collection-timeframe"
            st.text_area(
                label=(
                    "**Data Collection - Timeframe**. Timeframe in terms of start and end date of the collection process **range**: https://schema.org/DateTime "
                ),
                key="metadata-data-collection-timeframe",
                value=metadata.data_collection_timeframe,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_TIMEFRAME, metadata, key),
            )
         with st.expander("Data Annotation", expanded=False):
                key = "metadata-data-annotation-protocol"
                st.text_area(
                    label=(
                        "**Data Annotation - Protocol**. Description of annotations (labels, ratings) produced, including how these were created or authored -  Annotation Workforce Type, Annotation Characteristic(s), Annotation Description(s), Annotation Task(s), Annotation Distribution(s)  "
                    ),
                    key="metadata-data-annotation-protocol",
                    value=metadata.data_annotation_protocol,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_PROTOCOL, metadata, key),
                )
                key = "metadata-data-annotation-platform"
                st.text_area(
                    label=(
                        "**Data Annotation - Platform**. Platform, tool, or library used to collect annotations by human annotators "
                    ),
                    key="metadata-data-annotation-platform",
                    value=metadata.data_annotation_platform,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_PLATFORM, metadata, key),
                )
                key = "metadata-data-annotation-analysis"
                st.text_area(
                    label=(
                        "**Data Annotation - Analysis**. Considerations related to the process of converting the “raw” annotations into the labels that are ultimately packaged in a dataset - Uncertainty or disagreement between annotations on each instance as a signal in the dataset, analysis of systematic disagreements between annotators of different socio demographic group,  how the final dataset annotations will relate to individual annotator responses  "
                    ),
                    key="metadata-data-annotation-analysis",
                    value=metadata.data_annotation_analysis,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_ANALYSIS, metadata, key),
                )
                key = "metadata-data-annotation-demographics"
                st.text_area(
                    label=(
                        "**Data Annotation - Demogrpahics**. List of demographics specifications about the annotators "
                    ),
                    key="metadata-data-annotation-demographics",
                    value=metadata.data_annotation_demographics,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS, metadata, key),
                )
                key = "metadata-data-annotation-tools"
                st.text_area(
                    label=(
                        "**Data Annotation - Tools**. List of software used for data annotation ( e.g. concept extraction, NER, and additional characteristics of the tools used for annotation to allow for replication or extension)  "
                    ),
                    key="metadata-data-annotation-tools",
                    value=metadata.data_annotation_tools,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_ANNOTATION_TOOLS, metadata, key),
                )
                key = "metadata-data-annotation-peritem"
                st.text_area(
                    label=(
                        "**Data Annotation - Per Item**. Number of human labels per dataset item  "
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
                        "**Data Preprocessing - Protocol**. Description of data manipulation process if applicable   "
                    ),
                    key="metadata-data-preprocessing-protocol",
                    value=metadata.data_preprocessing_protocol,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL, metadata, key),
                )
                key = "metadata-data-preprocessing-manipulation"
                st.text_area(
                    label=(
                        "**Data Preprocessing - Manipulation**. Description of data manipulation process if applicable    "
                    ),
                    key="metadata-data-preprocessing-manipulation",
                    value=metadata.data_preprocessing_manipulation,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_PREPROCESSING_MANIPULATION, metadata, key),
                )
                key = "metadata-data-preprocessing-imputation"
                st.text_area(
                    label=(
                        "**Data Preprocessing - Imputation Protocol**. Description of data imputation process if applicable  "
                    ),
                    key="metadata-data-preprocessing-imputation",
                    value=metadata.data_preprocessing_imputation,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_PREPROCESSING_IMPUTATION, metadata, key),
                )
            
       
    with col2.expander("**Uses and social impact**", expanded=True):
        key = "metadata-data-usecases"
        st.text_area(
            label=(
                "**Data Use Cases**. Dataset Use(s) - Training, Testing, Validation, Development or Production Use, Fine Tuning, Others (please specify), Usage Guidelines. Recommended uses"
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
                "**Personal sensitive information**. Personal and sensitive information, if"
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
                "**Social Impact**. Discussion of social impact, if applicable"
            ),
            key=key,
            value=metadata.data_social_impact,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_SOCIAL_IMPACT, metadata, key),
        )
        key = "metadata-data-limitations"
        st.text_area(
            label=("**Data Limitation**. Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses."),
            key=key,
            value=metadata.data_limitation,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_LIMITATION, metadata, key),
        )
        key = "metadata-data-maintenance"
        st.text_area(
            label=("**Data Release Maintenance**. Versioning information in terms of the updating timeframe, the maintainers, and the deprecation policies. "),
            key=key,
            value=metadata.data_maintenance,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_MAINTENANCE, metadata, key),
        )

        
