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
            #with st.expander("Data Collection Type", expanded=True):
            #    key = "metadata-data-collection-type"
            #    st.multiselect(
            #        label=("Define the data collection type."),
            #        options=[
            #            "Surveys",
            #            "Secondary Data analysis",
            #            "Physical data collection",
            #            "Direct measurement",
            #            "Document analysis",
            #            "Manual Human Curator",
            #            "Software Collection",
            #            "Experiments",
            #            "Web Scraping",
            #            "Web API",
            #            "Focus groups",
            #           "Self-reporting",
            #            "Customer feedback data",
            #            "User-generated content data",
            #            "Passive Data Collection",
            #            "Others",
            #        ],
            #        key="metadata-data-collection-type",
            #        on_change=handle_rai_change,
            #        args=(RaiEvent.RAI_DATA_COLLECTION_TYPE, metadata, key),
            #    )
            key = "metadata-data-collection-type"
            st.text_area(
                label=("Define the data collection type. Recommended values Recommended values: Surveys, Secondary Data analysis, Physical data collection, Direct measurement, Document analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus groups, Self-reporting, Customer feedback data, User-generated content data, Passive Data Collection, Others"),
                key="metadata-data-collection-type",
                value=metadata.data_collection_type,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_TYPE_OTHERS, metadata, key),
            )
            key = "metadata-data-collection-missing"
            st.text_area(
                label=("**Missing Data**. "),
                key="metadata-data-collection-missing",
                placeholder="Description of missing data in structured/unstructured form",
                value=metadata.data_collection_missing_data,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA, metadata, key),
            )
            key = "metadata-data-collection-raw"
            st.text_area(
                label=("**Raw Data**. "),
                key="metadata-data-collection-raw",
                placeholder="Description of the raw data i.e. source of the data ",
                value=metadata.data_collection_raw_data,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_COLLECTION_RAW, metadata, key),
            )
        with st.expander("**Data Annotation**", expanded=False):
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
                value=metadata.annotator_demographics,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS, metadata, key),
            )
            key = "metadata-data-annotation-tools"
            st.text_area(
                label=(
                    "**Tools**. List of software used for data annotation ( e.g. concept extraction, NER, and additional characteristics of the tools used for annotation to allow for replication or extension)  "
                ),
                key="metadata-data-annotation-tools",
                value=metadata.machine_annotation_tools,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_TOOLS, metadata, key),
            )
            key = "metadata-data-annotation-per-item"
            st.text_area(
                label=(
                    "**Annotation per item**. Number of human labels per dataset item  "
                ),
                key="metadata-data-annotation-per-item",
                value=metadata.annotation_per_item,
                on_change=handle_rai_change,
                args=(RaiEvent.RAI_DATA_ANNOTATION_PER_ITEM, metadata, key),
            )
        with st.expander("**Data Preprocessing**", expanded=False):
            with st.expander("Protocols", expanded=True):
                if metadata.data_preprocessing_protocol:
                    if type(metadata.data_preprocessing_protocol) is list:
                        for index, protocol in enumerate(
                            metadata.data_preprocessing_protocol
                        ):
                            key = "metadata-data-preprocessing-protocol_" + str(index)
                            st.text_area(
                                label=(
                                    "Description of data manipulation process if applicable   "
                                ),
                                key=key,
                                value=protocol,
                                on_change=handle_rai_change,
                                args=(
                                    RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL,
                                    metadata,
                                    key,
                                ),
                            )
                    else:
                        metadata.data_preprocessing_protocol = [
                            metadata.data_preprocessing_protocol
                        ]
                        key = "metadata-data-preprocessing-protocol_" + "0"
                        st.text_area(
                            label=(
                                "Description of data manipulation process if applicable   "
                            ),
                            key=key,
                            value=metadata.data_preprocessing_protocol,
                            on_change=handle_rai_change,
                            args=(
                                RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL,
                                metadata,
                                key,
                            ),
                        )

                else:
                    key = "metadata-data-preprocessing-protocol_" + "0"
                    st.text_area(
                        label=(
                            "Description of data manipulation process if applicable   "
                        ),
                        key=key,
                        on_change=handle_rai_change,
                        args=(RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL, metadata, key),
                    )
                add, remove = st.columns(2)
                with add:
                    if st.button("+ add protocol"):
                        if metadata.data_preprocessing_protocol:
                            metadata.data_preprocessing_protocol.append("")
                            st.rerun()
                        else:
                            metadata.data_preprocessing_protocol = []
                            metadata.data_preprocessing_protocol.append("")
                            st.rerun()
                with remove:
                    if st.button("- remove protocol"):
                        if metadata.data_preprocessing_protocol:
                            metadata.data_preprocessing_protocol.pop()
                            st.rerun()

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
        with st.expander("**Use cases**", expanded=True):
            if metadata.data_use_cases:
                if type(metadata.data_use_cases) is list:
                    for index, protocol in enumerate(metadata.data_use_cases):
                        key = "metadata-data-use-cases_" + str(index)
                        st.text_area(
                            label=(
                                "Dataset use case - training, testing, validation, development or production use, fine tuning, others (please specify), usage guidelines, recommended uses, etc."
                            ),
                            key=key,
                            value=protocol,
                            on_change=handle_rai_change,
                            args=(RaiEvent.RAI_DATA_USE_CASES, metadata, key),
                        )
                else:
                    metadata.data_use_cases = [metadata.data_use_cases]
                    key = "metadata-data-use-cases_" + "0"
                    st.text_area(
                        label=(
                            "Dataset use case - training, testing, validation, development or production use, fine tuning, others (please specify), usage guidelines, recommended uses, etc."
                        ),
                        key=key,
                        value=metadata.data_use_cases,
                        on_change=handle_rai_change,
                        args=(RaiEvent.RAI_DATA_USE_CASES, metadata, key),
                    )
            else:
                key = "metadata-data-use-cases_" + "0"
                st.text_area(
                    label=(
                        "Dataset use case - training, testing, validation, development or production use, fine tuning, others (please specify), usage guidelines, recommended uses, etc."
                    ),
                    key=key,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_USE_CASES, metadata, key),
                )
            add, remove = st.columns(2)
            with add:
                if st.button("+ add use case"):
                    if metadata.data_use_cases:
                        metadata.data_use_cases.append("")
                        st.rerun()
                    else:
                        metadata.data_use_cases = []
                        metadata.data_use_cases.append("")
                        st.rerun()
            with remove:
                if st.button("- remove use case"):
                    if metadata.data_use_cases:
                        metadata.data_use_cases.pop()
                        st.rerun()
        with st.expander("**Data biases**", expanded=True):
            if metadata.data_biases:
                if type(metadata.data_biases) is list:
                    for index, protocol in enumerate(metadata.data_biases):
                        key = "metadata-data-biases_" + str(index)
                        st.text_area(
                            label=(
                                "**Data biases**. Involves understanding the potential risks associated"
                                " with data usage and to prevent unintended and potentially harmful"
                                " consequences that may arise from using models trained on or evaluated"
                                " with the respective data."
                            ),
                            key=key,
                            value=protocol,
                            on_change=handle_rai_change,
                            args=(RaiEvent.RAI_DATA_BIAS, metadata, key),
                        )
                else:
                    metadata.data_biases = [metadata.data_biases]
                    key = "metadata-data-biases_" + "0"
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
            else:
                key = "metadata-data-biases_" + "0"
                st.text_area(
                    label=(
                        "Involves understanding the potential risks associated"
                        " with data usage and to prevent unintended and potentially harmful"
                        " consequences that may arise from using models trained on or evaluated"
                        " with the respective data."
                    ),
                    key=key,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_BIAS, metadata, key),
                )
            add, remove = st.columns(2)
            with add:
                if st.button("+ add bias"):
                    if metadata.data_biases:
                        metadata.data_biases.append("")
                        st.rerun()
                    else:
                        metadata.data_biases = []
                        metadata.data_biases.append("")
                        st.rerun()
            with remove:
                if st.button("- remove bias"):
                    if metadata.data_biases:
                        metadata.data_biases.pop()
                        st.rerun()
        with st.expander("**Personal and sensitive information**", expanded=True):
            if metadata.personal_sensitive_information:
                if type(metadata.personal_sensitive_information) is list:
                    for index, protocol in enumerate(
                        metadata.personal_sensitive_information
                    ):
                        key = "metadata-personal-sensitive-information_" + str(index)
                        st.text_area(
                            label=(
                                "Personal and sensitive information, if"
                                " contained within the dataset, can play an important role in the"
                                " mitigation of any risks and the responsible use of the datasets."
                            ),
                            key=key,
                            value=protocol,
                            on_change=handle_rai_change,
                            args=(RaiEvent.RAI_SENSITIVE, metadata, key),
                        )
                else:
                    metadata.personal_sensitive_information = [
                        metadata.personal_sensitive_information
                    ]
                    key = "metadata-personal-sensitive-information_" + "0"
                    st.text_area(
                        label=(
                            "Personal and sensitive information, if"
                            " contained within the dataset, can play an important role in the"
                            " mitigation of any risks and the responsible use of the datasets."
                        ),
                        key=key,
                        value=metadata.personal_sensitive_information,
                        on_change=handle_rai_change,
                        args=(RaiEvent.RAI_SENSITIVE, metadata, key),
                    )
            else:
                key = "metadata-personal-sensitive-information_" + "0"
                st.text_area(
                    label=(
                        "if"
                        " contained within the dataset, can play an important role in the"
                        " mitigation of any risks and the responsible use of the datasets."
                    ),
                    key=key,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_SENSITIVE, metadata, key),
                )
            add, remove = st.columns(2)
            with add:
                if st.button("+ add sensitive"):
                    if metadata.personal_sensitive_information:
                        metadata.personal_sensitive_information.append("")
                        st.rerun()
                    else:
                        metadata.personal_sensitive_information = []
                        metadata.personal_sensitive_information.append("")
                        st.rerun()
            with remove:
                if st.button("- remove sensitive"):
                    if metadata.personal_sensitive_information:
                        metadata.personal_sensitive_information.pop()
                        st.rerun()

        key = "metadata-social-impact"
        st.text_area(
            label=("**Social impact**. Discussion of social impact, if applicable"),
            key=key,
            value=metadata.data_social_impact,
            on_change=handle_rai_change,
            args=(RaiEvent.RAI_DATA_SOCIAL_IMPACT, metadata, key),
        )
        with st.expander("**Data limitations**", expanded=True):
            if metadata.data_limitations:
                if type(metadata.data_limitations) is list:
                    for index, protocol in enumerate(metadata.data_limitations):
                        key = "metadata-data-limitations_" + str(index)
                        st.text_area(
                            label=(
                                "Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses."
                            ),
                            key=key,
                            value=protocol,
                            on_change=handle_rai_change,
                            args=(RaiEvent.RAI_DATA_LIMITATION, metadata, key),
                        )
                else:
                    metadata.data_limitations = [metadata.data_limitations]
                    key = "metadata-data-limitations_" + "0"
                    st.text_area(
                        label=(
                            "Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses."
                        ),
                        key=key,
                        value=metadata.data_limitations,
                        on_change=handle_rai_change,
                        args=(RaiEvent.RAI_DATA_LIMITATION, metadata, key),
                    )

            else:
                key = "metadata-data-limitations_" + "0"
                st.text_area(
                    label=(
                        "Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses."
                    ),
                    key=key,
                    on_change=handle_rai_change,
                    args=(RaiEvent.RAI_DATA_LIMITATION, metadata, key),
                )
            add, remove = st.columns(2)
            with add:
                if st.button("+ add limitations"):
                    if metadata.data_limitations:
                        metadata.data_limitations.append("")
                        st.rerun()
                    else:
                        metadata.data_limitations = []
                        metadata.data_limitations.append("")
                        st.rerun()
            with remove:
                if st.button("- remove limitations"):
                    if metadata.data_limitations:
                        metadata.data_limitations.pop()
                        st.rerun()
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
