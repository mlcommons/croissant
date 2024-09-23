"""Source module."""

import enum
from typing import Any

import jsonpath_rw
from jsonpath_rw import lexer
from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node


class FileProperty(enum.IntEnum):
    """Lists the intrinsic properties of a file that are accessible from Croissant.

    Notes:
    - Plural indicates a one-to-many relationship (one row gives many rows), while
      singular indicates a one-to-one relationship.
    - We may use camelCase to be conformed with the names in the JSON-LD Croissant
      standard.
    - We use enum.IntEnum (rather than enum.Enum) in order for FileProperty to be usable
      as column names in pd.DataFrames.

    Warning:
    - At the moment there may be an overlap with existing columns if columns
      have one of the following names.
    """

    content = 1
    filename = 2
    filepath = 3
    fullpath = 4
    lines = 5
    lineNumbers = 6


def is_file_property(file_property: str):
    """Checks if a string is a FileProperty (e.g., "content"->FileProperty.content)."""
    for possible_file_property in FileProperty:
        if possible_file_property.name == file_property:
            return True
    return False


def _cast_file_property(file_property: Any) -> FileProperty | None:
    if file_property is None:
        return None
    elif isinstance(file_property, str) and is_file_property(file_property):
        return FileProperty[file_property]
    raise ValueError(
        "Property fileProperty can only have values in `fullpath`, `filepath` and"
        f" `content`. Got: {file_property}"
    )


@mlc_dataclasses.dataclass
class Extract(Node):
    """Container for possible ways of extracting the data.

    Args:
        column: The column in a columnar format (e.g., CSV).
        file_property: The property of a file to extract.
        json_path: The JSON path if the source is a JSON.
    """

    JSONLD_TYPE = None

    column: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        exclusive_with=["file_property", "json_path"],
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_COLUMN,
    )
    file_property: FileProperty | None = mlc_dataclasses.jsonld_field(
        cast_fn=_cast_file_property,
        default=None,
        input_types=[SDO.Text],
        to_jsonld=lambda ctx, fp: fp.name if isinstance(fp, FileProperty) else fp,
        url=constants.ML_COMMONS_FILE_PROPERTY,
    )
    json_path: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_JSON_PATH,
    )


@mlc_dataclasses.dataclass
class Transform(Node):
    """Container for transformation.

    Args:
        format: The format for a date (e.g. "%Y-%m-%d %H:%M:%S.%f") or for a bounding
            box (e.g., "XYXY").
        regex: A regex pattern with a capturing group to extract information in a
            string.
        replace: A replace pattern, e.g. "pattern_to_remove/pattern_to_add".
        separator: A separator in a string to yield a list.
    """

    JSONLD_TYPE = None

    format: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        exclusive_with=["json_path", "regex", "replace", "separator"],
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_FORMAT,
    )
    json_path: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_JSON_PATH,
    )
    regex: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_REGEX,
    )
    replace: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_REPLACE,
    )
    separator: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_SEPARATOR,
    )


@mlc_dataclasses.dataclass
class Source(Node):
    r"""Python representation of sources and references.

    Croissant accepts several manners to declare sources:

    When the origin is a field:

    ```json
    "source": {
        "field": {"@id": "record_set/name"},
    }
    ```

    When the origin is a FileSet or a FileObject:

    ```json
    "source": {
        "distribution": {"@id": "my-csv"},
        "extract": {
            "column": "my-csv-column"
        }
    }
    ```

    See the specs for all supported parameters by `extract`.

    You can also add one or more transformations with `transform`:

    ```json
    "source": {
        "field": {"@id": "record_set/name"},
        "transform": {
            "format": "yyyy-MM-dd HH:mm:ss.S",
            "regex": "([^\\/]*)\\.jpg",
            "separator": "|"
        }
    }
    ```
    """

    JSONLD_TYPE = None

    distribution: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="",
        from_jsonld=lambda ctx, jsonld: uuid_from_jsonld(jsonld),
        to_jsonld=formatted_uuid_to_json,
        url=constants.SCHEMA_ORG_DISTRIBUTION,
        versions=[CroissantVersion.V_0_8],
    )
    field: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="",
        exclusive_with=["file_object", "file_set", "distribution"],
        from_jsonld=lambda ctx, jsonld: uuid_from_jsonld(jsonld),
        to_jsonld=formatted_uuid_to_json,
        url=constants.ML_COMMONS_FIELD,
    )
    file_object: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="",
        from_jsonld=lambda ctx, jsonld: uuid_from_jsonld(jsonld),
        to_jsonld=formatted_uuid_to_json,
        url=constants.ML_COMMONS_FILE_OBJECT,
    )
    file_set: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="",
        from_jsonld=lambda ctx, jsonld: uuid_from_jsonld(jsonld),
        to_jsonld=formatted_uuid_to_json,
        url=constants.ML_COMMONS_FILE_SET,
    )
    extract: Extract = mlc_dataclasses.jsonld_field(
        default_factory=Extract,
        description="",
        input_types=[Extract],
        url=constants.ML_COMMONS_EXTRACT,
    )
    transforms: list[Transform] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description="",
        input_types=[Transform],
        url=constants.ML_COMMONS_TRANSFORM,
    )

    def __bool__(self):
        """Allows to write `if not node.source` / `if node.source`."""
        return self.uuid is not None

    # TODO(https://github.com/mlcommons/croissant/issues/591): fix typing by having
    # `target_uuid` instead of overriding `Node.uuid`.
    @property
    def uuid(self) -> str | None:  # type: ignore
        """Unique identifier for the source."""
        if self.ctx.is_v0():
            return self.field or self.distribution
        else:
            return self.field or self.file_object or self.file_set

    def get_column(self) -> str | FileProperty:
        """Retrieves the name of the column associated to the source."""
        if self.uuid is None:
            raise ValueError(
                "No UUID! This case already rose an issue and should not happen at run"
                " time."
            )
        if self.extract.column:
            return self.extract.column
        elif self.extract.file_property:
            return self.extract.file_property
        elif self.extract.json_path:
            return self.extract.json_path
        else:
            if self.ctx.is_v0():
                return self.uuid.split("/")[-1]
            return self.uuid

    def check_source(self, add_error: Any):
        """Checks if the source is valid and adds error otherwise."""
        if self.extract.json_path:
            try:
                jsonpath_rw.parse(self.extract.json_path)
            except lexer.JsonPathLexerError as exception:
                add_error(
                    "Wrong JSONPath (https://goessner.net/articles/JsonPath/):"
                    f" {exception}"
                )
