import enum
from typing import Any

import streamlit as st

from core.data_types import str_to_mlc_data_type
from core.state import Field
from core.state import Metadata
import mlcroissant as mlc


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


class TransformType:
    """The type of transformation to perform."""

    FORMAT = "Apply format"
    JSON_PATH = "Apply JSON path"
    REGEX = "Apply regular expression"
    REPLACE = "Replace"
    SEPARATOR = "Separator"


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


class FieldEvent(enum.Enum):
    """Event that triggers a field change."""

    NAME = "NAME"
    ID = "ID"
    DESCRIPTION = "DESCRIPTION"
    DATA_TYPE = "DATA_TYPE"
    EQUIVALENT_PROPERTY = "EQUIVALENT_PROPERTY"
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


def handle_field_change(
    change: FieldEvent,
    field: Field,
    key: str,
    **kwargs,
):
    value = st.session_state[key]
    if change == FieldEvent.NAME:
        old_name = field.name
        new_name = value
        if old_name != new_name:
            metadata: Metadata = st.session_state[Metadata]
            metadata.rename_field(old_name=old_name, new_name=new_name)
        field.name = value
    elif change == FieldEvent.ID:
        old_id = field.id
        new_id = value
        if old_id != new_id:
            metadata: Metadata = st.session_state[Metadata]
            metadata.rename_id(old_id=old_id, new_id=new_id)
    elif change == FieldEvent.DESCRIPTION:
        field.description = value
    elif change == FieldEvent.EQUIVALENT_PROPERTY:
        field.equivalentProperty = value
    elif change == FieldEvent.DATA_TYPE:
        field.data_types = [str_to_mlc_data_type(value)]
    elif change == FieldEvent.SOURCE:
        source = (
            mlc.Source(field=value) if "/" in value else mlc.Source(file_object=value)
        )
        field.source = source
    elif change == FieldEvent.SOURCE_EXTRACT:
        source = field.source
        source = _get_source(source, value)
        field.source = source
    elif change == FieldEvent.SOURCE_EXTRACT_COLUMN:
        if not field.source:
            field.source = mlc.Source(extract=mlc.Extract())
        field.source.extract = mlc.Extract(column=value)
    elif change == FieldEvent.SOURCE_EXTRACT_JSON_PATH:
        if not field.source:
            field.source = mlc.Source(extract=mlc.Extract())
        field.source.extract = mlc.Extract(json_path=value)
    elif change == FieldEvent.TRANSFORM:
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
    elif change == FieldEvent.REFERENCE:
        source = (
            mlc.Source(field=value) if "/" in value else mlc.Source(file_object=value)
        )
        field.references = source
    elif change == FieldEvent.REFERENCE_EXTRACT:
        source = field.references
        source = _get_source(source, value)
        field.references = source
    elif change == FieldEvent.REFERENCE_EXTRACT_COLUMN:
        if not field.references:
            field.references = mlc.Source(extract=mlc.Extract())
        field.references.extract = mlc.Extract(column=value)
    elif change == FieldEvent.REFERENCE_EXTRACT_JSON_PATH:
        if not field.references:
            field.references = mlc.Source(extract=mlc.Extract())
        field.references.extract = mlc.Extract(json_path=value)
