import streamlit as st

from core.state import Metadata
from events.metadata import find_license_index
from events.metadata import LICENSES
from events.metadata import LICENSES_URL
from events.rai import handle_rai_change
from events.rai import RaiEvent

_INFO_TEXT = """This tab is the Responsible AI extension of Croissant. **Filling this tab is optional.**
        
More information on how to fill this part at: http://mlcommons.org/croissant/RAI/
"""


def render_rai_metadata():
    """Renders the `Metadata` view."""
    metadata: Metadata = st.session_state[Metadata]
    st.info(_INFO_TEXT, icon="💡")
    col1, col2 = st.columns([1, 1])
    with col1.expander("**Provenance**", expanded=True):
        with st.expander("**Data Collection**", expanded=False):
            key = "metadata-data-collection"
            st.text_area(
                label=("Explanation"),
                placeholder="Explain the key stages of the data collection process to improves understanding of potential users",
                key=key,
                value=metadata.data_collection,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION, metadata, key),
            )
            key = "metadata-data-collection-type"
            st.text_area(
                label=(
                    "Define the data collection type. Recommended values Recommended values: Surveys, Secondary Data analysis, Physical data collection, Direct measurement, Document analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus groups, Self-reporting, Customer feedback data, User-generated content data, Passive Data Collection, Others"
                ),
                key=key,
                value=metadata.data_collection_type,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_TYPE, metadata, key),
            )
            key = "metadata-data-collection-missing"
            st.text_area(
                label=("**Missing Data**."),
                key=key,
                placeholder="Description of missing data in structured/unstructured form",
                value=metadata.data_collection_missing_data,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA, metadata, key),
            )
            key = "metadata-data-collection-raw"
            st.text_area(
                label=("**Raw Data**."),
                key=key,
                placeholder="Description of the raw data i.e. source of the data ",
                value=metadata.data_collection_raw_data,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_RAW, metadata, key),
            )
        with st.expander("**Data Annotation**", expanded=False):
            key = "metadata-data-annotation-protocol"
            st.text_area(
                label=(
                    "**Protocol**. Description of annotations (labels, ratings) produced, including how these were created or authored -  Annotation Workforce Type, Annotation Characteristic(s), Annotation Description(s), Annotation Task(s), Annotation Distribution(s)"
                ),
                key=key,
                value=metadata.data_annotation_protocol,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_PROTOCOL, metadata, key),
            )
            key = "metadata-data-annotation-platform"
            st.text_area(
                label=(
                    "**Platform**. Platform, tool, or library used to collect annotations by human annotators"
                ),
                key=key,
                value=metadata.data_annotation_platform,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_PLATFORM, metadata, key),
            )
            key = "metadata-data-annotation-analysis"
            st.text_area(
                label=(
                    "**Analysis**. Considerations related to the process of converting the “raw” annotations into the labels that are ultimately packaged in a dataset - Uncertainty or disagreement between annotations on each instance as a signal in the dataset, analysis of systematic disagreements between annotators of different socio demographic group,  how the final dataset annotations will relate to individual annotator responses"
                ),
                key=key,
                value=metadata.data_annotation_analysis,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_ANALYSIS, metadata, key),
            )
            key = "metadata-data-annotation-demographics"
            st.text_area(
                label=(
                    "**Demographics**. List of demographics specifications about the annotators"
                ),
                key=key,
                value=metadata.annotator_demographics,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS, metadata, key),
            )
            key = "metadata-data-annotation-tools"
            st.text_area(
                label=(
                    "**Tools**. List of software used for data annotation ( e.g. concept extraction, NER, and additional characteristics of the tools used for annotation to allow for replication or extension)  "
                ),
                key=key,
                value=metadata.machine_annotation_tools,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_TOOLS, metadata, key),
            )
            key = "metadata-data-annotation-per-item"
            st.text_area(
                label=(
                    "**Annotation per item**. Number of human labels per dataset item  "
                ),
                key=key,
                value=metadata.annotation_per_item,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_PER_ITEM, metadata, key),
            )
        with st.expander("**Data Preprocessing**", expanded=False):
            one_to_many_property(
                title="**Protocols**",
                metadata=metadata,
                attributes=metadata.data_preprocessing_protocol,
                key="metadata-data-preprocessing-protocol_",
                label="Description of data manipulation process if applicable ",
                event=RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL,
            )

            key = "metadata-data-manipulation-protocol"
            st.text_area(
                label=(
                    "**Manipulation**. Description of data manipulation process if applicable    "
                ),
                key=key,
                value=metadata.data_manipulation_protocol,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_MANIPULATION_PROTOCOL, metadata, key),
            )
            key = "metadata-data-imputation-protocol"
            st.text_area(
                label=(
                    "**Imputation**. Description of data imputation process if applicable  "
                ),
                key=key,
                value=metadata.data_imputation_protocol,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_IMPUTATION_PROTOCOL, metadata, key),
            )

    with col2.expander("**Data uses and social impact**", expanded=True):
        one_to_many_property(
            title="**Use cases**",
            metadata=metadata,
            attributes=metadata.data_use_cases,
            key="metadata-data-use-cases_",
            label="Dataset use case - training, testing, validation, development or production use, fine tuning, others (please specify), usage guidelines, recommended uses, etc.",
            event=RaiEvent.RAI_DATA_USE_CASES,
        )

        one_to_many_property(
            title="**Data biases**",
            metadata= metadata,
            attributes=metadata.data_biases,
            key="metadata-data-biases_",
            label="**Data biases**. Involves understanding the potential risks associated  with data usage and to prevent unintended and potentially harmful consequences that may arise from using models trained on or evaluated with the respective data",
            event=RaiEvent.RAI_DATA_BIAS,
        )

        one_to_many_property(
            title="**Personal and sensitive information**",
            metadata=metadata,
            attributes=metadata.personal_sensitive_information,
            key="metadata-personal-sensitive-information_",
            label="Personal and sensitive information, if contained within the dataset, can play an important role in the mitigation of any risks and the responsible use of the datasets",
            event=RaiEvent.RAI_SENSITIVE,
        )

        key = "metadata-social-impact"
        st.text_area(
            label=("**Social impact**. Discussion of social impact, if applicable"),
            key=key,
            value=metadata.data_social_impact,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_SOCIAL_IMPACT, metadata, key),
        )

        one_to_many_property(
            "**Data limitations**",
            metadata,
            metadata.data_limitations,
            "metadata-data-limitations_",
            "Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses.",
            RaiEvent.RAI_DATA_LIMITATION,
        )

        key = "metadata-data-maintenance"
        st.text_area(
            label=(
                "**Data release maintenance**. Versioning information in terms of the updating timeframe, the maintainers, and the deprecation policies. "
            ),
            key=key,
            value=metadata.data_release_maintenance_plan,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_MAINTENANCE, metadata, key),
        )


def one_to_many_property(
    title: str, metadata: Metadata, attributes, key: str, label: str, event: str
):
    """Generates a one to many cardinality property. Attributes should be empty, have one element or being a list of elements"""
    with st.expander(title, expanded=True):
        if attributes:
            if not isinstance(attributes, list):  
                attributes = [attributes]
            for index, single_attribute in enumerate(attributes):
                key = key + str(index)
                st.text_area(
                    label=(label),
                    key=key,
                    value=single_attribute,
                    on_change=handle_rai_change,
                    args=(event, metadata, key, index),
                )
        else:
            key = key + "0"
            st.text_area(
                label=(label),
                key=key,
                on_change=handle_rai_change,
                args=(event, metadata, key),
            )
        add, remove = st.columns(2)
        with add:
            if st.button("+ add", key=key + "add"):
                if attributes:
                    attributes.append("")
                    st.rerun()
                else:
                    attributes = []
                    attributes.append("")
                    st.rerun()
        with remove:
            if st.button("- remove", key=key + "remove"):
                if attributes:
                    attributes.pop()
                    st.rerun()
