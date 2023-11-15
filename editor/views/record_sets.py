import numpy as np
import pandas as pd
import streamlit as st

from core.state import Field
from core.state import Metadata
from core.state import RecordSet
from core.state import SelectedRecordSet
import mlcroissant as mlc
from utils import DF_HEIGHT
from utils import needed_field

DATA_TYPES = [
    mlc.DataType.TEXT,
    mlc.DataType.FLOAT,
    mlc.DataType.INTEGER,
    mlc.DataType.BOOL,
    mlc.DataType.URL,
]


class SourceType:
    DISTRIBUTION = "distribution"
    FIELD = "field"


class ExtractType:
    COLUMN = "Column"
    JSON_PATH = "JSON path"
    FILE_CONTENT = "File content"
    FILE_NAME = "File name"
    FILE_PATH = "File path"
    FILE_FULLPATH = "Full path"
    FILE_LINES = "Lines in file"
    FILE_LINE_NUMBERS = "Line numbers in file"


EXTRACT_TYPES = [
    ExtractType.COLUMN,
    ExtractType.JSON_PATH,
    ExtractType.FILE_CONTENT,
    ExtractType.FILE_NAME,
    ExtractType.FILE_PATH,
    ExtractType.FILE_FULLPATH,
    ExtractType.FILE_LINES,
    ExtractType.FILE_LINE_NUMBERS,
]


class TransformType:
    FORMAT = "Apply format"
    JSON_PATH = "Apply JSON path"
    REGEX = "Apply regular expression"
    REPLACE = "Replace"
    SEPARATOR = "Separator"


TRANSFORM_TYPES = [
    TransformType.FORMAT,
    TransformType.JSON_PATH,
    TransformType.REGEX,
    TransformType.REPLACE,
    TransformType.SEPARATOR,
]


def _handle_close_fields():
    st.session_state[SelectedRecordSet] = None


def _handle_on_click_field(
    record_set_key: int,
    record_set: RecordSet,
):
    st.session_state[SelectedRecordSet] = SelectedRecordSet(
        record_set_key=record_set_key,
        record_set=record_set,
    )


def _data_editor_key(record_set_name: str) -> str:
    return f"{record_set_name}-dataframe"


def _get_possible_sources(metadata: Metadata) -> list[str]:
    possible_sources: list[str] = []
    for resource in metadata.distribution:
        possible_sources.append(resource.name)
    for record_set in metadata.record_sets:
        for field in record_set.fields:
            possible_sources.append(f"{record_set.name}/{field.name}")
    return possible_sources


def _get_extract(source: mlc.Source) -> str:
    if source.extract.column:
        return ExtractType.COLUMN
    elif source.extract.file_property:
        file_property = source.extract.file_property
        if file_property == mlc.FileProperty.content:
            return ExtractType.FILE_CONTENT
        elif file_property == mlc.FileProperty.filename:
            return ExtractType.FILE_NAME
        elif file_property == mlc.FileProperty.filepath:
            return ExtractType.FILE_PATH
        elif file_property == mlc.FileProperty.fullpath:
            return ExtractType.FILE_FULLPATH
        elif file_property == mlc.FileProperty.lines:
            return ExtractType.FILE_LINES
        elif file_property == mlc.FileProperty.lineNumbers:
            return ExtractType.FILE_LINE_NUMBERS
        else:
            raise ValueError(f"impossible value for mlc.FileProperty: {file_property}")
    elif source.extract.json_path:
        return ExtractType.JSON_PATH
    raise ValueError(f"impossible value for mlc.Source: {source}")


def _get_extract_index(source: mlc.Source) -> int | None:
    extract = _get_extract(source)
    if extract in EXTRACT_TYPES:
        return EXTRACT_TYPES.index(extract)
    return None


def _get_transforms(source: mlc.Source) -> list[str]:
    transforms = source.transforms
    return [_get_transform(transform) for transform in transforms]


def _get_transform(transform: mlc.Transform) -> str | None:
    if transform.format:
        return TransformType.FORMAT
    elif transform.json_path:
        return TransformType.JSON_PATH
    elif transform.regex:
        return TransformType.REGEX
    elif transform.replace:
        return TransformType.REPLACE
    elif transform.separator:
        return TransformType.SEPARATOR
    raise ValueError(f"impossible value for mlc.Transform: {transform}")


def _get_transforms_indices(source: mlc.Source) -> list[int]:
    transforms = _get_transforms(source)
    return [
        TRANSFORM_TYPES.index(transform) if transform in TRANSFORM_TYPES else None
        for transform in transforms
    ]


LeftOrRight = tuple[str, str]
Join = tuple[LeftOrRight, LeftOrRight]


def _find_left_or_right(source: mlc.Source) -> LeftOrRight:
    uid = source.uid
    if "/" in uid:
        parts = uid.split("/")
        return (parts[0], parts[1])
    elif source.extract.column:
        return (uid, source.extract.column)
    elif source.extract.json_path:
        return (uid, source.extract.json_path)
    elif source.extract.file_property:
        return (uid, source.extract.file_property)
    else:
        raise NotImplementedError(
            f"{source=} could not be parsed by the editor. Please contact us on GitHub"
            " by creating a new issue:"
            " https://github.com/mlcommons/croissant/issues/new"
        )


def _find_joins(fields: list[Field]) -> list[Join]:
    """Finds the existing joins in the fields."""
    joins: list[Join] = []
    for field in fields:
        if field.source and field.references:
            left = _find_left_or_right(field.source)
            right = _find_left_or_right(field.references)
            joins.append((left, right))
    return joins


def _handle_fields_change(record_set_key: int, record_set: RecordSet):
    data_editor_key = _data_editor_key(record_set.name)
    result = st.session_state[data_editor_key]
    # `result` has the following structure:
    # {'edited_rows': {1: {}}, 'added_rows': [], 'deleted_rows': []}
    fields = record_set.fields
    for field_key in result["edited_rows"]:
        field = fields[field_key]
        new_fields = result["edited_rows"][field_key]
        for new_field, new_value in new_fields.items():
            if new_field == FieldDataFrame.NAME:
                field.name = new_value
            elif new_field == FieldDataFrame.DESCRIPTION:
                field.description = new_value
            elif new_field == FieldDataFrame.DATA_TYPE:
                field.data_types = new_value
        st.session_state[Metadata].update_field(record_set_key, field_key, field)
    for added_row in result["added_rows"]:
        field = Field(
            name=added_row[FieldDataFrame.NAME],
            description=added_row[FieldDataFrame.DESCRIPTION],
            data_types=[added_row[FieldDataFrame.DATA_TYPE]],
            source=mlc.Source(
                uid="foo",
                node_type="distribution",
                extract=mlc.Extract(column=""),
            ),
            references=mlc.Source(),
        )
        st.session_state[Metadata].add_field(record_set_key, field)
    for field_key in result["deleted_rows"]:
        st.session_state[Metadata].remove_field(record_set_key, field_key)


class FieldDataFrame:
    """Names of the columns in the pd.DataFrame for `fields`."""

    NAME = "Name"
    DESCRIPTION = "Description"
    DATA_TYPE = "Data type"
    SOURCE_UID = "Source"
    SOURCE_EXTRACT = "Source extract"
    SOURCE_TRANSFORM = "Source transform"
    REFERENCE_UID = "Reference"
    REFERENCE_EXTRACT = "Reference extract"


def render_record_sets():
    col1, col2 = st.columns([1, 1])
    with col1:
        _render_left_panel()
    with col2:
        _render_right_panel()


def _render_left_panel():
    """Left panel: visualization of all RecordSets as expandable forms."""
    distribution = st.session_state[Metadata].distribution
    if not distribution:
        st.markdown("Please add resources first.")
        return
    record_sets = st.session_state[Metadata].record_sets
    possible_sources = _get_possible_sources(st.session_state[Metadata])
    record_set: RecordSet
    for key, record_set in enumerate(record_sets):
        title = f"**{record_set.name}** ({len(record_set.fields)} fields)"
        with st.expander(title, expanded=False):
            col1, col2 = st.columns([1, 3])
            name = col1.text_input(
                needed_field("Name"),
                placeholder="Name without special character.",
                key=f"{record_set.name}-name",
                value=record_set.name,
            )
            description = col2.text_input(
                "Description",
                placeholder="Provide a clear description of the RecordSet.",
                key=f"{record_set.name}-description",
                value=record_set.description,
            )
            is_enumeration = st.checkbox(
                "Whether the RecordSet is an enumeration",
                key=f"{record_set.name}-is-enumeration",
                value=record_set.is_enumeration,
            )

            joins = _find_joins(record_set.fields)
            has_join = st.checkbox(
                "Whether the RecordSet contains joins. To add a new join, add a"
                f" field with a source in `{record_set.name}` and a reference to"
                " another RecordSet or FileSet/FileObject.",
                key=f"{record_set.name}-has-joins",
                value=bool(joins),
                disabled=True,
            )
            if has_join:
                for left, right in joins:
                    col1, col2, _, col4, col5 = st.columns([2, 2, 1, 2, 2])
                    col1.text_input(
                        "Left join",
                        disabled=True,
                        value=left[0],
                        key=f"{record_set.name}-left-join-{left}",
                    )
                    col2.text_input(
                        "Left key",
                        disabled=True,
                        value=left[1],
                        key=f"{record_set.name}-left-key-{left}",
                    )
                    col4.text_input(
                        "Right join",
                        disabled=True,
                        value=right[0],
                        key=f"{record_set.name}-right-join-{right}",
                    )
                    col5.text_input(
                        "Right key",
                        disabled=True,
                        value=right[1],
                        key=f"{record_set.name}-right-key-{right}",
                    )

            if (
                name != record_set.name
                or description != record_set.description
                or is_enumeration != record_set.is_enumeration
            ):
                record_set.name = name
                record_set.description = description
                record_set.is_enumeration = is_enumeration
                st.session_state[Metadata].update_record_set(key, record_set)
            names = [field.name for field in record_set.fields]
            descriptions = [field.description for field in record_set.fields]
            # TODO(https://github.com/mlcommons/croissant/issues/350): Allow to display
            # several data types, not only the first.
            data_types = [
                field.data_types[0] if field.data_types else None
                for field in record_set.fields
            ]
            fields = pd.DataFrame(
                {
                    FieldDataFrame.NAME: names,
                    FieldDataFrame.DESCRIPTION: descriptions,
                    FieldDataFrame.DATA_TYPE: data_types,
                },
                dtype=np.str_,
            )
            data_editor_key = _data_editor_key(record_set.name)
            st.markdown(needed_field("Fields"))
            st.data_editor(
                fields,
                use_container_width=True,
                num_rows="dynamic",
                key=data_editor_key,
                column_config={
                    FieldDataFrame.NAME: st.column_config.TextColumn(
                        FieldDataFrame.NAME,
                        help="Name of the field",
                        required=True,
                    ),
                    FieldDataFrame.DESCRIPTION: st.column_config.TextColumn(
                        FieldDataFrame.DESCRIPTION,
                        help="Description of the field",
                        required=False,
                    ),
                    FieldDataFrame.DATA_TYPE: st.column_config.SelectboxColumn(
                        FieldDataFrame.DATA_TYPE,
                        help="The Croissant type",
                        options=DATA_TYPES,
                        required=True,
                    ),
                },
                on_change=_handle_fields_change,
                args=(key, record_set),
            )

            st.button(
                "Edit fields details",
                key=f"{record_set.name}-show-fields",
                on_click=_handle_on_click_field,
                args=(key, record_set),
            )


def _render_right_panel():
    """Right panel: visualization of the clicked Field."""
    metadata: Metadata = st.session_state.get(Metadata)
    selected: SelectedRecordSet = st.session_state.get(SelectedRecordSet)
    if not selected:
        return
    record_set = selected.record_set
    with st.expander("**Fields**", expanded=True):
        for _, field in enumerate(record_set.fields):
            col1, col2, col3 = st.columns([1, 1, 1])
            col1.text_input(
                needed_field("Name"),
                placeholder="Name without special character.",
                key=f"{record_set.name}-{field.name}-name",
                value=field.name,
            )
            col2.text_input(
                "Description",
                placeholder="Provide a clear description of the RecordSet.",
                key=f"{record_set.name}-{field.name}-description",
                value=field.description,
            )
            if field.data_types:
                data_type_index = DATA_TYPES.index(field.data_types[0])
            else:
                data_type_index = 0
            col3.selectbox(
                needed_field("Data type"),
                index=data_type_index,
                options=DATA_TYPES,
                key=f"{record_set.name}-{field.name}-datatypes",
            )
            possible_sources = _get_possible_sources(metadata)
            _render_source(record_set, field, possible_sources)
            _render_references(record_set, field, possible_sources)

            st.divider()

        st.button(
            "Close",
            key=f"{record_set.name}-close-fields",
            type="primary",
            on_click=_handle_close_fields,
        )


def _render_source(
    record_set: RecordSet,
    field: Field,
    possible_sources: list[str],
):
    source = field.source
    key = f"source-{record_set.name}-{field.name}"
    col1, col2, col3 = st.columns([1, 1, 1])
    index = (
        possible_sources.index(source.uid) if source.uid in possible_sources else None
    )
    col1.selectbox(
        needed_field("Source"),
        index=index,
        options=[s for s in possible_sources if not s.startswith(record_set.name)],
        key=f"{key}-source",
    )
    if source.node_type == "distribution":
        extract = col2.selectbox(
            needed_field("Extract"),
            index=_get_extract_index(source),
            key=f"{key}-extract",
            options=EXTRACT_TYPES,
        )
        if extract == ExtractType.COLUMN:
            col3.text_input(
                needed_field("Column name"),
                value=source.extract.column,
                key=f"{key}-columnname",
            )
        if extract == ExtractType.JSON_PATH:
            col3.text_input(
                needed_field("JSON path"),
                value=source.extract.json_path,
                key=f"{key}-jsonpath",
            )

    # Transforms
    _, col2, col3 = st.columns([1, 1, 1])
    indices = _get_transforms_indices(field.source)
    if source.transforms:
        for index, transform in zip(indices, source.transforms):
            transform = col2.selectbox(
                "Transform",
                index=index,
                key=f"{key}-{index}-transform",
                options=TRANSFORM_TYPES,
            )
            if transform == TransformType.FORMAT:
                col3.text_input(
                    needed_field("Format"),
                    value=transform.format,
                    key=f"{key}-{index}-transform-format",
                )

    def _handle_add_transform():
        # TODO(marcenacp): move this above and handle add_transform.
        pass

    col2.button(
        "Add transform on data",
        key=f"{key}-close-fields",
        on_click=_handle_add_transform,
    )


def _render_references(
    record_set: RecordSet,
    field: Field,
    possible_sources: list[str],
):
    key = f"source-{record_set.name}-{field.name}"

    def _handle_add_reference():
        # TODO(marcenacp): move this above and handle add_transform.
        pass

    references = field.references
    if references:
        col1, col2, col3 = st.columns([1, 1, 1])
        index = (
            possible_sources.index(references.uid)
            if references.uid in possible_sources
            else None
        )
        col1.selectbox(
            needed_field("Reference"),
            index=index,
            options=[s for s in possible_sources if not s.startswith(record_set.name)],
            key=f"{key}-reference",
        )
        if references.node_type == "distribution":
            extract = col2.selectbox(
                needed_field("Extract the reference"),
                index=_get_extract_index(references),
                key=f"{key}-extract-references",
                options=EXTRACT_TYPES,
            )
            if extract == ExtractType.COLUMN:
                col3.text_input(
                    needed_field("Column name"),
                    value=references.extract.column,
                    key=f"{key}-columnname",
                )
            if extract == ExtractType.JSON_PATH:
                col3.text_input(
                    needed_field("JSON path"),
                    value=references.extract.json_path,
                    key=f"{key}-jsonpath",
                )
    else:
        _, col2 = st.columns([1, 2])
        col2.button(
            "Add a join with another column/field",
            key=f"{key}-add-reference",
            on_click=_handle_add_reference,
        )
