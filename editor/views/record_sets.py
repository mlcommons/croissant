import enum
from typing import Any

import numpy as np
import pandas as pd
from rdflib import term
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


def _get_extract(source: mlc.Source) -> str | None:
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
            return None
    elif source.extract.json_path:
        return ExtractType.JSON_PATH
    return None


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
    return None


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
        return (uid, None)


def _find_joins(fields: list[Field]) -> set[Join]:
    """Finds the existing joins in the fields."""
    joins: set[Join] = set()
    for field in fields:
        if field.source and field.references:
            left = _find_left_or_right(field.source)
            right = _find_left_or_right(field.references)
            joins.add((left, right))
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
                field.data_types = [new_value]
        st.session_state[Metadata].update_field(record_set_key, field_key, field)
    for added_row in result["added_rows"]:
        field = Field(
            name=added_row.get(FieldDataFrame.NAME),
            description=added_row.get(FieldDataFrame.DESCRIPTION),
            data_types=[added_row.get(FieldDataFrame.DATA_TYPE)],
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


class Change(enum.Enum):
    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    DATA_TYPE = "DATA_TYPE"
    SOURCE = "SOURCE"
    SOURCE_EXTRACT = "SOURCE_EXTRACT"
    SOURCE_EXTRACT_COLUMN = "SOURCE_EXTRACT_COLUMN"
    SOURCE_EXTRACT_JSON_PATH = "SOURCE_EXTRACT_JSON_PATH"
    TRANSFORM = "TRANSFORM"
    TRANSFORM_FORMAT = "TRANSFORM_FORMAT"
    REFERENCE = "REFERENCE"
    REFERENCE_EXTRACT = "REFERENCE_EXTRACT"
    REFERENCE_EXTRACT_COLUMN = "REFERENCE_EXTRACT_COLUMN"
    REFERENCE_EXTRACT_JSON_PATH = "REFERENCE_EXTRACT_JSON_PATH"


def _get_source(source: mlc.Source | None, value: Any) -> mlc.Source:
    if not source:
        source = mlc.Source(extract=mlc.Extract())
    if value == ExtractType.COLUMN:
        source.extract = mlc.Extract(column="")
    elif value == ExtractType.FILE_CONTENT:
        source.extract = mlc.Extract(file_property=mlc.FileProperty.content)
    elif value == ExtractType.FILE_NAME:
        source.extract = mlc.Extract(file_property=mlc.FileProperty.filename)
    elif value == ExtractType.FILE_PATH:
        source.extract = mlc.Extract(file_property=mlc.FileProperty.filepath)
    elif value == ExtractType.FILE_FULLPATH:
        source.extract = mlc.Extract(file_property=mlc.FileProperty.fullpath)
    elif value == ExtractType.FILE_LINES:
        source.extract = mlc.Extract(file_property=mlc.FileProperty.lines)
    elif value == ExtractType.FILE_LINE_NUMBERS:
        source.extract = mlc.Extract(file_property=mlc.FileProperty.lineNumbers)
    elif value == ExtractType.JSON_PATH:
        source.extract = mlc.Extract(json_path="")
    return source


def _handle_field_change(
    change: Change,
    record_set_key: int,
    field_key: int,
    field: Field,
    key: str,
    **kwargs,
):
    value = st.session_state[key]
    if change == Change.NAME:
        field.name = value
    elif change == Change.DESCRIPTION:
        field.description = value
    elif change == Change.DATA_TYPE:
        field.data_types = [value]
    elif change == Change.SOURCE:
        node_type = "field" if "/" in value else "distribution"
        source = mlc.Source(uid=value, node_type=node_type)
        field.source = source
    elif change == Change.SOURCE_EXTRACT:
        source = field.source
        source = _get_source(source, value)
        field.source = source
    elif change == Change.SOURCE_EXTRACT_COLUMN:
        if not field.source:
            field.source = mlc.Source(extract=mlc.Extract())
        field.source.extract = mlc.Extract(column=value)
    elif change == Change.SOURCE_EXTRACT_JSON_PATH:
        if not field.source:
            field.source = mlc.Source(extract=mlc.Extract())
        field.source.extract = mlc.Extract(json_path=value)
    elif change == Change.TRANSFORM:
        number = kwargs.get("number")
        if number is not None and number < len(field.source.transforms):
            field.source.transforms[number] = mlc.Transform()
    elif change == TransformType.FORMAT:
        number = kwargs.get("number")
        if number is not None and number < len(field.source.transforms):
            field.source.transforms[number] = mlc.Transform(format=value)
    elif change == TransformType.JSON_PATH:
        number = kwargs.get("number")
        if number is not None and number < len(field.source.transforms):
            field.source.transforms[number] = mlc.Transform(json_path=value)
    elif change == TransformType.REGEX:
        number = kwargs.get("number")
        if number is not None and number < len(field.source.transforms):
            field.source.transforms[number] = mlc.Transform(regex=value)
    elif change == TransformType.REPLACE:
        number = kwargs.get("number")
        if number is not None and number < len(field.source.transforms):
            field.source.transforms[number] = mlc.Transform(replace=value)
    elif change == TransformType.SEPARATOR:
        number = kwargs.get("number")
        if number is not None and number < len(field.source.transforms):
            field.source.transforms[number] = mlc.Transform(separator=value)
    elif change == Change.REFERENCE:
        node_type = "field" if "/" in value else "distribution"
        source = mlc.Source(uid=value, node_type=node_type)
        field.references = source
    elif change == Change.REFERENCE_EXTRACT:
        source = field.references
        source = _get_source(source, value)
        field.references = source
    elif change == Change.REFERENCE_EXTRACT_COLUMN:
        if not field.references:
            field.references = mlc.Source(extract=mlc.Extract())
        field.references.extract = mlc.Extract(column=value)
    elif change == Change.REFERENCE_EXTRACT_JSON_PATH:
        if not field.references:
            field.references = mlc.Source(extract=mlc.Extract())
        field.references.extract = mlc.Extract(json_path=value)
    st.session_state[Metadata].update_field(record_set_key, field_key, field)


def _render_right_panel():
    """Right panel: visualization of the clicked Field."""
    metadata: Metadata = st.session_state.get(Metadata)
    selected: SelectedRecordSet = st.session_state.get(SelectedRecordSet)
    if not selected:
        return
    record_set = selected.record_set
    record_set_key = selected.record_set_key
    with st.expander("**Fields**", expanded=True):
        for field_key, field in enumerate(record_set.fields):
            col1, col2, col3 = st.columns([1, 1, 1])

            key = f"{record_set.name}-{field.name}-name"
            col1.text_input(
                needed_field("Name"),
                placeholder="Name without special character.",
                key=key,
                value=field.name,
                on_change=_handle_field_change,
                args=(Change.NAME, record_set_key, field_key, field, key),
            )
            key = f"{record_set.name}-{field.name}-description"
            col2.text_input(
                "Description",
                placeholder="Provide a clear description of the RecordSet.",
                key=key,
                on_change=_handle_field_change,
                value=field.description,
                args=(Change.DESCRIPTION, record_set_key, field_key, field, key),
            )
            if field.data_types:
                data_type = field.data_types[0]
                if isinstance(data_type, str):
                    data_type = term.URIRef(data_type)
                if data_type in DATA_TYPES:
                    data_type_index = DATA_TYPES.index(data_type)
                else:
                    data_type_index = None
            else:
                data_type_index = None
            key = f"{record_set.name}-{field.name}-datatypes"
            col3.selectbox(
                needed_field("Data type"),
                index=data_type_index,
                options=DATA_TYPES,
                key=key,
                on_change=_handle_field_change,
                args=(Change.DATA_TYPE, record_set_key, field_key, field, key),
            )
            possible_sources = _get_possible_sources(metadata)
            _render_source(
                record_set_key, record_set, field, field_key, possible_sources
            )
            _render_references(
                record_set_key, record_set, field, field_key, possible_sources
            )

            st.divider()

        st.button(
            "Close",
            key=f"{record_set.name}-close-fields",
            type="primary",
            on_click=_handle_close_fields,
        )


def _render_source(
    record_set_key: int,
    record_set: RecordSet,
    field: Field,
    field_key: int,
    possible_sources: list[str],
):
    source = field.source
    postfix = f"source-{record_set.name}-{field.name}"
    col1, col2, col3 = st.columns([1, 1, 1])
    index = (
        possible_sources.index(source.uid) if source.uid in possible_sources else None
    )
    key = f"{postfix}-source"
    col1.selectbox(
        needed_field("Source"),
        index=index,
        options=[s for s in possible_sources if not s.startswith(record_set.name)],
        key=key,
        on_change=_handle_field_change,
        args=(Change.SOURCE, record_set_key, field_key, field, key),
    )
    if source.node_type == "distribution":
        extract = col2.selectbox(
            needed_field("Extract"),
            index=_get_extract_index(source),
            key=f"{postfix}-extract",
            options=EXTRACT_TYPES,
            on_change=_handle_field_change,
            args=(Change.SOURCE_EXTRACT, record_set_key, field_key, field, key),
        )
        if extract == ExtractType.COLUMN:
            key = f"{postfix}-columnname"
            col3.text_input(
                needed_field("Column name"),
                value=source.extract.column,
                key=key,
                on_change=_handle_field_change,
                args=(
                    Change.SOURCE_EXTRACT_COLUMN,
                    record_set_key,
                    field_key,
                    field,
                    key,
                ),
            )
        if extract == ExtractType.JSON_PATH:
            key = f"{postfix}-jsonpath"
            col3.text_input(
                needed_field("JSON path"),
                value=source.extract.json_path,
                key=key,
                on_change=_handle_field_change,
                args=(
                    Change.SOURCE_EXTRACT_JSON_PATH,
                    record_set_key,
                    field_key,
                    field,
                    key,
                ),
            )

    # Transforms
    indices = _get_transforms_indices(field.source)
    if source.transforms:
        for number, (index, transform) in enumerate(zip(indices, source.transforms)):
            _, col2, col3, col4 = st.columns([4.5, 4, 4, 1])
            key = f"{postfix}-{number}-transform"
            selected = col2.selectbox(
                "Transform",
                index=index,
                key=key,
                options=TRANSFORM_TYPES,
                on_change=_handle_field_change,
                args=(Change.TRANSFORM, record_set_key, field_key, field, key),
                kwargs={"number": number},
            )
            if selected == TransformType.FORMAT:
                key = f"{postfix}-{number}-transform-format"
                col3.text_input(
                    needed_field("Format"),
                    value=transform.format,
                    key=key,
                    on_change=_handle_field_change,
                    args=(selected, record_set_key, field_key, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.JSON_PATH:
                key = f"{postfix}-{number}-jsonpath"
                col3.text_input(
                    needed_field("JSON path"),
                    value=transform.json_path,
                    key=key,
                    on_change=_handle_field_change,
                    args=(selected, record_set_key, field_key, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.REGEX:
                key = f"{postfix}-{number}-regex"
                col3.text_input(
                    needed_field("Regular expression"),
                    value=transform.regex,
                    key=key,
                    on_change=_handle_field_change,
                    args=(selected, record_set_key, field_key, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.REPLACE:
                key = f"{postfix}-{number}-replace"
                col3.text_input(
                    needed_field("Replace pattern"),
                    value=transform.replace,
                    key=key,
                    on_change=_handle_field_change,
                    args=(selected, record_set_key, field_key, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.SEPARATOR:
                key = f"{postfix}-{number}-separator"
                col3.text_input(
                    needed_field("Separator"),
                    value=transform.separator,
                    key=key,
                    on_change=_handle_field_change,
                    args=(selected, record_set_key, field_key, field, key),
                    kwargs={"number": number, "type": "format"},
                )

            def _handle_remove_transform(record_set_key, field_key, field, number):
                del field.source.transforms[number]
                st.session_state[Metadata].update_field(
                    record_set_key, field_key, field
                )

            col4.button(
                "✖️",
                key=f"{postfix}-{number}-remove-transform",
                on_click=_handle_remove_transform,
                args=(record_set_key, field_key, field, number),
            )

    def _handle_add_transform(record_set_key, field_key, field):
        if not field.source:
            field.source = mlc.Source(transforms=[])
        field.source.transforms.append(mlc.Transform())
        st.session_state[Metadata].update_field(record_set_key, field_key, field)

    col1, _, _ = st.columns([1, 1, 1])
    col1.button(
        "Add transform on data",
        key=f"{postfix}-close-fields",
        on_click=_handle_add_transform,
        args=(record_set_key, field_key, field),
    )


def _render_references(
    record_set_key: int,
    record_set: RecordSet,
    field: Field,
    field_key: int,
    possible_sources: list[str],
):
    key = f"references-{record_set.name}-{field.name}"
    button_key = f"{key}-add-reference"
    has_clicked_button = st.session_state.get(button_key)
    references = field.references
    if references or has_clicked_button:
        col1, col2, col3 = st.columns([1, 1, 1])
        index = (
            possible_sources.index(references.uid)
            if references.uid in possible_sources
            else None
        )
        key = f"{key}-reference"
        col1.selectbox(
            needed_field("Reference"),
            index=index,
            options=[s for s in possible_sources if not s.startswith(record_set.name)],
            key=key,
            on_change=_handle_field_change,
            args=(Change.REFERENCE, record_set_key, field_key, field, key),
        )
        if references.node_type == "distribution":
            key = f"{key}-extract-references"
            extract = col2.selectbox(
                needed_field("Extract the reference"),
                index=_get_extract_index(references),
                key=key,
                options=EXTRACT_TYPES,
                on_change=_handle_field_change,
                args=(Change.REFERENCE_EXTRACT, record_set_key, field_key, field, key),
            )
            if extract == ExtractType.COLUMN:
                key = f"{key}-columnname"
                col3.text_input(
                    needed_field("Column name"),
                    value=references.extract.column,
                    key=key,
                    on_change=_handle_field_change,
                    args=(
                        Change.REFERENCE_EXTRACT_COLUMN,
                        record_set_key,
                        field_key,
                        field,
                        key,
                    ),
                )
            if extract == ExtractType.JSON_PATH:
                key = f"{key}-jsonpath"
                col3.text_input(
                    needed_field("JSON path"),
                    value=references.extract.json_path,
                    key=key,
                    on_change=_handle_field_change,
                    args=(
                        Change.REFERENCE_EXTRACT_JSON_PATH,
                        record_set_key,
                        field_key,
                        field,
                        key,
                    ),
                )
    elif not has_clicked_button:
        st.button(
            "Add a join with another column/field",
            key=button_key,
        )
