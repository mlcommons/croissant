from core.data_types import convert_dtype
from core.names import find_unique_name
from core.state import Field
from core.state import FileObject
from core.state import FileSet
from core.state import RecordSet
import mlcroissant as mlc


def infer_record_sets(file: FileObject | FileSet, names: set[str]) -> list[RecordSet]:
    """Infers one or several ml:RecordSets from a FileOject/FileSet."""
    # For the moment, there is no inference support for FileSets.
    if isinstance(file, FileSet):
        return []
    # We can infer only if the underlying `pd.DataFrame` could be built.
    if file.df is None:
        return []
    fields = []
    for column, value in file.df.dtypes.items():
        source = mlc.Source(
            uid=file.name,
            node_type="distribution",
            extract=mlc.Extract(column=column),
        )
        field = Field(
            name=column,
            data_types=[convert_dtype(value)],
            source=source,
            references=mlc.Source(),
        )
        fields.append(field)
    return [
        RecordSet(
            fields=fields,
            name=find_unique_name(names, file.name + "_record_set"),
            description="",
        )
    ]
