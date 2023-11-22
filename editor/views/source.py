import enum
from typing import Any

import streamlit as st

from core.state import Field
from core.state import Metadata
from core.state import RecordSet
import mlcroissant as mlc
from utils import DF_HEIGHT
from utils import needed_field


class SourceType:
    """The type of the source (distribution or field)."""

    DISTRIBUTION = "distribution"
    FIELD = "field"


class ExtractType:
    """The type of extraction to perform."""

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
    """The type of transformation to perform."""

    FORMAT = "Apply format"
    JSON_PATH = "Apply JSON path"
    REGEX = "Apply regular expression"
    REPLACE = "Replace"
    SEPARATOR = "Separator"


# TODO(marcenacp): Possible to remove?
TRANSFORM_TYPES = [
    TransformType.FORMAT,
    TransformType.JSON_PATH,
    TransformType.REGEX,
    TransformType.REPLACE,
    TransformType.SEPARATOR,
]


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


def _handle_remove_reference(field):
    """Removes the reference from a field."""
    field.references = mlc.Source()


class ChangeEvent(enum.Enum):
    """Event that triggers a field change."""

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


def handle_field_change(
    change: ChangeEvent,
    field: Field,
    key: str,
    **kwargs,
):
    value = st.session_state[key]
    if change == ChangeEvent.NAME:
        field.name = value
    elif change == ChangeEvent.DESCRIPTION:
        field.description = value
    elif change == ChangeEvent.DATA_TYPE:
        field.data_types = [value]
    elif change == ChangeEvent.SOURCE:
        node_type = "field" if "/" in value else "distribution"
        source = mlc.Source(uid=value, node_type=node_type)
        field.source = source
    elif change == ChangeEvent.SOURCE_EXTRACT:
        source = field.source
        source = _get_source(source, value)
        field.source = source
    elif change == ChangeEvent.SOURCE_EXTRACT_COLUMN:
        if not field.source:
            field.source = mlc.Source(extract=mlc.Extract())
        field.source.extract = mlc.Extract(column=value)
    elif change == ChangeEvent.SOURCE_EXTRACT_JSON_PATH:
        if not field.source:
            field.source = mlc.Source(extract=mlc.Extract())
        field.source.extract = mlc.Extract(json_path=value)
    elif change == ChangeEvent.TRANSFORM:
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
    elif change == ChangeEvent.REFERENCE:
        node_type = "field" if "/" in value else "distribution"
        source = mlc.Source(uid=value, node_type=node_type)
        field.references = source
    elif change == ChangeEvent.REFERENCE_EXTRACT:
        source = field.references
        source = _get_source(source, value)
        field.references = source
    elif change == ChangeEvent.REFERENCE_EXTRACT_COLUMN:
        if not field.references:
            field.references = mlc.Source(extract=mlc.Extract())
        field.references.extract = mlc.Extract(column=value)
    elif change == ChangeEvent.REFERENCE_EXTRACT_JSON_PATH:
        if not field.references:
            field.references = mlc.Source(extract=mlc.Extract())
        field.references.extract = mlc.Extract(json_path=value)


def render_source(
    record_set_key: int,
    record_set: RecordSet,
    field: Field,
    field_key: int,
    possible_sources: list[str],
):
    """Renders the form for the source."""
    source = field.source
    prefix = f"source-{record_set.name}-{field.name}"
    col1, col2, col3 = st.columns([1, 1, 1])
    index = (
        possible_sources.index(source.uid) if source.uid in possible_sources else None
    )
    key = f"{prefix}-source"
    col1.selectbox(
        needed_field("Source"),
        index=index,
        options=[s for s in possible_sources if not s.startswith(record_set.name)],
        key=key,
        on_change=handle_field_change,
        args=(ChangeEvent.SOURCE, field, key),
    )
    if source.node_type == "distribution":
        extract = col2.selectbox(
            needed_field("Extract"),
            index=_get_extract_index(source),
            key=f"{prefix}-extract",
            options=EXTRACT_TYPES,
            on_change=handle_field_change,
            args=(ChangeEvent.SOURCE_EXTRACT, field, key),
        )
        if extract == ExtractType.COLUMN:
            key = f"{prefix}-columnname"
            col3.text_input(
                needed_field("Column name"),
                value=source.extract.column,
                key=key,
                on_change=handle_field_change,
                args=(ChangeEvent.SOURCE_EXTRACT_COLUMN, field, key),
            )
        if extract == ExtractType.JSON_PATH:
            key = f"{prefix}-jsonpath"
            col3.text_input(
                needed_field("JSON path"),
                value=source.extract.json_path,
                key=key,
                on_change=handle_field_change,
                args=(ChangeEvent.SOURCE_EXTRACT_JSON_PATH, field, key),
            )

    # Transforms
    indices = _get_transforms_indices(field.source)
    if source.transforms:
        for number, (index, transform) in enumerate(zip(indices, source.transforms)):
            _, col2, col3, col4 = st.columns([4.5, 4, 4, 1])
            key = f"{prefix}-{number}-transform"
            selected = col2.selectbox(
                "Transform",
                index=index,
                key=key,
                options=TRANSFORM_TYPES,
                on_change=handle_field_change,
                args=(ChangeEvent.TRANSFORM, field, key),
                kwargs={"number": number},
            )
            if selected == TransformType.FORMAT:
                key = f"{prefix}-{number}-transform-format"
                col3.text_input(
                    needed_field("Format"),
                    value=transform.format,
                    key=key,
                    on_change=handle_field_change,
                    args=(selected, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.JSON_PATH:
                key = f"{prefix}-{number}-jsonpath"
                col3.text_input(
                    needed_field("JSON path"),
                    value=transform.json_path,
                    key=key,
                    on_change=handle_field_change,
                    args=(selected, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.REGEX:
                key = f"{prefix}-{number}-regex"
                col3.text_input(
                    needed_field("Regular expression"),
                    value=transform.regex,
                    key=key,
                    on_change=handle_field_change,
                    args=(selected, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.REPLACE:
                key = f"{prefix}-{number}-replace"
                col3.text_input(
                    needed_field("Replace pattern"),
                    value=transform.replace,
                    key=key,
                    on_change=handle_field_change,
                    args=(selected, field, key),
                    kwargs={"number": number, "type": "format"},
                )
            elif selected == TransformType.SEPARATOR:
                key = f"{prefix}-{number}-separator"
                col3.text_input(
                    needed_field("Separator"),
                    value=transform.separator,
                    key=key,
                    on_change=handle_field_change,
                    args=(selected, field, key),
                    kwargs={"number": number, "type": "format"},
                )

            def _handle_remove_transform(field, number):
                del field.source.transforms[number]

            col4.button(
                "✖️",
                key=f"{prefix}-{number}-remove-transform",
                on_click=_handle_remove_transform,
                args=(field, number),
            )

    def _handle_add_transform(field):
        if not field.source:
            field.source = mlc.Source(transforms=[])
        field.source.transforms.append(mlc.Transform())

    col1, _, _ = st.columns([1, 1, 1])
    col1.button(
        "Add transform on data",
        key=f"{prefix}-close-fields",
        on_click=_handle_add_transform,
        args=(field,),
    )


def render_references(
    record_set_key: int,
    record_set: RecordSet,
    field: Field,
    field_key: int,
    possible_sources: list[str],
):
    """Renders the form for references."""
    key = f"references-{record_set.name}-{field.name}"
    button_key = f"{key}-add-reference"
    has_clicked_button = st.session_state.get(button_key)
    references = field.references
    if references or has_clicked_button:
        col1, col2, col3, col4 = st.columns([4.5, 4, 4, 1])
        index = (
            possible_sources.index(references.uid)
            if references.uid in possible_sources
            else None
        )
        key = f"{key}-reference"
        col1.selectbox(
            "Reference",
            index=index,
            options=[s for s in possible_sources if not s.startswith(record_set.name)],
            key=key,
            on_change=handle_field_change,
            args=(ChangeEvent.REFERENCE, field, key),
        )
        if references.node_type == "distribution":
            key = f"{key}-extract-references"
            extract = col2.selectbox(
                needed_field("Extract the reference"),
                index=_get_extract_index(references),
                key=key,
                options=EXTRACT_TYPES,
                on_change=handle_field_change,
                args=(ChangeEvent.REFERENCE_EXTRACT, field, key),
            )
            if extract == ExtractType.COLUMN:
                key = f"{key}-columnname"
                col3.text_input(
                    needed_field("Column name"),
                    value=references.extract.column,
                    key=key,
                    on_change=handle_field_change,
                    args=(ChangeEvent.REFERENCE_EXTRACT_COLUMN, field, key),
                )
            if extract == ExtractType.JSON_PATH:
                key = f"{key}-jsonpath"
                col3.text_input(
                    needed_field("JSON path"),
                    value=references.extract.json_path,
                    key=key,
                    on_change=handle_field_change,
                    args=(ChangeEvent.REFERENCE_EXTRACT_JSON_PATH, field, key),
                )
        col4.button(
            "✖️",
            key=f"{key}-remove-reference",
            on_click=_handle_remove_reference,
            args=(field,),
        )
    elif not has_clicked_button:
        st.button(
            "Add a join with another column/field",
            key=button_key,
        )
