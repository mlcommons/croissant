"""Utilities for building Croissant files."""

import pathlib
from typing import List

import mlcroissant as mlc


def image_folder_to_croissant(base_directory: str, record_set_directories: List[str]):
    """Creates a Croissant file from a base_directory.

    NOTE: The implementation currently assumes a .JPEG structure!

    base_directory: The directory that contains all records.
    record_set_directories: The directories mapping to individual records.
    return: A Croissant object with records identical to the record_set_directories.
    """
    base_directory = pathlib.Path(base_directory)
    distribution = []
    record_sets = []
    for record_set_dir in record_set_directories:
        record_directories = []
        directory = base_directory / record_set_dir
        for f in directory.iterdir():
            if f.is_dir():
                dir_name = f.name
                description = f"Files in '{f}'"
                dir_path = f.resolve().as_posix()
                name = f"folder_{record_set_dir}_{dir_name}"
                dir_object = mlc.FileObject(
                    name=name,
                    description="",
                    content_url=dir_path,
                    encoding_format="application/x-dir",
                    sha256="main",
                )
                record_directories.append(dir_object)
        distribution.extend(record_directories)
        name = f"{record_set_dir}_images"
        description = f"All ImageFolder images in '{record_set_dir}'"
        encoding_format = "image/jpeg"
        includes = "*.JPEG"
        file_set = mlc.FileSet(
            name=name,
            description=description,
            contained_in=[d.name for d in record_directories],
            encoding_format=encoding_format,
            includes=includes,
        )
        distribution.append(file_set)
        record_set = mlc.RecordSet(
            name=record_set_dir,
            description=f"Record set for {record_set_dir}",
            fields=[
                mlc.Field(
                    name="image_path",
                    description="The class of the image",
                    data_types=mlc.DataType.TEXT,
                    source=mlc.Source(
                        uid=name,
                        node_type="fileSet",
                        extract=mlc.Extract(
                            file_property=(
                                mlc._src.structure_graph.nodes.source.FileProperty.filepath
                            )
                        ),
                    ),
                ),
                mlc.Field(
                    name="image_bytes",
                    description="The bytes of the image",
                    data_types=mlc.DataType.TEXT,
                    source=mlc.Source(
                        uid=name,
                        node_type="fileSet",
                        extract=mlc.Extract(
                            file_property=(
                                mlc._src.structure_graph.nodes.source.FileProperty.content
                            )
                        ),
                    ),
                ),
            ],
        )
        record_sets.append(record_set)
    metadata = mlc.Metadata(
        name="imagefolder_dataset",
        description="An imagefolder dataset",
        distribution=distribution,
        record_sets=record_sets,
    )
    return metadata
